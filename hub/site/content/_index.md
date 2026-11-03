+++
title = "CAPTCHAs in the age of AI agents: a neutral, living guide"
description = "How CAPTCHAs work, how AI agents fare against them, which one fits your site, and measured data from real widgets. No vendor money, no third-party scripts."
[extra]
checked = "2026-11-01"
script = "live-summary.js"
+++

CAPTCHArena explains human checks on the web from both sides: for the people who run sites and for the people who build AI agents. Every fact carries the date it was checked and a link to its source. We sell nothing, take no vendor money and run no third-party scripts.

{{ <doors /> }}

## The state of CAPTCHAs, November 2026

| Finding | Evidence (checked 2026-11-01) |
|---|---|
| Most checks now happen before any puzzle. The site scores the session and shows a puzzle only when unsure. | Turnstile asks for a click only ["if a further check is necessary"](https://developers.cloudflare.com/turnstile/concepts/widget/); hCaptcha Pro defaults to ["99.9% Passive"](https://docs.hcaptcha.com/pro). |
| Visible picture puzzles no longer stop capable models. | Free local models passed 92.6% of 500 real reCAPTCHA image sessions; the authors say such CAPTCHAs ["may have reached the end of their useful life"](https://arxiv.org/abs/2609.18518). |
| New "AI-proof" puzzle designs tend to fall within months. | Agents passed 40% of Open CaptchaWorld in May 2025 ([paper](https://arxiv.org/abs/2505.24878)); nine months later the same group reported up to 90% on its hardest type ([Next-Gen CAPTCHAs](https://arxiv.org/abs/2602.09012)). |
| Human solving farms remain the cheap baseline. | Token services return reCAPTCHA v2 and Turnstile passes in 4–13 s for $0.0006–0.003 each ([Broken Gates](https://arxiv.org/abs/2607.18659)). |
| What lasts is cost, scarce human-bound resources and accountability. | Signed agents ([Web Bot Auth](https://datatracker.ietf.org/wg/webbotauth/about/)), rate-limited anonymous credentials ([Privacy Pass ARC draft](https://datatracker.ietf.org/doc/html/draft-ietf-privacypass-arc-crypto-01)), and pricing abuse above what it earns ([Motoyama et al.](https://www.usenix.org/legacy/event/sec10/tech/full_papers/Motoyama.pdf)). |

Details and more sources: [How AI agents fare against CAPTCHAs](@/learn/ai-agents.md) and [What still works](@/learn/what-lasts.md).

{{ <live_summary /> }}

## What is on this site

| Section | What it gives you |
|---|---|
| [Learn](@/learn/_index.md) | How CAPTCHAs work, every major vendor and open option, the history, the economics, how agents fare, a fake-CAPTCHA safety guide, a glossary. |
| [Play](@/play/_index.md) | Real CAPTCHA widgets on our own domain with the vendor's live verdict; practice puzzles are coming. |
| [Scoreboard](@/scoreboard/_index.md) | How we measure agents, solvers and widgets, and the live results once the warm-up ends. |
| [Browser score](@/browser-score/_index.md) | The invisible score sites give your browser, what each vendor weighs, and a live check of your own browser. |
| [Defend](@/defend/_index.md) | A neutral chooser for site owners, defence recipes per threat, fact sheets, accessibility, attacker cost. |
| [Build](@/build/_index.md) | For agent developers: signing, hand-off to the human, the policy and legal map, test pages that still work. |
| [Research](@/research/_index.md) | The literature map, industry roadmap, benchmarks and datasets, the half-life measure, open questions. |

## How this site stays honest

- **Neutral.** No vendor money, no affiliate links, no ads. Recommendations come with their trade-offs. [Our policy](@/about/_index.md).
- **Dated.** Vendors change their products and terms every few months, so every fact shows when we checked it.
- **Measured.** Our own numbers come from real widgets on our own domain, checked by each vendor's own server, never from puzzle answers we grade ourselves. [Method](@/scoreboard/method.md).
- **Safe.** We never sell CAPTCHA solving, and our practice puzzles never imitate a vendor's look. A real CAPTCHA never asks you to press keys, paste a command or download anything: [spot a fake one](@/learn/is-this-captcha-real.md).
