"""Measurement page: real CAPTCHA widgets on our own domain, each scored by the vendor's own server check.

Build-order step 2 of research/plan.html, and the instrument page of research/deep-2-browser-score.md §6.3.
Every widget on the page hands its token to POST /api/verify, which asks the vendor (or our own self-hosted
CAPTCHA server) whether the token is good and appends one JSON line per attempt to the run log. The visitor sees
the same verdict we record.

What is logged, and what is not: no IP address and no cookie of ours. A line holds the lane, the verdict, the
vendor's score and error codes, the token's age, the client's solve time and interactive flag, Cloudflare's
country header, the user agent, and a bounded set of browser signals the page collected (BotD, navigator,
WebGL renderer). Lines made with a vendor TEST key are marked "test" and never mixed with real data.
"""
import datetime
import hashlib
import json
import os
import pathlib
import re
import threading
import time

import altcha
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

HERE = pathlib.Path(__file__).parent
LOG = pathlib.Path(os.environ.get("MEASURE_LOG", "/data/runs.jsonl"))
# The commit this build came from: `deploy-tool deploy` writes .deployed ("<sha> <time>") into the build folder.
_deployed = HERE.parent / ".deployed"
VERSION = os.environ.get("MEASURE_VERSION") or (_deployed.read_text().split()[0] if _deployed.exists() else "dev")
try:
    LOG.parent.mkdir(parents=True, exist_ok=True)
except OSError:
    pass                          # /health reports an unwritable log

# Vendor test keys: they always pass and measure nothing. Used until the real keys exist; marked in every line.
TEST_SITE_KEYS = {"6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI", "1x00000000000000000000AA", "2x00000000000000000000AB",
                  "3x00000000000000000000FF"}


def env(name):
    v = os.environ.get(name, "").strip()
    return v or None


LANES = {
    # lane: (site key, secret, verify URL)
    "recaptcha_v3": (env("RECAPTCHA_V3_SITE"), env("RECAPTCHA_V3_SECRET"), "https://www.google.com/recaptcha/api/siteverify"),
    "recaptcha_v2": (env("RECAPTCHA_V2_SITE"), env("RECAPTCHA_V2_SECRET"), "https://www.google.com/recaptcha/api/siteverify"),
    "turnstile": (env("TURNSTILE_SITE"), env("TURNSTILE_SECRET"), "https://challenges.cloudflare.com/turnstile/v0/siteverify"),
}
ALTCHA_SECRET = env("ALTCHA_HMAC_SECRET")
ALTCHA_COST = int(os.environ.get("ALTCHA_COST", "5000"))
CAP_URL = env("CAP_URL")              # internal address of the Cap standalone server, e.g. http://cap:3000
CAP_SITE = env("CAP_SITE")
CAP_SECRET = env("CAP_SECRET")

# Budget guard for the vendors' free tiers (reCAPTCHA: 10k assessments a month). Global, not per visitor,
# because we keep no IPs. Over the cap, verify answers 429 and logs nothing.
DAILY_CAP = int(os.environ.get("MEASURE_DAILY_CAP", "300"))
_count = {"day": "", "n": 0}
_lock = threading.Lock()

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
http = httpx.Client(timeout=10)

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'wasm-unsafe-eval' https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/ https://challenges.cloudflare.com",
    "frame-src https://www.google.com/recaptcha/ https://recaptcha.google.com/recaptcha/ https://challenges.cloudflare.com",
    "connect-src 'self'",
    "worker-src 'self' blob:",
    "img-src 'self' data:",
    "style-src 'self' 'unsafe-inline'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])


@app.middleware("http")
async def headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["Content-Security-Policy"] = CSP
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return resp


def key_kind(site):
    return "test" if site in TEST_SITE_KEYS else "real"


@app.get("/health")
def health():
    # "Up but recording nothing" is the failure that matters here, so health fails if the run log is not writable.
    if not os.access(LOG.parent, os.W_OK) or (LOG.exists() and not os.access(LOG, os.W_OK)):
        return JSONResponse({"status": "cannot write the run log", "log": str(LOG)}, status_code=503)
    return {"status": "ok", "version": VERSION,
            "lanes": {k: (key_kind(v[0]) if v[0] and v[1] else "off") for k, v in LANES.items()}
            | {"altcha": "on" if ALTCHA_SECRET else "off", "cap": "on" if CAP_URL and CAP_SITE and CAP_SECRET else "off"}}


@app.get("/api/config")
def config():
    """Site keys the page needs (public by design), and which lanes are live."""
    out = {k: {"site": v[0], "key": key_kind(v[0])} for k, v in LANES.items() if v[0] and v[1]}
    if ALTCHA_SECRET:
        out["altcha"] = {"challenge": "/api/altcha/challenge", "key": "real"}
    if CAP_URL and CAP_SITE and CAP_SECRET:
        out["cap"] = {"endpoint": f"/cap/{CAP_SITE}/", "key": "real"}
    return {"lanes": out, "version": VERSION}


@app.get("/api/altcha/challenge")
def altcha_challenge():
    if not ALTCHA_SECRET:
        return JSONResponse({"error": "altcha lane off"}, status_code=404)
    # Values from ALTCHA's proof-of-work page (read 2026-11-03): PBKDF2/SHA-256 is the widget's bundled default.
    ch = altcha.create_challenge(algorithm="PBKDF2/SHA-256", cost=ALTCHA_COST, hmac_secret=ALTCHA_SECRET,
                                 expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10))
    return JSONResponse(ch.to_dict(), headers={"Cache-Control": "no-store"})


@app.api_route("/cap/{site}/{path:path}", methods=["GET", "POST"])
async def cap_proxy(site: str, path: str, request: Request):
    """The Cap widget talks to <endpoint>/challenge and /redeem; forward those to the Cap server, nothing else."""
    if not (CAP_URL and site == CAP_SITE and path in ("challenge", "redeem")):
        return JSONResponse({"error": "not found"}, status_code=404)
    body = await request.body()
    if len(body) > 64_000:
        return JSONResponse({"error": "too large"}, status_code=413)
    r = http.request(request.method, f"{CAP_URL}/{site}/{path}", content=body,
                     headers={"content-type": request.headers.get("content-type", "application/json")})
    return Response(r.content, status_code=r.status_code, media_type=r.headers.get("content-type"))


SAFE = re.compile(r"[^a-z0-9_.-]")


def bounded(obj, limit=4000):
    s = json.dumps(obj, separators=(",", ":"), default=str)
    return obj if len(s) <= limit else {"truncated": s[:limit]}


def vendor_verify(lane, token):
    site, secret, url = LANES[lane]
    r = http.post(url, data={"secret": secret, "response": token})
    return r.json()


@app.post("/api/verify")
async def verify(request: Request):
    raw = await request.body()
    if len(raw) > 32_000:
        return JSONResponse({"error": "too large"}, status_code=413)
    try:
        body = json.loads(raw)
    except ValueError:
        return JSONResponse({"error": "bad json"}, status_code=400)
    lane = str(body.get("lane", ""))
    token = str(body.get("token", ""))
    if not token or len(token) > 16_000:
        return JSONResponse({"error": "missing or oversized token"}, status_code=400)

    live = (lane in LANES and LANES[lane][0] and LANES[lane][1]) or (lane == "altcha" and ALTCHA_SECRET) \
        or (lane == "cap" and CAP_URL and CAP_SITE and CAP_SECRET)
    if not live:
        return JSONResponse({"error": f"lane {lane!r} is not configured"}, status_code=404)

    today = datetime.date.today().isoformat()
    with _lock:
        if _count["day"] != today:
            _count.update(day=today, n=0)
        if _count["n"] >= DAILY_CAP:
            return JSONResponse({"error": "daily measurement cap reached; try tomorrow"}, status_code=429)
        _count["n"] += 1

    t0 = time.time()
    line = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "run_id": SAFE.sub("", str(body.get("run_id", "")).lower())[:40],
            "condition": SAFE.sub("", str(body.get("condition", "")).lower())[:40],
            "lane": lane, "version": VERSION}
    try:
        if lane in LANES and LANES[lane][0] and LANES[lane][1]:
            v = vendor_verify(lane, token)
            line.update(key=key_kind(LANES[lane][0]), success=bool(v.get("success")), score=v.get("score"),
                        action=v.get("action"), hostname=v.get("hostname"), errors=v.get("error-codes", []))
            if v.get("challenge_ts"):
                try:
                    ts = datetime.datetime.fromisoformat(v["challenge_ts"].replace("Z", "+00:00"))
                    line["token_age_s"] = round(time.time() - ts.timestamp(), 1)
                except ValueError:
                    pass
        elif lane == "altcha" and ALTCHA_SECRET:
            res = altcha.verify_solution(token, ALTCHA_SECRET)
            line.update(key="real", success=bool(getattr(res, "verified", False)),
                        errors=[] if getattr(res, "verified", False) else [str(getattr(res, "error", "") or "not verified")])
        elif lane == "cap" and CAP_URL and CAP_SITE and CAP_SECRET:
            r = http.post(f"{CAP_URL}/{CAP_SITE}/siteverify", json={"secret": CAP_SECRET, "response": token})
            v = r.json()
            line.update(key="real", success=bool(v.get("success")), errors=[] if v.get("success") else [str(v)[:200]])
        else:
            return JSONResponse({"error": f"lane {lane!r} is not configured"}, status_code=404)
    except (httpx.HTTPError, ValueError) as e:
        line.update(success=False, errors=[f"verify call failed: {type(e).__name__}"])
    line["verify_ms"] = round((time.time() - t0) * 1000)

    client = body.get("client") if isinstance(body.get("client"), dict) else {}
    line["solve_ms"] = client.get("solve_ms") if isinstance(client.get("solve_ms"), (int, float)) else None
    line["interactive"] = client.get("interactive") if isinstance(client.get("interactive"), bool) else None
    line["country"] = request.headers.get("cf-ipcountry")
    line["ua"] = request.headers.get("user-agent", "")[:300]
    line["signals"] = bounded(client.get("signals", {}))
    line["token_sha"] = hashlib.sha256(token.encode()).hexdigest()[:16]   # spots a replayed token, keeps no token

    shown = {k: line.get(k) for k in ("lane", "key", "success", "score", "action", "hostname", "errors",
                                      "token_age_s", "verify_ms")}
    try:
        with _lock, LOG.open("a") as fh:
            fh.write(json.dumps(line, separators=(",", ":")) + "\n")
        shown["logged"] = True
    except OSError as e:          # the visitor still gets the verdict; /health turns 503 so the box restarts and flags it
        print(f"run log write failed: {e}", flush=True)
        shown["logged"] = False
    return shown


@app.api_route("/", methods=["GET", "HEAD"])
def index():
    return FileResponse(HERE / "static" / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/favicon.ico")
def favicon():
    return FileResponse(HERE / "static" / "favicon.svg", media_type="image/svg+xml")


app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

