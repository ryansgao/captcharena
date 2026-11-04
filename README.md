# CAPTCHA project — solver, blue team, hub

Agent-facing status. Last updated 2026-11-04. One-page overview for the owner (kept private).

| Part | State |
|---|---|
| Research (9 reports) + plan v2 | done — plan v2 (kept private) |
| Essay | drafted, unpublished — `research/essay-draft.md` |
| Hosting server (Oracle Cloud, us-sanjose-1) | **built and checked 2026-11-03**: SSH locked to the owner's private key, automatic updates, Docker, cloudflared installed, 2-minute health timer, nightly check (verifier 39), Oracle API key authorised and every read verified. Record and handle: `the deploy tool` |
| Domain | **captcharena.org** (the owner, Cloudflare Registrar, 2026-11-03); token in the secret store |
| Measurement page (build step 2) | **live, real keys**: https://measure.captcharena.org — reCAPTCHA v3 + v2, Turnstile, ALTCHA, Cap; `/api/summary` feed; warm-up to ~2026-11-10 (`measure/`) |
| Browser-score runner (step 6) | **paused 2026-11-04** (kill switch `runner/OFF`; up to 100 loads/day from the shared exit address may hurt its reputation, unmeasured). 7 browser arms, timer `captcha-runner` (`runner/`) |
| Hub (step 9) | **live**: https://captcharena.org, 41 pages, 7 sections (`hub/`) |
| Solver (steps 3 + 5) | **built**: ladder 0-5, saved-solution cache, daily free-model timer `captcha-solver-models` (`solver/`) |
| Clone benchmarks + half-life clock (steps 7 + 4) | **built**: 4 suites, 97 types, weekly timer `captcha-halflife`, first detector data point (`bench/`) |
| Blue team path A (step 10) | **live**: https://observatory.captcharena.org (C4), https://anubis.captcharena.org (C5); PACT-lab C1 slice in tests (`defence/`) |
| Gap-discovery engine (step 8, M2) | **not started** — after the weekly usage reset (Plan `captcha-gap-engine`) |

Next, in order: gap-discovery engine → C7 process-check Anchor → C2 private scoring → solver picture grids → essay with
our data (the owner checks before publishing). Status of each part lives in its folder's README.
