"""Solver adapters: one interface, three solvers.

    class Solver:
        name, version
        available() -> (bool, reason)         a missing solver is logged as "skipped", never as a fail
        solve(ctx) -> {"cost_usd", "step", "note"}   act on the task; the verdict comes from the suite's checker

ctx (SimpleNamespace): cdp (the bench browser's CDP URL), page (a Playwright Page on the task, in that browser),
task (suites.Task), deadline_s, rng (random.Random seeded by the task key: reruns of a frozen task repeat).

random   trivial baseline: random clicks, drags and keys on whatever looks interactive, then a submit-like click.
v0       the owner's private solver, <private v0 solver> (automatic ladder only), via harness/v0_shim.py.
tiered   the new tiered solver in projects/captcha/solver/ (another agent builds it; this folder never edits it).
"""
import json
import os
import string
import subprocess
import sys
import time

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIERED = "solver"

INTERACTIVE = ("button, [role=button], canvas, img, input, select, a, svg, [onclick], [draggable=true], "
               "[class*=slider i], [class*=btn i], [class*=option i], [class*=tile i], [class*=cell i], "
               "[class*=item i], [class*=arrow i], [class*=grid i] > *")
SUBMIT_WORDS = ("submit", "verify", "confirm", "check", "done", "ok", "next", "skip", "提交", "确认", "验证", "确定")


class Solver:
    name = "base"
    version = "0"

    def available(self):
        return True, ""

    def solve(self, ctx):
        raise NotImplementedError


class RandomSolver(Solver):
    """Chance level for each type, measured through the same page and checker as every other solver."""
    name = "random"
    version = "1"

    def _boxes(self, page):
        boxes = []
        for fr in page.frames:
            try:
                loc = fr.locator(INTERACTIVE)
                n = min(loc.count(), 40)
            except Exception:
                continue
            for i in range(n):
                try:
                    el = loc.nth(i)
                    if not el.is_visible():
                        continue
                    b = el.bounding_box()
                    if b and b["width"] * b["height"] >= 64:
                        tag = el.evaluate("e => e.tagName.toLowerCase() + '|' + (e.type||'') + '|' + "
                                          "(e.innerText||e.value||'').slice(0,30).toLowerCase()")
                        boxes.append((b, tag))
                except Exception:
                    continue
        return boxes

    def solve(self, ctx):
        page, rng = ctx.page, ctx.rng
        time.sleep(1.5)                                   # let the puzzle draw
        boxes = self._boxes(page)
        if not boxes:
            return {"cost_usd": 0.0, "step": "random", "note": "nothing interactive found"}
        acts = []
        texts = [b for b in boxes if b[1].startswith("input|text") or b[1].startswith("input|")]
        for b, _ in texts[:2]:
            page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
            page.keyboard.type("".join(rng.choice(string.ascii_letters + string.digits) for _ in range(rng.randint(3, 6))))
            acts.append("type")
        for _ in range(rng.randint(1, 4)):
            b, _t = rng.choice(boxes)
            x, y = b["x"] + rng.random() * b["width"], b["y"] + rng.random() * b["height"]
            if rng.random() < 0.3:                        # a random drag: sliders, jigsaws
                page.mouse.move(x, y)
                page.mouse.down()
                page.mouse.move(x + rng.uniform(-200, 300), y + rng.uniform(-60, 60), steps=12)
                page.mouse.up()
                acts.append("drag")
            else:
                page.mouse.click(x, y)
                acts.append("click")
            time.sleep(0.2)
        subs = [b for b in self._boxes(page) if any(w in b[1].split("|")[-1] for w in SUBMIT_WORDS)]
        if subs:
            b, _ = rng.choice(subs)
            page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
            acts.append("submit")
        else:
            page.keyboard.press("Enter")
            acts.append("enter")
        return {"cost_usd": 0.0, "step": "random", "note": ",".join(acts)}


class V0Solver(Solver):
    """captcha.py's automatic ladder (`solve`), attached to the bench browser over CDP. Its second rung is the
    calling agent's own eyes (a Claude model reading screenshots); the bench does not run that rung — the project
    keeps solver model calls off Claude — so v0 here is exactly what fires without a model."""
    name = "v0"
    version = "captcha.py@" + subprocess.run(["git", "-C", "<private>", "log", "-1", "--format=%h", "--",
                                              "<private v0 solver>"],
                                             capture_output=True, text=True).stdout.strip()

    def available(self):
        return (os.path.exists("<private v0 solver>"), "captcha.py missing")

    def solve(self, ctx):
        cmd = ["uv", "run", "--quiet", "--script", os.path.join(BENCH, "harness", "v0_shim.py"),
               "--cdp", ctx.cdp, "--log", os.path.join(BENCH, "results", "v0-log"), "--",
               "solve", "--url", ctx.task.url.split("?")[0]]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=ctx.deadline_s)
        except subprocess.TimeoutExpired:
            return {"cost_usd": 0.0, "step": "v0:timeout", "note": "captcha.py did not finish in time"}
        line = (p.stdout.strip().splitlines() or ["{}"])[-1]
        try:
            out = json.loads(line)
        except ValueError:
            out = {"detail": (p.stdout + p.stderr)[-200:]}
        return {"cost_usd": 0.0, "step": f"v0:exit{p.returncode}:{out.get('result', '?')}",
                "note": str(out.get("detail", ""))[:200]}


class TieredSolver(Solver):
    """Adapter for projects/captcha/solver/ (read-only from here). Its `solve.py solve --url U` drives its own
    browser and prints one JSON line per challenge; the verdict still comes from the suite's server-side tap, so
    it is scored exactly like the others. Its own guard admits 127.0.0.1 URLs, which is all the clones are.
    The contract this adapter assumes (2026-11-03, read from solve.py's docstring): exit 0 and JSON lines with
    `cost_usd` and `step` keys when present. Until the solver's README exists the adapter reports it as
    unavailable, and its rows are logged as skipped."""
    name = "tiered"
    own_browser = True

    @property
    def version(self):
        return subprocess.run(["git", "-C", TIERED, "log", "-1", "--format=%h", "--", "."], capture_output=True,
                              text=True).stdout.strip() or "uncommitted"

    def available(self):
        if not os.path.exists(os.path.join(TIERED, "solve.py")):
            return False, "projects/captcha/solver/solve.py not present"
        if not os.path.exists(os.path.join(TIERED, "README.md")):
            return False, "solver/README.md not present yet: the tiered solver is still being built by another agent"
        return True, ""

    def solve(self, ctx):
        cmd = ["uv", "run", "--project", TIERED, "python", os.path.join(TIERED, "solve.py"), "solve",
               "--url", ctx.task.url]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=ctx.deadline_s, cwd=TIERED)
        except subprocess.TimeoutExpired:
            return {"cost_usd": 0.0, "step": "tiered:timeout", "note": ""}
        cost, steps = 0.0, []
        for line in p.stdout.splitlines():
            try:
                j = json.loads(line)
            except ValueError:
                continue
            cost += float(j.get("cost_usd") or 0)
            if j.get("step") is not None:
                steps.append(str(j["step"]))
        return {"cost_usd": cost, "step": "tiered:" + ("+".join(steps) or f"exit{p.returncode}"),
                "note": p.stderr[-200:] if p.returncode else "", "own_browser": True}


SOLVERS = {s.name: s for s in (RandomSolver(), V0Solver(), TieredSolver())}
