# solver/ — the tiered CAPTCHA solver (plan build steps 3 and 5)

Agent-facing. A measurement and research harness: it solves CAPTCHAs on **our own domain**
(https://measure.captcharena.org) and on **open-source CAPTCHAs run locally** (`lab/`), in its own Playwright browser,
and logs what each ladder step cost. Never third-party sites (`solve.py` refuses other URLs), never hCaptcha (the
router refuses it), never a token service. Model calls go to **free APIs only**; Claude is refused in code.
Built 2026-11-03 on the owner's private solver (`<private v0 solver>`, ours first).

## Result in one table (measured 2026-11-03, n per row in brackets)

| Kind | Where | Solved by | Pass rate | Median time | Model calls | Cost |
|---|---|---|---|---|---|---|
| go-captcha slide | lab | step 1 (OpenCV gap match), then step 3 | **10/10** in browser; 10/10 engine-only | 1.6 s | 0 | $0 |
| go-captcha drag | lab | step 1, then step 3 | **10/10** in browser; 9/10 engine-only | 1.6 s | 0 | $0 |
| go-captcha rotate | lab | step 1 (ring-continuity search), then step 3 | **10/10** in browser; 20/20 engine-only | 1.6 s | 0 | $0 |
| distorted text (lepture/captcha) | lab | step 2 (ddddocr) | 4/12 (ddddocr alone 13/30 = 43 %) | 3.0 s | 0 | $0 |
| distorted text | lab | step 4 (free vision call) | 3 of 6 answers accepted | 5–9 s | 1–2 per answer | $0 |
| reCAPTCHA v2 (real key) | measure | step 1 (audio + local Whisper) | **7/7** (5 bench + 2 smoke) | 6.7 s | 0 | $0 |
| reCAPTCHA v2 picture grid | measure | step 4 | 0/1 (4 rounds, 89 s) | — | 7 | $0 |
| reCAPTCHA v3 (real key) | measure | step 0 (score only) | 8/8, score **0.9** headless and headed | — | 0 | $0 |
| ALTCHA | measure | step 0 (proof of work) | 7/7 | 1.0 s | 0 | $0 |
| Cap | measure | step 0 (tick + proof of work) | 7/7 | 1.8 s | 0 | $0 |
| Cloudflare Turnstile (real key) | measure | — | **0/9**: widget error 600010, headless and headed | — | 0 | — |
| go-captcha click (characters / shapes) | lab | — | 0/2 at step 4 (no parseable answer), ddddocr 0/10 | — | 1–3 | $0 |

"Pass" always means the CAPTCHA's own server accepted the answer: the vendor's siteverify via our measurement page
(`data-done_<lane>`), or the lab's own check (go-captcha's `check-data`, one-shot). Raw lines: `runs/solver-runs.jsonl`
(series `curve-*`, `measure-ladder`, `measure-s4`, `lab-s4`, `smoke*`).

**Learning curve (the step-3 cache).** For each lab type the first encounter is solved by the cheapest working
step, the server accepts, the type is promoted, and encounters 2–10 replay the saved solution straight away (step 3):
slide/drag/rotate `curve_step = [1, 3, 3, 3, 3, 3, 3, 3, 3, 3]`, all 1.5–1.7 s. On text the saved ddddocr policy
passed 3 of 6 replays, was **demoted** after two misses in a row (encounters 9–10), and encounter 11 went back to the
full ladder — the demotion rule working. The speed-up from cache is small here because steps 1–2 are already fast;
its value is skipping rungs that are known to fail (and, for a model-solved type, skipping the fallback chain).

## The ladder as built

| Step | Code | What it does |
|---|---|---|
| −1 trust | `router.py`, `solve.py trust` | Reads the browser's own reCAPTCHA v3 score from our page (saved whenever the v3 lane is solved). Below 0.3 the plan skips reCAPTCHA audio (Google refuses it) and carries the advice to raise trust first. One persistent profile (`.profile/`) keeps history |
| 0 tick / wait | `kinds.py` `step0()` | reCAPTCHA tick, Turnstile tick, ALTCHA/Cap proof of work, v3 nothing-to-do |
| 1 recipes | `engines.py`, `kinds.RecaptchaV2.audio` | reCAPTCHA audio → faster-whisper small.en; tesseract; OpenCV gap match (slide, drag); rotation search |
| 2 local models | `engines.py` | ddddocr OCR, ddddocr click detection, ddddocr slide match (0/20 on go-captcha slide: kept out of the slide route's default) |
| 3 saved solutions | `cache.py`, `run.cached_step` | Per type (kind + instruction template + layout), a policy: a local engine, or a vision call naming the model that worked. **Promoted only from a server-accepted solve**; demoted after 2 misses in a row or < 50 % over the last 6. Stored with evidence in `cache/policies/` |
| 4 one focused call | `models.py`, `kinds.*.vision` | Crop + instruction (+ pixel grid or numbered tiles) → one JSON answer → our precise drag/click/type tools. Fallback chain with 429 cool-downs, daily parking, a daily counter |
| 5 general agent | `agent.py` | Multi-turn observe → one action → look again, model-agnostic (`decide(image, instruction, history)`). Runs only for kinds without a handler (Arkose, GeeTest, page-drawn puzzles) or when forced with `--steps 5` |
| write-back | `agent.writeback` | After any server-accepted solve at steps 1, 2, 4, 5: save the label (image + accepted answer: step 2's training set, `cache/labels/`, not committed), then pick the cheapest local engine that reproduces **every** saved answer (≥ 3 labels when a model solved it), else keep the model that solved it. Outside agents teach it through `solve.py writeback` (needs a server verdict) |

Reused from `captcha.py` (vendored in `ladder/primitives.py`, note at its top on why not imported): human-paced move,
drag, stroke, hold, local Whisper, the gridded look. Drags here are closed-loop: press, move, read where the piece
actually is, correct, release (go-captcha tolerates ±4 px and ±2°).

## Free model keys (checked 2026-11-03)

| Provider | State |
|---|---|
| OpenRouter | **Key copied** from another project to a local secrets file (0600; a project Google account, $0 limit). Vision models that answered: `nvidia/nemotron-3.5-super-vl:free` (first in chain), `nemotron-3-nano-omni-30b-a3b-reasoning:free`, `dots-3-note-preview:free`, `openrouter/free`. Both Gemma 4 free models returned "rate-limited upstream" on every call. `inkling:free` 403 ("agentic harnesses only"). **50 requests per UTC day** without $10 of credit: the binding limit on how much step 4 could be measured |
| Mistral | **No key.** Account created with the a project mailbox (password in the owner's password manager); the console says the Free plan does not activate API keys any more — only Pro / Pay-as-you-go. Free mode as described in our Oct research is gone |
| Groq | **Blocked**: console and API both answer "Access denied. Please check your network settings." from this machine's exit |
| Gemini | Not retried (refused a project Google account in Oct 2026) |
| GitHub Models (extra, tried) | `models.github.ai` answers a plain-text "OK" to every request from this machine: intercepted, unusable here |

## Run

    docker compose -f lab/compose.yml up -d          # go-captcha-service 1.0.5, loopback only
    uv run lab/server.py &                           # http://127.0.0.1:8411/?t=text|go-slide|go-drag|go-rotate|go-click-en|go-click-shape
    uv run solve.py --url "http://127.0.0.1:8411/?t=go-slide"
    uv run solve.py --url "https://measure.captcharena.org/?c=solver-x" [--max-step 1] [--headed]
    uv run solve.py bench --url URL --n 10 --fresh [--steps 4]   # learning curve; --steps forces steps for measurement
    ./suite.sh local | models                        # the runs behind this README

`--headed` starts its own Xvfb (:91–:98), never the automation browser display. The measurement page caps verify calls at
300 a day; a full page load spends ~5.

## Decisions taken (2026-11-03)

- Lab widgets are our own minimal UI with go-captcha-jslib's interactions; image generation and checking are the
  projects' own unmodified code (go-captcha-service container, lepture/captcha). Our lab server makes every challenge
  one-shot, like real widgets.
- Step 5 is not in the default plan for kinds with a handler: on text it spent 9–10 calls an encounter with no pass.
- Distillation from a model solve needs 3 labels: with 2, ddddocr matched by chance and was promoted, then failed.
- A local answer under the kind's confidence gate is not submitted (a wrong answer burns the challenge); the same
  challenge goes up the ladder. ddddocr's confidence is badly calibrated (0.95 on wrong reads), so text relies on
  the server verdict and demotion instead.
- Prompts end with "answer at once with the JSON only" and OpenRouter calls ask for low reasoning effort: reasoning
  models spent the whole token budget thinking and returned an empty answer.
- Turnstile's 600010 is a browser-trust result (step −1), not a puzzle: no stealth patches added (research-2 §5 keeps
  them out of anything published). The agents' real browser passes the same lane (measure README, 2026-11-03).

## Not solved yet / next

- **Step 4 sample sizes are tiny** (OpenRouter's 50 calls a day ran out): run `./suite.sh models` once
  per UTC day. Wanted: a daily timer for it — not installed, because registering an automation is a shared private file.
- reCAPTCHA picture grids by free models: 0/1. Next: per-tile yes/no calls instead of one grid call, or step 2 CLIP/YOLO.
- go-captcha click puzzles: no answer parsed from any free model; ddddocr detection 0/10. Next: detect candidate glyphs
  locally, ask the model only to match crops.
- Turnstile in a Playwright-launched browser (600010). Next: measure through the agents' real browser over CDP, or a
  CDP-only launch.
- Step 2 does not retrain yet: labels are saved, nothing trains on them (the Salman & Bicakci half). Next: fine-tune
  ddddocr on `cache/labels/` once a type has ~200.
- Open clones still to add: mCaptcha, Procaptcha, Halligan's 26 types (Arkose-style), Open CaptchaWorld.

## Should be registered on the owner's machine (not edited from here)

- `knowledge/architecture/features.toml`: the solver (this folder) as a feature of `prj-captcha`.
- `knowledge/planning/plan.toml`: build steps 3 and 5 → `review`, evidence = this README + `runs/solver-runs.jsonl`.
- `knowledge/harnesses/github-watchlist.md`: wenlng/go-captcha-service (40★, Apache-2.0, 1.0.5 2026-03-07: used as the
  lab's engine, one-shot checks, ±4 px / ±2° tolerances); lepture/captcha (python, 0.7.1: lab text generator);
  ddddocr measured (43 % on lepture/captcha text, 0/20 slide_match on go-captcha, 0/10 click); GitHub Models
  unreachable from the owner's machine.
- `the private automation registry`: the daily `suite.sh models` timer, once built.
- Mistral and Groq findings into `knowledge/studies/hackathon-environment/research-free-llm.md` (both changed since Oct).
