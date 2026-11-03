"""Local answerers for ladder steps 1 (fixed recipes) and 2 (small local models). All CPU, all $0.

Each engine takes an observation's images (PIL) and returns {"value": ..., "conf": 0..1, "engine": name} or None.
`conf` gates submission: below the kind's threshold the answer is not sent (a wrong answer burns the challenge), and
the router escalates on the same challenge instead.

Step 1 (recipes): tesseract OCR; OpenCV gap finding for slide / drag puzzles; rotation search for rotate puzzles.
Step 2 (local models): ddddocr (sml2h3/ddddocr, MIT: a small ONNX OCR + detector, the Chinese-market standard) for
text and click-the-characters puzzles. Audio (local Whisper) is step 1 too, but lives in kinds.py with reCAPTCHA.
"""
import re
import subprocess
import tempfile

import numpy as np

_DDDD = {}


def _dddd(kind="ocr"):
    if kind not in _DDDD:
        import contextlib
        import io as _io
        import ddddocr
        with contextlib.redirect_stdout(_io.StringIO()):          # it prints an advert on load
            _DDDD[kind] = ddddocr.DdddOcr(show_ad=False, ocr=(kind == "ocr"), det=(kind == "det"),
                                         **({"beta": True} if kind == "beta" else {}))
    return _DDDD[kind]


# --- text ------------------------------------------------------------------------------------------------------

def tesseract_text(im, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"):
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        g = im.convert("L")
        g = g.resize((g.width * 2, g.height * 2))
        g.save(f.name)
        out = subprocess.run(["tesseract", f.name, "-", "--psm", "7", "-c", f"tessedit_char_whitelist={charset}", "tsv"],
                             capture_output=True, text=True).stdout
    words, confs = [], []
    for line in out.splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) == 12 and cols[11].strip():
            words.append(cols[11].strip())
            confs.append(max(0.0, float(cols[10])) / 100)
    text = "".join(words)
    if not text:
        return None
    return {"value": text, "conf": round(min(confs), 2), "engine": "tesseract"}


def ddddocr_text(im, upper=True):
    o = _dddd("ocr")
    try:
        r = o.classification(im, probability=True)        # ddddocr 1.6: {"text", "confidence", ...}
        text, conf = r["text"], float(r["confidence"])
    except Exception:
        text, conf = o.classification(im), 0.5
    text = re.sub(r"[^A-Za-z0-9]", "", text)
    if upper:
        text = text.upper()
    return {"value": text, "conf": round(conf, 2), "engine": "ddddocr.ocr"} if text else None


# --- slide / drag ----------------------------------------------------------------------------------------------

def _gray(im):
    import cv2
    return cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2GRAY)


def _match_gap(master, thumb, row=None):
    """Where the piece's outline best fits the master's edges. The gap is a darkened copy of the piece's shape, so
    edge maps (Canny) of the master and of the piece's alpha outline correlate there. With `row`, search only that
    row (slide); else everywhere (drag). Returns (x, y, score, runner_up_ratio)."""
    import cv2
    m = cv2.Canny(cv2.GaussianBlur(_gray(master), (3, 3), 0), 60, 160)
    a = np.array(thumb.convert("RGBA"))[:, :, 3]
    t = cv2.Canny((a > 128).astype(np.uint8) * 255, 50, 150)
    h, w = t.shape
    if row is not None:
        y0 = max(0, row - 2)
        band = m[y0:y0 + h + 4, :]
        res = cv2.matchTemplate(band, t, cv2.TM_CCOEFF_NORMED)
        _, best, _, loc = cv2.minMaxLoc(res)
        x, y = loc[0], y0 + loc[1]
    else:
        res = cv2.matchTemplate(m, t, cv2.TM_CCOEFF_NORMED)
        _, best, _, loc = cv2.minMaxLoc(res)
        x, y = loc
    # runner-up outside the winner's neighbourhood: a clear winner is a confident answer
    r2 = res.copy()
    ly, lx = (loc[1], loc[0])
    r2[max(0, ly - h // 2):ly + h // 2 + 1, max(0, lx - w // 2):lx + w // 2 + 1] = -1
    second = float(r2.max()) if r2.size else 0.0
    return int(x), int(y), float(best), (second / best if best > 0 else 1.0)


def cv_slide(master, thumb, row):
    x, y, score, ratio = _match_gap(master, thumb, row)
    conf = max(0.0, min(1.0, (1 - ratio) * 2 + score / 2))
    return {"value": [x, row], "conf": round(conf, 2), "engine": "cv.slide", "score": round(score, 3)}


def cv_drag(master, thumb):
    x, y, score, ratio = _match_gap(master, thumb)
    conf = max(0.0, min(1.0, (1 - ratio) * 2 + score / 2))
    return {"value": [x, y], "conf": round(conf, 2), "engine": "cv.drag", "score": round(score, 3)}


def dddd_slide(master, thumb, row=None):
    """ddddocr's own slide matcher (step 2 alternative to cv.slide)."""
    import io as _io
    o = _dddd("det")
    tb, mb = _io.BytesIO(), _io.BytesIO()
    thumb.save(tb, "PNG")
    master.convert("RGB").save(mb, "PNG")
    r = o.slide_match(tb.getvalue(), mb.getvalue(), simple_target=True)
    x, y = r["target"][0], r["target"][1]
    return {"value": [int(x), int(row if row is not None else y)], "conf": 0.6, "engine": "ddddocr.slide"}


# --- rotate ----------------------------------------------------------------------------------------------------

def cv_rotate(master, thumb, direction=1):
    """Angle that makes the inner disc continue the outer ring: for each candidate angle, compare the disc's outermost
    rings of pixels (rotated) with the master's rings just outside it. Sampled every 1 degree, bilinear, two radii."""
    import cv2
    M = cv2.GaussianBlur(np.array(master.convert("RGB")).astype(np.float32), (3, 3), 0)
    T = cv2.GaussianBlur(np.array(thumb.convert("RGB")).astype(np.float32), (3, 3), 0)
    c, tc, R = M.shape[0] / 2, T.shape[0] / 2, T.shape[0] // 2
    a = np.deg2rad(np.arange(0, 360, 1.0)).astype(np.float32)

    def ring(img, cx, r, angles):
        mx = (cx + r * np.cos(angles)).astype(np.float32)[None, :]
        my = (cx + r * np.sin(angles)).astype(np.float32)[None, :]
        return cv2.remap(img, mx, my, cv2.INTER_LINEAR)[0]
    outer = np.concatenate([ring(M, c, R + 2, a), ring(M, c, R + 4, a)])
    scores = []
    for deg in range(360):
        src = a - np.deg2rad(direction * deg)
        inner = np.concatenate([ring(T, tc, R - 3, src), ring(T, tc, R - 5, src)])
        scores.append(float(np.mean(np.abs(inner - outer))))
    s = np.array(scores)
    best = int(np.argmin(s))
    conf = float(max(0.0, min(1.0, (np.median(s) - s[best]) / (np.median(s) + 1e-6))))
    return {"value": best, "conf": round(conf, 2), "engine": "cv.rotate", "dist": round(float(s[best]), 1)}


# --- click the characters in order -----------------------------------------------------------------------------

def dddd_click(master, thumb):
    """Read the order strip, detect characters on the master, read each, match. Returns ordered [[x, y], ...]."""
    import io as _io
    det = _dddd("det")
    ocr = _dddd("ocr")
    mb = _io.BytesIO()
    master.convert("RGB").save(mb, "PNG")
    boxes = det.detection(mb.getvalue())
    reads = []
    for x1, y1, x2, y2 in boxes:
        crop = master.crop((x1, y1, x2, y2))
        t = re.sub(r"[^A-Za-z0-9]", "", ocr.classification(crop)).upper()
        reads.append((t, ((x1 + x2) // 2, (y1 + y2) // 2)))
    want = re.sub(r"[^A-Za-z0-9]", "", ocr.classification(thumb.convert("RGB"))).upper()
    if not want or not reads:
        return None
    pts, used, hits = [], set(), 0
    for ch in want:
        cand = [i for i, (t, _) in enumerate(reads) if i not in used and ch in t]
        if cand:
            hits += 1
        else:
            cand = [i for i in range(len(reads)) if i not in used]
        if not cand:
            return None
        used.add(cand[0])
        pts.append(list(reads[cand[0]][1]))
    return {"value": pts, "conf": round(hits / len(want), 2), "engine": "ddddocr.click", "read": want}


ENGINES = {
    "tesseract": lambda o: tesseract_text(o.images["image"]),
    "ddddocr.ocr": lambda o: ddddocr_text(o.images["image"]),
    "cv.slide": lambda o: cv_slide(o.images["master"], o.images["thumb"], o.geom["display_y"]),
    "ddddocr.slide": lambda o: dddd_slide(o.images["master"], o.images["thumb"], o.geom["display_y"]),
    "cv.drag": lambda o: cv_drag(o.images["master"], o.images["thumb"]),
    "cv.rotate": lambda o: cv_rotate(o.images["master"], o.images["thumb"], 1),
    "ddddocr.click": lambda o: dddd_click(o.images["master"], o.images["thumb"]),
}
