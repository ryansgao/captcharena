"""Ladder step 5: the general agent — slow, multi-turn, for types no cheaper step can do — and its write-back.

The agent is model-agnostic: anything with `decide(image, instruction, history) -> action` works. The default,
FreeVisionAgent, uses the same free-API chain as step 4 (never Claude). An outside agent (a person, or a coding
agent driving the owner's private captcha.py by eye) can teach the cache too, through `solve.py writeback` — the promotion
rule still needs the site's own verdict.

Actions (viewport coordinates, as on the gridded screenshot):
  {"action": "click", "points": [[x, y], ...]}     {"action": "drag", "from": [x, y], "to": [x, y]}
  {"action": "type", "text": "...", "at": [x, y]}  {"action": "press", "key": "Enter"}
  {"action": "hold", "at": [x, y], "seconds": 3}   {"action": "wait", "seconds": 2}     {"action": "done"}
"""
import time

from . import engines, models
from .kinds import Obs
from .primitives import gridded, human_click, human_drag, human_hold, shot

ACTION_PROMPT = """You are solving a CAPTCHA in a web page, one action at a time. The screenshot shows the CAPTCHA's
region with a pixel grid; the grid labels are page (viewport) coordinates — use them for every point.
Task as shown on the page: {instruction}
Actions so far (oldest first): {history}
Reply with ONE next action as JSON only, one of:
{{"action": "click", "points": [[x, y], ...]}}  (several points = clicks in that order)
{{"action": "drag", "from": [x, y], "to": [x, y]}}
{{"action": "type", "text": "...", "at": [x, y]}}
{{"action": "press", "key": "Enter"}}
{{"action": "hold", "at": [x, y], "seconds": 3}}
{{"action": "wait", "seconds": 2}}
{{"action": "done"}}  (when you have submitted and nothing is left to do)"""


class FreeVisionAgent:
    def __init__(self, calls, prefer=None, exclude=()):
        self.calls, self.prefer, self.exclude, self.model = calls, prefer, exclude, None

    def decide(self, image, instruction, history):
        def parse(t):
            j = models.json_from(t)
            return j if isinstance(j, dict) and j.get("action") in (
                "click", "drag", "type", "press", "hold", "wait", "done") else None
        hist = "; ".join(f"{h['action']}" + (f" {h.get('points') or h.get('to') or h.get('text') or ''}") for h in history) or "none"
        a, ident = models.ask(ACTION_PROMPT.format(instruction=instruction, history=hist), [image], parse, self.calls,
                              prefer=self.prefer or ([self.model] if self.model else None), exclude=self.exclude,
                              max_tokens=400)
        if ident:
            self.model = ident
        return a


def region(kind):
    """The CAPTCHA's own region on the page, padded; the whole viewport if unknown."""
    p = kind.page
    for sel in (".captcha-box", "[class*=captcha i]", "iframe[src*=captcha i]", "form"):
        loc = p.locator(sel).first
        try:
            if loc.count() and loc.is_visible():
                b = loc.bounding_box()
                vw, vh = p.evaluate("() => [innerWidth, innerHeight]")
                x, y = max(0, b["x"] - 20), max(0, b["y"] - 20)
                return (x, y, min(vw - x, b["width"] + 40), min(vh - y, b["height"] + 40))
        except Exception:
            continue
    vw, vh = p.evaluate("() => [innerWidth, innerHeight]")
    return (0, 0, vw, vh)


def execute(page, a):
    act = a["action"]
    if act == "click":
        for x, y in a["points"]:
            human_click(page, float(x), float(y))
    elif act == "drag":
        human_drag(page, *map(float, a["from"]), *map(float, a["to"]), overshoot=False)
    elif act == "type":
        if a.get("at"):
            human_click(page, *map(float, a["at"]))
        page.keyboard.type(str(a["text"]), delay=90)
    elif act == "press":
        page.keyboard.press(str(a["key"]))
    elif act == "hold":
        human_hold(page, *map(float, a["at"]), float(a.get("seconds", 3)))
    elif act == "wait":
        time.sleep(min(5.0, float(a.get("seconds", 2))))


def general_solve(kind, ctx, agent, turns=6):
    """Observe -> one action -> look again, until the site's verdict arrives or `turns` run out.
    Returns (verdict, trace)."""
    trace = []
    instruction = ""
    try:
        instruction = kind.page.locator(".gc-instruction, .rc-imageselect-desc-wrapper, label, h2").first.inner_text(timeout=1500)
    except Exception:
        pass
    instruction = " ".join(instruction.split()) or "solve the CAPTCHA shown"
    start_round = kind.page.evaluate("() => document.body.dataset.round || ''")
    for _ in range(turns):
        reg = region(kind)
        im, _ = gridded(shot(kind.page, reg), origin=(reg[0], reg[1]), step=25)
        a = agent.decide(im, instruction, trace)
        if not a:
            return None, trace
        trace.append(a)
        if a["action"] == "done":
            break
        execute(kind.page, a)
        v = kind.verdict(timeout=2.5)
        if v == "pass":
            return "pass", trace
        if v == "fail" or kind.page.evaluate("() => document.body.dataset.round || ''") != start_round:
            return "fail", trace
    return kind.verdict(timeout=3) or "unverified", trace


# --- write-back: what a slow solve teaches the cheaper steps ---------------------------------------------------------

def _same(kind_name, a, b):
    if a is None or b is None:
        return False
    if kind_name == "text-image":
        return str(a).upper() == str(b).upper()
    if kind_name in ("gocaptcha-slide", "gocaptcha-drag"):
        return abs(a[0] - b[0]) <= 3 and abs(a[1] - b[1]) <= 3
    if kind_name == "gocaptcha-rotate":
        d = abs(int(a) - int(b)) % 360
        return min(d, 360 - d) <= 2
    if kind_name == "gocaptcha-click":
        return len(a) == len(b) and all(abs(p[0] - q[0]) <= 10 and abs(p[1] - q[1]) <= 10 for p, q in zip(a, b))
    return a == b


def writeback(cache, kind, sig, obs, answer, evidence, step):
    """After the site's server accepted a solve from steps 1, 2, 4 or 5: save the label (step 2's training data), then
    pick the policy the next encounter replays (step 3): the cheapest local engine that reproduces every saved
    accepted answer of this type (needs >= 3 labels when the solve came from a model), else what solved it."""
    if obs is not None and obs.images:
        cache.save_label(sig, obs.images, answer.get("value"), {"geom": {k: v for k, v in obs.geom.items()
                                                                         if isinstance(v, (int, float, str))},
                                                                 "engine": answer.get("engine"), "model": answer.get("model")})
    policy = {"engine": answer.get("engine")}
    if answer.get("model"):
        policy["model"] = answer["model"]
    if answer.get("engine") == "agent":
        policy["trace_actions"] = [a.get("action") for a in answer.get("trace", [])]
    labels = cache.labels(sig, last=5)
    need = 3 if answer.get("engine") in ("vision", "agent") else 1     # 2 was too few: chance agreement (2026-11-03)
    distilled = None
    if len(labels) >= need:
        for eng in kind.local.get(1, []) + kind.local.get(2, []):
            if eng not in engines.ENGINES:
                continue
            hits = 0
            for lab in labels:
                try:
                    r = engines.ENGINES[eng](Obs(lab["images"], lab.get("geom", {})))
                except Exception:
                    r = None
                hits += _same(kind.name, r and r["value"], lab["answer"])
            if hits == len(labels):
                distilled = eng
                break
    if distilled and distilled != policy["engine"]:
        policy = {"engine": distilled, "distilled_from": answer.get("model") or answer.get("engine"), "labels_checked": len(labels)}
    return cache.promote(sig, kind.name, policy, evidence, step)
