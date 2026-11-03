"""Suite adapters: what tasks a suite has, where each task's page is, and how to read the suite's own checker.

Every suite is scored by its own server-side checker, never by us: the harness only watches the browser's network
traffic for the checker's reply (OCW/NextGen `POST /api/check_answer` -> `correct`; Halligan `POST .../submit`
-> `solved`; HLL `POST /verify` -> `success`). The first final reply is the verdict: one attempt per task, as on
a real site. No reply before the time limit = fail ("no-submit").
"""
import glob
import json
import os
import re
from dataclasses import dataclass, field, asdict

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(BENCH, "suites", "_build")
MANIFEST = json.load(open(os.path.join(BENCH, "suites", "suites.json")))["suites"]
HOST = "http://127.0.0.1"


@dataclass
class Task:
    suite: str
    type: str
    task_id: str
    url: str
    rewrite: dict = field(default_factory=dict)   # request-path prefix -> replacement URL (exact-task selection)
    frozen: bool = True                            # False: the suite generates a fresh instance on every load

    def key(self):
        return f"{self.suite}/{self.type}/{self.task_id}"

    def as_dict(self):
        return asdict(self)


def _natural(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def _gt(suite, ctype):
    try:
        g = json.load(open(os.path.join(BUILD, suite, "captcha_data", ctype, "ground_truth.json")))
    except (OSError, ValueError):
        return []
    return sorted((k for k in g if k != "config"), key=_natural)


def ocw_tasks():
    port = MANIFEST["ocw"]["port"]
    out = []
    for t in sorted(os.listdir(os.path.join(BUILD, "ocw", "captcha_data"))):
        for pid in _gt("ocw", t):
            out.append(Task("ocw", t, pid, f"{HOST}:{port}/",
                            rewrite={"/api/get_puzzle": f"{HOST}:{port}/api/get_puzzle?type={t}&puzzle_id={pid}"}))
    return out


def nextgen_tasks():
    port = MANIFEST["nextgen"]["port"]
    out = []
    for t in sorted(os.listdir(os.path.join(BUILD, "nextgen", "captcha_data"))):
        ids = _gt("nextgen", t)
        n = len(ids) or 20                          # config-only (generated) types: indices with a fixed seed
        for i in range(n):
            out.append(Task("nextgen", t, str(i), f"{HOST}:{port}/?type={t}&puzzle_index={i}&seed=0"))
    return out


def _halligan_routes():
    root = os.path.join(BUILD, "halligan", "apis")
    routes = []
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if not os.path.isdir(d) or name.startswith("__"):
            continue
        if os.path.exists(os.path.join(d, "challenges.json")):
            routes.append((name, d + "/challenges.json"))
        for sub in sorted(os.listdir(d)):
            sd = os.path.join(d, sub)
            if not os.path.isdir(sd) or sub in ("static", "templates", "__pycache__"):
                continue
            if os.path.exists(os.path.join(sd, "challenges.json")):
                routes.append((f"{name}/{sub}", sd + "/challenges.json"))
            for variant in sorted(glob.glob(os.path.join(sd, "*.json"))):   # arkose multichoice / paged variants
                if not variant.endswith("challenges.json"):
                    routes.append((f"{name}/{sub}/{os.path.basename(variant)[:-5]}", variant))
    return routes


def halligan_tasks():
    port = MANIFEST["halligan"]["port"]
    out = []
    for route, path in _halligan_routes():
        n = len(json.load(open(path)).get("challenges", []))
        for i in range(1, n + 1):
            out.append(Task("halligan", route, str(i), f"{HOST}:{port}/{route}/{i}"))
    return out


def hll_tasks(per_type=20):
    types = json.load(open(os.path.join(BUILD, "hll", "hll_types.json")))
    port = MANIFEST["hll"]["port"]
    return [Task("hll", t, f"fresh-{n}", f"{HOST}:{port + i}/refresh", frozen=False)
            for i, t in enumerate(types) for n in range(per_type)]


TASKS = {"ocw": ocw_tasks, "nextgen": nextgen_tasks, "halligan": halligan_tasks, "hll": hll_tasks}


def all_tasks(suites=None):
    out = []
    for s, f in TASKS.items():
        if suites and s not in suites:
            continue
        out += f()
    return out


def verdict(suite, method, url, body):
    """The suite's own checker reply -> True / False, or None if this response is not a final verdict."""
    if method != "POST" or not isinstance(body, dict):
        return None
    path = url.split("?")[0]
    if suite in ("ocw", "nextgen") and path.endswith("/api/check_answer"):
        if body.get("status") == "continue":       # multi-hit puzzles (NextGen Red_Dot): not final yet
            return None
        if "correct" in body:
            return bool(body["correct"])
        return False if "error" in body else None
    if suite == "halligan" and "solved" in body:
        return bool(body["solved"])
    if suite == "hll" and path.endswith("/verify") and "success" in body:
        return bool(body["success"])
    return None


# Endpoints that hand out answers: closed for every solver (server patch where we can, browser block here too).
LEAKS = re.compile(r"/api/get_ground_truth|/api/answer\b|/api/last_result")
