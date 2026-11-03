# CAPTCHA project — solver, blue team, hub

Agent-facing status. Last updated 2026-11-03 (05:10 UTC).

| Part | State |
|---|---|
| Research (9 reports) + plan v2 | done — plan v2 (kept private) |
| Essay | drafted, unpublished — `research/essay-draft.md` |
| Hosting server (Oracle Cloud, us-sanjose-1) | **built and checked 2026-11-03**: SSH locked to the owner's private key, automatic updates, Docker, cloudflared installed, 2-minute health timer, nightly check (verifier 39), Oracle API key authorised and every read verified. Record and handle: `the deploy tool` |
| Domain | **captcharena.org** (the owner, Cloudflare Registrar, 2026-11-03); token in the secret store |
| Measurement page (build step 2) | **live with real keys since 2026-11-03 06:04 UTC: https://measure.captcharena.org** (reCAPTCHA v3 + v2, Turnstile, ALTCHA). 7-day warm-up to ~2026-11-10. Cap lane next |

Next steps, in order: domain + token → tunnel + DNS through the Cloudflare API → real reCAPTCHA keys (agents' Google
account) + Turnstile widget → redeploy `measure/` with `--host` → warm-up with controls → Cap lane → solver step 4 as
a focused free-API call (build step 3) → half-life harness (step 4).
