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
`?c=<condition>`; `document.body.dataset.done_<lane>` turns `pass` / `fail` (server verdict), `capped` (daily cap) or
`error` when a lane finishes, `result_<lane>` holds the server's JSON verdict, `challenged_recaptcha_v2` /
`challenged_turnstile` turn `1` when a challenge is shown, and `run` holds the page's run id.

| Lane | State 2026-11-03 | Key |
|---|---|---|
| reCAPTCHA v3 | live, real key since 2026-11-03 06:04 UTC; warm-up to ~2026-11-10 | a project Google account (a project Google Cloud project, no billing) |
| reCAPTCHA v2 tick box | live, real key | a project Google account |
| Turnstile (managed) | live, real key; `before-interactive-callback` sets `interactive` | the owner's Cloudflare, widget made through the API |
| ALTCHA (PBKDF2/SHA-256, cost 5000) | live, real (self-hosted, our HMAC secret) | `ALTCHA_HMAC_SECRET` |
| Cap (HashWX proof of work, instrumentation off) | live, real (self-hosted: `tiago2/cap:3.1.17` + `valkey/valkey:9.0.7-alpine3.24` on the compose network, no published port; key made through its API on the box 2026-11-03). Widget 0.1.58 and its WASM vendored; browser calls go through `/cap/<site>/{challenge,redeem}`. Instrumentation stays off: it runs an inline script in a srcdoc iframe, which our CSP blocks | `ADMIN_KEY`, `CAP_URL`, `CAP_SITE`, `CAP_SECRET` |

Lines made with a vendor test key carry `"key": "test"`; analysis must drop them.

## Privacy and limits

No IP address and no cookie of ours (country from Cloudflare's `CF-IPCountry` only); the page says so. Strict CSP:
scripts only from self, Google reCAPTCHA and Cloudflare Turnstile; no inline script.

**Daily caps (UTC day), per lane, in two pools** (`CAPS` in `app/main.py`, override `MEASURE_CAPS` as JSON
`{"lane": [runner, public]}`; over a cap verify answers 429 and logs nothing; counts are rebuilt from the log at start,
so a redeploy does not reset them):

| Lane | Runner pool | Public pool | Why |
|---|---|---|---|
| reCAPTCHA v3 | 130 | 30 | v2 + v3 share one Google Cloud project's 10k free assessments a month: 320/day = 9.6k/month |
| reCAPTCHA v2 | 130 | 30 | same |
| Turnstile | 1500 | 500 | free and unmetered; the cap only bounds the log |
| ALTCHA, Cap | 1500 | 1000 | self-hosted; bounds our CPU and the log |

The runner pool is for requests carrying `X-Measure-Runner: <MEASURE_RUNNER_KEY>` (secret in `.env`; the runner adds it
to its own `/api/verify` calls only, never to vendor requests). Each line records `"source": "runner" | "public"`, so a
public visitor reusing a runner condition tag cannot be mistaken for the runner.

## Summary feed — `GET /api/summary` (schema 1; the hub reads this)

Aggregate of the run log, nothing per visitor (no user agent, no signals, no run ids, no token hashes). Rebuilt at most
every 30 s when the log changed; `Cache-Control: public, max-age=300, stale-while-revalidate=600`, `ETag` (answers 304
to `If-None-Match`), `Access-Control-Allow-Origin: https://captcharena.org` (the hub fetches it from the browser; GET only, no credentials).

Dropped before aggregating: lines with `"key": "test"` (counted in `excluded.test_key`), conditions with a `smoke` or
`test` word in them (`cap-smoke`, `local-test`, `x1-….smoke`; `excluded.smoke`), unparseable lines (`excluded.unparsed`).

```
{
  "schema": 1, "generated": "<UTC ISO time>", "version": "<commit>",
  "days": ["<first UTC day>", "<last UTC day>"] | null,
  "excluded": {"test_key": n, "smoke": n, "unparsed": n},
  "score_bins": ["0.0","0.1","0.3","0.5","0.7","0.9","1.0"],      // v3 scores are snapped to the nearest bin
  "factor_levels": {"n": {"0": "…", …}, "b": {…}, "a": {…}, "s": {…}, "h": {…}, "c": {…}, "d": {…}, "w": {…}},
  "conditions": {"x1-n0b0a2s2h0c0d0w1": {"design": 1, "factors": {"n": "0", "b": "0", …}}},   // runner tags only
  "rows": [{
    "day": "2026-11-03", "lane": "recaptcha_v3|recaptcha_v2|turnstile|altcha|cap",
    "condition": "<tag>" | "untagged" | "other",       // "other" folds conditions past the 60 busiest per day+lane
    "source": "runner" | "public",
    "n": 12, "passed": 11, "pass_rate": 0.9167,       // passed = the vendor's (or our server's) success
    "score_hist": {"0.7": 3, "0.9": 9} | null,        // reCAPTCHA v3 only
    "score_mean": 0.85 | null,
    "solve_ms_median": 412 | null,                    // widget start to token, client-measured (> 10 min ignored)
    "interactive_known": 12, "interactive_rate": 0.0 | null,   // Turnstile: went interactive; v2: picture/audio shown
    "errors": {"timeout-or-duplicate": 1, "other": 0}           // vendor error codes; anything else counts as "other"
  }]
}
```

What the feed cannot show: page loads that never produced a token (a v2 challenge left unsolved, a Turnstile that
stayed interactive, a timeout) reach no server. The runner keeps those in its own log (`../runner/state/runs.jsonl`),
and `../runner/analyze.py --local` reads both. Condition tags: `../runner/README.md`.

## Run and deploy

- Local: `cp .env.example .env`, set `ALTCHA_HMAC_SECRET`, then `uv run --no-project --with-requirements
  requirements.txt uvicorn app.main:app --port 8399` (env from `.env`).
- Hosting server: `deploy-tool deploy captcha-measure <this folder> 8300 --health /health
  [--host <hostname>]`; secrets with `deploy-tool secret captcha-measure VAR <file>`. Only committed trees deploy.
- Tested 2026-11-03 in the automation browser on test keys: Turnstile, reCAPTCHA v2 (tick) and ALTCHA each accepted by
  their server and logged; bad payload, unknown lane, missing token and bad JSON rejected cleanly.

## Next

Domain → real reCAPTCHA v2/v3 keys (a project Google account) and Turnstile widget (the owner's token) → `--host` deploy →
7-day warm-up with controls (deep-2 §6.3 step 1; ~~waiting~~ running since 2026-11-03 through `../runner/`) → ~~Cap lane~~ (live 2026-11-03) → open clones (go-captcha, mCaptcha, Procaptcha).

- 2026-11-03, Cap wired (commits e140e48, ece26dd): on https://measure.captcharena.org/?c=cap-smoke in the automation browser all five lanes said "accepted by its server" (v3 score 0.9, v2 after an audio round, Turnstile, ALTCHA, Cap 1.2 s). Page files now carry `?v=<commit>`: Cloudflare forces a 4 h browser cache on /static/, which served the old script after the deploy.
- 2026-11-03, summary feed and budgets (083a4e7 → 4cf1bda): `/api/summary` (schema above), per lane caps in a runner
  and a public pool (the old global `MEASURE_DAILY_CAP` of 300 is gone), done flags `capped` / `error` /
  `widget-error`, `challenged_*` flags, v2 `interactive` = challenge shown, and one server check per lane per load (a
  smoke-test tab left open in the automation browser had the watcher re-tick v2 and Turnstile re-issue tokens every few
  minutes, spending the public budget; that tab was closed).
