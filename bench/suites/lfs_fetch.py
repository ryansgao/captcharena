#!/usr/bin/env python3
"""lfs_fetch.py — replace Git LFS pointer files in a fetched suite with their content, over plain HTTPS.

    python3 suites/lfs_fetch.py <repo dir> <owner/repo> <commit>

OCW and NextGen keep captcha_data in Git LFS; a plain clone holds only pointers. This uses GitHub's LFS batch API
(the same calls `git lfs pull` makes) and checks every object's sha256 against its pointer, so the data is
exactly what the pinned commit names. No git-lfs binary needed.
"""
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import urllib.request

POINTER = b"version https://git-lfs.github.com/spec/v1"


def pointers(root):
    for d, dirs, files in os.walk(root):
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            p = os.path.join(d, f)
            if os.path.getsize(p) < 400:
                b = open(p, "rb").read()
                if b.startswith(POINTER):
                    kv = dict(l.split(" ", 1) for l in b.decode().splitlines() if " " in l)
                    yield p, kv["oid"].split(":", 1)[1], int(kv["size"])


def batch(slug, objs):
    req = urllib.request.Request(
        f"https://github.com/{slug}.git/info/lfs/objects/batch",
        data=json.dumps({"operation": "download", "transfers": ["basic"],
                         "objects": [{"oid": o, "size": s} for o, s in objs]}).encode(),
        headers={"Accept": "application/vnd.git-lfs+json", "Content-Type": "application/vnd.git-lfs+json"})
    return {o["oid"]: o for o in json.load(urllib.request.urlopen(req, timeout=60))["objects"]}


def get(path, oid, href, headers):
    data = urllib.request.urlopen(urllib.request.Request(href, headers=headers), timeout=120).read()
    if hashlib.sha256(data).hexdigest() != oid:
        raise ValueError(f"sha256 mismatch for {path}")
    open(path, "wb").write(data)


def main(root, slug, commit):
    todo = list(pointers(root))
    print(f"{len(todo)} LFS pointers in {root}")
    done = 0
    for i in range(0, len(todo), 100):
        chunk = todo[i:i + 100]
        info = batch(slug, {(o, s) for _, o, s in chunk})
        with cf.ThreadPoolExecutor(8) as ex:
            futs = []
            for path, oid, _ in chunk:
                a = info[oid].get("actions", {}).get("download")
                if not a:
                    print("no download for", path, info[oid].get("error"))
                    continue
                futs.append(ex.submit(get, path, oid, a["href"], a.get("header", {})))
            for f in futs:
                f.result()
                done += 1
    left = len(list(pointers(root)))
    print(f"fetched {done}; pointers left {left}")
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
