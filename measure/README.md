# measure/ — the CAPTCHA measurement page (build-order step 2)

Agent-facing. Real CAPTCHA widgets on our own domain with our own keys; every token goes to the vendor's own server
check (or our self-hosted CAPTCHA's), and one JSON line per attempt lands in the run log. It is test set 1 of the
solver proof, the instrument page of the browser-score experiment (`../research/deep-2-browser-score.md` §6.3), and
later the hub's "Browser score" and "Play" pages.

## How a check flows

Page loads → `GET /api/config` (which lanes are live, public site keys) → browser signals collected (navigator,
WebGL renderer, BotD with `monitoring: false`) → each widget produces a token → `POST /api/verify {lane, token,
run_id, condition, client}` → server calls the vendor (`siteverify`) or verifies locally (ALTCHA) → appends a line
to `/data/runs.jsonl` (volume `runs`) → returns the verdict, which the page shows. A runner tags a batch with
`?c=<condition>`; `document.body.dataset.done_<lane>` turns `pass`/`fail` when a lane finishes.

| Lane | State 2026-11-03 | Key |
|---|---|---|
| reCAPTCHA v3 | off until a real key exists (no v3 test key) | a project Google account, after the domain |
| reCAPTCHA v2 tick box | live with Google's test key | real key after the domain |
| Turnstile (managed) | live with Cloudflare's test key; `before-interactive-callback` sets `interactive` | real key via the Turnstile token permission |
| ALTCHA (PBKDF2/SHA-256, cost 5000) | live, real (self-hosted, our HMAC secret) | `ALTCHA_HMAC_SECRET` |
| Cap | not wired: needs `tiago2/cap` + Valkey containers and a site key from its dashboard/API; the proxy route `/cap/<site>/{challenge,redeem}` and the verify branch are already in `app/main.py` | — |

Lines made with a vendor test key carry `"key": "test"`; analysis must drop them.

## Privacy and limits

No IP address and no cookie of ours (country from Cloudflare's `CF-IPCountry` only); the page says so. Strict CSP:
scripts only from self, Google reCAPTCHA and Cloudflare Turnstile; no inline script. `MEASURE_DAILY_CAP` (300) is a
global daily cap on verify calls so public traffic cannot burn the reCAPTCHA free tier (10k/month).

## Run and deploy

- Local: `cp .env.example .env`, set `ALTCHA_HMAC_SECRET`, then `uv run --no-project --with-requirements
  requirements.txt uvicorn app.main:app --port 8399` (env from `.env`).
- Hosting server: `deploy-tool deploy captcha-measure <this folder> 8300 --health /health
  [--host <hostname>]`; secrets with `deploy-tool secret captcha-measure VAR <file>`. Only committed trees deploy.
- Tested 2026-11-03 in the automation browser on test keys: Turnstile, reCAPTCHA v2 (tick) and ALTCHA each accepted by
  their server and logged; bad payload, unknown lane, missing token and bad JSON rejected cleanly.

## Next

Domain → real reCAPTCHA v2/v3 keys (a project Google account) and Turnstile widget (the owner's token) → `--host` deploy →
7-day warm-up with controls (deep-2 §6.3 step 1) → Cap lane → open clones (go-captcha, mCaptcha, Procaptcha).
