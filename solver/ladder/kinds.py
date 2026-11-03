"""What the solver knows per kind of CAPTCHA: how to find it, look at it, answer it at each ladder step, act, and read
the site's verdict.

Every kind implements the same small interface (class Kind). Steps 1-2 name local engines (engines.py); step 4 is
`vision()` (one focused free-API call); step 0 is `step0()`; acting is `act()`; `verdict()` reads the site's own
judgement where the page exposes it (our measurement page and the lab do), else returns None ("unverified").
"""
import io
import base64
import os
import re
import tempfile
import time
import urllib.request

from PIL import Image, ImageDraw

from . import engines, models
from .primitives import human_click, human_drag, human_move, shot, gridded, transcribe

RC_ANCHOR = re.compile(r"/recaptcha/(api2|enterprise)/anchor")
RC_BFRAME = re.compile(r"/recaptcha/(api2|enterprise)/bframe")
HC = re.compile(r"hcaptcha\.com/captcha/v1/")
TURNSTILE = re.compile(r"challenges\.cloudflare\.com/cdn-cgi/challenge-platform")
ARKOSE = re.compile(r"arkoselabs\.com|funcaptcha\.com")
GEETEST = re.compile(r"geetest\.com|gt4\.|static\.geetest")


class Obs:
    def __init__(self, images=None, geom=None, instruction=""):
        self.images, self.geom, self.instruction = images or {}, geom or {}, instruction


def _img_from_src(src):
    if src.startswith("data:"):
        return Image.open(io.BytesIO(base64.b64decode(src.split(",", 1)[1])))
    return Image.open(io.BytesIO(urllib.request.urlopen(src, timeout=10).read()))


def _box(loc):
    b = loc.bounding_box()
    return (b["x"], b["y"], b["width"], b["height"]) if b else None


def measure_lane_verdict(page, lane, timeout):
    """Our measurement page writes the vendor's server verdict to body[data-done_<lane>]."""
    end = time.time() + timeout
    while time.time() < end:
        v = page.evaluate(f"() => document.body.dataset['done_{lane}'] || ''")
        if v in ("pass", "fail"):
            return v
        time.sleep(0.25)
    return None


class Kind:
    name = "unknown"
    vendor = "unknown"
    local = {1: [], 2: []}
    conf_gate = 0.5                 # local answers under this are not submitted
    has_step0 = False
    lane = None                     # measurement-page lane

    def __init__(self, page, root=None):
        self.page, self.root = page, root

    @property
    def layout(self):
        return ""

    def instruction_template(self, obs=None):
        return ""

    def signature(self, obs=None):
        return f"{self.name}|{self.instruction_template(obs)}|{self.layout}"

    # the site's verdict -------------------------------------------------------------------------------------
    def verdict_source(self):
        p = self.page
        if self.lane and p.evaluate("() => !!document.getElementById('lane-' + %r)" % self.lane):
            return "measure-page"
        if p.evaluate("() => 'verdict' in document.body.dataset && 'round' in document.body.dataset"):
            return "lab-page"
        return None

    def verdict(self, timeout=8.0):
        src = self.verdict_source()
        if src == "measure-page":
            return measure_lane_verdict(self.page, self.lane, timeout)
        if src == "lab-page":
            end = time.time() + timeout
            while time.time() < end:
                v = self.page.evaluate("() => document.body.dataset.verdict")
                if v in ("pass", "fail"):
                    return v
                time.sleep(0.15)
        return None

    def shown_verdict(self):
        """The verdict text the page shows (measurement page: score, error codes)."""
        try:
            if self.verdict_source() == "measure-page":
                return self.page.locator(f"#v-{self.lane}").inner_text(timeout=1000)[:160]
        except Exception:
            pass
        return None

    def wait_ready(self, timeout=10):
        """Lab pages load a fresh challenge after a miss; wait for it."""
        if self.verdict_source() != "lab-page":
            return
        end = time.time() + timeout
        while time.time() < end:
            if self.page.evaluate("() => document.body.dataset.state") == "ready":
                return
            time.sleep(0.15)

    def step0(self, ctx):
        return None

    def observe(self):
        return Obs()

    def vision(self, obs, calls, **route):
        return None

    def act(self, obs, answer):
        raise NotImplementedError


# ---- proof-of-work and tick-box widgets (step 0 only) --------------------------------------------------------------

class Altcha(Kind):
    name, vendor, lane, has_step0 = "altcha", "altcha", "altcha", True

    def step0(self, ctx):
        # auto="onload": the browser does the proof of work by itself; a click starts it if not
        el = self.page.locator("altcha-widget").first
        state = lambda: self.page.evaluate("() => { const w = document.querySelector('altcha-widget'); return w ? (w.getState ? w.getState() : '') : '' }")
        time.sleep(1.0)
        if state() not in ("verifying", "verified"):
            try:
                cb = el.locator("input[type=checkbox]")
                if cb.count():
                    b = _box(cb.first)
                    human_click(self.page, b[0] + b[2] / 2, b[1] + b[3] / 2)
            except Exception:
                pass
        return {"engine": "pow-wait"}


class Cap(Kind):
    name, vendor, lane, has_step0 = "cap", "cap", "cap", True

    def step0(self, ctx):
        w = self.page.locator("cap-widget").first
        b = _box(w)
        if b:
            human_click(self.page, b[0] + 30, b[1] + b[3] / 2)      # the box sits at the left of the widget
        return {"engine": "tick+pow"}


class RecaptchaV3(Kind):
    name, vendor, lane, has_step0 = "recaptcha-v3", "google", "recaptcha_v3", True

    def step0(self, ctx):
        return {"engine": "score-only (nothing to solve)"}


class Turnstile(Kind):
    name, vendor, lane, has_step0 = "turnstile", "cloudflare", "turnstile", True

    def token(self):
        return self.page.evaluate("""() => { try { if (window.turnstile && turnstile.getResponse()) return turnstile.getResponse(); } catch (e) {}
            return [...document.querySelectorAll('input[name="cf-turnstile-response"]')].map(i => i.value).join(''); }""")

    def step0(self, ctx):
        for _ in range(16):                                         # it usually passes by itself
            if self.token():
                return {"engine": "passed by itself"}
            time.sleep(0.25)
        el = self.page.query_selector('iframe[src*="challenges.cloudflare.com"]') or self.page.query_selector("#w-turnstile, .cf-turnstile")
        b = el.bounding_box() if el else None
        if b:   # the box is in a closed shadow root: click where it is drawn (captcha.py's method)
            human_click(self.page, b["x"] + 30, b["y"] + min(b["height"] / 2, 32))
        return {"engine": "tick"}


# ---- reCAPTCHA v2: tick (0) -> audio + local Whisper (1) -> picture grid by one focused call (4) ---------------------

class RecaptchaV2(Kind):
    name, vendor, lane, has_step0 = "recaptcha-v2", "google", "recaptcha_v2", True
    local = {1: ["audio"], 2: []}

    def anchor(self):
        return next((f for f in self.page.frames if RC_ANCHOR.search(f.url) and "size=invisible" not in f.url), None)

    def bframe(self):
        return next((f for f in self.page.frames if RC_BFRAME.search(f.url)), None)

    def checked(self):
        a = self.anchor()
        try:
            return a is not None and a.locator("#recaptcha-anchor").get_attribute("aria-checked", timeout=1500) == "true"
        except Exception:
            return False

    def challenge_open(self):
        b = self.bframe()
        try:
            return b is not None and b.locator("#rc-imageselect, .rc-audiochallenge-control, .rc-imageselect-payload").first.is_visible()
        except Exception:
            return False

    def wait_outcome(self, timeout):
        """'checked' once Google issues a token, 'challenge' if a puzzle is up, None on timeout."""
        end = time.time() + timeout
        while time.time() < end:
            if self.checked():
                return "checked"
            if self.challenge_open():
                return "challenge"
            time.sleep(0.25)
        return None

    def step0(self, ctx):
        a = self.anchor()
        if not a:
            return {"engine": "tick", "note": "no tick box"}
        if not self.checked():
            box = a.frame_element().bounding_box()
            human_click(self.page, box["x"] + 27, box["y"] + box["height"] / 2)   # the box is ~27 px in from the left
        out = self.wait_outcome(6)
        return {"engine": "tick", "note": out or "no outcome"}

    def instruction_template(self, obs=None):
        if obs and obs.geom.get("target"):
            return f"grid:{obs.geom['target']}"
        return ""

    @property
    def layout(self):
        return ""

    def signature(self, obs=None):
        if obs and obs.geom.get("target"):
            return f"{self.name}|grid:{obs.geom['target']}|{obs.geom.get('dims', '')}"
        return f"{self.name}||"

    # step 1: audio
    def audio(self, ctx, rounds=3):
        b = self.bframe()
        if not b:
            return "no-challenge"
        try:
            if b.locator("#recaptcha-audio-button").is_visible():
                bb = b.locator("#recaptcha-audio-button").bounding_box()
                human_click(self.page, bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        except Exception:
            pass
        tmp = tempfile.mkdtemp(prefix="solver-audio-")
        try:
            for n in range(rounds):
                link = None
                for _ in range(40):
                    time.sleep(0.25)
                    if self.checked():
                        return "passed"
                    if b.locator(".rc-doscaptcha-header-text").count() and b.locator(".rc-doscaptcha-header-text").first.is_visible():
                        return "refused"                    # "Try again later": Google refuses audio to this address
                    if b.locator(".rc-audiochallenge-tdownload-link").count():
                        link = b.locator(".rc-audiochallenge-tdownload-link").get_attribute("href")
                        break
                if not link:
                    return "no-audio"
                mp3 = os.path.join(tmp, f"a{n}.mp3")
                urllib.request.urlretrieve(link, mp3)
                words = transcribe(mp3)
                ctx.trace.append({"audio_heard": words})
                if not words:
                    b.locator("#recaptcha-reload-button").click()
                    continue
                b.locator("#audio-response").click()
                b.locator("#audio-response").press_sequentially(words, delay=70)
                b.locator("#recaptcha-verify-button").click()
                for _ in range(24):
                    time.sleep(0.25)
                    if self.checked():
                        return "passed"
            return "not-accepted"
        finally:
            for f in os.listdir(tmp):
                os.remove(os.path.join(tmp, f))
            os.rmdir(tmp)

    # step 4: picture grid
    def observe(self):
        b = self.bframe()
        if not b or not self.challenge_open():
            return None
        if b.locator(".rc-audiochallenge-control").count() and b.locator(".rc-audiochallenge-control").first.is_visible():
            return None                                           # the audio view is up: no grid to look at
        desc = b.locator(".rc-imageselect-desc-wrapper").first.inner_text(timeout=3000)
        target = (b.locator(".rc-imageselect-desc-wrapper strong").first.inner_text(timeout=2000) or "").strip().lower()
        tiles = b.locator("td.rc-imageselect-tile")
        n = tiles.count()
        dims = {9: "3x3", 16: "4x4", 8: "4x2"}.get(n, f"{n}")
        frame_box = b.frame_element().bounding_box()
        tbox = []
        for i in range(n):
            bb = tiles.nth(i).bounding_box()
            tbox.append((bb["x"], bb["y"], bb["width"], bb["height"]))
        x0 = min(t[0] for t in tbox)
        y0 = min(t[1] for t in tbox)
        x1 = max(t[0] + t[2] for t in tbox)
        y1 = max(t[1] + t[3] for t in tbox)
        im = shot(self.page, (x0, y0, x1 - x0, y1 - y0))
        d = ImageDraw.Draw(im)
        for i, (tx, ty, tw, th) in enumerate(tbox):                # number every tile so the model can name it
            d.rectangle([tx - x0 + 2, ty - y0 + 2, tx - x0 + 26, ty - y0 + 22], fill=(255, 255, 255))
            d.text((tx - x0 + 6, ty - y0 + 5), str(i + 1), fill=(200, 0, 0))
        return Obs({"grid": im}, {"target": target, "dims": dims, "tiles": tbox, "frame": frame_box,
                                  "dynamic": "none left" in desc.lower() or "no new" in desc.lower()},
                   " ".join(desc.split()))

    def vision(self, obs, calls, **route):
        prompt = (f"This is a picture CAPTCHA. Instruction: \"{obs.instruction}\". The tiles are numbered 1-{len(obs.geom['tiles'])}"
                  f" in the top-left corner of each tile (row by row). Which tiles contain any part of: {obs.geom['target']}? "
                  "Reply with JSON only: {\"tiles\": [numbers]} (an empty list if none).")

        def parse(t):
            j = models.json_from(t)
            tiles = j["tiles"] if isinstance(j, dict) else j
            return {"value": sorted({int(x) for x in tiles if 1 <= int(x) <= len(obs.geom["tiles"])}), "engine": "vision"}
        ans, ident = models.ask(prompt, [obs.images["grid"].resize((obs.images["grid"].width * 2, obs.images["grid"].height * 2))],
                                parse, calls, **route)
        if ans:
            ans["model"] = ident
        return ans

    def act(self, obs, answer):
        for i in answer["value"]:
            tx, ty, tw, th = obs.geom["tiles"][i - 1]
            human_click(self.page, tx + tw / 2, ty + th / 2, jitter=tw / 6)
        time.sleep(0.8)

    def press_verify(self):
        b = self.bframe()
        bb = b.locator("#recaptcha-verify-button").bounding_box()
        human_click(self.page, bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)


# ---- text in a distorted image (generic: any <img> named captcha next to a text box) -------------------------------

class TextImage(Kind):
    name, vendor = "text-image", "generic"
    local = {1: ["tesseract"], 2: ["ddddocr.ocr"]}
    conf_gate = 0.8

    def _img(self):
        return self.page.locator("img[id*=captcha i], img[class*=captcha i], img[alt*=captcha i], img[src*=captcha i]").first

    @property
    def layout(self):
        b = _box(self._img())
        return f"{int(b[2]) // 10 * 10}x{int(b[3]) // 10 * 10}" if b else ""

    def observe(self):
        img = self._img()
        im = _img_from_src(img.get_attribute("src"))
        return Obs({"image": im.convert("RGB")}, {"img": _box(img)}, "Type the characters you see")

    def vision(self, obs, calls, **route):
        im = obs.images["image"]
        prompt = ("Read the distorted characters in this CAPTCHA image exactly. They are uppercase letters A-Z and digits "
                  "0-9, usually 4 to 6 of them. Reply with JSON only: {\"text\": \"...\"}")

        def parse(t):
            v = re.sub(r"[^A-Za-z0-9]", "", str(models.json_from(t)["text"])).upper()
            return {"value": v, "engine": "vision"} if 3 <= len(v) <= 8 else None
        ans, ident = models.ask(prompt, [im.resize((im.width * 2, im.height * 2))], parse, calls, **route)
        if ans:
            ans["model"] = ident
        return ans

    def act(self, obs, answer):
        inp = self.page.locator("input[type=text], input:not([type])").first
        b = _box(inp)
        human_click(self.page, b[0] + b[2] / 2, b[1] + b[3] / 2)
        inp.fill("")
        self.page.keyboard.type(str(answer["value"]), delay=90)
        btn = self.page.locator("button:has-text('Verify'), button[type=submit], input[type=submit]").first
        bb = _box(btn)
        human_click(self.page, bb[0] + bb[2] / 2, bb[1] + bb[3] / 2)

    @staticmethod
    def same(a, b):
        return str(a).upper() == str(b).upper()


# ---- go-captcha (wenlng/go-captcha) widgets: slide, drag, rotate, click ----------------------------------------------

class GoBase(Kind):
    vendor = "go-captcha"

    def body(self):
        return self.page.locator(f".{self.css} .gc-body").first

    @property
    def layout(self):
        b = _box(self.body())
        return f"{int(b[2])}x{int(b[3])}" if b else ""

    def _images(self):
        m = _img_from_src(self.page.locator(f".{self.css} .gc-master").first.get_attribute("src"))
        tsel = ".gc-tile, .gc-thumb-rot, .gc-thumb"
        t = _img_from_src(self.page.locator(f".{self.css}").locator(tsel).first.get_attribute("src"))
        return m, t

    def _tile_pos(self):
        return self.page.evaluate(f"""() => {{ const t = document.querySelector('.{self.css} .gc-tile');
            return [parseFloat(t.style.left) || 0, parseFloat(t.style.top) || 0]; }}""")


class GoSlide(GoBase):
    name, css = "gocaptcha-slide", "gc-slide"
    local = {1: ["cv.slide"], 2: ["ddddocr.slide"]}
    conf_gate = 0.45

    def observe(self):
        m, t = self._images()
        x, y = self._tile_pos()
        return Obs({"master": m, "thumb": t}, {"display_x": x, "display_y": y, "body": _box(self.body())},
                   "Slide the piece into the gap")

    def vision(self, obs, calls, **route):
        g, f = gridded(obs.images["master"].convert("RGB"), step=25)
        prompt = ("Image 1 is a picture with a pixel grid (labels are pixel coordinates). Somewhere along the row at "
                  f"y={obs.geom['display_y']} there is a darker gap shaped like the puzzle piece in image 2. Give the "
                  "x coordinate of the gap's LEFT edge in the grid's pixel coordinates. JSON only: {\"x\": number}")

        def parse(t):
            return {"value": [int(round(float(models.json_from(t)["x"]))), int(obs.geom["display_y"])], "engine": "vision"}
        ans, ident = models.ask(prompt, [g, obs.images["thumb"].convert("RGB")], parse, calls, **route)
        if ans:
            ans["model"] = ident
        return ans

    def act(self, obs, answer):
        """Closed loop, as a hand does: drag the handle most of the way, read where the piece is, finish exactly."""
        p = self.page
        h = _box(p.locator(".gc-slide .gc-handle").first)
        hx, hy = h[0] + h[2] / 2, h[1] + h[3] / 2
        target = answer["value"][0]
        dx = target - obs.geom["display_x"]
        human_move(p, hx, hy)
        p.mouse.down()
        time.sleep(0.12)
        steps = 30
        for i in range(1, steps + 1):
            e = (i / steps) ** 2 * (3 - 2 * i / steps)
            p.mouse.move(hx + dx * e, hy + (i % 3 - 1) * 0.6)
            time.sleep(0.012)
        for _ in range(4):                                         # correct by what the piece shows
            x, _ = self._tile_pos()
            err = target - x
            if abs(err) < 0.5:
                break
            dx += err
            p.mouse.move(hx + dx, hy)
            time.sleep(0.05)
        time.sleep(0.15)
        p.mouse.up()


class GoDrag(GoBase):
    name, css = "gocaptcha-drag", "gc-drag"
    local = {1: ["cv.drag"], 2: []}
    conf_gate = 0.45

    def observe(self):
        m, t = self._images()
        x, y = self._tile_pos()
        return Obs({"master": m, "thumb": t}, {"display_x": x, "display_y": y, "body": _box(self.body())},
                   "Drag the piece into the gap")

    def vision(self, obs, calls, **route):
        g, f = gridded(obs.images["master"].convert("RGB"), step=25)
        prompt = ("Image 1 is a picture with a pixel grid (labels are pixel coordinates). It contains a darker gap shaped "
                  "like the puzzle piece in image 2 (ignore the piece itself if drawn). Give the gap's top-left corner in "
                  "the grid's pixel coordinates. JSON only: {\"x\": number, \"y\": number}")

        def parse(t):
            j = models.json_from(t)
            return {"value": [int(round(float(j["x"]))), int(round(float(j["y"])))], "engine": "vision"}
        ans, ident = models.ask(prompt, [g, obs.images["thumb"].convert("RGB")], parse, calls, **route)
        if ans:
            ans["model"] = ident
        return ans

    def act(self, obs, answer):
        p = self.page
        t = _box(p.locator(".gc-drag .gc-tile").first)
        sx, sy = t[0] + t[2] / 2, t[1] + t[3] / 2
        tx, ty = answer["value"]
        dx, dy = tx - obs.geom["display_x"], ty - obs.geom["display_y"]
        human_move(p, sx, sy)
        p.mouse.down()
        time.sleep(0.12)
        for i in range(1, 31):
            e = (i / 30) ** 2 * (3 - 2 * i / 30)
            p.mouse.move(sx + dx * e, sy + dy * e)
            time.sleep(0.012)
        for _ in range(4):
            x, y = self._tile_pos()
            ex, ey = tx - x, ty - y
            if abs(ex) < 0.5 and abs(ey) < 0.5:
                break
            dx += ex
            dy += ey
            p.mouse.move(sx + dx, sy + dy)
            time.sleep(0.05)
        time.sleep(0.15)
        p.mouse.up()


class GoRotate(GoBase):
    name, css = "gocaptcha-rotate", "gc-rotate"
    local = {1: ["cv.rotate"], 2: []}
    conf_gate = 0.3

    def observe(self):
        m, t = self._images()
        return Obs({"master": m, "thumb": t}, {"body": _box(self.body())}, "Rotate the picture upright")

    def vision(self, obs, calls, **route):
        m = obs.images["master"].convert("RGB")
        t = obs.images["thumb"].convert("RGB")
        prompt = ("Image 1 is a round picture; image 2 is its centre disc, turned by some angle. By how many degrees "
                  "CLOCKWISE (0-359) must image 2 be rotated so that it lines up with the surrounding picture in image 1? "
                  "JSON only: {\"angle\": number}")

        def parse(tx):
            return {"value": int(round(float(models.json_from(tx)["angle"]))) % 360, "engine": "vision"}
        ans, ident = models.ask(prompt, [m, t], parse, calls, **route)
        if ans:
            ans["model"] = ident
        return ans

    def _angle(self):
        return self.page.evaluate("""() => { const t = document.querySelector('.gc-rotate .gc-thumb-rot');
            const m = /rotate\\(([-0-9.]+)deg\\)/.exec(t.style.transform || ''); return m ? parseFloat(m[1]) : 0; }""")

    def act(self, obs, answer):
        p = self.page
        h = _box(p.locator(".gc-rotate .gc-handle").first)
        track = _box(p.locator(".gc-rotate .gc-track").first)
        hx, hy = h[0] + h[2] / 2, h[1] + h[3] / 2
        target = float(answer["value"])
        dx = target / 360 * (track[2] - h[2])
        human_move(p, hx, hy)
        p.mouse.down()
        time.sleep(0.12)
        for i in range(1, 31):
            e = (i / 30) ** 2 * (3 - 2 * i / 30)
            p.mouse.move(hx + dx * e, hy)
            time.sleep(0.012)
        for _ in range(5):
            err = target - self._angle()
            if abs(err) < 0.6:
                break
            dx += err / 360 * (track[2] - h[2])
            p.mouse.move(hx + dx, hy)
            time.sleep(0.05)
        time.sleep(0.15)
        p.mouse.up()


class GoClick(GoBase):
    name, css = "gocaptcha-click", "gc-click"
    local = {1: [], 2: ["ddddocr.click"]}
    conf_gate = 0.99

    def instruction_template(self, obs=None):
        return "click-in-order"

    def observe(self):
        m, t = self._images()
        return Obs({"master": m, "thumb": t}, {"body": _box(self.body())}, "Click in this order")

    def vision(self, obs, calls, **route):
        g, f = gridded(obs.images["master"].convert("RGB"), step=25)
        th = obs.images["thumb"].convert("RGBA")
        bg = Image.new("RGB", th.size, (255, 255, 255))
        bg.paste(th, mask=th.split()[3])
        bg = bg.resize((bg.width * 3, bg.height * 3))
        prompt = ("Image 2 is a strip showing, left to right, the items (characters or shapes) to click, in order. Image 1 "
                  "is a picture with a pixel grid (labels are pixel coordinates) where those same items appear scattered, "
                  "possibly rotated and in other colours. For each item in image 2, in order, give the centre of the "
                  "matching item in image 1 in the grid's pixel coordinates. JSON only: {\"points\": [[x, y], ...]}")

        def parse(t):
            pts = models.json_from(t)
            pts = pts["points"] if isinstance(pts, dict) else pts
            pts = [[int(round(float(a))), int(round(float(b)))] for a, b in pts]
            return {"value": pts, "engine": "vision"} if pts else None
        ans, ident = models.ask(prompt, [g, bg], parse, calls, **route)
        if ans:
            ans["model"] = ident
        return ans

    def act(self, obs, answer):
        bx, by = obs.geom["body"][0], obs.geom["body"][1]
        for x, y in answer["value"]:
            human_click(self.page, bx + x, by + y, jitter=1)
        b = _box(self.page.locator(".gc-click .gc-confirm").first)
        human_click(self.page, b[0] + b[2] / 2, b[1] + b[3] / 2)


# ---- recognised but not solved here --------------------------------------------------------------------------------

class Refused(Kind):
    """hCaptcha: its terms forbid AI passing its challenges; only with written permission (project rule)."""
    name, vendor = "hcaptcha", "hcaptcha"


class Unknown(Kind):
    """A vendor we recognise but have no handler for (Arkose, GeeTest), or a page-drawn puzzle: steps 4-5 only, via the
    general agent looking at the widget's region."""
    name = "unknown"

    def __init__(self, page, root=None, vendor="unknown"):
        super().__init__(page, root)
        self.vendor = vendor
        self.name = f"unknown-{vendor}"


def detect(page):
    """Every CAPTCHA on the page, as Kind objects, in the order a person would meet them."""
    found = []
    urls = [f.url for f in page.frames]
    if any(RC_ANCHOR.search(u) and "size=invisible" not in u for u in urls):
        found.append(RecaptchaV2(page))
    if page.evaluate("() => !!(window.grecaptcha && document.getElementById('w-recaptcha_v3'))"):
        found.append(RecaptchaV3(page))
    if any(TURNSTILE.search(u) for u in urls) or page.query_selector('iframe[src*="challenges.cloudflare.com"], .cf-turnstile'):
        found.append(Turnstile(page))
    if any(HC.search(u) for u in urls):
        found.append(Refused(page))
    if any(ARKOSE.search(u) for u in urls):
        found.append(Unknown(page, vendor="arkose"))
    if any(GEETEST.search(u) for u in urls):
        found.append(Unknown(page, vendor="geetest"))
    if page.query_selector("altcha-widget"):
        found.append(Altcha(page))
    if page.query_selector("cap-widget"):
        found.append(Cap(page))
    for cls in (GoSlide, GoDrag, GoRotate, GoClick):
        if page.query_selector(f".{cls.css}"):
            found.append(cls(page))
    if page.query_selector("img[id*=captcha i], img[class*=captcha i], img[alt*=captcha i], img[src*=captcha i]") and \
            page.query_selector("input[type=text], input:not([type])"):
        found.append(TextImage(page))
    return found
