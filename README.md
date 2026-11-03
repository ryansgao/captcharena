# CAPTCHA project — solver, blue team, hub

Agent-facing status. Last updated 2026-11-03.

| Part | State |
|---|---|
| Research (9 reports) + plan v2 | done — plan v2 (kept private) |
| Essay | drafted, unpublished — `research/essay-draft.md` |
| Hosting server (Oracle Cloud, us-sanjose-1) | machine up, private workspace SSH works (verified 2026-11-03: Ubuntu 24.04 aarch64, 2 CPU / 11 GB / 96 GB, sudo). **Agent's Oracle API key authenticates but is not authorised** (list_instances 404; it can read only itself) — group membership or policy not in effect; the owner to check. Hardening not started. |
| Domain | the owner buying (Cloudflare Registrar); then a Zone DNS + Tunnel token via the secret form |
| Build | nothing yet. First step: measurement page on our domain (plan "Build order" step 2) |

Next steps, in order: fix Oracle policy → harden the hosting server + Docker + tunnel + health timer (recipe
`<private>/ops/hackbox/README.md`) → domain + token → measurement page → solver step 4 as a focused
free-API call → half-life harness.
