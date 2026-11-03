"""The bench's own browsers. Never the shared the automation browser (127.0.0.1:9223): another agent runs timed
experiments in it, and a benchmark must not touch the agent accounts' profile.

Setups ("rigs"), named in every result row:
  replica      the automation browser setup, copied: /usr/bin/chromium, headed, on a private virtual screen (Xvfb),
               the same launch flags as ops/browser-cdp-launch.sh, a fresh throwaway profile, CDP on 127.0.0.1.
               Solvers attach over CDP exactly as captcha.py attaches to the real one. This is "the browser our
               solver drives". Not copied: the agent accounts' profile (cookies, history) and the tab-groups
               extension.
  pw-headless  control: Playwright's own launch (automation flags on), headless, same binary.
  pw-headed    control: Playwright's own launch, headed on the private screen.
offline=True blocks every name lookup except 127.0.0.1/localhost at the browser level (--host-resolver-rules),
so clone pages cannot call any vendor or the internet, whatever their code says.
"""
import contextlib
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request

CHROMIUM = "/usr/bin/chromium"
DISPLAY = os.environ.get("BENCH_DISPLAY", ":88")
SCREEN = "1440x900x24"
OFFLINE_RULES = "MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost"
# Copied from ops/browser-cdp-launch.sh (headed branch), 2026-11-03.
REPLICA_FLAGS = ["--password-store=basic", "--no-first-run", "--no-default-browser-check", "--start-maximized",
                 "--hide-crash-restore-bubble", "--disk-cache-size=268435456",
                 "--disable-background-timer-throttling", "--disable-backgrounding-occluded-windows",
                 "--disable-renderer-backgrounding", "--allow-browser-signin=false"]


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


@contextlib.contextmanager
def screen():
    """A private X display for headed browsers; reused if one is already up on BENCH_DISPLAY."""
    num = DISPLAY.lstrip(":")
    sock = f"/tmp/.X11-unix/X{num}"
    proc = None
    if not os.path.exists(sock):
        proc = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", SCREEN, "-nolisten", "tcp"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            if os.path.exists(sock):
                break
            time.sleep(0.1)
    try:
        yield DISPLAY
    finally:
        if proc:
            proc.terminate()
            proc.wait(5)


@contextlib.contextmanager
def replica(offline=True):
    """Launch the replica browser; yield its CDP URL."""
    with screen() as disp:
        prof = tempfile.mkdtemp(prefix="bench-profile-")
        port = free_port()
        args = [CHROMIUM, f"--remote-debugging-port={port}", "--remote-debugging-address=127.0.0.1",
                f"--user-data-dir={prof}", *REPLICA_FLAGS]
        if offline:
            args.append(f"--host-resolver-rules={OFFLINE_RULES}")
        env = dict(os.environ, DISPLAY=disp)
        proc = subprocess.Popen(args + ["about:blank"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp = f"http://127.0.0.1:{port}"
        try:
            for _ in range(100):
                try:
                    json.load(urllib.request.urlopen(cdp + "/json/version", timeout=1))
                    break
                except Exception:
                    time.sleep(0.15)
            else:
                raise RuntimeError("replica browser did not open its CDP port")
            yield cdp
        finally:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
            shutil.rmtree(prof, ignore_errors=True)


def version():
    return subprocess.run([CHROMIUM, "--version"], capture_output=True, text=True).stdout.strip()
