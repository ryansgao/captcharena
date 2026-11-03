"""Pick the ladder steps for one challenge, cheapest first.

Inputs: the kind (what it is and which local engines exist), the saved-solution cache entry for its type, the
browser's measured trust (reCAPTCHA v3 score from our own measurement page; None if unknown) and --max-step.

    -1  don't get challenged: not an action here; when trust is low the plan carries advice to raise it first
     0  tick / wait (tick boxes, proof of work, score-only widgets)
     1  fixed recipes (audio -> local Whisper, tesseract, OpenCV gap / rotation search)
     2  small local models (ddddocr)
     3  saved solution for this type (only if promoted by a server-accepted solve; demoted entries are skipped)
     4  one focused free-API vision call
     5  the general agent (multi-turn), which writes back into 2-3
A promoted cache entry replaces steps 1-2: it already names the cheapest engine known to pass this type.
Step 5 runs only for kinds without a handler (Unknown): for a known kind it re-did step 4's work at ~5x the calls
(measured 2026-11-03 on text images: 9-10 calls an encounter, no pass), so --steps 5 forces it for measurement.
"""
import json
import os
import time

from . import kinds as K

TRUST_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs", ".trust.json")
LOW_TRUST = 0.3


def read_trust(max_age_s=3600):
    try:
        t = json.load(open(TRUST_FILE))
        return t["score"] if time.time() - t["at"] < max_age_s else None
    except (OSError, ValueError, KeyError):
        return None


def save_trust(score, source):
    os.makedirs(os.path.dirname(TRUST_FILE), exist_ok=True)
    json.dump({"score": score, "at": time.time(), "source": source}, open(TRUST_FILE, "w"))


def plan(kind, entry, trust, max_step=5):
    notes = []
    if isinstance(kind, K.Refused):
        return [], ["hCaptcha is not solved: its terms forbid AI passing its challenges without written permission"]
    if trust is not None and trust < LOW_TRUST:
        notes.append(f"step -1: browser trust {trust:.1f} is low; a cleaner profile or exit would avoid challenges")
    steps = [0] if kind.has_step0 else []
    if isinstance(kind, (K.Altcha, K.Cap, K.RecaptchaV3, K.Turnstile)):
        return [s for s in steps if s <= max_step], notes             # nothing beyond the widget's own step
    if entry and entry.get("status") == "promoted":
        steps.append(3)
    else:
        if entry and entry.get("status") == "demoted":
            notes.append("saved solution demoted after failures: full ladder")
        if kind.local.get(1):
            steps.append(1)
        if kind.local.get(2):
            steps.append(2)
    if isinstance(kind, K.RecaptchaV2) and trust is not None and trust < LOW_TRUST and 1 in steps:
        steps.remove(1)                                               # Google refuses audio to low-reputation clients
        notes.append("audio skipped: low trust (Google answers 'try again later')")
    steps.append(4)
    if isinstance(kind, K.Unknown):                                   # the general agent is for types never seen
        steps.append(5)
    return [s for s in steps if s <= max_step], notes
