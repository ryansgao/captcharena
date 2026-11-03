#!/usr/bin/env -S uv run --project solver python
"""solve.py — the tiered CAPTCHA solver (a measurement and research harness, own browser, own domain and local clones).

    solve.py [solve] --url URL [--max-step N] [--headed] [--kinds k1,k2] [--series NAME]
                                     solve every CAPTCHA on the page; one JSON line per challenge
    solve.py bench --url URL --n 5 [--max-step N] [--steps 4] [--fresh] [--series NAME] [--headed]
                                     N fresh encounters of the same page; per-encounter lines + summary (learning curve)
    solve.py trust [--headed]        read the browser's reCAPTCHA v3 score on our measurement page (router input)
    solve.py cache [--clear PREFIX]  saved solutions (ladder step 3) and their evidence
    solve.py models                  the free vision chain usable right now, and today's call counts
    solve.py writeback --json FILE   teach the cache from an outside solve (needs a server verdict in the record)
    solve.py report [--series S]     summary table of runs/solver-runs.jsonl

Targets: only our own domain (https://measure.captcharena.org, tag runs with ?c=solver-<step>) and the local lab
(lab/server.py: open-source CAPTCHAs on 127.0.0.1). Never third-party sites, never hCaptcha (refused by the router),
never as a token service. Model calls go to free APIs only (ladder/models.py); never Claude.
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ladder import models, router  # noqa: E402
from ladder.cache import Cache  # noqa: E402
from ladder.run import LOG, solve_page  # noqa: E402

PROFILE = os.path.join(HERE, ".profile")          # one persistent profile: history is part of step -1 (trust)
ALLOWED = re.compile(r"^https?://(measure\.captcharena\.org|127\.0\.0\.1|localhost)(:\d+)?(/|$)")
MEASURE = "https://measure.captcharena.org/"


def own_display():
    """Headed runs get their own virtual display, never the automation browser's (:1)."""
    for n in range(91, 99):
        if not os.path.exists(f"/tmp/.X11-unix/X{n}"):
            p = subprocess.Popen(["Xvfb", f":{n}", "-screen", "0", "1366x900x24", "-nolisten", "tcp"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.8)
            return f":{n}", p
    raise RuntimeError("no free display number")


class Browser:
    def __init__(self, headed=False):
        self.headed = headed

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        env = dict(os.environ)
        self.xvfb = None
        if self.headed:
            env["DISPLAY"], self.xvfb = own_display()
        self.ctx = self.pw.chromium.launch_persistent_context(
            PROFILE, headless=not self.headed, env=env, viewport={"width": 1280, "height": 860},
            args=["--disable-blink-features=AutomationControlled"], locale="en-US")
        self.page = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
        return self

    def __exit__(self, *a):
        try:
            self.ctx.close()
            self.pw.stop()
        finally:
            if self.xvfb:
                self.xvfb.terminate()


def guard(url):
    if not ALLOWED.match(url):
        sys.exit(f"refused: {url} — this harness runs only on our own domain and local clones")


def load(page, url, settle=6.0):
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    end = time.time() + settle                         # widgets build after load; the lab sets data-state=ready
    while time.time() < end:
        if page.evaluate("() => document.body && document.body.dataset.state === 'ready'"):
            break
        time.sleep(0.25)
    else:
        return
    time.sleep(0.3)


def steps_arg(a):
    return [int(x) for x in a.steps.split(",")] if a.steps else None


def cmd_solve(a):
    guard(a.url)
    trust = a.trust if a.trust is not None else router.read_trust()
    with Browser(a.headed) as b:
        load(b.page, a.url)
        lines = solve_page(b.page, a.max_step, trust, a.series, a.kinds.split(",") if a.kinds else None,
                           only_steps=steps_arg(a))
    for ln in lines:
        print(json.dumps({k: ln[k] for k in ("kind", "verdict", "solved_at_step", "seconds", "model_calls", "attempts", "notes")}))
    if not lines:
        print(json.dumps({"verdict": "none", "detail": "no CAPTCHA found"}))


def cmd_bench(a):
    guard(a.url)
    trust = a.trust if a.trust is not None else router.read_trust()
    series = a.series or time.strftime("bench-%Y%m%d-%H%M%S")
    cache = Cache()
    out = []
    with Browser(a.headed) as b:
        for i in range(1, a.n + 1):
            load(b.page, a.url)
            if i == 1 and a.fresh:
                from ladder import kinds as K
                for k in K.detect(b.page):
                    cache.clear(k.name)
            lines = solve_page(b.page, a.max_step, trust, series, a.kinds.split(",") if a.kinds else None, cache,
                               steps_arg(a))
            for ln in lines:
                ln["encounter"] = i
                out.append(ln)
                print(json.dumps({"encounter": i, "kind": ln["kind"], "verdict": ln["verdict"], "step": ln["solved_at_step"],
                                  "s": ln["seconds"], "calls": ln["model_calls"],
                                  "path": [(t["step"], t["outcome"], t.get("engine")) for t in ln["attempts"]]}), flush=True)
            time.sleep(a.pause)
    print(json.dumps({"series": series, **summary(out)}))


def summary(lines):
    by = {}
    for ln in lines:
        by.setdefault(ln["kind"], []).append(ln)
    res = {}
    for kind, ls in by.items():
        passed = [l for l in ls if l["verdict"] == "pass"]
        res[kind] = {"n": len(ls), "passed": len(passed),
                     "median_s": round(statistics.median([l["seconds"] for l in passed]), 1) if passed else None,
                     "model_calls": sum(l["model_calls"] for l in ls),
                     "steps": {str(s): sum(1 for l in passed if l["solved_at_step"] == s) for s in sorted({l["solved_at_step"] for l in passed}, key=str)},
                     "curve_s": [l["seconds"] for l in ls], "curve_step": [l["solved_at_step"] for l in ls]}
    return res


def cmd_trust(a):
    with Browser(a.headed) as b:
        b.page.goto(MEASURE + "?c=solver-trust", wait_until="domcontentloaded")
        score = None
        for _ in range(60):
            t = b.page.locator("#v-recaptcha_v3").inner_text()
            m = re.search(r"score ([0-9.]+)", t)
            if m:
                score = float(m.group(1))
                break
            time.sleep(0.5)
    if score is not None:
        router.save_trust(score, "measure.captcharena.org reCAPTCHA v3 (" + ("headed" if a.headed else "headless") + ")")
    print(json.dumps({"trust": score, "headed": a.headed}))


def cmd_cache(a):
    c = Cache()
    if a.clear is not None:
        c.clear(a.clear)
    for e in c.all():
        print(json.dumps({"type": e["signature"], "status": e["status"], "policy": e["policy"], "uses": e.get("uses"),
                          "evidence": len(e["evidence"]), "origin_step": e.get("origin_step")}))


def cmd_models(a):
    s = models._load()
    print(json.dumps({"chain_now": models.available(), "today": s}, indent=1))


def cmd_writeback(a):
    """{"signature", "kind", "policy", "evidence": {"verdict": "pass", "verdict_source": "measure-page"|"lab-page", ...}}"""
    rec = json.load(open(a.json))
    ev = rec.get("evidence", {})
    if ev.get("verdict") != "pass" or ev.get("verdict_source") not in ("measure-page", "lab-page"):
        sys.exit("refused: a saved solution needs the site's own server verdict (verdict=pass from a known source)")
    if re.search(r"claude|anthropic", json.dumps(rec.get("policy", {})), re.I):
        sys.exit("refused: a saved solution may not call Claude")
    e = Cache().promote(rec["signature"], rec["kind"], rec["policy"], ev, rec.get("step", 5))
    print(json.dumps({"promoted": e["signature"], "policy": e["policy"]}))


def cmd_report(a):
    lines = [json.loads(l) for l in open(LOG)] if os.path.exists(LOG) else []
    if a.series:
        lines = [l for l in lines if l.get("series") and l["series"].startswith(a.series)]
    print(json.dumps(summary(lines), indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", default="solve", choices=["solve", "bench", "trust", "cache", "models", "writeback", "report"])
    ap.add_argument("--url", default="")
    ap.add_argument("--max-step", type=int, default=5)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--kinds", default="", help="only these kinds (prefixes), e.g. gocaptcha-slide,text-image")
    ap.add_argument("--series", default=None)
    ap.add_argument("--trust", type=float, default=None, help="override the measured browser trust (0-1)")
    ap.add_argument("--steps", default="", help="measurement mode: only these ladder steps, e.g. 4 or 3,4")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--pause", type=float, default=1.0)
    ap.add_argument("--fresh", action="store_true", help="bench: forget saved solutions for these kinds first")
    ap.add_argument("--clear", default=None)
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    {"solve": cmd_solve, "bench": cmd_bench, "trust": cmd_trust, "cache": cmd_cache, "models": cmd_models,
     "writeback": cmd_writeback, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
