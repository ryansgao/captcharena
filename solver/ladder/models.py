"""Ladder step 4's eyes: free vision APIs only, as a fallback chain with rate-limit handling.

the owner, 2026-11-03: "if solver needs to make llm call, make it use free apis online". Order (cheapest first, as in
plan.html step 4): Mistral Small free mode -> OpenRouter free vision models -> Groq vision -> Gemini free tier. A
provider is in the chain only if its key file exists in ~/.config/agent-secrets/ (or its env var is set). Claude is
refused by construction (`_refuse`): the solver never calls it.

Rate limits: a 429 cools that model down (Retry-After / X-RateLimit-Reset, else 60 s for "upstream" limits); a 402/403
or a daily-quota message parks it until the next UTC day; state persists in runs/.model-state.json so separate runs
share the cool-downs. OpenRouter's free tier allows 50 requests a UTC day on an account with <$10 of credit bought
(docs, checked 2026-11-03), so its calls are counted and stopped at OPENROUTER_DAILY (default 48).
"""
import base64
import datetime
import io
import json
import os
import re
import time

import httpx

SECRETS = os.path.expanduser("~/.config/agent-secrets")
STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs", ".model-state.json")
OPENROUTER_DAILY = int(os.environ.get("OPENROUTER_DAILY", 48))

# (provider, base URL, key file, env var, models in preference order). Model lists checked 2026-11-03.
PROVIDERS = [
    ("mistral", "https://api.mistral.ai/v1", "mistral", "MISTRAL_API_KEY", ["mistral-small-latest"]),
    ("openrouter", "https://openrouter.ai/api/v1", "openrouter", "OPENROUTER_API_KEY", [
        "nvidia/nemotron-3.5-super-vl:free",        # first: answered every probe on 2026-11-03
        "google/gemma-4-31b-it:free",               # often "rate-limited upstream" (shared Google AI Studio pool)
        "google/gemma-4-26b-a4b-it:free",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "dots-studio/dots-3-note-preview:free",
        "openrouter/free",                          # OpenRouter's own router over whatever free models are up
    ]),
    ("groq", "https://api.groq.com/openai/v1", "groq", "GROQ_API_KEY", ["meta-llama/llama-4-scout-17b-16e-instruct"]),
    ("gemini", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini", "GEMINI_API_KEY",
     ["gemini-flash-lite-latest", "gemini-flash-latest"]),
]


def _refuse(model):
    if re.search(r"claude|anthropic", model, re.I):
        raise ValueError("the solver never calls Claude (project rule, 2026-11-03)")


def _key(fname, env):
    if os.environ.get(env):
        return os.environ[env].strip()
    p = os.path.join(SECRETS, fname)
    return open(p).read().strip() if os.path.exists(p) else None


def _today():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def _load():
    try:
        s = json.load(open(STATE))
    except (OSError, ValueError):
        s = {}
    if s.get("day") != _today():
        s = {"day": _today(), "count": {}, "cool": {}, "parked": {}}
    return s


def _save(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(s, open(STATE, "w"), indent=1)


def to_data_url(im, fmt="PNG"):
    buf = io.BytesIO()
    im.save(buf, fmt)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()


def chain(only=None):
    """[(provider, base, key, model)] usable now, in order. `only` = list of 'provider/model' or 'provider'."""
    s = _load()
    out = []
    for prov, base, fname, env, models in PROVIDERS:
        key = _key(fname, env)
        if not key:
            continue
        for m in models:
            _refuse(m)
            ident = f"{prov}/{m}"
            if only and not any(ident == o or prov == o or ident.startswith(o + "/") for o in only):
                continue
            if s["parked"].get(ident) or s["cool"].get(ident, 0) > time.time():
                continue
            if prov == "openrouter" and s["count"].get("openrouter", 0) >= OPENROUTER_DAILY:
                continue
            out.append((prov, base, key, m))
    if only:                                           # keep the caller's order (a cached policy names its model first)
        rank = {o: i for i, o in enumerate(only)}
        out.sort(key=lambda t: min([rank[o] for o in rank if f"{t[0]}/{t[3]}" == o or t[0] == o] or [99]))
    return out


def available():
    return [f"{p}/{m}" for p, _, _, m in chain()]


class Calls:
    """Counts what one solve spent: calls made, by model, seconds, failures (for the run log)."""

    def __init__(self):
        self.n = 0
        self.log = []

    def add(self, ident, ok, seconds, note=""):
        self.n += 1
        self.log.append({"model": ident, "ok": ok, "s": round(seconds, 1), **({"note": note[:120]} if note else {})})


def ask(prompt, images, parse, calls=None, prefer=None, only=None, exclude=(), max_models=3, max_tokens=1500, timeout=90):
    """One focused call: prompt + images -> parse(text) -> answer. Walks the chain until a model gives an answer that
    parses (not until one is right: the site's verdict decides that, upstream). `prefer` puts named models first,
    `only` restricts to them, `exclude` skips models that already failed this challenge. Returns (answer,
    'provider/model') or (None, None) when every usable model failed or is rate-limited."""
    calls = calls if calls is not None else Calls()
    if only:
        order = chain(only)
    elif prefer:
        first = chain(prefer)
        order = first + [c for c in chain() if c not in first]
    else:
        order = chain()
    order = [c for c in order if f"{c[0]}/{c[3]}" not in exclude]
    # reasoning models spent all their tokens thinking and returned no answer (2026-11-03)
    prompt += "\nAnswer at once with the JSON only: no explanation, no step-by-step reasoning."
    content = [{"type": "text", "text": prompt}] + [{"type": "image_url", "image_url": {"url": to_data_url(im)}}
                                                    for im in images]
    tried = 0
    for prov, base, key, model in order:
        if tried >= max_models:
            break
        ident = f"{prov}/{model}"
        s = _load()
        if prov == "openrouter":
            if s["count"].get("openrouter", 0) >= OPENROUTER_DAILY:
                continue
        tried += 1
        t0 = time.time()
        try:
            r = httpx.post(base + "/chat/completions", timeout=timeout,
                           headers={"Authorization": f"Bearer {key}"},
                           json={"model": model, "max_tokens": max_tokens, "temperature": 0,
                                 "messages": [{"role": "user", "content": content}],
                                 **({"reasoning": {"effort": "low"}} if prov == "openrouter" else {})})
        except httpx.HTTPError as e:
            calls.add(ident, False, time.time() - t0, f"network: {type(e).__name__}")
            s["cool"][ident] = time.time() + 30
            _save(s)
            continue
        s = _load()
        s["count"][prov] = s["count"].get(prov, 0) + 1
        if r.status_code == 429:
            body = r.text[:400]
            wait = r.headers.get("retry-after")
            reset = r.headers.get("x-ratelimit-reset")
            if "per-day" in body or "free-models-per-day" in body or "daily" in body.lower():
                s["parked"][ident if "upstream" in body else prov + "/*"] = True
                if "upstream" not in body:
                    for p2, _, _, _, ms in PROVIDERS:
                        if p2 == prov:
                            for m2 in ms:
                                s["parked"][f"{prov}/{m2}"] = True
            elif wait and wait.replace(".", "").isdigit():
                s["cool"][ident] = time.time() + float(wait)
            elif reset and reset.isdigit():
                s["cool"][ident] = int(reset) / (1000 if int(reset) > 1e11 else 1)
            else:
                s["cool"][ident] = time.time() + 60
            _save(s)
            calls.add(ident, False, time.time() - t0, "429 " + body[:100])
            continue
        if r.status_code in (401, 402, 403, 404):
            s["parked"][ident] = True
            _save(s)
            calls.add(ident, False, time.time() - t0, f"{r.status_code} {r.text[:100]}")
            continue
        _save(s)
        if r.status_code != 200:
            calls.add(ident, False, time.time() - t0, f"{r.status_code} {r.text[:100]}")
            continue
        try:
            msg = r.json()["choices"][0]["message"]
            text = msg.get("content") or ""
            if isinstance(text, list):
                text = " ".join(p.get("text", "") for p in text if isinstance(p, dict))
            if not text.strip():                     # reasoning models sometimes leave the answer in their reasoning
                text = msg.get("reasoning") or ""
        except (ValueError, KeyError, IndexError):
            calls.add(ident, False, time.time() - t0, "unreadable reply")
            continue
        try:
            ans = parse(text)
        except Exception:
            ans = None
        calls.add(ident, ans is not None, time.time() - t0, "" if ans is not None else "unparsable: " + text[:80])
        if ans is not None:
            return ans, ident
    return None, None


def json_from(text):
    """The last JSON object or array in a model's reply (they wrap it in prose or ``` fences)."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    dec = json.JSONDecoder()
    found = None
    i = 0
    while i < len(text):
        if text[i] in "{[":
            try:
                obj, end = dec.raw_decode(text, i)
                found = obj                          # keep the last complete one
                i = end
                continue
            except ValueError:
                pass
        i += 1
    if found is None:
        raise ValueError("no JSON in reply")
    return found
