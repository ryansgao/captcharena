"""End-to-end check of tokens in Anubis against a running stack (local compose or the public demo).

    uv run --with playwright python e2e/run.py [site]        (default http://localhost:18330/)

Needs e2e/out/ppclient (built from cmd/ppclient) and, for the agent-signature cases, node plus the observatory's
node_modules (../observatory). A real headless Chromium solves Anubis's proof of work, exactly as a visitor would;
every other step is plain HTTP. Prints one PASS/FAIL line per case and timings."""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright

SITE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:18330/").rstrip("/") + "/"
HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.path.join(HERE, "out", "ppclient")
STORE = os.path.join(HERE, "out", "tokens.json")
SIGNER = os.path.join(HERE, "..", "..", "observatory", "tools", "sign-headers.mjs")
OBS_DIR = "https://observatory.captcharena.org/.well-known/http-message-signatures-directory"
CF_DIR = "https://http-message-signatures-example.research.cloudflare.com/.well-known/http-message-signatures-directory"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}{': ' + detail if detail else ''}", flush=True)


def http(path, headers=None, method="GET", data=None):
    req = urllib.request.Request(SITE.rstrip("/") + path, headers={"User-Agent": "captcharena-e2e/1", **(headers or {})}, method=method, data=data)  # Cloudflare refuses the default Python UA (error 1010)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode(errors="replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace"), dict(e.headers)


def client(*args):
    out = subprocess.run([CLIENT, *args], capture_output=True, text=True, timeout=60)
    return out.returncode, out.stdout + out.stderr


# 1. A plain request gets Anubis's proof-of-work page, plus a PrivateToken challenge.
status, body, headers = http("/")
check("no token: Anubis challenge page", "Making sure" in body, f"HTTP {status}")
check("no token: WWW-Authenticate PrivateToken challenge offered", "PrivateToken challenge=" in {k.lower(): v for k, v in headers.items()}.get("www-authenticate", ""))

# 2. A real browser pays the proof of work once.
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    t0 = time.time()
    page.goto(SITE)
    page.wait_for_function('document.body.innerText.includes("Protected page")', timeout=90_000)
    pow_seconds = time.time() - t0
    check("browser solves Anubis proof of work", "after Anubis proof of work" in page.inner_text("body"), f"{pow_seconds:.2f} s to the page")
    cookie = "; ".join(f"{c['name']}={c['value']}" for c in page.context.cookies())
    browser.close()

# 3. The pass buys tokens (cap 10), blind-signed, so the gate cannot link them to this pass later.
if os.path.exists(STORE):
    os.remove(STORE)
code, out = client("fetch", "-site", SITE, "-cookie", cookie, "-n", "11", "-tokens", STORE)
tokens = json.load(open(STORE)) if os.path.exists(STORE) else []
check("one pass buys exactly 10 tokens, the 11th is refused", len(tokens) == 10 and "HTTP 429" in out, out.strip().splitlines()[-1] if out.strip() else out)
code, out = client("fetch", "-site", SITE, "-n", "1", "-tokens", os.path.join(HERE, "out", "none.json"))
check("no pass: token request refused", "HTTP 403" in out, out.strip()[:90])

# 4. Later visits, with no cookie at all, spend a token and skip the proof of work.
first = tokens[0]
t0 = time.time()
code, out = client("get", "-site", SITE, "-tokens", STORE)
token_ms = (time.time() - t0) * 1000
check("token holder skips the proof of work", "without proof of work. Pass: privacy-pass" in out, f"{token_ms:.0f} ms, no cookie sent")
status, body, _ = http("/", {"Authorization": f'PrivateToken token="{first}"'})
check("spent token cannot be reused", status == 401 and "already spent" in body, f"HTTP {status}")
status, body, _ = http("/", {"Authorization": 'PrivateToken token="' + first[:-6] + 'AAAAAA"'})
check("forged token refused", status == 401, f"HTTP {status}: {body.strip()[:60]}")
status, body, _ = http("/", {"Authorization": "PrivateToken token=AAAA"})
check("garbage token refused", status == 401, f"HTTP {status}")

# 5. Verified agents skip the proof of work too; test keys and bad signatures do not.
def signed(agent_dir, key, url=SITE):
    out = subprocess.run(["node", SIGNER, url, agent_dir, key], capture_output=True, text=True, timeout=30)
    return json.loads(out.stdout) if out.returncode == 0 else None

h = signed(OBS_DIR, "own")
if h:
    status, body, _ = http("/", h)
    check("agent with a valid Web Bot Auth signature skips the proof of work", "Pass: web-bot-auth; agent=observatory.captcharena.org" in body, body.strip()[:90])
    status, body, _ = http("/", signed(OBS_DIR, "own", url="https://example.com/"))
    check("signature made for another site gets the proof of work", "Making sure" in body, f"HTTP {status}")
h = signed(CF_DIR, "rfc-test")
if h:
    status, body, _ = http("/", h)
    check("signature with the published RFC 9421 test key gets the proof of work", "Making sure" in body, f"HTTP {status}")

status, body, _ = http("/.well-known/ppgate-stats")
print("gate counters:", body.strip())
print(f"{sum(results)}/{len(results)} cases passed against {SITE}; proof of work {pow_seconds:.2f} s in Chromium, token visit {token_ms:.0f} ms")
sys.exit(0 if all(results) else 1)
