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
import collections
import datetime
import hashlib
import hmac
import json
import statistics
import os
import pathlib
import re
import threading
import time

import altcha
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
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

# Budget guard for the vendors' free tiers. reCAPTCHA: 10k assessments a month per Google Cloud project, and the v2
# and v3 keys share one project, so v2 + v3 stay under 320 a day (9.6k a month). Global, not per visitor, because
# we keep no IPs. Two pools per lane, so public traffic can never starve the experiment and a runner bug can never
# eat the public page: "runner" (requests carrying X-Measure-Runner = MEASURE_RUNNER_KEY) and "public" (everyone).
# Over a cap, verify answers 429 and logs nothing. Override with MEASURE_CAPS='{"lane": [runner, public], ...}'.
CAPS = {"recaptcha_v3": (130, 30), "recaptcha_v2": (130, 30), "turnstile": (1500, 500),
        "altcha": (1500, 1000), "cap": (1500, 1000)}
try:
    CAPS.update({k: tuple(v) for k, v in json.loads(os.environ.get("MEASURE_CAPS") or "{}").items()})
except (ValueError, TypeError):
    print("MEASURE_CAPS is not valid JSON; using the defaults", flush=True)
RUNNER_KEY = env("MEASURE_RUNNER_KEY")
_count = {"day": "", "n": collections.Counter()}
_lock = threading.Lock()


def utc_day():
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def _restore_counts():
    """Rebuild today's counts from the log, so a redeploy or restart does not reset the budget."""
    today, n = utc_day(), collections.Counter()
    try:
        with LOG.open() as fh:
            for raw in fh:
                if raw.startswith('{"ts":"' + today):
                    try:
                        d = json.loads(raw)
                    except ValueError:
                        continue
                    n[(d.get("lane"), d.get("source", "public"))] += 1
    except OSError:
        pass
    _count.update(day=today, n=n)


_restore_counts()

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
http = httpx.Client(timeout=10)

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'wasm-unsafe-eval' https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/ https://challenges.cloudflare.com",
    "frame-src https://www.google.com/recaptcha/ https://recaptcha.google.com/recaptcha/ https://challenges.cloudflare.com",
    "connect-src 'self' https://www.google.com/recaptcha/ https://challenges.cloudflare.com",
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

    source = "runner" if RUNNER_KEY and hmac.compare_digest(
        request.headers.get("x-measure-runner", "").encode(), RUNNER_KEY.encode()) else "public"
    today = utc_day()
    with _lock:
        if _count["day"] != today:
            _count.update(day=today, n=collections.Counter())
        cap = CAPS.get(lane, (0, 0))[0 if source == "runner" else 1]
        if _count["n"][(lane, source)] >= cap:
            return JSONResponse({"error": "daily measurement cap reached; try tomorrow", "capped": True},
                                status_code=429)
        _count["n"][(lane, source)] += 1

    t0 = time.time()
    line = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "run_id": SAFE.sub("", str(body.get("run_id", "")).lower())[:40],
            "condition": SAFE.sub("", str(body.get("condition", "")).lower())[:40],
            "lane": lane, "source": source, "version": VERSION}
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


# ---- /api/summary: the public, aggregate view of the run log (schema in README.md "Summary feed") -------------
SUMMARY_SCHEMA = 1
SMOKE = re.compile(r"(^|[-_.])(smoke|test)([-_.]|$)")
RUNNER_TAG = re.compile(r"^x(\d+)-((?:[a-z]\d+)+)$")     # e.g. x1-n0b0a2s2h0c0d0w1 (runner/README.md)
ERROR_CODE = re.compile(r"^[a-z0-9-]{1,40}$")
SCORE_BINS = ("0.0", "0.1", "0.3", "0.5", "0.7", "0.9", "1.0")
MAX_CONDITIONS_PER_DAY_LANE = 60          # bound the feed: a visitor inventing ?c= values cannot bloat it
FACTOR_LEVELS = {
    "n": {"0": "private workspace's usual exit (a commercial VPN, home region, datacentre host)", "1": "another a commercial VPN exit (SOCKS5, Sydney, M247)",
          "2": "home line (not run)", "3": "cellular (not run)", "4": "static ISP address (not run)"},
    "b": {"0": "Debian Chromium", "1": "Google Chrome stable", "2": "Camoufox (Firefox)", "3": "CloakBrowser",
          "5": "Playwright's bundled Chromium"},
    "a": {"0": "no automation client during the load", "1": "raw CDP", "2": "Playwright over CDP (connect)",
          "3": "Playwright launched the browser"},
    "s": {"0": "fresh profile", "1": "aged profile, no Google sign-in", "2": "aged profile, signed in to Google"},
    "h": {"0": "no behaviour before the check", "1": "dwell, scroll and pointer movement first"},
    "c": {"0": "coherent (timezone matches exit)", "1": "timezone/locale mismatch", "2": "spoofed user agent"},
    "d": {"0": "headed (window on a virtual screen)", "1": "headless"},
    "w": {"0": "no CAPTCHA watcher", "1": "the agents' CAPTCHA watcher may tick and solve v2/Turnstile"},
}
_summary = {"key": None, "at": 0.0, "body": b"", "etag": ""}


def _score_bin(score):
    if not isinstance(score, (int, float)):
        return None
    return min(SCORE_BINS, key=lambda b: abs(float(b) - score))


def build_summary():
    groups, excluded, days = {}, collections.Counter(), set()
    try:
        fh = LOG.open()
    except OSError:
        fh = []
    for raw in fh:
        try:
            d = json.loads(raw)
        except ValueError:
            excluded["unparsed"] += 1
            continue
        cond = d.get("condition") or ""
        if d.get("key") == "test":
            excluded["test_key"] += 1
            continue
        if SMOKE.search(cond):
            excluded["smoke"] += 1
            continue
        day = str(d.get("ts", ""))[:10]
        days.add(day)
        k = (day, d.get("lane"), cond or "untagged", d.get("source", "public"))
        g = groups.setdefault(k, {"n": 0, "passed": 0, "scores": collections.Counter(), "score_sum": 0.0,
                                  "score_n": 0, "solve": [], "inter_n": 0, "inter_yes": 0,
                                  "errors": collections.Counter()})
        g["n"] += 1
        g["passed"] += bool(d.get("success"))
        b = _score_bin(d.get("score"))
        if b:
            g["scores"][b] += 1
            g["score_sum"] += d["score"]
            g["score_n"] += 1
        if isinstance(d.get("solve_ms"), (int, float)) and d["solve_ms"] < 600_000:
            g["solve"].append(d["solve_ms"])
        if isinstance(d.get("interactive"), bool):
            g["inter_n"] += 1
            g["inter_yes"] += d["interactive"]
        for e in d.get("errors") or []:
            g["errors"][e if isinstance(e, str) and ERROR_CODE.match(e) else "other"] += 1
    if hasattr(fh, "close"):
        fh.close()

    # Bound distinct conditions per (day, lane): keep the busiest, fold the rest into "other".
    by_dl = collections.defaultdict(list)
    for k, g in groups.items():
        by_dl[(k[0], k[1])].append((k, g))
    rows, conditions = [], {}
    for (day, lane), items in sorted(by_dl.items()):
        items.sort(key=lambda kg: -kg[1]["n"])
        keep, fold = items[:MAX_CONDITIONS_PER_DAY_LANE], items[MAX_CONDITIONS_PER_DAY_LANE:]
        if fold:
            o = {"n": 0, "passed": 0, "scores": collections.Counter(), "score_sum": 0.0, "score_n": 0, "solve": [],
                 "inter_n": 0, "inter_yes": 0, "errors": collections.Counter()}
            for _, g in fold:
                for f in ("n", "passed", "score_sum", "score_n", "inter_n", "inter_yes"):
                    o[f] += g[f]
                o["scores"] += g["scores"]; o["errors"] += g["errors"]; o["solve"] += g["solve"]
            keep.append(((day, lane, "other", "public"), o))
        for (day, lane, cond, source), g in sorted(keep, key=lambda kg: (kg[0][2], kg[0][3])):
            rows.append({
                "day": day, "lane": lane, "condition": cond, "source": source,
                "n": g["n"], "passed": g["passed"], "pass_rate": round(g["passed"] / g["n"], 4),
                "score_hist": dict(sorted(g["scores"].items())) if g["score_n"] else None,
                "score_mean": round(g["score_sum"] / g["score_n"], 3) if g["score_n"] else None,
                "solve_ms_median": round(statistics.median(g["solve"])) if g["solve"] else None,
                "interactive_known": g["inter_n"],
                "interactive_rate": round(g["inter_yes"] / g["inter_n"], 4) if g["inter_n"] else None,
                "errors": dict(g["errors"]),
            })
            m = RUNNER_TAG.match(cond)
            if m and cond not in conditions:
                conditions[cond] = {"design": int(m.group(1)),
                                    "factors": {f: lvl for f, lvl in re.findall(r"([a-z])(\d+)", m.group(2))}}
    return {"schema": SUMMARY_SCHEMA, "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(
                timespec="seconds"),
            "version": VERSION, "days": [min(days), max(days)] if days else None,
            "excluded": dict(excluded), "score_bins": list(SCORE_BINS), "factor_levels": FACTOR_LEVELS,
            "conditions": conditions, "rows": rows}


@app.get("/api/summary")
def summary(request: Request):
    """Aggregate, cache-friendly view of the run log: per day x lane x condition x source. Nothing per visitor."""
    try:
        st = LOG.stat()
        key = (st.st_mtime_ns, st.st_size)
    except OSError:
        key = None
    with _lock:
        if key != _summary["key"] and time.time() - _summary["at"] > 30 or not _summary["body"]:
            body = json.dumps(build_summary(), separators=(",", ":")).encode()
            _summary.update(key=key, at=time.time(), body=body, etag='"' + hashlib.sha256(body).hexdigest()[:20] + '"')
    hdrs = {"Cache-Control": "public, max-age=300, stale-while-revalidate=600", "ETag": _summary["etag"],
            "Access-Control-Allow-Origin": "https://captcharena.org"}     # the hub; GET only, no credentials
    if request.headers.get("if-none-match") == _summary["etag"]:
        return Response(status_code=304, headers=hdrs)
    return Response(_summary["body"], media_type="application/json", headers=hdrs)


@app.api_route("/", methods=["GET", "HEAD"])
def index():
    # Version the page's own files in their URLs: Cloudflare sets a 4 h browser cache on /static/ whatever we send,
    # so a deploy would otherwise reach returning browsers hours late.
    html = (HERE / "static" / "index.html").read_text()
    for f in ("style.css", "measure.js"):
        html = html.replace(f'/static/{f}"', f'/static/{f}?v={VERSION}"')
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@app.get("/favicon.ico")
def favicon():
    return FileResponse(HERE / "static" / "favicon.svg", media_type="image/svg+xml")


app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

