+++
title = "Scoreboard lanes: what each one measures"
description = "Each scoreboard lane in detail: the question it answers, how it is scored, and its status. Real widgets are live; the rest are coming."
weight = 20
[extra]
checked = "2026-11-03"
+++

A lane is one kind of test, run the same way every cycle. Each lane answers a question a specific reader has.

## Real widgets

**Question:** does a given agent setup get accepted by the real vendor's server, and what invisible score does it get?

- **Widgets (2026-11-03):** reCAPTCHA v3 and v2 tick box, Cloudflare Turnstile (managed mode), ALTCHA and Cap (both self-hosted proof of work). All on [measure.captcharena.org](https://measure.captcharena.org) with our own keys.
- **Planned additions:** reCAPTCHA Enterprise, mCaptcha, Anubis, Procaptcha, go-captcha. hCaptcha only with its written permission, because its terms forbid AI passing its challenges.
- **Scored by:** the vendor's server verdict; for v3, the score.
- **Reported:** acceptance rate, v3 score distribution, time per pass, by agent setup and network type.
- **Not possible:** Arkose Labs, DataDome and HUMAN sell only to businesses and cannot be put on a demo page without a sales contract, so real-widget results for them are out of reach. Open research clones stand in for some of their puzzle types.

## Practice puzzles

**Question:** how well do agents see and reason through puzzle types, at what cost?

- **Sources:** open research benchmarks (Open CaptchaWorld, Next-Gen CAPTCHAs, HLL, Halligan's clearly licensed types). Licences: [Practice puzzles](@/play/practice-puzzles.md).
- **Scored by:** the puzzle's own answer check, on fresh instances each cycle, with a private held-out set.
- **Reported:** accuracy, median and slow-case time, cost per solve, next to the human result on the same instances.

{% <coming> %}

Practice-puzzle runs start after the real-widget warm-up.

{% </coming> %}

## Behaviour

**Question:** when a CAPTCHA appears in the middle of an ordinary task, what does the agent choose to do?

The choices are: solve it, hand off to its human, refuse, call a paid solver, or misrepresent itself. This matters for safety, not only capability. In 2023 a model under test asked a human worker to solve a CAPTCHA and reasoned "I should not reveal that I am a robot" ([GPT-4 system card](https://cdn.openai.com/papers/gpt-4-system-card.pdf), checked 2026-11-01). No public benchmark measures this choice today. More on good hand-off design: [Hand-off patterns](@/build/hand-off.md).

{% <coming> %}

The behaviour lane needs scripted tasks with a CAPTCHA placed mid-task; it follows the practice-puzzle lane.

{% </coming> %}

## Solving services

**Question:** what do commercial solving services actually deliver, against their list price?

Method: the mystery-shopper approach on the [method page](@/scoreboard/method.md#paid-solving-services-the-mystery-shopper-method). Reported: acceptance rate by vendor's server, time, effective price per accepted solve.

{% <coming> %}

Monthly from the first full cycle.

{% </coming> %}

## Hosted browsers

**Question:** how often are hosted agent browsers challenged, and accepted, on real widgets?

{% <coming> %}

Planned after the real-widget lane has a stable baseline.

{% </coming> %}

## Half-life

**Question:** how many months does a published "AI-proof" design survive?

Every design in the [literature map](@/research/literature-map.md) is re-run each quarter against current agents and an attacker built for it. Definition and method: [The CAPTCHA half-life](@/research/half-life.md).

{% <coming> %}

The first re-tests follow the practice-puzzle lane.

{% </coming> %}

