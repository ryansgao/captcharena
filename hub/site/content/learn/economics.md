+++
title = "The economics: what a CAPTCHA solve costs"
description = "Prices and speeds of human solving farms and token services, model-based solve costs from papers, users' lost time, and why cost is the real test."
weight = 60
[extra]
checked = "2026-11-01"
+++

## The rule that has held since 2010

A CAPTCHA does not have to keep every bot out. It has to make abuse cost more than it earns. Motoyama et al. made this argument after studying CAPTCHA-solving businesses in 2010: CAPTCHAs are best "evaluated in purely economic terms", the market price of a solve against the value of what it unlocks ([USENIX Security 2010](https://www.usenix.org/legacy/event/sec10/tech/full_papers/Motoyama.pdf), checked 2026-11-02). Arkose Labs now describes its own goal in the same terms: making abuse economically unattractive, not impossible ([Xataka](https://www.xataka.com/robotica-e-ia/agentes-ia-parecen-haber-amenazado-muerte-a-captcha-solo-les-han-puesto-cosas-dificiles), checked 2026-11-01).

So the useful questions are: what does one solve cost an attacker, and what does one check cost your real users?

## Human solving farms

The cheapest way to pass most puzzles is still to pay people to solve them. Solving services take a site key and page address, hand the puzzle to a worker or a model, and return a valid token.

- Anti-Captcha states that "100% of captchas are solved by human workers from around the world" ([anti-captcha.com](https://anti-captcha.com/), checked 2026-11-01).
- The Halligan researchers signed up as workers and describe 2Captcha as "a human-driven CAPTCHA farm" ([Halligan paper, PDF](https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf), checked 2026-11-01).
- Other services (CapSolver, CapMonster Cloud) describe themselves only as "AI-based" or "automated" and do not say how ([CapSolver](https://www.capsolver.com/); [CapMonster](https://capmonster.cloud/en/prices), checked 2026-11-01). Broken Gates calls the category "hybrid human/automation pipelines".

This work runs on low-paid human labour. At the buyer's price of roughly $0.50–3.00 per thousand solves (table below), the worker's share of one solve is a fraction of a cent (our arithmetic from the published prices). Motoyama et al. studied these labour markets directly in 2010; at that time a million solves could cost as little as about $1,000 ([Wikipedia summary of Motoyama et al.](https://en.wikipedia.org/wiki/CAPTCHA), checked 2026-11-03).

## Token services: measured price and speed

Broken Gates measured seven services on real widgets it hosted itself, checking every token with the vendor ([arXiv 2607.18659](https://arxiv.org/abs/2607.18659), Table 2, checked 2026-11-01). List prices are from the services' own pages on the same date.

| Target | Measured time per token | Price per 1,000 | Pass rate (server-checked) |
|---|---|---|---|
| reCAPTCHA v2 checkbox | 8.4 s (fastest) to 132.2 s (slowest) | $0.60–2.99 | 100% for all seven |
| Cloudflare Turnstile | 4.0 s to 88.8 s | $1.20–2.00 | 100% |
| hCaptcha Easy | 42.3–67.0 s | about $1.45–2.99 | 100% (2 of 7 services accept it) |
| hCaptcha Hard | 82.7–102.5 s | about $1.45–2.99 | 58% and 100% |
| reCAPTCHA v3 (score above 0.5) | 1.6–40.4 s | $0.90–3.00 | 0–63% |

Across targets the paper puts farm prices at $0.10–5.00 per thousand. The Halligan authors list similar prices from Q1 2025: 0.05 to 5.00 cents per CAPTCHA, depending on service and type ([Halligan](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh), checked 2026-11-01). One service prices reCAPTCHA v3 by score: $1.45 per thousand for a score of 0.3 or less, $2.99 above ([2Captcha pricing](https://2captcha.com/pricing), checked 2026-11-01). That price split shows a good score is the scarce thing.

## Model-based solving: costs from papers

| Approach | Time | Cost per solve | Success | Source (checked 2026-11-01) |
|---|---|---|---|---|
| Free local models, zero-shot (CLIP, OWLv2) | 0.5–2.6 s per challenge on a CPU or GPU; mean 81 s per successful session | $0 beyond hardware | 92.6% of 500 reCAPTCHA sessions | [Robot Visions](https://arxiv.org/abs/2609.18518) |
| A commercial frontier model through a prompt-only skill (same paper) | mean 38.4 s per challenge | $0.150 per challenge | 95.5% on one challenge type | [Robot Visions](https://arxiv.org/abs/2609.18518) |
| Halligan, focused model calls (2025 prices) | median 21.8 s | $0.024; $0.006 when its generated code is reused | 70.6% live | [Halligan](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh) |
| COGNITION, "broken" types | tens of seconds | under 10 cents per success; hard types 10–100× more | varies by type | [COGNITION](https://arxiv.org/abs/2512.02318) |
| Next-Gen CAPTCHAs, frontier models at maximum reasoning | "16 to 77 minutes to attempt a single complex puzzle" | from about $0.013 (a small fast model) to about $23 (the most expensive setting) per puzzle, derived from the paper's totals | 0.9–5.9% | [Next-Gen CAPTCHAs](https://arxiv.org/abs/2602.09012) |
| Open CaptchaWorld, one reasoning model | — | $66.4 for one full evaluation | 40% | [Open CaptchaWorld](https://arxiv.org/abs/2505.24878) |

Two lessons follow. For common puzzles, a focused call to a hosted model costs a few cents, more than a farm's fraction of a cent, while free local models cost nothing beyond hardware. For the hardest research puzzles, models are slow and expensive, but there a farm of people is the cheaper attack anyway. Either way, a visible puzzle sets a price of a few cents at most, and often a fraction of one.

## Proof of work

Proof of work sets the price in CPU time instead of money. At Anubis's default settings, one analysis estimated that a crawler could cover every Anubis-protected site for a week in about six minutes of a free cloud VM, and priced it at "approximately $0" ([Ormandy](https://lock.cmpxchg8b.com/anubis.html), checked 2026-11-01). Proof of work is still useful as rate shaping; see [Open-source CAPTCHAs](@/learn/open-source.md).

## What CAPTCHAs cost real people

The other side of the ledger is your users' time and frustration.

| Measure | Value | Source |
|---|---|---|
| Human time on distorted-text CAPTCHAs | 9–15 s, with 50–84% accuracy | [Searles et al., USENIX Security 2023](https://arxiv.org/abs/2307.12108) (1,400 participants), checked 2026-11-01 |
| Human time range across CAPTCHA types | 3.1–42 s (as cited by Halligan from Searles et al.) | [Halligan](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh), checked 2026-11-01 |
| Average CAPTCHA, Cloudflare's estimate (2021) | about 32 s | [Cloudflare blog](https://blog.cloudflare.com/introducing-cryptographic-attestation-of-personhood/), checked 2026-11-03 |
| Median human time on modern puzzle types | 8.5 s (CaptchaArena); 31.1 s (Next-Gen CAPTCHAs) | [CaptchaArena](https://arxiv.org/abs/2609.31957); [Next-Gen](https://arxiv.org/abs/2602.09012), checked 2026-11-01 |
| A 13-month field study of reCAPTCHA v2 with over 3,600 users | "an immense cost and no security" | [Searles, Prapty, Tsudik, 2023](https://arxiv.org/abs/2311.10911), checked 2026-11-03 |

A quick way to price it for your own site: multiply the number of challenges shown per month by the seconds each takes. One million challenges at 30 seconds is about 8,300 hours of your visitors' time (our arithmetic). Some of those visitors give up. People with disabilities pay the most; see [CAPTCHAs and accessibility](@/defend/accessibility.md).

## Putting the two sides together

| | Cost per check |
|---|---|
| Attacker, paid farm | $0.0006–0.003 per reCAPTCHA v2 or Turnstile token ([Broken Gates](https://arxiv.org/abs/2607.18659)) |
| Attacker, local model | about $0 per solve |
| Attacker, proof of work | about $0 at common settings |
| Your real user | 8–32 s of attention, and some abandonment |

A visible puzzle therefore costs real users far more than it costs a motivated attacker. The defences that change this balance price the **action** rather than the visitor: rate limits per account and per action, scaled to what abuse would earn, plus scarce credentials and accountable agents. See [What still works](@/learn/what-lasts.md) and the [attacker-cost calculator](@/defend/attacker-cost.md).
