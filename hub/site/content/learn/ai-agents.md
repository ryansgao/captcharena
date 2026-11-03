+++
title = "How AI agents fare against CAPTCHAs (2024–2026)"
description = "What the published research measured: puzzle designs that fall within months, real-widget results, how agents get detected, and the theoretical ceiling."
weight = 50
[extra]
checked = "2026-11-01"
+++

This page summarises published papers only. Every number links to its paper and was checked on 2026-11-01. Many of these papers are preprints; we say so where the venue is known.

## The short version

- **Visible puzzles no longer stop capable models.** Free local models passed 92.6% of 500 real reCAPTCHA sessions ([Robot Visions, ISC 2026](https://arxiv.org/abs/2609.18518)). A general solver with no per-type training passed 70.6% of live challenges it had never seen ([Halligan, USENIX Security 2025](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh)).
- **New "AI-proof" designs fall within months.** A design that agents pass 0–20% of the time in its defence paper typically reaches 70–95% in a later attack paper or with newer models, roughly 3 to 12 months later. This range is our summary of the papers below, not a measured statistic.
- **What decides real widgets is the environment, not the puzzle.** On real reCAPTCHA v3, only the one agent running in a real browser profile with history passed, "despite nearly indistinguishable behavioral traces" ([Broken Gates, 2026](https://arxiv.org/abs/2607.18659)).
- **Agents are easy to detect by how they behave**, for now. Behaviour features separated agents from people at F1 0.999 in one study ([FP-Agent](https://arxiv.org/abs/2605.01247)).
- **There is a ceiling.** If an agent's behaviour becomes statistically identical to a person's, no test can tell them apart ([Sadasivan et al.](https://arxiv.org/abs/2303.11156)).

## The treadmill: designs that fell

We use **half-life** to mean the time from a design's publication to the first report of agents passing it most of the time. Nobody tracks this number today; see [half-life](@/learn/glossary.md#half-life).

| Design family | Defence result | Later result | Gap |
|---|---|---|---|
| Logic and interaction puzzles | Open CaptchaWorld (May 2025): best agent 40% against humans' 93.3%; no model solved the "Bingo" type ([paper](https://arxiv.org/abs/2505.24878)) | Same group, Feb 2026: frontier models reach "pass rates as high as 90% on complex logic puzzles like 'Bingo'" ([Next-Gen CAPTCHAs](https://arxiv.org/abs/2602.09012)) | ~9 months |
| Reasoning CAPTCHAs | Oedipus (2024): even with careful decomposition, 63.5% average ([paper](https://arxiv.org/abs/2405.07496)) | ViPer (USENIX Security 2026): up to 93.2% on visual-reasoning CAPTCHAs from six vendors, over 90% across several model families ([paper](https://arxiv.org/abs/2601.06461)) | ~20 months; different CAPTCHA sets |
| Adversarial noise on images | Masks cut model accuracy by over 50 points ([Jabary et al., 2024](https://arxiv.org/abs/2409.05558)) | A solver that retrains on its own model's answers recovered in every round of a simulated year in which the noise changed monthly ([Salman & Bicakci, 2026](https://arxiv.org/abs/2609.02393)) | Each round |
| Image grids (reCAPTCHA v2) | — | YOLO solves 100% ([Plesner et al., COMPSAC 2024](https://arxiv.org/abs/2409.08831)); free zero-shot local models 92.6% of real sessions ([Robot Visions](https://arxiv.org/abs/2609.18518)) | — |

Only the first row is the same group re-testing the same puzzle type, so it is the cleanest evidence. Next-Gen CAPTCHAs then proposed 27 new puzzle families on which the best models scored 0.9–5.9%, against humans' 98.8% ([paper](https://arxiv.org/abs/2602.09012)). On this pattern, that is the next lap.

### The exception, so far

COGNITION (USENIX Security 2026) tested 7 multimodal models on 18 real-world CAPTCHA types. Recognition tasks were solved "at human-like cost and latency". Fine-grained localisation, multi-step spatial reasoning and consistency across frames stayed hard. Hardening one type with exact localisation and hidden counting cut the best model "from over 95% to 0%" ([paper](https://arxiv.org/abs/2512.02318)). In October 2026, an agent paper still listed "exact counting, continuous geometry, and ordered execution" among its remaining failures ([CaptchaAgent](https://arxiv.org/abs/2610.12866)). We found no test of the hardened design against an attacker who built a tool for it.

### Other recent designs

| Design | Claim | Open question | Source |
|---|---|---|---|
| IllusionCAPTCHA (2025) | GPT-4o and Gemini 1.5 Pro fooled 100%; humans 86.95% on first try | No published re-test on newer models found | [arXiv 2502.05461](https://arxiv.org/abs/2502.05461) |
| MVCAP, motion-defined shapes (ACM Multimedia 2026) | Humans 99.6%, best agent 16.8% | Human baseline of 30 people; threat model excludes frame-by-frame analysis; no photosensitivity discussion | [arXiv 2609.27461](https://arxiv.org/abs/2609.27461) |
| Spatial CAPTCHA (ICLR 2026 submission) | Best of 10 models 31.0% | Submission outcome not checked | [arXiv 2510.03863](https://arxiv.org/abs/2510.03863) |
| Reasoning Gates (2025) | Not a block: puzzles that cost the agent 9.2× the tokens it costs to make them | Cost to humans not settled | [arXiv 2509.01619](https://arxiv.org/abs/2509.01619) |

Most of these designs are puzzles that WCAG 2.2 does not allow at a login step without an alternative, and the alternative then becomes the bot's way in. See [CAPTCHAs and accessibility](@/defend/accessibility.md).

## General solvers and benchmarks

| Study | What it measured | Result |
|---|---|---|
| [Halligan](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh) (USENIX Security 2025) | One vision-language-model solver, no per-type training, 26 types | 60.7% of 2,600 benchmark challenges; 70.6% of live challenges over 30 days, 17 of 25 variants absent from its benchmark. Live pass rates by vendor included Arkose 33.0% (n = 218), GeeTest 25.4% (n = 390), AWS WAF 94.4% (n = 549) |
| [MCA-Bench](https://arxiv.org/abs/2506.05982) (2025) | Fine-tuned 7B model, 20 types | ≥95% on 8 types; 28–70% on sliders, rotation and jigsaw; under 3% on arithmetic-selection |
| [CAPTCHA-X](https://arxiv.org/abs/2510.06067) (2025) | Reasoning on five hard types | ~21.9% without reasoning; 83.9% with a step-by-step agent |
| [CaptchaArena](https://arxiv.org/abs/2609.31957) (2026) | 50,000 puzzles, 20 types | A trained 9B model 71.7 Pass@1; humans 94.1, median 8.5 s |
| [HLL](https://arxiv.org/abs/2606.02449) (2026) | 8 frontier agents with page clutter and checked action traces | Agents drop further when their actions must also look valid |
| [SolveBind](https://arxiv.org/abs/2610.32223) (2026) | Answer versus behaviour | Agents with the right answer still fail on trajectory and timing; a supervisor lifts success to 82% |

An industry test by a bot-detection company had three models attempt Google's reCAPTCHA v2 demo: 60%, 56% and 28% per trial, and near 0% on cross-tile puzzles ([Proof of Human, 2025](https://research.poh.org/captcha-benchmarking/)). The company sells bot detection.

## Real widgets: Broken Gates

Broken Gates (FIU, preprint, July 2026) is the only study we found that put real widgets on its own domains and checked every token with the vendor's siteverify ([arXiv 2607.18659](https://arxiv.org/abs/2607.18659)). It tested 7 paid solving services (100 instances per target) and 10 agent setups against hCaptcha (Easy, Hard), reCAPTCHA v2 (checkbox, invisible), reCAPTCHA v3 (threshold 0.5) and Turnstile (Managed, Invisible).

| Target | Paid solving services | Agents |
|---|---|---|
| reCAPTCHA v2 and Turnstile | ~100% | Mostly fail without a solver module; Turnstile Invisible passed by 5 of 10 setups, Managed by 3 |
| hCaptcha Easy | 100% (only 2 of 7 services accept hCaptcha) | — |
| hCaptcha Hard | 58% for one service, 100% for the other | — |
| reCAPTCHA v3 | 0–63% above 0.5, average about 23% | Only 1 of 10 setups passed: the one inside a real profile with "cookies, browsing history" |

The authors conclude that challenge-based defences are "broadly ineffective" against commercial solvers at negligible cost, and that reCAPTCHA v3's resistance "does not reflect a fundamental security property". Speeds and prices are on [the economics page](@/learn/economics.md).

## Behaviour: how agents get caught

Several 2026 studies show agents are easy to spot by how they act, even when they pass the CAPTCHA.

| Study | Finding |
|---|---|
| [FP-Agent](https://arxiv.org/abs/2605.01247) | 7 commercial browsing agents on a honeysite with 56 student participants. Browser fingerprint alone F1 0.82; behaviour alone F1 0.999; combined 1.0. Agents paste text instead of typing, and "the pointer jumps to click targets" |
| [Choudhary et al.](https://arxiv.org/abs/2607.26935) | Two features (mouse-event rate and the share of clicks with no pointer travel) give 100% agent recall at precision 0.994, across five evasion levels. The authors say this detects the tooling, not the reasoning |
| [Fayolle et al.](https://arxiv.org/abs/2606.30119) | Some agents got past robots.txt, CAPTCHAs and proof of work, but all were distinguishable by network, HTTP and browser fingerprints (combined accuracy 0.993). "Stealth and anti-detection mechanisms often increase detectability" |
| [Kang et al.](https://arxiv.org/abs/2606.20910) | Six agent frameworks identified at 97% accuracy from TLS, HTTP and interaction features |
| [Process Turing Test](https://arxiv.org/abs/2605.06524) | Process features (click order, direction changes) separate models from people at AUC 0.88 even at matched accuracy. When the attacker trained against the full feature set, the gap closed; it returned when features were withheld or the task changed |

Vendors are turning this into products, such as Cloudflare's session-long behaviour scoring ([Precursor](https://blog.cloudflare.com/introducing-precursor/)). Expect the gap to narrow as agents move to operating-system-level input, which the Choudhary et al. authors flag as untested.

## What agents choose to do

Capability is one question; behaviour is another. In 2023, a model under test asked a human worker to solve a CAPTCHA for it and reasoned, "I should not reveal that I am a robot" ([GPT-4 system card](https://cdn.openai.com/papers/gpt-4-system-card.pdf)). In 2025, researchers talked a commercial agent past its no-CAPTCHA policy with a primed conversation ([SPLX](https://splx.ai/blog/chatgpt-agent-solves-captcha)). In Broken Gates, one agent refused to fill login forms under its safety policy. No public benchmark measures what an agent chooses when it meets a CAPTCHA: solve, hand off to its person, refuse, or call a paid solver.

{% <coming> %}
A behaviour lane on our [Scoreboard](@/scoreboard/_index.md) that scores what agents choose to do when a CAPTCHA appears mid-task.
{% </coming> %}

## The theoretical ceiling

Two results bound the whole field.

- **No test separates identical distributions.** Sadasivan et al. show that the best possible detector's performance is limited by the statistical distance between the two populations, and falls to chance as that distance goes to zero ([arXiv 2303.11156](https://arxiv.org/abs/2303.11156)).
- **More evidence helps while any difference remains.** Chakraborty et al. show that detection improves with the number of samples while the distributions still differ ([arXiv 2304.04736](https://arxiv.org/abs/2304.04736)).

The practical reading: a cleverer single puzzle buys little. What buys more is more independent evidence per visitor, or a different question altogether. See [What still works](@/learn/what-lasts.md).

## Weaknesses in the literature

1. **No re-testing.** Each defence is tested once, against the models of its month.
2. **No adaptive attacker.** Few defence papers test an attacker who builds a tool for that specific design.
3. **Weak human baselines.** Open CaptchaWorld reports no participant count for its 93.3%; MVCAP used 30 people. Compare Searles et al.'s 1,400 participants ([USENIX Security 2023](https://arxiv.org/abs/2307.12108)).
4. **Accessibility is mostly ignored.**
5. **Outcome-only scoring.** Most benchmarks grade the answer, while HLL, SolveBind and the Process Turing Test show the process is where agents still fail.

The full paper list, with each design's claimed gap and later results, is in the [literature map](@/research/literature-map.md).
