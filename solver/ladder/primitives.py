"""Input and perception primitives, vendored from the owner's private solver.

Source: <private v0 solver> at private commit dba4e84f (human_move, human_drag, human_stroke,
transcribe, the gridded look). Vendored, not imported, because that file is a CLI bound to the shared the automation browser
(CDP 127.0.0.1:9223) whose helpers end the process (`say()` calls sys.exit) and log into the owner's private CAPTCHA log; the
solver here drives its own Playwright browser and must keep running after a step fails. Behaviour is unchanged except:
functions return values instead of exiting, and `transcribe` keeps one Whisper model per process.
"""
import io
import math
import random
import re
import subprocess
import time

_WHISPER = {}


def human_move(page, x, y):
    """Travel to x,y like a hand: from a nearby resting point, on a slight curve, ~500-900 px/s, ease-in-out."""
    ang = random.uniform(0, 2 * math.pi)
    d0 = random.uniform(120, 260)
    sx, sy = x + d0 * math.cos(ang), y + d0 * math.sin(ang)
    page.mouse.move(sx, sy)
    time.sleep(random.uniform(0.05, 0.12))
    dist = math.hypot(x - sx, y - sy)
    n = max(8, int(dist / 9))
    dur = dist / random.uniform(500, 900)
    bend = random.uniform(-0.18, 0.18) * dist
    nx, ny = -(y - sy) / (dist or 1), (x - sx) / (dist or 1)
    for i in range(1, n + 1):
        t = i / n
        e = t * t * (3 - 2 * t)
        arc = math.sin(math.pi * t) * bend
        page.mouse.move(sx + (x - sx) * e + nx * arc + random.uniform(-0.4, 0.4),
                        sy + (y - sy) * e + ny * arc + random.uniform(-0.4, 0.4))
        time.sleep(dur / n)
    time.sleep(random.uniform(0.12, 0.3))


def human_click(page, x, y, jitter=1.5):
    human_move(page, x + random.uniform(-jitter, jitter), y + random.uniform(-jitter, jitter))
    page.mouse.down()
    time.sleep(random.uniform(0.06, 0.14))
    page.mouse.up()
    time.sleep(random.uniform(0.25, 0.6))


def human_drag(page, x1, y1, x2, y2, overshoot=True):
    """Press, travel with easing, a little wobble and (optionally) overshoot, settle, release.
    The endpoint is exact: tolerances of 2-4 px (go-captcha) leave no room for a resting wobble."""
    human_move(page, x1, y1)
    page.mouse.down()
    time.sleep(random.uniform(0.08, 0.18))
    dist = math.hypot(x2 - x1, y2 - y1)
    n = max(24, int(dist / 6))
    dur = max(0.25, dist / random.uniform(250, 450))
    over = (x2 - x1) * random.uniform(0.02, 0.06) if overshoot else 0.0
    for i in range(1, n + 1):
        t = i / n
        e = t * t * (3 - 2 * t)
        page.mouse.move(x1 + (x2 - x1 + over) * e + random.uniform(-0.6, 0.6),
                        y1 + (y2 - y1) * e + random.uniform(-1.2, 1.2))
        time.sleep(dur / n * random.uniform(0.7, 1.3))
    for i in range(1, 6):
        page.mouse.move(x2 + over * (1 - i / 5), y2 + random.uniform(-0.5, 0.5) * (5 - i) / 5)
        time.sleep(random.uniform(0.02, 0.05))
    page.mouse.move(x2, y2)
    time.sleep(random.uniform(0.08, 0.2))
    page.mouse.up()


def human_stroke(page, pts):
    """One continuous stroke through several points (pattern lock, trace the path)."""
    human_move(page, *pts[0])
    page.mouse.down()
    time.sleep(random.uniform(0.08, 0.15))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dist = math.hypot(bx - ax, by - ay)
        n = max(10, int(dist / 6))
        dur = dist / random.uniform(300, 500)
        for i in range(1, n + 1):
            t = i / n
            e = t * t * (3 - 2 * t)
            page.mouse.move(ax + (bx - ax) * e + random.uniform(-0.5, 0.5), ay + (by - ay) * e + random.uniform(-0.5, 0.5))
            time.sleep(dur / n)
        time.sleep(random.uniform(0.04, 0.1))
    page.mouse.up()


def human_hold(page, x, y, secs=3.0):
    human_move(page, x, y)
    page.mouse.down()
    end = time.time() + secs
    while time.time() < end:
        page.mouse.move(x + random.uniform(-0.6, 0.6), y + random.uniform(-0.6, 0.6))
        time.sleep(random.uniform(0.08, 0.16))
    page.mouse.up()


def transcribe(path, language="en"):
    """Local speech-to-text: ffmpeg -> 16 kHz mono float array -> faster-whisper small(.en), int8, CPU."""
    import numpy as np
    from faster_whisper import WhisperModel
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, dtype=np.float32)        # an array, not a path: PyAV 19 breaks on paths (2026-10-11)
    name = "small.en" if language == "en" else "small"
    if name not in _WHISPER:
        _WHISPER[name] = WhisperModel(name, device="cpu", compute_type="int8")
    segs, _ = _WHISPER[name].transcribe(audio, language=language, beam_size=5, vad_filter=False)
    text = " ".join(s.text for s in segs).strip()
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip() if language == "en" else text


def shot(page, clip=None):
    """Viewport (or clip) screenshot as a PIL image. clip = (x, y, w, h) in viewport coordinates."""
    from PIL import Image
    kw = {"clip": {"x": clip[0], "y": clip[1], "width": clip[2], "height": clip[3]}} if clip else {}
    return Image.open(io.BytesIO(page.screenshot(timeout=10000, **kw))).convert("RGB")


def gridded(im, origin=(0, 0), step=None, min_width=640):
    """The look's grid: lines every `step` px labelled in the coordinates of `origin` (viewport or image px), so a
    model can name a point. Small images are enlarged first. Returns (image, scale)."""
    from PIL import Image, ImageDraw
    w, h = im.size
    f = 1.0
    if w < min_width:
        f = min(3.0, min_width / w)
        im = im.resize((int(w * f), int(h * f)), Image.LANCZOS)
    else:
        im = im.copy()
    step = step or (25 if max(w, h) <= 500 else 50)
    d = ImageDraw.Draw(im)
    x0, y0 = origin
    for gx in range(int(x0 // step * step), int(x0 + w) + 1, step):
        X = (gx - x0) * f
        major = gx % (step * 2) == 0
        d.line([(X, 0), (X, im.height)], fill=(255, 0, 255) if major else (255, 150, 255), width=1)
        if major:
            d.text((X + 2, 2), str(gx), fill=(200, 0, 200))
    for gy in range(int(y0 // step * step), int(y0 + h) + 1, step):
        Y = (gy - y0) * f
        major = gy % (step * 2) == 0
        d.line([(0, Y), (im.width, Y)], fill=(255, 0, 255) if major else (255, 150, 255), width=1)
        if major:
            d.text((2, Y + 2), str(gy), fill=(200, 0, 200))
    return im, f
