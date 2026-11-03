+++
title = "Research: CAPTCHAs and AI agents, for researchers and students"
description = "The literature map, the industry roadmap, benchmarks with licences, open questions, and the three method gaps that make most CAPTCHA results go stale."
sort_by = "weight"
[extra]
checked = "2026-11-01"
+++

This section is for people who study human verification: researchers, students, and anyone writing a paper or a thesis on CAPTCHAs and AI agents. It collects what the field has published since 2023, what industry says comes next, the benchmarks and their licences, and the questions still open. Every entry links to its primary source and carries the date we checked it.

## What is here

| Page | What it answers |
|---|---|
| [Literature map, 2023–2026](@/research/literature-map.md) | Every attack, defence, detection method, benchmark and theory paper we found, in one set of tables, plus how long published designs have lasted. |
| [Industry roadmap](@/research/industry-roadmap.md) | What vendors and standards bodies say replaces CAPTCHAs (PACT, Privacy Pass, Web Bot Auth, delegation, personhood), and which of it exists as open code. |
| [Benchmarks and datasets](@/research/benchmarks.md) | Each CAPTCHA benchmark's licence, status and limits, and what other agent leaderboards have learned. |
| [The CAPTCHA half-life](@/research/half-life.md) | A measure nobody publishes yet: how many months a design lasts against agents, and how we plan to measure it. |
| [Open questions](@/research/open-questions.md) | The theoretical ceiling, what survives it, and the research problems nobody has solved. |

## Three method gaps in the field

The 2025–2026 literature contains at least 15 designs that claim to stop AI agents. Reading them side by side shows three weaknesses that most of them share.

1. **Each design is tested once, against the models of its month.** A defence paper reports low agent success against the frontier models available when it was written, and is never re-run. When the same group did re-test, the result was a collapse: no model solved Open CaptchaWorld's "Bingo" type in May 2025 ([arXiv 2505.24878](https://arxiv.org/abs/2505.24878)); nine months later the same group reported *"pass rates as high as 90% on complex logic puzzles like 'Bingo'"* ([arXiv 2602.09012](https://arxiv.org/abs/2602.09012)). Checked 2026-11-01. IllusionCAPTCHA, tested on GPT-4o and Gemini 1.5 Pro, has no published re-test on current models that we could find ([arXiv 2502.05461](https://arxiv.org/abs/2502.05461), searched 2026-11-01).
2. **Almost none faces an attacker who builds a tool for it.** Security practice requires testing a defence against an *adaptive attacker*: one who knows the design and builds an attack for it. Most CAPTCHA papers test only off-the-shelf chat models. MVCAP, a motion-based design, excludes offline frame analysis by its threat model ([arXiv 2609.27461](https://arxiv.org/abs/2609.27461)), although moving-object CAPTCHAs were broken by tracking in 2012 ([Xu et al., USENIX Security 2012](https://www.usenix.org/biblio/security-and-usability-challenges-moving-object-captchas-decoding-codewords-motion)). When an adaptive solver was simulated against monthly re-perturbed images for a year, it recovered every round ([Salman & Bicakci, arXiv 2609.02393](https://arxiv.org/abs/2609.02393)). Checked 2026-11-01.
3. **Human baselines are small or undocumented.** Open CaptchaWorld reports a 93.3% human pass rate with no participant count, recruitment or ethics review described. MVCAP used 30 people, with no recruitment or review described. MCA-Bench's human tables contradict each other (sliding block 98% in one, 74% in another) ([arXiv 2506.05982](https://arxiv.org/abs/2506.05982)). Compare Searles et al.: 1,400 paid participants and 14,000 CAPTCHAs ([USENIX Security 2023](https://arxiv.org/abs/2307.12108)). Human variance by age, device, disability or language is almost never reported. Checked 2026-11-01.

Two more gaps follow from these. Most benchmarks score only the final answer, although trace and process validity is where agents still fail ([HLL](https://arxiv.org/abs/2606.02449), [SolveBind](https://arxiv.org/abs/2610.32223)). And cost per solve is rarely reported, although it decides deployment: human solving farms charge about $0.10–5.00 per thousand ([Broken Gates, arXiv 2607.18659](https://arxiv.org/abs/2607.18659), checked 2026-11-01).

## Submit a design for re-testing

If you have published a CAPTCHA or bot-check design, or you are about to, we want to re-test it: against current agents, against an attacker built for it, and again each cycle, so its [half-life](@/research/half-life.md) can be published.

To propose a design now, write to us through the [contact page](@/contact/_index.md). Tell us the paper, the code or a running instance, and the threat model you claim.

{% <coming> %}
A public submission process: what we need from authors, how we reimplement or host a design, how and when results are shared with the authors before publication, and how the private held-out instances are handled.
{% </coming> %}

For background on the economics, see [what a CAPTCHA costs an attacker](@/defend/attacker-cost.md) and [the economics of CAPTCHAs](@/learn/economics.md).
