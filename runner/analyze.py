#!/usr/bin/env python3
"""analyze.py — per-condition results of the browser-score experiment, with 95% confidence intervals.

    runner/analyze.py                 server-verified numbers from /api/summary + the runner's own log (default)
    runner/analyze.py --summary-only  only /api/summary (what the hub sees)
    runner/analyze.py --since 2026-11-10   only days from then (e.g. after the reCAPTCHA warm-up)
    runner/analyze.py --json          machine-readable

Two sources, because the server only ever sees a token: /api/summary gives reCAPTCHA v3 scores, pass rates and
interactive rates for every attempt that produced a token; the runner's log (state/runs.jsonl) also has the loads
that produced none (a v2 challenge left unsolved, a Turnstile widget error, a timeout). Intervals are Wilson score
intervals for proportions and a normal interval for the mean v3 score. deep-2 §6.3 "Analysis" asks for ordinal
regression on the factors once stage 1 and 2 data exist; this script is the per-arm table that comes first.
"""
import argparse
import collections
import json
import math
import pathlib
import statistics
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
RUNS = HERE / "state" / "runs.jsonl"
SITE = "https://measure.captcharena.org"
WARMUP_END = "2026-11-10"      # reCAPTCHA v3 real key since 2026-11-03 06:04 UTC + 7 days (Google's warm-up note)
Z = 1.96


def wilson(k, n):
    if not n:
        return None
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return round(p, 3), round(max(0, c - h), 3), round(min(1, c + h), 3)


def fmt(w):
    return "    -" if w is None else f"{w[0]:.2f} [{w[1]:.2f}-{w[2]:.2f}]"


def fetch_summary():
    req = urllib.request.Request(SITE + "/api/summary", headers={"User-Agent": "captcha-runner/1 analyze"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def from_summary(summ, since):
    """condition/source -> lane -> pooled counts across days."""
    out = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.Counter()))
    for r in summ["rows"]:
        if since and r["day"] < since:
            continue
        g = out[(r["condition"], r["source"])][r["lane"]]
        g["n"] += r["n"]
        g["passed"] += r["passed"]
        g["inter_n"] += r["interactive_known"]
        g["inter_yes"] += round((r["interactive_rate"] or 0) * r["interactive_known"])
        for b, c in (r["score_hist"] or {}).items():
            g["score:" + b] += c
    return out


def from_local(since):
    out = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    meta = collections.defaultdict(dict)
    if not RUNS.exists():
        return out, meta
    for raw in RUNS.open():
        d = json.loads(raw)
        if d.get("smoke") or (since and d["ts"][:10] < since):
            continue
        c = d["condition"]
        out[c]["_loads"]["n"] += 1
        out[c]["_loads"]["error"] += bool(d.get("error"))
        meta[c].update(arm=d["arm"], age=d.get("profile_age_days"), version=d.get("browser_version"))
        for lane, v in d["lanes"].items():
            out[c][lane]["n"] += 1
            out[c][lane][v["done"]] += 1
            out[c][lane]["challenged"] += bool(v.get("challenged"))
            out[c][lane]["tick_only"] += v["done"] == "pass" and not v.get("challenged")
    return out, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary-only", action="store_true")
    ap.add_argument("--since")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    summ = fetch_summary()
    server = from_summary(summ, a.since)
    local, meta = ({}, {}) if a.summary_only else from_local(a.since)
    result = {"days": summ["days"], "since": a.since, "warmup_ends": WARMUP_END, "conditions": {}}

    for (cond, source), lanes in sorted(server.items()):
        row = {"source": source, "factors": summ["conditions"].get(cond, {}).get("factors"), "server": {}, "local": {}}
        v3 = lanes.get("recaptcha_v3")
        if v3:
            scores = [float(k[6:]) for k, c in v3.items() if k.startswith("score:") for _ in range(c)]
            m = statistics.mean(scores) if scores else None
            sd = statistics.stdev(scores) if len(scores) > 1 else 0.0
            row["server"]["v3_n"] = len(scores)
            row["server"]["v3_mean"] = None if m is None else (round(m, 3), round(m - Z * sd / math.sqrt(len(scores)), 3),
                                                              round(m + Z * sd / math.sqrt(len(scores)), 3))
            row["server"]["v3_p_ge_0.7"] = wilson(sum(1 for s in scores if s >= 0.7), len(scores))
            row["server"]["v3_hist"] = {k[6:]: c for k, c in sorted(v3.items()) if k.startswith("score:")}
        for lane in ("turnstile", "recaptcha_v2"):
            g = lanes.get(lane)
            if g:
                row["server"][lane + "_interactive"] = wilson(g["inter_yes"], g["inter_n"])
                row["server"][lane + "_pass"] = wilson(g["passed"], g["n"])
        for lane in ("altcha", "cap"):
            g = lanes.get(lane)
            if g:
                row["server"][lane + "_pass"] = wilson(g["passed"], g["n"])
        loc = local.get(cond) if source == "runner" else None
        if loc:
            n = loc["_loads"]["n"]
            row["local"]["loads"] = n
            row["local"]["load_errors"] = loc["_loads"]["error"]
            row["local"].update({k: v for k, v in meta[cond].items()})
            v2 = loc.get("recaptcha_v2")
            if v2:   # "passed on the tick alone": a token with no picture/audio challenge shown
                row["local"]["v2_tick_only_pass"] = wilson(v2["tick_only"], v2["n"])
                row["local"]["v2_challenged"] = wilson(v2["challenged"], v2["n"])
            ts = loc.get("turnstile")
            if ts:
                row["local"]["turnstile_token"] = wilson(ts["pass"], ts["n"])
                row["local"]["turnstile_widget_error"] = wilson(ts["widget-error"], ts["n"])
        result["conditions"][f"{cond} ({source})"] = row

    if a.json:
        print(json.dumps(result, indent=1))
        return
    print(f"days in feed: {summ['days']}   since: {a.since or 'all'}   reCAPTCHA warm-up ends {WARMUP_END}")
    print("Proportions: estimate [95% Wilson interval]. v3 mean: estimate [95% normal interval].\n")
    hdr = f"{'condition (source)':38} {'loads':>5} {'v3 n':>4} {'v3 mean':>18} {'P(v3>=0.7)':>18} " \
          f"{'v2 tick-only pass':>18} {'Turnstile interactive':>21} {'Turnstile token':>18} {'ALTCHA/Cap pass':>11}"
    print(hdr)
    print("-" * len(hdr))
    for name, r in result["conditions"].items():
        s, l = r["server"], r["local"]
        alt = s.get("altcha_pass"), s.get("cap_pass")
        print(f"{name[:38]:38} {l.get('loads', '-'):>5} {s.get('v3_n', '-'):>4} {fmt(s.get('v3_mean')):>18} "
              f"{fmt(s.get('v3_p_ge_0.7')):>18} {fmt(l.get('v2_tick_only_pass')):>18} "
              f"{fmt(s.get('turnstile_interactive')):>21} {fmt(l.get('turnstile_token')):>18} "
              f"{'/'.join('-' if x is None else f'{x[0]:.2f}' for x in alt):>11}")
    print("\nv3 score histograms:")
    for name, r in result["conditions"].items():
        if r["server"].get("v3_hist"):
            extra = r["local"]
            print(f"  {name[:40]:40} {r['server']['v3_hist']}"
                  + (f"  [{extra.get('arm')}, {extra.get('version')}, profile age {extra.get('age')} d]" if extra else ""))


if __name__ == "__main__":
    main()
