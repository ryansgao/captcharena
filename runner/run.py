#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright==1.62.0", "camoufox[geoip]==0.5.9"]
# ///
"""run.py — the browser-score experiment's runner (research/deep-2-browser-score.md §6.3; plan.html build step 6).

    runner/run.py batch                 one timer batch: next arms from the randomised queue, spaced, under budget
    runner/run.py one <arm> [--smoke]   one page load in one arm (--smoke tags it so /api/summary drops it)
    runner/run.py arms                  list the arms and their condition tags
    runner/run.py status                today's loads, the queue, the kill switch, profile ages

Each load opens https://measure.captcharena.org/?c=<tag> in the arm's browser, ticks the boxes a person would tick
(reCAPTCHA v2, Cap; Turnstile only if it turns interactive), waits for every live lane's done flag, saves one JSON
line to state/runs.jsonl and closes its tab or browser. It never solves a picture or audio challenge: a challenge
shown is the outcome. (In the baseline arm the agents' CAPTCHA watcher may solve v2 by audio; that is part of that
arm, w1 in its tag.)

CONDITION TAG = "x1-" + one letter-digit pair per factor of §6.3, e.g. x1-n0b0a2s2h0c0d0w1. Levels are listed in
measure/app/main.py FACTOR_LEVELS (and served in /api/summary as factor_levels). x1 = design version 1.

BUDGET: the measurement page caps verify calls per lane per day in two pools; this runner's requests carry
X-Measure-Runner (state/runner-key) so they count against the runner pool (130 reCAPTCHA v3 a day). The runner
itself stops at DAILY_LOADS page loads per UTC day, so the timer can never exceed the pool.

KILL SWITCH: touch runner/OFF (or $CAPTCHA_KILL_DIR/captcha-runner). Batches then exit at once.
"""
import contextlib
import datetime
import fcntl
import json
import os
import pathlib
import random
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
STATE = HERE / "state"
RUNS = STATE / "runs.jsonl"
LOGF = STATE / "runner.log"
QUEUE = STATE / "queue.json"
PROFILES = STATE / "profiles"
KEYF = STATE / "runner-key"
OFF_FILES = [HERE / "OFF"] + ([pathlib.Path(os.environ["CAPTCHA_KILL_DIR"]) / "captcha-runner"]
                             if os.environ.get("CAPTCHA_KILL_DIR") else [])

SITE = os.environ.get("MEASURE_URL", "https://measure.captcharena.org")
SHARED_CDP = "http://127.0.0.1:9222"          # the automation browser, through the tab broker
DEBIAN_CHROMIUM = "/usr/bin/chromium"          # the same binary the shared browser runs
CHROME_STABLE = STATE / "bin/chrome-stable/opt/google/chrome/chrome"   # Google's .deb, extracted (no root)
DISPLAY = ":37"                                # the runner's own virtual screen; never the live view's :1
SCREEN = "1440x900x24"                         # same size and depth as the agents' screen
PER_BATCH = int(os.environ.get("RUNNER_PER_BATCH", "2"))
SPACING_S = (150, 240)                         # between loads: >= 2.5 min (deep-2 §6.3 step 5)
DAILY_LOADS = int(os.environ.get("RUNNER_DAILY_LOADS", "100"))
LOAD_TIMEOUT_S = 90

# Flags the shared browser starts with (ops/browser-cdp-launch.sh), minus what only makes sense there
# (--restore-last-session, the tab-group extension, --start-maximized under openbox -> an explicit window size).
CHROMIUM_FLAGS = ["--password-store=basic", "--no-first-run", "--no-default-browser-check",
                  "--hide-crash-restore-bubble", "--disk-cache-size=268435456",
                  "--disable-background-timer-throttling", "--disable-backgrounding-occluded-windows",
                  "--disable-renderer-backgrounding", "--allow-browser-signin=false",
                  "--window-position=0,0", "--window-size=1440,870"]

# arm -> (factors, how it is launched, extra). Factors per deep-2 §6.3 plus d (headless) and w (watcher).
ARMS = {
    "base":      (dict(n=0, b=0, a=2, s=2, h=0, c=0, d=0, w=1), "shared", {}),
    "fresh":     (dict(n=0, b=0, a=2, s=0, h=0, c=0, d=0, w=0), "chromium", {"profile": None}),
    "aged":      (dict(n=0, b=0, a=2, s=1, h=0, c=0, d=0, w=0), "chromium", {"profile": "aged-chromium"}),
    "headless":  (dict(n=0, b=5, a=3, s=0, h=0, c=0, d=1, w=0), "playwright-headless", {}),
    "exit-syd":  (dict(n=1, b=0, a=2, s=1, h=0, c=0, d=0, w=0), "chromium",
                  {"profile": "aged-chromium-syd", "proxy": os.environ.get("RUNNER_PROXY_N1", ""),
                   "tz": "Australia/Sydney"}),
    "chrome":    (dict(n=0, b=1, a=2, s=1, h=0, c=0, d=0, w=0), "chrome", {"profile": "aged-chrome"}),
    "camoufox":  (dict(n=0, b=2, a=3, s=1, h=0, c=0, d=0, w=0), "camoufox", {"profile": "aged-camoufox"}),
}
if not ARMS["exit-syd"][2]["proxy"]:   # the second exit is a local setting; never run that arm unproxied
    del ARMS["exit-syd"]


def tag(arm, smoke=False):
    f = ARMS[arm][0]
    return "x1-" + "".join(f"{k}{f[k]}" for k in "nbashcdw") + (".smoke" if smoke else "")


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def log(*a):
    STATE.mkdir(parents=True, exist_ok=True)
    line = now().isoformat(timespec="seconds") + " " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with LOGF.open("a") as fh:
        fh.write(line + "\n")


def runner_key():
    """The shared secret that puts this runner's verify calls in the runner pool. Made once; never printed."""
    if not KEYF.exists():
        STATE.mkdir(parents=True, exist_ok=True)
        KEYF.write_text(os.urandom(24).hex())
        KEYF.chmod(0o600)
    return KEYF.read_text().strip()


def profile_age_days(name):
    stamp = PROFILES / name / ".created"
    if not stamp.exists():
        return None
    return round((time.time() - float(stamp.read_text())) / 86400, 2)


def profile_dir(name):
    p = PROFILES / name
    if not p.exists():
        p.mkdir(parents=True)
        (p / ".created").write_text(str(time.time()))
    return p


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def virtual_screen():
    """The runner's own X screen, so its windows never cover the automation browser in the live view."""
    sock = pathlib.Path(f"/tmp/.X11-unix/X{DISPLAY[1:]}")
    proc = None
    if not sock.exists():
        proc = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", SCREEN, "-nolisten", "tcp"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            if sock.exists():
                break
            time.sleep(0.1)
    try:
        yield
    finally:
        if proc:
            proc.terminate()
            proc.wait(10)


def wait_cdp(port, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as r:
                return json.load(r)
        except OSError:
            time.sleep(0.3)
    raise RuntimeError(f"browser on port {port} did not open its debugging port")


@contextlib.contextmanager
def open_page(pw, arm):
    """Yield (page, info) for one load in this arm, and clean up everything it opened."""
    factors, kind, extra = ARMS[arm]
    info = {"profile_age_days": None}
    if kind == "shared":
        browser = pw.chromium.connect_over_cdp(SHARED_CDP)
        page = browser.contexts[0].new_page()          # our own tab (the broker gives each client its own pages)
        info["browser_version"] = browser.version
        try:
            yield page, info
        finally:
            with contextlib.suppress(Exception):
                page.close()
            with contextlib.suppress(Exception):
                browser.close()                          # disconnects only; the shared browser keeps running
        return

    if kind == "playwright-headless":                    # stock Playwright, nothing changed: the negative control
        browser = pw.chromium.launch(headless=True)
        info["browser_version"] = browser.version
        try:
            yield browser.new_page(), info
        finally:
            browser.close()
        return

    with virtual_screen():
        if kind == "camoufox":
            from camoufox.sync_api import NewBrowser
            prof = profile_dir(extra["profile"])
            info["profile_age_days"] = profile_age_days(extra["profile"])
            # os="linux": the fingerprint stays on the real OS (C0); geoip: timezone and locale follow the exit IP.
            ctx = NewBrowser(pw, headless=False, persistent_context=True, user_data_dir=str(prof), os="linux",
                             geoip=True, virtual_display=DISPLAY, i_know_what_im_doing=True)
            info["browser_version"] = "camoufox " + next(
                (p.name for p in (pathlib.Path.home() / ".cache/camoufox/browsers/official").glob("*")), "?")
            try:
                yield ctx.new_page(), info
            finally:
                with contextlib.suppress(Exception):
                    ctx.close()
            return

        binary = DEBIAN_CHROMIUM if kind == "chromium" else str(CHROME_STABLE)
        tmp = None
        if extra.get("profile"):
            prof = profile_dir(extra["profile"])
            info["profile_age_days"] = profile_age_days(extra["profile"])
        else:
            tmp = tempfile.mkdtemp(prefix="fresh-", dir=STATE)
            prof = pathlib.Path(tmp)
            info["profile_age_days"] = 0.0
        port = free_port()
        args = [binary, f"--remote-debugging-port={port}", "--remote-debugging-address=127.0.0.1",
                f"--user-data-dir={prof}", *CHROMIUM_FLAGS]
        if extra.get("proxy"):
            args += [f"--proxy-server={extra['proxy']}", "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]
        env = dict(os.environ, DISPLAY=DISPLAY)
        if extra.get("tz"):
            env["TZ"] = extra["tz"]
        proc = subprocess.Popen(args + ["about:blank"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            wait_cdp(port)
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            info["browser_version"] = browser.version
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            yield page, info
            with contextlib.suppress(Exception):
                browser.close()
        finally:
            proc.terminate()
            try:
                proc.wait(15)
            except subprocess.TimeoutExpired:
                proc.kill()
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)


def live_lanes():
    # Cloudflare refuses Python's default user agent (403); name ourselves instead.
    req = urllib.request.Request(SITE + "/api/config", headers={"User-Agent": "captcha-runner/1 (+runner/README.md)"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return sorted(json.load(r)["lanes"])


def one_load(pw, arm, smoke=False):
    """One page load in one arm. Returns the record saved to state/runs.jsonl."""
    t = tag(arm, smoke)
    rec = {"ts": now().isoformat(timespec="seconds"), "arm": arm, "condition": t, "factors": ARMS[arm][0],
           "smoke": smoke, "lanes": {}}
    t0 = time.time()
    try:
        lanes = live_lanes()
        key = runner_key()
        with open_page(pw, arm) as (page, info):
            rec.update(info)
            # Our runner header, on our own verify endpoint only (never sent to Google or Cloudflare).
            page.route(SITE + "/api/verify",
                       lambda route: route.continue_(headers={**route.request.headers, "x-measure-runner": key}))
            page.goto(f"{SITE}/?c={t}", wait_until="load", timeout=45_000)
            rec["load_ms"] = round((time.time() - t0) * 1000)
            rec["run_id"] = page.evaluate("document.body.dataset.run || null")
            ticked = {"recaptcha_v2": False, "cap": False, "turnstile": False}
            rec["ticked"] = ticked
            end = time.time() + LOAD_TIMEOUT_S
            given_up = set()
            while time.time() < end:
                ds = page.evaluate("Object.assign({}, document.body.dataset)")
                done = {l for l in lanes if ds.get("done_" + l)}
                elapsed = time.time() - t0
                # Tick what a person would tick, a few seconds in. Order matters: an open v2 challenge covers the
                # Cap and Turnstile boxes, so those go first and v2 waits for Turnstile to settle (or 15 s).
                if "cap" in lanes and not ticked["cap"] and elapsed > 3:
                    with contextlib.suppress(Exception):
                        page.locator("#w-cap cap-widget").click(timeout=5000)
                        ticked["cap"] = True
                if "turnstile" in lanes and ds.get("challenged_turnstile") and not ticked["turnstile"]:
                    with contextlib.suppress(Exception):
                        time.sleep(1.5)                  # the box appears just after the callback
                        b = page.locator("#w-turnstile").bounding_box()
                        page.mouse.click(b["x"] + 30, b["y"] + b["height"] / 2)
                        ticked["turnstile"] = True
                ts_settled = "turnstile" not in lanes or "turnstile" in done or ticked["turnstile"] or elapsed > 15
                if "recaptcha_v2" in lanes and not ticked["recaptcha_v2"] and elapsed > 5 and ts_settled:
                    # The v2 box's own frame (the v3 badge is an anchor frame too, so never pick by URL).
                    with contextlib.suppress(Exception):
                        box = page.frame_locator("#w-recaptcha_v2 iframe").first.locator("#recaptcha-anchor")
                        if box.get_attribute("aria-checked", timeout=3000) != "true":
                            box.click(timeout=5000)
                        ticked["recaptcha_v2"] = True
                # A Turnstile widget error is final only if no retry passed within 30 s.
                if ds.get("done_turnstile") == "widget-error" and elapsed < 30:
                    done.discard("turnstile")
                # A v2 challenge we will not solve: give the watcher (base arm) time, then stop waiting.
                if ds.get("challenged_recaptcha_v2") and "recaptcha_v2" not in done:
                    rec.setdefault("v2_challenged_at_s", round(elapsed, 1))
                    if ARMS[arm][0]["w"] == 0 and elapsed - rec["v2_challenged_at_s"] > 5:
                        given_up.add("recaptcha_v2")
                if done | given_up >= set(lanes):
                    break
                time.sleep(0.5)
            if os.environ.get("RUNNER_SHOTS"):                # debugging aid: what the page looked like at the end
                (STATE / "shots").mkdir(exist_ok=True)
                page.screenshot(path=str(STATE / "shots" / f"{rec['ts'][:19].replace(':', '')}-{arm}.png"), full_page=True)
            ds = page.evaluate("Object.assign({}, document.body.dataset)")
            for l in lanes:
                r = {"done": ds.get("done_" + l) or ("challenged" if l in given_up else "timeout"),
                     "challenged": bool(ds.get("challenged_" + l))}
                with contextlib.suppress(Exception):
                    res = json.loads(ds.get("result_" + l) or "null") or {}
                    r.update({k: res.get(k) for k in ("success", "score", "errors", "interactive", "logged",
                                                      "widget_error")
                              if k in res})
                rec["lanes"][l] = r
            rec["webdriver"] = page.evaluate("navigator.webdriver")
            rec["ua"] = page.evaluate("navigator.userAgent")
    except Exception as e:  # one failed load is a data point (recorded), never a crashed batch
        rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    rec["total_ms"] = round((time.time() - t0) * 1000)
    STATE.mkdir(parents=True, exist_ok=True)
    with RUNS.open("a") as fh:
        fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
    summary = " ".join(f"{l}={v['done']}" + (f"({v['score']})" if v.get("score") is not None else "")
                       for l, v in rec["lanes"].items())
    log(f"load {arm} {t} run={rec.get('run_id')} {summary} {rec.get('error', '')}".rstrip())
    return rec


def loads_today():
    day, n = now().date().isoformat(), 0
    if RUNS.exists():
        for raw in RUNS.open():
            if raw.startswith('{"ts":"' + day) and '"smoke":false' in raw:
                n += 1
    return n


def next_arm():
    """Block randomisation: every arm once per block, in a fresh random order each block."""
    q = json.loads(QUEUE.read_text()) if QUEUE.exists() else []
    q = [a for a in q if a in ARMS and arm_available(a)]
    if not q:
        q = [a for a in ARMS if arm_available(a)]
        random.shuffle(q)
    arm = q.pop(0)
    QUEUE.write_text(json.dumps(q))
    return arm


def arm_available(arm):
    kind = ARMS[arm][1]
    if kind == "chrome":
        return CHROME_STABLE.exists()
    if kind == "camoufox":
        return any((pathlib.Path.home() / ".cache/camoufox/browsers").glob("*/*/camoufox-bin"))
    return True


def off():
    return next((str(p) for p in OFF_FILES if p.exists()), None)


def batch():
    from playwright.sync_api import sync_playwright
    STATE.mkdir(parents=True, exist_ok=True)
    lock = open(STATE / "batch.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("batch: another batch is still running; skipped")
        return
    if off():
        log(f"batch: kill switch {off()} present; nothing run")
        return
    done = loads_today()
    if done >= DAILY_LOADS:
        log(f"batch: {done} loads today already (budget {DAILY_LOADS}); nothing run")
        return
    n = min(PER_BATCH, DAILY_LOADS - done)
    log(f"batch: start, {n} load(s), {done} done today")
    with sync_playwright() as pw:
        for i in range(n):
            if off():
                log("batch: kill switch appeared; stopping")
                break
            if i:
                time.sleep(random.uniform(*SPACING_S))
            rec = one_load(pw, next_arm())
            if any(v.get("done") == "capped" for v in rec["lanes"].values()):
                log("batch: the page's daily cap answered; stopping for today's batch")
                break
    log("batch: end")


def status():
    print(f"kill switch: {off() or 'off (runner active)'}")
    print(f"loads today (UTC): {loads_today()} / {DAILY_LOADS}")
    print(f"queue: {QUEUE.read_text() if QUEUE.exists() else '[]'}")
    for a in ARMS:
        p = ARMS[a][2].get("profile")
        print(f"  {a:9} {tag(a):24} available={arm_available(a)}"
              + (f" profile={p} age_days={profile_age_days(p)}" if p else ""))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "batch":
        batch()
    elif cmd == "one":
        from playwright.sync_api import sync_playwright
        arm = sys.argv[2]
        with sync_playwright() as pw:
            print(json.dumps(one_load(pw, arm, smoke="--smoke" in sys.argv), indent=1))
    elif cmd == "arms":
        for a in ARMS:
            print(a, tag(a), ARMS[a][1])
    else:
        status()


if __name__ == "__main__":
    main()
