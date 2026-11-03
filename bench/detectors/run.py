#!/usr/bin/env python3
"""run.py — does a 2026 open bot detector catch the browser our solver drives? (M10 data point 1)

    .venv/bin/python detectors/run.py [--think 3]

Serves detectors/page on 127.0.0.1 and visits it with three setups ("rigs"):
  replica+v0   the agents'-browser replica (harness/browser.py), driven by solver v0's own input code: each step is
               one `captcha.py click|drag` call through harness/v0_shim.py, with a pause between steps standing in
               for the model's look-and-decide time (--think seconds), exactly as the web-captcha skill uses it.
  pw-headless  control: Playwright-launched headless Chromium, page.mouse.click (pointer jumps to the target).
  pw-headed    control: Playwright-launched headed Chromium on the private screen, same input.
Detectors: BotD 2.0.0 (botKind/bot), fpscanner 1.0.8 (fastBotDetection + which checks fired), CreepJS
(headless / like-headless / stealth ratings, from the repo's built page at commit in detectors/README note),
and the two behaviour features of arXiv 2607.26935.

Flag rules (ours, written down because the paper publishes no thresholds):
  BotD        flagged if detect().bot is true
  fpscanner   flagged if fastBotDetection is true
  CreepJS     flagged if headlessRating > 0 or stealthRating > 0 (likeHeadless reported, not used: real
              Linux desktops score on it too)
  behaviour   flagged if mouse_event_rate < 10 Hz (paper: humans produce "dense event streams (10-50 Hz)") or
              teleport_click_ratio > 0.2 (paper: humans "cluster around 0.05")
Appends one row per (rig, detector) to results/halflife/detector-runs.jsonl and the full readings to
results/detectors/<date>.json.
"""
import argparse
import datetime as dt
import functools
import http.server
import json
import os
import subprocess
import sys
import threading
import time

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BENCH, "harness"))
import browser  # noqa: E402

PAGE_DIR = os.path.join(BENCH, "detectors", "page")
OUT = os.path.join(BENCH, "results")


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=PAGE_DIR)
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def centre(page, sel):
    b = page.locator(sel).bounding_box()
    return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2


def v0(cdp, url, *args):
    cmd = ["uv", "run", "--quiet", "--script", os.path.join(BENCH, "harness", "v0_shim.py"), "--cdp", cdp,
           "--log", os.path.join(OUT, "v0-log"), "--", *args, "--url", url]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout.strip()[-200:]


def act(page, think, how, cdp=None, url=None):
    """Click A, B, C, then drag the knob: through v0's primitives (how='v0') or Playwright's (how='pw')."""
    steps = []
    for sel in ("#a", "#b", "#c"):
        time.sleep(think)
        x, y = centre(page, sel)
        if how == "v0":
            steps.append(v0(cdp, url, "click", f"{x:.0f},{y:.0f}"))
        else:
            page.mouse.click(x, y)
    time.sleep(think)
    x, y = centre(page, "#knob")
    tx = x + 376
    if how == "v0":
        steps.append(v0(cdp, url, "drag", f"{x:.0f},{y:.0f}", f"{tx:.0f},{y:.0f}"))
    else:
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(tx, y, steps=10)
        page.mouse.up()
    time.sleep(1)
    return steps


def read(page, base):
    page.bring_to_front()
    page.wait_for_function("window.__benchReady === true", timeout=60000)
    res = page.evaluate("window.__benchResult()")
    creep = page.context.new_page()           # same browser, same context: CreepJS's own page
    try:
        creep.goto(base + "/creepjs/index.html", wait_until="load", timeout=30000)
        creep.bring_to_front()
        creep.wait_for_function("window.Fingerprint && window.Fingerprint.headless", timeout=90000)
        h = creep.evaluate("window.Fingerprint.headless")
        res["creepjs"] = {k: h.get(k) for k in ("headlessRating", "likeHeadlessRating", "stealthRating")}
        res["creepjs"]["fired"] = {grp: [k for k, v in (h.get(grp) or {}).items() if v is True]
                                   for grp in ("headless", "stealth", "likeHeadless")}
    except Exception as e:
        res["creepjs"] = {"error": repr(e)[:200]}
    finally:
        creep.close()
    return res


def verdicts(res):
    b = res.get("behaviour", {})
    c = res.get("creepjs", {})
    fp = res.get("fpscanner") or {}
    rows = {
        "botd": (bool((res.get("botd") or {}).get("bot")), res.get("botd")),
        "fpscanner": (None if "error" in fp else bool(fp.get("fastBotDetection")),
                      {k: v for k, v in (fp.get("fastBotDetectionDetails") or {}).items()
                       if (v.get("detected") if isinstance(v, dict) else v)}
                      if isinstance(fp.get("fastBotDetectionDetails"), dict) else fp),
        "creepjs": (None if "error" in c else bool((c.get("headlessRating") or 0) > 0 or (c.get("stealthRating") or 0) > 0), c),
        "behaviour-2607.26935": (bool(b.get("mouse_event_rate_hz", 0) < 10 or (b.get("teleport_click_ratio") or 0) > 0.2), b),
    }
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--think", type=float, default=3.0)
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    srv, base = serve()
    url = base + "/index.html"
    today = dt.date.today().isoformat()
    readings = {}
    with sync_playwright() as pw:
        with browser.replica(offline=True) as cdp:
            ctx = pw.chromium.connect_over_cdp(cdp).contexts[0]
            page = ctx.new_page()
            page.goto(url, wait_until="load")
            steps = act(page, a.think, "v0", cdp, url)
            readings["replica+v0"] = {**read(page, base), "v0_steps": steps}
            page.close()
        with browser.screen() as disp:
            for rig, headless in (("pw-headless", True), ("pw-headed", False)):
                br = pw.chromium.launch(executable_path=browser.CHROMIUM, headless=headless,
                                        env={**os.environ, "DISPLAY": disp},
                                        args=[f"--host-resolver-rules={browser.OFFLINE_RULES}"])
                page = br.new_context().new_page()
                page.goto(url, wait_until="load")
                act(page, a.think, "pw")
                readings[rig] = read(page, base)
                br.close()
    srv.shutdown()
    os.makedirs(os.path.join(OUT, "detectors"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "halflife"), exist_ok=True)
    json.dump({"date": today, "think_s": a.think, "browser": browser.version(), "readings": readings},
              open(os.path.join(OUT, "detectors", f"{today}.json"), "w"), indent=1)
    with open(os.path.join(OUT, "halflife", "detector-runs.jsonl"), "a") as f:
        for rig, res in readings.items():
            for det, (flag, detail) in verdicts(res).items():
                row = {"date": today, "defence": f"detector:{det}", "solver": "v0" if rig == "replica+v0" else "control",
                       "rig": rig, "flagged": flag, "passed": None if flag is None else not flag,
                       "detail": json.dumps(detail, default=str)[:600]}
                f.write(json.dumps(row) + "\n")
                print(f"{rig:12} {det:22} {'FLAGGED' if flag else ('not flagged' if flag is False else 'n/a')}  {row['detail'][:160]}")


if __name__ == "__main__":
    main()
