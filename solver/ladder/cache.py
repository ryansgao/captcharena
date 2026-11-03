"""Ladder step 3: saved solutions, one per CAPTCHA type, promoted only on the site's own verdict.

A *type* is a signature: kind + instruction template + layout (see detect.Challenge.signature). Its entry holds a
*policy* — which answerer to run on the observation and with what parameters (a local engine such as `ddddocr.ocr`
or `cv.slide`, or a focused vision call naming the model and prompt that worked) — plus the evidence behind it.

Rules (plan.html §1, step 3):
- Promotion: an entry is created or replaced only from a solve the site's server accepted (`verdict == "pass"`).
  A solve with no server verdict (a widget token, nothing more) is kept as evidence but never promoted.
- Demotion: two failures in a row, or a pass rate under 50 % over the last 6 uses, demotes the entry; the router then
  skips it and the next server-accepted solve from steps 4-5 replaces the policy.
- Labels: every accepted answer is also saved with its images under cache/labels/<type>/ — the training set for step
  2's local models, and the test set the write-back uses to see whether a cheaper engine reproduces the answer.
"""
import hashlib
import json
import os
import time

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")


def _slug(sig):
    return hashlib.sha1(sig.encode()).hexdigest()[:12]


class Cache:
    def __init__(self, root=ROOT):
        self.root = root
        os.makedirs(os.path.join(root, "policies"), exist_ok=True)
        os.makedirs(os.path.join(root, "labels"), exist_ok=True)

    def _path(self, sig):
        return os.path.join(self.root, "policies", _slug(sig) + ".json")

    def get(self, sig):
        try:
            return json.load(open(self._path(sig)))
        except (OSError, ValueError):
            return None

    def usable(self, sig):
        e = self.get(sig)
        return e if e and e.get("status") == "promoted" else None

    def _put(self, e):
        e["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        json.dump(e, open(self._path(e["signature"]), "w"), indent=1)

    def promote(self, sig, kind, policy, evidence, origin_step):
        """Called only after the site's server accepted a solve made with `policy`."""
        assert evidence.get("verdict") == "pass", "promotion needs the server's acceptance"
        e = self.get(sig) or {"signature": sig, "kind": kind, "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                              "history": [], "evidence": []}
        if e.get("policy") != policy:
            if e.get("policy"):
                e["history"].append({"policy": e["policy"], "status": e.get("status"), "replaced": time.strftime("%Y-%m-%dT%H:%M:%S")})
            e["uses"] = []
        e.update(status="promoted", policy=policy, origin_step=origin_step)
        e["evidence"] = (e["evidence"] + [evidence])[-20:]
        self._put(e)
        return e

    def record_use(self, sig, ok, evidence):
        """A replay (step 3) result. Returns the entry's new status."""
        e = self.get(sig)
        if not e:
            return None
        e.setdefault("uses", []).append(1 if ok else 0)
        e["uses"] = e["uses"][-6:]
        e["evidence"] = (e["evidence"] + [evidence])[-20:]
        u = e["uses"]
        if (len(u) >= 2 and u[-1] == 0 and u[-2] == 0) or (len(u) >= 4 and sum(u) / len(u) < 0.5):
            e["status"] = "demoted"
        self._put(e)
        return e["status"]

    def save_label(self, sig, images, answer, meta):
        d = os.path.join(self.root, "labels", _slug(sig))
        os.makedirs(d, exist_ok=True)
        n = len([f for f in os.listdir(d) if f.endswith(".json")])
        names = {}
        for name, im in images.items():
            fn = f"{n:04d}-{name}.png"
            im.save(os.path.join(d, fn))
            names[name] = fn
        json.dump({"signature": sig, "answer": answer, "images": names, **meta}, open(os.path.join(d, f"{n:04d}.json"), "w"))
        return n

    def labels(self, sig, last=5):
        from PIL import Image
        d = os.path.join(self.root, "labels", _slug(sig))
        if not os.path.isdir(d):
            return []
        out = []
        for f in sorted(f for f in os.listdir(d) if f.endswith(".json"))[-last:]:
            m = json.load(open(os.path.join(d, f)))
            m["images"] = {k: Image.open(os.path.join(d, v)) for k, v in m["images"].items()}
            out.append(m)
        return out

    def all(self):
        out = []
        for f in sorted(os.listdir(os.path.join(self.root, "policies"))):
            try:
                out.append(json.load(open(os.path.join(self.root, "policies", f))))
            except ValueError:
                pass
        return out

    def clear(self, kind_prefix=""):
        import shutil
        for e in self.all():
            if e["kind"].startswith(kind_prefix):
                os.remove(self._path(e["signature"]))
                shutil.rmtree(os.path.join(self.root, "labels", _slug(e["signature"])), ignore_errors=True)
