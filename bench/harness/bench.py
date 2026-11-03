#!/usr/bin/env python3
"""bench.py — one harness over the open CAPTCHA clone suites (plan build step 7, test set 2).

    .venv/bin/python harness/bench.py list [--suite ocw]
    .venv/bin/python harness/bench.py selftest                 each checker says yes to a right answer, no to a wrong one
    .venv/bin/python harness/bench.py debrand-check            every type's page: no vendor name visible, screenshot
    .venv/bin/python harness/bench.py run --solver random,v0 [--suite ocw,hll] [--per-type 3 | --sample FILE]
    .venv/bin/python harness/bench.py report results/runs/*.jsonl

One JSONL row per attempt (results/runs/<run id>.jsonl): suite, type, task id, solver (+ version), pass, time,
cost, which step answered, the rig (browser setup) and the suite commit. The verdict is always the suite's own
server-side checker, read from the verdict tap build.py adds to each server (/bench/verdicts): the solver's own
claim is never used. Suites must be up: `python3 suites/build.py`.
"""
import argparse
import collections
import datetime as dt
import glob
import hashlib
import json
import os
import random
import re
import sys
import threading
import time
import types
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import browser  # noqa: E402
import suites  # noqa: E402
from solvers import SOLVERS  # noqa: E402

BENCH = suites.BENCH
RUNS = os.path.join(BENCH, "results", "runs")
HARNESS_VERSION = "1"


def tap_url(task):
    m = suites.MANIFEST[task.suite]
    if task.suite == "hll":
        types_ = json.load(open(os.path.join(suites.BUILD, "hll", "hll_types.json")))
        return f"{suites.HOST}:{m['port']}/bench/verdicts", 8000 + types_.index(task.type)
    return f"{suites.HOST}:{m['port']}/bench/verdicts", None


def tap(task, after):
    url, port = tap_url(task)
    rows = json.load(urllib.request.urlopen(f"{url}?after={after}", timeout=5))
    return [r for r in rows if port is None or r.get("port") == port]


def tap_head(task):
    """The newest verdict number on this suite's server (all ports): verdicts after it belong to this attempt."""
    url, _ = tap_url(task)
    allrows = json.load(urllib.request.urlopen(f"{url}?after=0", timeout=5))
    return allrows[-1]["seq"] if allrows else 0


def install_routes(page, task):
    def block(route, request):
        route.abort()
    page.route(re.compile(r".*(/api/get_ground_truth|/api/answer|/api/last_result|/bench/verdicts).*"), block)
    for prefix, target in task.rewrite.items():
        page.route(re.compile(r"^https?://[^/]+" + re.escape(prefix) + r"(\?.*)?$"),
                   lambda route, request, t=target: route.continue_(url=t))


def attempt(ctxb, solver, task, deadline, rig):
    """One task, one solver: open, act, read the server's verdict."""
    rng = random.Random(int(hashlib.sha256(f"{solver.name}|{task.key()}".encode()).hexdigest()[:12], 16))
    seq0 = tap_head(task)
    page = watchdog = None
    t0 = time.time()
    res, err = {}, ""
    try:
        if not getattr(solver, "own_browser", False):
            page = ctxb.new_page()
            page.set_default_timeout(8000)                  # no single action may hang an attempt
            target = ctxb.new_cdp_session(page).send("Target.getTargetInfo")["targetInfo"]["targetId"]
            # Watchdog: some page states (a form post mid-navigation) block raw mouse/keyboard calls, which have
            # no timeout. Closing the tab from outside Playwright, over plain HTTP, ends the stuck call.
            watchdog = threading.Timer(deadline + 20, lambda: _close_target(ctxb._bench_cdp, target))
            watchdog.daemon = True
            watchdog.start()
            page.on("dialog", lambda d: d.dismiss())
            install_routes(page, task)
            page.goto(task.url, wait_until="load", timeout=30000)
            t0 = time.time()
        ctx = types.SimpleNamespace(cdp=ctxb._bench_cdp, page=page, task=task, deadline_s=deadline, rng=rng)
        res = solver.solve(ctx) or {}
    except Exception as e:
        err = repr(e)[:200]
    verdict, t_verdict = None, None
    end = time.time() + 4                                  # grace for a submission still in flight
    while time.time() < end:
        rows = tap(task, seq0)
        if rows:
            verdict, t_verdict = rows[0]["pass"], rows[0]["t"]
            break
        time.sleep(0.4)
    if watchdog:
        watchdog.cancel()
    if page:
        try:
            page.close()
        except Exception:
            pass
    return {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "suite": task.suite, "suite_commit": suites.MANIFEST[task.suite]["commit"][:12], "type": task.type,
        "task_id": task.task_id, "frozen": task.frozen, "solver": solver.name, "solver_version": solver.version,
        "rig": rig, "pass": bool(verdict), "verdict": "pass" if verdict else ("fail" if verdict is False else "no-submit"),
        "time_s": round((t_verdict or time.time()) - t0, 2), "cost_usd": res.get("cost_usd", 0.0),
        "step": res.get("step", ""), "note": (res.get("note") or err)[:200], "harness_version": HARNESS_VERSION,
    }


def _close_target(cdp, target):
    try:
        urllib.request.urlopen(f"{cdp}/json/close/{target}", timeout=5)   # GET (Chromium 155 answers "Target is closing")
    except Exception:
        pass


def pick(tasks, per_type, seed=0):
    by = collections.defaultdict(list)
    for t in tasks:
        by[(t.suite, t.type)].append(t)
    out = []
    for k in sorted(by):
        ts = by[k]
        rng = random.Random(f"{seed}|{k}")
        out += rng.sample(ts, min(per_type, len(ts))) if ts[0].frozen else ts[:per_type]
    return out


def load_sample(path):
    keys = json.load(open(path))["tasks"]
    index = {t.key(): t for t in suites.all_tasks()}
    return [index[k] for k in keys if k in index]


def cmd_run(a):
    from playwright.sync_api import sync_playwright
    wanted = a.solver.split(",")
    names = a.suite.split(",") if a.suite else None
    tasks = load_sample(a.sample) if a.sample else pick(suites.all_tasks(names), a.per_type)
    if names:
        tasks = [t for t in tasks if t.suite in names]
    if a.type:
        tasks = [t for t in tasks if t.type in a.type.split(",")]
    if a.limit:
        tasks = tasks[:a.limit]
    run_id = a.run_id or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(RUNS, exist_ok=True)
    out = a.out or os.path.join(RUNS, f"{run_id}.jsonl")
    print(f"run {run_id}: {len(tasks)} tasks x {wanted} -> {out}", flush=True)
    with browser.replica(offline=True) as cdp, sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(cdp)
        ctxb = br.contexts[0]
        ctxb._bench_cdp = cdp
        rig = "replica:" + browser.version()
        with open(out, "a") as f:
            done = set()
            if os.path.exists(out):                          # rerunning a run id resumes it
                done = {(r["solver"], f"{r['suite']}/{r['type']}/{r['task_id']}")
                        for r in map(json.loads, open(out)) if r.get("verdict") != "skipped"}
            for sname in wanted:
                s = SOLVERS[sname]
                ok, why = s.available()
                for i, t in enumerate(tasks):
                    if (s.name, t.key()) in done:
                        continue
                    if not ok:
                        row = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "suite": t.suite,
                               "type": t.type, "task_id": t.task_id, "solver": s.name, "verdict": "skipped",
                               "pass": None, "note": why, "run_id": run_id, "harness_version": HARNESS_VERSION}
                    else:
                        row = attempt(ctxb, s, t, a.deadline, rig)
                        row["run_id"] = run_id
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    f.flush()
                    if ok:
                        print(f"[{s.name} {i + 1}/{len(tasks)}] {t.key()} {row['verdict']} {row.get('time_s')}s {row.get('step')}", flush=True)
                if not ok:
                    print(f"[{s.name}] skipped {len(tasks)} tasks: {why}", flush=True)
    return out


def cmd_selftest(a):
    """Right and wrong answers straight to each checker: proves the checker and the tap both work."""
    def post(u, d, form=False):
        data = d.encode() if form else json.dumps(d).encode()
        h = {"Content-Type": "application/x-www-form-urlencoded" if form else "application/json"}
        return json.load(urllib.request.urlopen(urllib.request.Request(u, data=data, headers=h), timeout=10))
    B = suites.BUILD
    results = []
    g = json.load(open(f"{B}/ocw/captcha_data/Dice_Count/ground_truth.json"))
    pid = sorted(g)[0]
    base = f"{suites.HOST}:{suites.MANIFEST['ocw']['port']}"
    results.append(("ocw right", post(base + "/api/check_answer", {"puzzle_type": "Dice_Count", "puzzle_id": pid, "answer": g[pid]["sum"]})["correct"] is True))
    results.append(("ocw wrong", post(base + "/api/check_answer", {"puzzle_type": "Dice_Count", "puzzle_id": pid, "answer": -1})["correct"] is False))
    results.append(("ocw leak closed", _status(base + "/api/get_ground_truth", {"puzzle_type": "Dice_Count", "puzzle_id": pid}) == 404))
    base = f"{suites.HOST}:{suites.MANIFEST['nextgen']['port']}"
    results.append(("nextgen leak closed", _status(base + "/api/get_ground_truth", {"puzzle_type": "Mirror", "puzzle_id": "x"}) == 404))
    p = json.load(urllib.request.urlopen(base + "/api/get_puzzle?type=Mirror&puzzle_index=0&seed=0"))
    results.append(("nextgen wrong", post(base + "/api/check_answer", {"puzzle_type": "Mirror", "puzzle_id": p["puzzle_id"], "answer": []}).get("correct") is False))
    c = json.load(open(f"{B}/halligan/apis/amazon/challenges.json"))["challenges"][0]
    base = f"{suites.HOST}:{suites.MANIFEST['halligan']['port']}"
    results.append(("halligan right", post(base + "/amazon/submit", {"id": 1, "state": c["labels"]})["solved"] is True))
    results.append(("halligan wrong", post(base + "/amazon/submit", {"id": 1, "state": [9, 9]})["solved"] is False))
    base = f"{suites.HOST}:{suites.MANIFEST['hll']['port']}"
    urllib.request.urlopen(base + "/").read()
    results.append(("hll wrong", post(base + "/verify", "captcha=zzzz", form=True)["success"] is False))
    results.append(("hll debug answers off", _status(base + "/api/answer") == 404))
    for name in suites.MANIFEST:
        url = f"{suites.HOST}:{suites.MANIFEST[name]['port']}/bench/verdicts"
        results.append((f"{name} tap", isinstance(json.load(urllib.request.urlopen(url)), list)))
    for k, ok in results:
        print(("PASS " if ok else "FAIL ") + k)
    return 0 if all(ok for _, ok in results) else 1


def _status(url, body=None):
    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                     headers={"Content-Type": "application/json"})
        return urllib.request.urlopen(req, timeout=10).status
    except urllib.error.HTTPError as e:
        return e.code


def cmd_debrand_check(a):
    """Load one task per type in the replica browser; flag any vendor name a person would see; keep a shot."""
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, os.path.join(BENCH, "suites"))
    from build import VENDOR_RX
    shots = os.path.join(BENCH, "results", "shots")
    os.makedirs(shots, exist_ok=True)
    tasks = pick(suites.all_tasks(a.suite.split(",") if a.suite else None), 1)
    bad = []
    with browser.replica(offline=True) as cdp, sync_playwright() as pw:
        ctxb = pw.chromium.connect_over_cdp(cdp).contexts[0]
        for t in tasks:
            page = ctxb.new_page()
            install_routes(page, t)
            try:
                page.goto(t.url, wait_until="load", timeout=30000)
                time.sleep(2.5)
                seen = [page.title()]
                for fr in page.frames:
                    try:
                        seen.append(fr.evaluate("() => (document.title||'') + ' ' + (document.body ? document.body.innerText : '') + ' ' + "
                                                "[...document.querySelectorAll('img[alt],[aria-label],[title]')].map(e => (e.alt||'') + ' ' + (e.getAttribute('aria-label')||'') + ' ' + (e.title||'')).join(' ')"))
                    except Exception:
                        pass
                hits = sorted({m.group(0).lower() for s in seen for m in VENDOR_RX.finditer(s or "")})
                name = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{t.suite}-{t.type}") + ".png"
                page.screenshot(path=os.path.join(shots, name))
                print(f"{'FLAG' if hits else 'ok  '} {t.key()} {hits if hits else ''}")
                if hits:
                    bad.append((t.key(), hits))
            except Exception as e:
                print(f"ERR  {t.key()} {repr(e)[:120]}")
                bad.append((t.key(), ["load error"]))
            finally:
                page.close()
    out = os.path.join(BENCH, "results", "debrand-check.json")
    json.dump({"date": dt.date.today().isoformat(), "types_checked": len(tasks), "flagged": bad}, open(out, "w"), indent=1)
    print(f"{len(tasks)} types checked, {len(bad)} flagged -> {out}")
    return 1 if bad else 0


def summarise(rows):
    agg = collections.defaultdict(lambda: [0, 0, 0, 0.0, 0.0])   # attempts, passes, no-submit, time, cost
    for r in rows:
        if r.get("verdict") == "skipped":
            continue
        a = agg[(r["suite"], r["type"], r["solver"])]
        a[0] += 1
        a[1] += bool(r["pass"])
        a[2] += r["verdict"] == "no-submit"
        a[3] += r.get("time_s") or 0
        a[4] += r.get("cost_usd") or 0
    return agg


def cmd_report(a):
    rows = [json.loads(l) for p in a.files for l in open(p) if l.strip()]
    agg = summarise(rows)
    by_suite = collections.defaultdict(lambda: [0, 0, 0])
    print("| suite | type | solver | pass / tried | no submit | mean time s | cost $ |")
    print("|---|---|---|---|---|---|---|")
    for (s, t, so), (n, p, ns, tm, c) in sorted(agg.items()):
        by_suite[(s, so)][0] += n
        by_suite[(s, so)][1] += p
        by_suite[(s, so)][2] += ns
        if not a.suites_only:
            print(f"| {s} | {t} | {so} | {p}/{n} | {ns} | {tm / n:.1f} | {c:.2f} |")
    print("\n| suite | solver | pass / tried | pass rate | no submit |\n|---|---|---|---|---|")
    for (s, so), (n, p, ns) in sorted(by_suite.items()):
        print(f"| {s} | {so} | {p}/{n} | {100 * p / n:.1f}% | {ns} |")
    skipped = collections.Counter((r["solver"], r.get("note", "")) for r in rows if r.get("verdict") == "skipped")
    for (so, why), n in skipped.items():
        print(f"\nskipped: {so} x{n}: {why}")


def cmd_list(a):
    c = collections.Counter((t.suite, t.type) for t in suites.all_tasks(a.suite.split(",") if a.suite else None))
    for (s, t), n in sorted(c.items()):
        print(f"{s}\t{t}\t{n}")
    print(f"{len(c)} types, {sum(c.values())} tasks")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--suite", default="")
    sub.add_parser("selftest")
    p = sub.add_parser("debrand-check"); p.add_argument("--suite", default="")
    p = sub.add_parser("run")
    p.add_argument("--solver", default="random")
    p.add_argument("--suite", default="")
    p.add_argument("--per-type", type=int, default=3)
    p.add_argument("--sample", default="")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--deadline", type=int, default=90)
    p.add_argument("--run-id", default="")
    p.add_argument("--type", default="", help="only these types (comma list)")
    p.add_argument("--out", default="")
    p = sub.add_parser("report"); p.add_argument("files", nargs="+"); p.add_argument("--suites-only", action="store_true")
    a = ap.parse_args()
    return {"list": cmd_list, "selftest": cmd_selftest, "debrand-check": cmd_debrand_check, "run": cmd_run,
            "report": cmd_report}[a.cmd](a) or 0


if __name__ == "__main__":
    r = main()
    sys.exit(r if isinstance(r, int) else 0)
