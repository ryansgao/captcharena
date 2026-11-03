#!/usr/bin/env python3
"""compute.py — the half-life numbers from every dated result the clock has stored.

    .venv/bin/python halflife/compute.py        -> results/halflife/halflife.json + halflife.md

Definitions (M10, deep-4; written down so every later run means the same thing):
  defence     one CAPTCHA type of a clone suite (suite/type), or one open bot detector (detector:<name>)
  pass rate   share of the frozen sample's tasks the solver passed on that date (detectors: 1 if not flagged)
  broken      pass rate >= BROKEN (0.5): the defence no longer stops this solver more often than not
  first broken  the first dated run where a solver broke it; "time since first broken" counts from there
  survival    first broken - the defence's public date (suite paper date; detector release date). A defence
              still standing is right-censored at today.
  half-life   Kaplan-Meier median survival over all defences, per solver and for "any solver": the time by which
              half the defences are broken. "not reached" while fewer than half are broken.
Inputs: results/runs/*.jsonl rows whose run_id is a clock run (baseline or weekly) and
results/halflife/detector-runs.jsonl.
"""
import collections
import datetime as dt
import glob
import json
import os

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BENCH, "results", "halflife")
BROKEN = 0.5
SUITES = json.load(open(os.path.join(BENCH, "suites", "suites.json")))["suites"]
# Public dates of the detector versions measured (npm publish / commit date / paper date, read 2026-11-03).
DETECTOR_SINCE = {"botd": "2025-11-04", "fpscanner": "2026-08-05", "creepjs": "2026-06-11",
                  "behaviour-2607.26935": "2026-07-29"}


def clock_rows():
    rows = []
    for p in sorted(glob.glob(os.path.join(BENCH, "results", "runs", "*.jsonl"))):
        for line in open(p):
            r = json.loads(line)
            rid = r.get("run_id", "")
            if r.get("verdict") in ("skipped", None) or not (rid.endswith("-baseline") or rid.endswith("-weekly")):
                continue
            rows.append({"date": r["ts"][:10], "defence": f"{r['suite']}/{r['type']}", "solver": r["solver"],
                         "pass": bool(r["pass"]), "since": SUITES[r["suite"]]["published"]})
    det = os.path.join(OUT, "detector-runs.jsonl")
    if os.path.exists(det):
        for line in open(det):
            r = json.loads(line)
            if r.get("solver") != "v0" or r.get("passed") is None:
                continue
            name = r["defence"].split(":", 1)[1]
            rows.append({"date": r["date"], "defence": r["defence"], "solver": "v0", "pass": r["passed"],
                         "since": DETECTOR_SINCE.get(name, r["date"])})
    return rows


def km_median(times):
    """times: [(days, broken?)]. Kaplan-Meier median survival in days, or None if not reached."""
    s = 1.0
    at_risk = len(times)
    for t in sorted({t for t, _ in times}):
        d = sum(1 for tt, b in times if tt == t and b)
        if at_risk and d:
            s *= 1 - d / at_risk
        if s <= 0.5:
            return t
        at_risk -= sum(1 for tt, _ in times if tt == t)
    return None


def main():
    today = dt.date.today()
    rows = clock_rows()
    series = collections.defaultdict(lambda: collections.defaultdict(list))   # (defence, solver) -> date -> [pass]
    since = {}
    for r in rows:
        series[(r["defence"], r["solver"])][r["date"]].append(r["pass"])
        since[r["defence"]] = r["since"]
    table = []
    for (defence, solver), by_date in sorted(series.items()):
        trend = [(d, round(sum(v) / len(v), 3), len(v)) for d, v in sorted(by_date.items())]
        first = next((d for d, rate, _ in trend if rate >= BROKEN), None)
        table.append({"defence": defence, "solver": solver, "since": since[defence], "trend": trend,
                      "first_broken": first,
                      "days_since_first_broken": (today - dt.date.fromisoformat(first)).days if first else None})
    half = {}
    for solver in sorted({t["solver"] for t in table}) + ["any"]:
        per_def = collections.defaultdict(list)
        for t in table:
            if solver in ("any", t["solver"]):
                per_def[t["defence"]].append(t)
        times = []
        for d, ts in per_def.items():
            firsts = [t["first_broken"] for t in ts if t["first_broken"]]
            start = dt.date.fromisoformat(ts[0]["since"])
            if firsts:
                times.append(((dt.date.fromisoformat(min(firsts)) - start).days, True))
            else:
                times.append(((today - start).days, False))
        m = km_median(times)
        half[solver] = {"defences": len(times), "broken": sum(b for _, b in times),
                        "half_life_days": m, "half_life": f"{m} days" if m is not None else "not reached"}
    os.makedirs(OUT, exist_ok=True)
    json.dump({"computed": today.isoformat(), "broken_threshold": BROKEN, "half_life": half, "defences": table},
              open(os.path.join(OUT, "halflife.json"), "w"), indent=1)
    lines = [f"# Half-life clock — computed {today}", "",
             "| solver | defences measured | broken | half-life |", "|---|---|---|---|"]
    lines += [f"| {s} | {h['defences']} | {h['broken']} | {h['half_life']} |" for s, h in half.items()]
    lines += ["", "| defence | solver | public since | latest pass rate | first broken | days since |", "|---|---|---|---|---|---|"]
    for t in table:
        d, rate, n = t["trend"][-1]
        lines.append(f"| {t['defence']} | {t['solver']} | {t['since']} | {rate:.2f} (n={n}, {d}) | "
                     f"{t['first_broken'] or '—'} | {t['days_since_first_broken'] if t['first_broken'] else '—'} |")
    open(os.path.join(OUT, "halflife.md"), "w").write("\n".join(lines) + "\n")
    print(json.dumps(half, indent=1))


if __name__ == "__main__":
    main()
