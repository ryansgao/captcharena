"""The solver lab: open-source CAPTCHAs served unmodified on loopback, each answer judged by its own server.

    uv run lab/server.py [--port 8411]        (needs `docker compose -f lab/compose.yml up -d` for the go-captcha types)

Types (open the page with ?t=<type>):
    text            distorted text image from `captcha` (lepture/captcha, BSD) — the generator's own defaults
    go-slide        go-captcha-service (wenlng, Apache-2.0): slide the piece along its row into the gap
    go-drag         go-captcha: drag the piece anywhere into the gap
    go-rotate       go-captcha: rotate the inner disc until the picture lines up
    go-click-en     go-captcha: click the characters shown in the strip, in order
    go-click-shape  go-captcha: click the shapes shown in the strip, in order

Every challenge is one-shot (a wrong answer burns it, as with real widgets) and the page then loads a fresh one.
The verdict comes from the CAPTCHA's own check (go-captcha's `check-data`; for `text`, the answer kept server-side)
and is written to `document.body.dataset.verdict` (pass / fail) with `dataset.round` counting challenges. The page
widget is our own minimal re-implementation of go-captcha-jslib's interactions (same class names `gc-*`), so the
image generation and the checking are the projects' own code, not ours.
"""
import argparse
import base64
import io
import json
import os
import random
import secrets
import string
import time

import httpx
import uvicorn
from captcha.image import ImageCaptcha
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

HERE = os.path.dirname(os.path.abspath(__file__))
GOCAP = os.environ.get("GOCAP_URL", "http://127.0.0.1:18181")
GO_IDS = {"go-slide": "slide-default", "go-drag": "drag-default", "go-rotate": "rotate-default",
          "go-click-en": "click-default-en", "go-click-shape": "click-shape-default"}
TYPES = ["text", *GO_IDS]
STATE = os.path.join(HERE, ".state")
os.makedirs(STATE, exist_ok=True)
LOG = os.path.join(STATE, "lab-verdicts.jsonl")

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")
_text = {}                       # id -> (answer, created)
_gen = ImageCaptcha(width=200, height=70)


def log(line):
    line["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG, "a") as f:
        f.write(json.dumps(line) + "\n")


@app.get("/", response_class=HTMLResponse)
def page(t: str = "text"):
    if t not in TYPES:
        return HTMLResponse("unknown type; one of: " + ", ".join(TYPES), status_code=404)
    return open(os.path.join(HERE, "static", "lab.html")).read().replace("{{TYPE}}", t)


@app.get("/api/new")
def new(t: str):
    if t == "text":
        n = random.choice([4, 5, 6])
        answer = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))
        buf = io.BytesIO()
        _gen.write(answer, buf, format="png")
        cid = secrets.token_hex(8)
        _text[cid] = (answer, time.time())
        return {"type": t, "key": cid, "image": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()}
    if t in GO_IDS:
        d = httpx.get(f"{GOCAP}/api/v1/public/get-data", params={"id": GO_IDS[t]}, timeout=10).json()["data"]
        return {"type": t, "key": d["captcha_key"], "master": d["master_image_base64"],
                "thumb": d["thumb_image_base64"], **{k: v for k, v in d.items() if not k.endswith("base64")}}
    return JSONResponse({"error": "unknown type"}, status_code=404)


@app.post("/api/check")
async def check(request: Request):
    b = await request.json()
    t, key, value = b.get("type"), str(b.get("key", "")), str(b.get("value", ""))
    ok = False
    if t == "text":
        answer, _ = _text.pop(key, (None, 0))                      # one-shot
        ok = answer is not None and value.strip().upper() == answer
    elif t in GO_IDS:
        r = httpx.post(f"{GOCAP}/api/v1/public/check-data", json={"id": GO_IDS[t], "captchaKey": key, "value": value},
                       timeout=10).json()
        ok = r.get("data") == "ok"                                 # go-captcha marks a key failed after one miss
    log({"type": t, "key": key, "ok": ok, "client": b.get("client", "")[:40]})
    return {"ok": ok}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("LAB_PORT", 8411)))
    a = ap.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
