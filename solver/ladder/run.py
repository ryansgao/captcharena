"""Work the ladder for every CAPTCHA on a page; log one line per challenge to runs/solver-runs.jsonl."""
import json
import os
import time

from . import agent as A
from . import engines, models, router
from . import kinds as K
from .cache import Cache

RUNS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs")
LOG = os.path.join(RUNS, "solver-runs.jsonl")


class Ctx:
    def __init__(self, page, cache=None, trust=None, rounds4=2):
        self.page, self.cache, self.trust, self.rounds4 = page, cache or Cache(), trust, rounds4
        self.calls = models.Calls()
        self.trace = []


def _res(outcome, **kw):
    return {"outcome": outcome, **kw}


def _submit(kind, obs, ans):
    kind.act(obs, ans)
    return kind.verdict(timeout=8) or "unverified"


def step0(kind, ctx):
    r = kind.step0(ctx) or {}
    if isinstance(kind, K.RecaptchaV2):
        if r.get("note") == "challenge":
            return _res("escalate", engine="tick", note="a picture challenge opened")
        if r.get("note") != "checked":
            return _res("escalate", engine="tick", note=r.get("note"))
    v = kind.verdict(timeout=25)
    shown = kind.shown_verdict()
    if isinstance(kind, K.RecaptchaV3) and shown:
        import re as _re
        m = _re.search(r"score ([0-9.]+)", shown)
        if m:                                              # our own measured score: the router's trust input
            router.save_trust(float(m.group(1)), "reCAPTCHA v3 lane, during a solve")
            ctx.trust = float(m.group(1))
    return _res(v or "unverified", engine=r.get("engine"), note=r.get("note") or shown)


def local_step(kind, ctx, step):
    if isinstance(kind, K.RecaptchaV2):                     # step 1 for reCAPTCHA = the audio challenge
        out = kind.audio(ctx)
        if out == "passed":
            return _res(kind.verdict(timeout=10) or "unverified", engine="audio+whisper")
        return _res("escalate", engine="audio+whisper", note=out)
    obs = kind.observe()
    best = None
    for eng in kind.local.get(step, []):
        a = engines.ENGINES[eng](obs)
        if a and (best is None or a["conf"] > best["conf"]):
            best = a
    if not best:
        return _res("escalate", note="no local answer", obs=obs)
    if best["conf"] < kind.conf_gate:
        return _res("escalate", engine=best["engine"], conf=best["conf"], note="below confidence gate: not sent", obs=obs)
    v = _submit(kind, obs, best)
    return _res(v, engine=best["engine"], conf=best["conf"], answer=best, obs=obs)


def recaptcha_grid(kind, ctx, label_step, max_rounds=4):
    """Picture grids, a round at a time: one focused call names the tiles; replaced tiles get another look."""
    b = kind.bframe()
    if b is not None:
        try:
            if b.locator("#recaptcha-image-button").is_visible():       # back from the audio view to pictures
                b.locator("#recaptcha-image-button").click()
                time.sleep(1.5)
        except Exception:
            pass
    used_cache = False
    last = {}
    for _ in range(max_rounds):
        if kind.checked():
            break
        obs = kind.observe()
        if not obs:
            break
        sig = kind.signature(obs)
        entry = ctx.cache.usable(sig)
        route = {}
        if entry and entry["policy"].get("model"):
            route, used_cache = {"prefer": [entry["policy"]["model"]]}, True
        ans = kind.vision(obs, ctx.calls, **route)
        if not ans:
            return _res("escalate", note="no model answered", step_label=label_step)
        last = {"obs": obs, "answer": ans, "sig": sig}
        ctx.trace.append({"grid": obs.instruction, "tiles": ans["value"], "model": ans.get("model")})
        kind.act(obs, ans)
        if obs.geom.get("dynamic"):                                  # tiles fade in again: look until none match
            for _ in range(3):
                time.sleep(3.5)
                o2 = kind.observe()
                if not o2:
                    break
                a2 = kind.vision(o2, ctx.calls, prefer=[ans["model"]])
                if not a2 or not a2["value"]:
                    break
                kind.act(o2, a2)
        kind.press_verify()
        out = kind.wait_outcome(6)
        if out == "checked":
            v = kind.verdict(timeout=10) or "unverified"
            return _res(v, engine="vision", model=ans.get("model"), answer=ans, obs=obs, sig=sig,
                        step_label=3 if used_cache else label_step)
        time.sleep(1.0)
    return _res("fail" if last else "escalate", engine="vision", note="grid not accepted", step_label=label_step,
                sig=last.get("sig"))


def vision_step(kind, ctx, step, entry=None):
    if isinstance(kind, K.RecaptchaV2):
        return recaptcha_grid(kind, ctx, step)
    failed = []
    r = _res("escalate", note="no model answered")
    for _ in range(ctx.rounds4 if step == 4 else 1):
        obs = kind.observe()
        route = {"only": [entry["policy"]["model"]], "max_models": 1} if step == 3 else {"exclude": tuple(failed)}
        ans = kind.vision(obs, ctx.calls, **route)
        if not ans:
            return r
        v = _submit(kind, obs, ans)
        r = _res(v, engine="vision", model=ans.get("model"), answer=ans, obs=obs)
        if v != "fail":
            return r
        failed.append(ans.get("model"))
        kind.wait_ready()
    return r


def cached_step(kind, ctx, entry):
    pol = entry["policy"]
    if pol["engine"] in engines.ENGINES:
        obs = kind.observe()
        ans = engines.ENGINES[pol["engine"]](obs)
        if not ans:
            return _res("escalate", engine=pol["engine"], note="saved engine gave no answer")
        v = _submit(kind, obs, ans)
        return _res(v, engine=pol["engine"], answer=ans, obs=obs)
    if pol["engine"] == "vision":
        r = vision_step(kind, ctx, 3, entry)
        return r
    if pol["engine"] == "agent":
        ag = A.FreeVisionAgent(ctx.calls, prefer=[pol["model"]] if pol.get("model") else None)
        v, trace = A.general_solve(kind, ctx, ag)
        return _res(v or "escalate", engine="agent", model=ag.model, answer={"engine": "agent", "model": ag.model, "trace": trace})
    return _res("escalate", note=f"unknown saved engine {pol['engine']}")


def general_step(kind, ctx):
    ag = A.FreeVisionAgent(ctx.calls)
    v, trace = A.general_solve(kind, ctx, ag)
    ctx.trace.append({"agent_trace": trace})
    obs = None
    try:
        obs = kind.observe()
    except Exception:
        pass
    return _res(v or "escalate", engine="agent", model=ag.model, answer={"engine": "agent", "model": ag.model, "trace": trace,
                                                                       "value": None}, obs=obs)


def solve_kind(kind, ctx, max_step=5, series=None, url="", only_steps=None):
    t0 = time.time()
    sig = kind.signature()
    entry = ctx.cache.get(sig) if not isinstance(kind, K.RecaptchaV2) else None
    steps, notes = router.plan(kind, entry, ctx.trust, max_step)
    if only_steps:                                   # measurement mode: force the named steps (step 0 always kept)
        steps = [s for s in steps if s in only_steps or s == 0] or [s for s in only_steps if s in (1, 2, 4, 5)]
    attempts, final, won = [], None, None
    for step in steps:
        ts, c0 = time.time(), ctx.calls.n
        try:
            if step == 0:
                r = step0(kind, ctx)
            elif step in (1, 2):
                r = local_step(kind, ctx, step)
            elif step == 3:
                r = cached_step(kind, ctx, entry)
            elif step == 4:
                r = vision_step(kind, ctx, 4)
            else:
                r = general_step(kind, ctx)
        except Exception as e:                                   # one step breaking must not end the ladder
            r = _res("error", note=f"{type(e).__name__}: {str(e)[:160]}")
        label = r.get("step_label", step)
        attempts.append({"step": label, "outcome": r["outcome"], "engine": r.get("engine"), "model": r.get("model"),
                         "conf": r.get("conf"), "note": r.get("note"), "s": round(time.time() - ts, 1),
                         "model_calls": ctx.calls.n - c0})
        if label == 3 and entry and r["outcome"] in ("pass", "fail"):
            ctx.cache.record_use(sig, r["outcome"] == "pass", {"verdict": r["outcome"], "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                                              "url": url, "seconds": round(time.time() - ts, 1)})
        if r["outcome"] in ("pass", "unverified"):
            final, won = r["outcome"], (label, r)
            break
        if r["outcome"] == "fail":
            final = "fail"
            kind.wait_ready()
    sig_final = (won[1].get("sig") if won and won[1].get("sig") else None) or sig
    promoted = None
    if won and final == "pass" and won[0] in (1, 2, 4, 5) and won[1].get("answer") and kind.verdict_source():
        ev = {"verdict": "pass", "verdict_source": kind.verdict_source(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "url": url, "seconds": round(time.time() - t0, 1), "step": won[0], "model_calls": ctx.calls.n}
        e = A.writeback(ctx.cache, kind, sig_final, won[1].get("obs"), won[1]["answer"], ev, won[0])
        promoted = e["policy"]
    line = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "series": series, "url": url, "kind": kind.name, "vendor": kind.vendor,
            "signature": sig_final, "trust": ctx.trust, "plan": steps, "notes": notes, "attempts": attempts,
            "verdict": final or "unsolved", "solved_at_step": won[0] if won else None,
            "verdict_source": kind.verdict_source(), "seconds": round(time.time() - t0, 1),
            "model_calls": ctx.calls.n, "calls": ctx.calls.log, "cost_usd": 0.0, "promoted": promoted,
            "trace": ctx.trace}
    os.makedirs(RUNS, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(line, default=str) + "\n")
    ctx.calls = models.Calls()
    ctx.trace = []
    return line


def solve_page(page, max_step=5, trust=None, series=None, only_kinds=None, cache=None, only_steps=None):
    ctx = Ctx(page, cache=cache, trust=trust)
    found = K.detect(page)
    if only_kinds:
        found = [k for k in found if any(k.name.startswith(o) for o in only_kinds)]
    return [solve_kind(k, ctx, max_step, series, page.url, only_steps) for k in found]
