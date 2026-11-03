#!/usr/bin/env python3
"""build.py — fetch, debrand, patch and containerise the open clone suites listed in suites.json.

    python3 suites/build.py            fetch (if missing) + prepare every suite + docker compose build + up
    python3 suites/build.py --no-up    prepare and build only
    python3 suites/build.py --down     stop the containers

Each suite's repository is cloned at its pinned commit into suites/_src/<name>/repo (third-party code: never run
on the host, only inside its container). The server part is copied into suites/_build/<name>, where:
  1. debrand(): every link to a vendor's servers is removed, vendor names in visible text (titles, text nodes,
     alt/title/aria-label/placeholder) become neutral words, logo-ish elements are hidden by an injected style,
     and image files named like logos are replaced by a blank pixel. The check that it worked is visual and
     textual, in the browser: `harness/bench.py debrand-check`.
  2. patch(): small, asserted edits — answer-leak endpoints closed, a task-id parameter so the harness can ask
     for one exact puzzle, debug answer routes off.
  3. Dockerfile: our own, minimal (the suites' own images pull agent frameworks we do not need on the server).
All containers publish on 127.0.0.1 only (compose.yml): the clones are never public.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "_src")
BUILD = os.path.join(HERE, "_build")
MANIFEST = json.load(open(os.path.join(HERE, "suites.json")))["suites"]

VENDORS = ["arkose labs", "arkoselabs", "arkose", "funcaptcha", "geetest", "hcaptcha", "recaptcha", "google",
           "gstatic", "tencent", "yandex", "amazon", "aws", "lemin", "mtcaptcha", "botdetect", "baidu",
           "cloudflare", "turnstile", "smartcaptcha", "datadome", "perimeterx", "netease", "dingxiang",
           "极验", "腾讯", "百度", "网易", "易盾", "顶象"]
VENDOR_RX = re.compile("|".join(sorted(((r"\b" + re.escape(v) + r"\b") if v.isascii() else re.escape(v) for v in VENDORS),
                                       key=len, reverse=True)), re.I)
# A vendor link (now about:blank) is hidden with whatever it wraps: that is where logo images sit.
# Links that must survive: XML namespaces are identifiers, not network requests.
KEEP_URL = re.compile(r"^https?://(www\.)?w3\.org/|^https?://(127\.0\.0\.1|localhost)")
URL_RX = re.compile(r"https?://[^\s\"'()<>`]+")
LOGO_FILE = re.compile(r"logo|brand|wordmark", re.I)
HIDE_STYLE = ('<style data-bench="debrand">[class*="logo" i],[id*="logo" i],[class*="brand" i],[id*="brand" i],'
              '[class*="footer_right" i],[class*="powered" i],a[href="about:blank"]{display:none!important}</style>')
BLANK_PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                          "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")


def sh(*cmd, cwd=None):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def fetch(name, s):
    repo = os.path.join(SRC, name, "repo")
    if not os.path.isdir(os.path.join(repo, ".git")):
        os.makedirs(os.path.dirname(repo), exist_ok=True)
        sh("git", "clone", "-q", s["repo"] + ".git", repo)
    head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != s["commit"]:
        try:
            sh("git", "-C", repo, "checkout", "-q", s["commit"])
        except subprocess.CalledProcessError:   # a shallow clone may not hold the pinned commit
            sh("git", "-C", repo, "fetch", "-q", "--depth", "1", "origin", s["commit"])
            sh("git", "-C", repo, "checkout", "-q", s["commit"])
    import lfs_fetch                                   # OCW and NextGen keep their puzzles in Git LFS
    if next(lfs_fetch.pointers(repo), None):
        slug = s["repo"].split("github.com/")[1]
        assert lfs_fetch.main(repo, slug, s["commit"]) == 0, f"{name}: LFS objects missing"
    return repo


def neutral(m):
    return "Puzzle"


def debrand_text(html):
    """Vendor names in what a person sees: text between tags and a few attributes. Code (script/style bodies,
    class names, ids, selectors) is left alone so the page keeps working."""
    out, pos = [], 0
    for m in re.finditer(r"<(script|style)\b.*?</\1\s*>", html, re.S | re.I):
        out.append(_debrand_markup(html[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_debrand_markup(html[pos:]))
    return "".join(out)


def _debrand_markup(s):
    s = re.sub(r">([^<]+)<", lambda m: ">" + _text_only(m.group(1)) + "<", s)
    s = re.sub(r"\b(alt|title|aria-label|placeholder)=(\"[^\"]*\"|'[^']*')",
               lambda m: m.group(1) + "=" + VENDOR_RX.sub(neutral, m.group(2)), s, flags=re.I)
    return s


def _text_only(t):
    if "{{" in t or "{%" in t:                                   # leave Jinja expressions intact
        return t
    return re.sub(r"powered\s+by", "", VENDOR_RX.sub(neutral, t), flags=re.I)   # leave Jinja expressions intact


def debrand(root):
    stats = {"urls": 0, "texts": 0, "logos": 0, "styles": 0}
    for d, _, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            ext = f.rsplit(".", 1)[-1].lower()
            if LOGO_FILE.search(f) and ext in ("png", "jpg", "jpeg", "gif", "svg", "webp", "ico"):
                open(p, "wb").write(BLANK_PNG)
                stats["logos"] += 1
                continue
            if ext not in ("html", "htm", "css", "js", "py"):
                continue
            src = open(p, encoding="utf-8", errors="surrogateescape").read()
            new = src
            if ext in ("html", "htm", "css", "js"):
                new = URL_RX.sub(lambda m: m.group(0) if KEEP_URL.search(m.group(0)) else "about:blank", new)
            if ext in ("html", "htm") or (ext == "py" and "<html" in new.lower()):
                t = debrand_text(new)
                if t != new:
                    stats["texts"] += 1
                new = t
                if "<head" in new.lower() and 'data-bench="debrand"' not in new:
                    new = re.sub(r"(<head[^>]*>)", lambda m: m.group(1) + HIDE_STYLE.replace("{", "{{").replace("}", "}}")
                                 if ext == "py" else m.group(1) + HIDE_STYLE, new, count=1, flags=re.I)
                    stats["styles"] += 1
            if new != src:
                stats["urls"] += len(URL_RX.findall(src)) - len(URL_RX.findall(new))
                open(p, "w", encoding="utf-8", errors="surrogateescape").write(new)
    return stats


def replace_once(path, old, new):
    s = open(path, encoding="utf-8").read()
    assert s.count(old) >= 1, f"patch anchor not found in {path}: {old[:60]!r}"
    open(path, "w", encoding="utf-8").write(s.replace(old, new, 1))


LEAK_CLOSED = ("@app.route('/api/get_ground_truth', methods=['POST'])\ndef get_ground_truth():\n"
               "    return jsonify({'error': 'closed by the bench harness (answer leak)'}), 404\n\n"
               "def _get_ground_truth_original():")


THREE = ("https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js",
         "9274bbcec8d96168626c732b5d31c775aa8cfb7eaa0599bec0c175908a2c1ce2")


def prepatch(name, root):
    """Before debranding: third-party libraries a suite loads from a CDN are served locally instead (the bench
    browser cannot reach the internet)."""
    if name == "nextgen":
        import hashlib, urllib.request
        cache = os.path.join(SRC, "vendor", "three-r128.min.js")
        if not os.path.exists(cache):
            os.makedirs(os.path.dirname(cache), exist_ok=True)
            urllib.request.urlretrieve(THREE[0], cache)
        got = hashlib.sha256(open(cache, "rb").read()).hexdigest()
        assert got == THREE[1], f"three.js r128 checksum mismatch: {got}"
        os.makedirs(os.path.join(root, "static", "vendor"), exist_ok=True)
        shutil.copy2(cache, os.path.join(root, "static", "vendor", "three.min.js"))
        replace_once(os.path.join(root, "templates", "index.html"), THREE[0], "/static/vendor/three.min.js")


def patch(name, root):
    if name in ("ocw", "nextgen"):
        app = os.path.join(root, "app.py")
        replace_once(app, "@app.route('/api/get_ground_truth', methods=['POST'])\ndef get_ground_truth():", LEAK_CLOSED)
    if name == "ocw":
        # The harness asks for one exact puzzle: ?type=T&puzzle_id=ID (OCW only serves a per-type sequence).
        replace_once(os.path.join(root, "app.py"), "    selected_puzzle = sequence[idx % len(sequence)]\n",
                     "    selected_puzzle = sequence[idx % len(sequence)]\n"
                     "    if request.args.get('puzzle_id') in ground_truth:  # bench harness: exact task\n"
                     "        selected_puzzle = request.args.get('puzzle_id')\n")
    if name in ("ocw", "nextgen", "halligan"):
        app = os.path.join(root, "server.py" if name == "halligan" else "app.py")
        open(app, "a").write(FLASK_TAP)
    if name == "hll":
        open(os.path.join(root, "serve_all.py"), "w").write(HLL_ENTRY)
        page = os.path.join(root, "web", "captcha_page.py")
        replace_once(page, "            result = session.verify(user_input, trap_input=trap_input)\n",
                     "            result = session.verify(user_input, trap_input=trap_input)\n"
                     "            _bench_tap(self.server.server_address[1], result.success)\n")
        replace_once(page, '            elif path == "/api/stats":\n',
                     '            elif path == "/bench/verdicts":\n'
                     '                self._send_json(_bench_since(urllib.parse.parse_qs(parsed.query)))\n'
                     '            elif path == "/api/stats":\n')
        replace_once(page, "        def _serve_stats(self):\n",
                     "        def _send_json(self, obj):\n"
                     "            self.send_response(200)\n"
                     '            self.send_header("Content-Type", "application/json; charset=utf-8")\n'
                     "            self.end_headers()\n"
                     '            self.wfile.write(json.dumps(obj).encode("utf-8"))\n\n'
                     "        def _serve_stats(self):\n")
        replace_once(page, "class CaptchaSession:", HLL_TAP + "\n\nclass CaptchaSession:")


# The verdict tap: every final checker reply, verdict only (never the answer), in order. The harness reads it at
# /bench/verdicts?after=<seq>, so every solver is scored by the same server-side record, whichever browser it uses.
FLASK_TAP = '''

# --- bench harness verdict tap (added by captcha/bench/suites/build.py) ---
import threading as _bench_threading, time as _bench_time
_BENCH_V, _BENCH_L = [], _bench_threading.Lock()


@app.after_request
def _bench_tap(resp):
    try:
        if request.method == "POST" and resp.is_json:
            j = resp.get_json(silent=True) or {}
            v = None
            if "solved" in j:
                v = bool(j["solved"])
            elif request.path.endswith("/api/check_answer") and j.get("status") != "continue" and "correct" in j:
                v = bool(j["correct"])
            if v is not None:
                body = request.get_json(silent=True) or {}
                with _BENCH_L:
                    _BENCH_V.append({"seq": len(_BENCH_V) + 1, "t": _bench_time.time(), "path": request.path,
                                     "task": str(body.get("puzzle_id") or body.get("id") or j.get("id") or ""),
                                     "pass": v})
    except Exception:
        pass
    return resp


@app.route("/bench/verdicts")
def _bench_verdicts():
    after = int(request.args.get("after", 0))
    with _BENCH_L:
        return jsonify([v for v in _BENCH_V if v["seq"] > after])
'''

HLL_TAP = '''# --- bench harness verdict tap (added by captcha/bench/suites/build.py) ---
import time as _bench_time
_BENCH_V, _BENCH_L = [], Lock()


def _bench_tap(port, ok):
    with _BENCH_L:
        _BENCH_V.append({"seq": len(_BENCH_V) + 1, "t": _bench_time.time(), "port": port, "pass": bool(ok)})


def _bench_since(q):
    after = int((q.get("after") or ["0"])[0])
    with _BENCH_L:
        return [v for v in _BENCH_V if v["seq"] > after]
'''

HLL_ENTRY = '''"""Bench harness entry: one HLL server per CAPTCHA type, debug answers off. Configs copied from the suite's
own run_captcha_demo.py defaults (length 4, difficulty "normal", images from the repo's own folders)."""
import json, os, signal
from web.captcha_page import start_captcha_server_in_thread
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "web", "captcha", "images")
TYPES = json.load(open(os.path.join(HERE, "hll_types.json")))


def config(t):
    c = {}
    if t in ("text", "text_trace"):
        c["length"] = 4
    if t in ("click", "click_icon", "click_icon_dynamic", "click_real", "click_real_dynamic"):
        c["click_count"] = 3
    if t in ("slider_real", "slider_real_dynamic", "puzzle_real", "puzzle_real_dynamic", "image_grid",
             "image_grid_dynamic", "pic_puzzle", "pic_puzzle_click", "pic_puzzle_dynamic", "missing_piece",
             "missing_piece_dynamic"):
        c["difficulty"] = "normal"
    folder = {"slider_real": "slider", "slider_real_dynamic": "slider", "click_real": "click",
              "click_real_dynamic": "click", "puzzle_real": "puzzle", "puzzle_real_dynamic": "puzzle",
              "image_grid": "image_grid", "image_grid_dynamic": "image_grid"}.get(t)
    if folder:
        c["image_dir"] = os.path.join(IMG, folder)
    return c


for i, t in enumerate(TYPES):
    start_captcha_server_in_thread(captcha_type=t, captcha_config=config(t), host="0.0.0.0", port=8000 + i, debug=False)
signal.pause()
'''
HLL_TYPES = ["text", "text_trace", "slider", "slider_real", "slider_real_dynamic", "click", "click_icon",
             "click_icon_dynamic", "click_anywhere", "click_trace", "click_real", "click_real_dynamic", "puzzle",
             "puzzle_real", "puzzle_real_dynamic", "pic_puzzle", "pic_puzzle_click", "pic_puzzle_dynamic",
             "image_grid", "image_grid_dynamic", "missing_piece", "missing_piece_dynamic",
             "logic_arithmetic_dynamic", "five_line", "five_line_dynamic"]

DOCKERFILES = {
    "ocw": "FROM python:3.11-slim\nRUN pip install --no-cache-dir flask==3.0.3 flask-cors==5.0.0 pillow==11.0.0 gunicorn==23.0.0\n"
           "WORKDIR /app\nCOPY . /app/\nUSER nobody\nCMD [\"gunicorn\", \"--bind=0.0.0.0:8000\", \"--workers=1\", \"--threads=8\", \"app:app\"]\n",
    "nextgen": "FROM python:3.11-slim\nRUN pip install --no-cache-dir flask==3.0.3 flask-cors==5.0.0 pillow==11.0.0 gunicorn==23.0.0 numpy==2.1.3\n"
               "WORKDIR /app\nCOPY . /app/\nUSER nobody\nCMD [\"gunicorn\", \"--bind=0.0.0.0:8000\", \"--workers=1\", \"--threads=8\", \"app:app\"]\n",
    "halligan": "FROM python:3.10-slim\nRUN pip install --no-cache-dir flask==3.0.2 werkzeug==3.0.1 gunicorn==23.0.0 requests==2.31.0\n"
                "WORKDIR /benchmark\nCOPY . /benchmark/\nRUN chown -R nobody /benchmark\nUSER nobody\n"
                "CMD [\"gunicorn\", \"--bind=0.0.0.0:8000\", \"--threads=10\", \"server:app\"]\n",
    "hll": "FROM python:3.11-slim\nRUN pip install --no-cache-dir Pillow==11.0.0 PyYAML==6.0.2 numpy==2.1.3\n"
           "WORKDIR /app\nCOPY . /app/\nUSER nobody\nENV PYTHONUNBUFFERED=1\nCMD [\"python\", \"serve_all.py\"]\n",
}


def compose():
    lines = ["# Generated by suites/build.py. Every port is bound to 127.0.0.1: the clones are never public.",
             "name: captcha-bench", "services:"]
    for name, s in MANIFEST.items():
        lines += [f"  {name}:", f"    build: ./_build/{name}", f"    image: captcha-bench-{name}:{s['commit'][:12]}",
                  "    restart: unless-stopped", "    read_only: false", "    cap_drop: [ALL]",
                  "    security_opt: [\"no-new-privileges:true\"]", "    mem_limit: 2g", "    ports:"]
        if name == "hll":
            lines.append(f"      - \"127.0.0.1:{s['port']}-{s['port'] + len(HLL_TYPES) - 1}:8000-{8000 + len(HLL_TYPES) - 1}\"")
        else:
            lines.append(f"      - \"127.0.0.1:{s['port']}:8000\"")
    open(os.path.join(HERE, "compose.yml"), "w").write("\n".join(lines) + "\n")


def prepare(name, s):
    repo = fetch(name, s)
    base = os.path.join(repo, s.get("copy_from", ""))
    dst = os.path.join(BUILD, name)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(dst)
    for item in s["copy"]:
        src = os.path.join(base, item)
        (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, os.path.join(dst, item))
    for t in s.get("excluded_types", {}):          # excluded types are not even copied where they are a folder
        p = os.path.join(dst, "apis", t)
        if name == "halligan" and os.path.isdir(p):
            shutil.rmtree(p)
            replace_once(os.path.join(dst, "server.py"), f"from apis.{t} import {t}\n", "")
            replace_once(os.path.join(dst, "server.py"), f'app.register_blueprint({t}, url_prefix="/{t}")\n', "")
            for d, _, files in os.walk(os.path.join(dst, "apis")):   # commented-out links Jinja still resolves
                for f in files:
                    if f.endswith(".html"):
                        fp = os.path.join(d, f)
                        src = open(fp).read()
                        new = re.sub(r"[^\n]*url_for\('" + t + r"\.static'[^\n]*\n", "", src)
                        if new != src:
                            open(fp, "w").write(new)
    prepatch(name, dst)
    stats = debrand(dst)
    patch(name, dst)
    if name == "hll":
        json.dump(HLL_TYPES, open(os.path.join(dst, "hll_types.json"), "w"))
    open(os.path.join(dst, "Dockerfile"), "w").write(DOCKERFILES[name])
    open(os.path.join(dst, ".dockerignore"), "w").write(".git\n__pycache__\n")
    print(f"{name}: prepared from {s['commit'][:12]}; debrand {stats}")
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-up", action="store_true")
    ap.add_argument("--down", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    if a.down:
        sh("docker", "compose", "-f", os.path.join(HERE, "compose.yml"), "down")
        return
    report = {}
    for name, s in MANIFEST.items():
        if a.only and name != a.only:
            continue
        report[name] = prepare(name, s)
    compose()
    old = {}
    if os.path.exists(os.path.join(HERE, "build-report.json")):
        old = json.load(open(os.path.join(HERE, "build-report.json"))).get("debrand", {})
    json.dump({"hll_types": HLL_TYPES, "debrand": {**old, **report}}, open(os.path.join(HERE, "build-report.json"), "w"), indent=2)
    sh("docker", "compose", "-f", os.path.join(HERE, "compose.yml"), "build")
    if not a.no_up:
        sh("docker", "compose", "-f", os.path.join(HERE, "compose.yml"), "up", "-d")


if __name__ == "__main__":
    sys.exit(main())
