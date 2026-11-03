# CAPTCHA project — solver, blue team, hub

Agent-facing status. Last updated 2026-11-03 (05:10 UTC).

| Part | State |
|---|---|
| Research (9 reports) + plan v2 | done — plan v2 (kept private) |
| Essay | drafted, unpublished — `research/essay-draft.md` |
| Hosting server (Oracle Cloud, us-sanjose-1) | **built and checked 2026-11-03**: SSH locked to the owner's private key, automatic updates, Docker, cloudflared installed, 2-minute health timer, nightly check (verifier 39), Oracle API key authorised and every read verified. Record and handle: `the deploy tool` |
| Domain | the owner buying (Cloudflare Registrar). Candidates unregistered at 05:00 UTC: captcha.watch, captchaindex.com, captchalab.org, thecaptcha.org, captchawatch.org/.dev, captcha-lab.dev, captcha-observatory.org. Then a token (Zone DNS Edit + Account Tunnel Edit + Account Turnstile Edit, that zone only) via `<private>/ops/agent-browser/secret-drop.py cloudflare-the hosting server-token` |
| Measurement page (build step 2) | **built, running on the hosting server on vendor test keys** (local only) — `measure/` (README there). Waits on the domain for real keys, the public address and the 7-day warm-up. Plan `captcha-measure-page` |

Next steps, in order: domain + token → tunnel + DNS through the Cloudflare API → real reCAPTCHA keys (agents' Google
account) + Turnstile widget → redeploy `measure/` with `--host` → warm-up with controls → Cap lane → solver step 4 as
a focused free-API call (build step 3) → half-life harness (step 4).
