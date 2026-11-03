+++
title = "CAPTCHA scoreboard: agents, solvers and widgets, measured"
description = "A neutral scoreboard of how AI agents, solving services and browsers fare against real CAPTCHAs, scored by each vendor's own server. First results after 2026-11-10."
sort_by = "weight"
[extra]
checked = "2026-11-03"
script = "live-summary.js"
+++

The scoreboard answers one question for every audience: **what does it take, today, to get past each kind of human check, and how fast is that changing?** Site owners learn whether their CAPTCHA still holds. Agent builders learn what will stop them. Researchers get a re-test of published designs.

{{ <live_summary /> }}

## What will be on it

| Lane | What is measured | Status (2026-11-03) |
|---|---|---|
| Real widgets | Server-accepted rate per agent setup on reCAPTCHA v2 and v3, Turnstile and self-hosted open CAPTCHAs on our own domain; the v3 score distribution per setup and network type | Measurement page live; warm-up until ~2026-11-10 |
| Practice puzzles | Accuracy, time and cost per solve on open research puzzles, fresh instances each cycle | Coming |
| Behaviour | What an agent does when a CAPTCHA appears in the middle of a task: solve it, hand off to its human, refuse, call a paid solver, or misrepresent itself | Coming |
| Solving services | Acceptance rate, time and effective price of commercial services, bought as an ordinary customer at list price | Coming |
| Hosted browsers | How often hosted agent browsers are challenged and accepted | Coming |
| Half-life | For each published "AI-proof" design: the months from launch until agents pass it | Coming; [method](@/research/half-life.md) |

Why each lane exists and how it is run: [Scoreboard method](@/scoreboard/method.md). Lane-by-lane detail: [Scoreboard lanes](@/scoreboard/lanes.md).

## Why another scoreboard

The existing ones each cover one slice, and most are run by a party with something to sell (checked 2026-11-01):

| Existing source | What it covers | What it lacks |
|---|---|---|
| [CaptchaTheCat](https://captchathecat.com) | 24 solving services, daily | No named operator, no published method, paid-visibility pitch |
| [HasData benchmark](https://hasdata.com/blog/captcha-solving) | 5 solving services, 6 types, 50 challenges each | One-off article by a seller of scraping APIs; test pages not disclosed |
| [Scrapeway](https://scrapeway.com) | 7 scraping APIs against 11 protected sites | Operator not named; cadence stated inconsistently |
| [Open CaptchaWorld](https://github.com/MetaAgentX/OpenCaptchaWorld) | AI agents on logic puzzles | Frozen at publication (May 2025) |

None puts agents, solving services and real widgets side by side, and none publishes real server verdicts continuously. The closest precedent is a research paper, [Broken Gates](https://arxiv.org/abs/2607.18659), which put real widgets on its own domains and checked every token with the vendor's server, once.

{% <note> %}

**What the scoreboard will never be:** a solving service. We do not sell, broker or hand out CAPTCHA tokens or solving code. We publish outcomes, methods and data.

{% </note> %}

