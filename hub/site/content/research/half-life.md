+++
title = "The CAPTCHA half-life: a measure nobody publishes yet"
description = "How many months a CAPTCHA design lasts against AI agents, why nobody measures it, and how we plan to: a scheduled re-test of every solver against every design."
weight = 40
[extra]
checked = "2026-11-01"
status = "coming"
+++

Every CAPTCHA design paper reports how well agents do against it on the day it was tested. None reports how long that lasts. We call that missing number the **CAPTCHA half-life**: the number of months from a design's launch until agents pass it most of the time. This page defines it, explains how we will measure it, and why it matters.

## The definition

**Half-life** = months from a design's launch (its paper, its release, or its deployment) until current agents first pass it at a rate that makes it useless as a barrier.

Three choices make the number precise:

| Choice | Proposed default | Why |
|---|---|---|
| Start date | The design's first public appearance (preprint or release) | That is when attackers can start working on it. |
| Collapse threshold | Agent pass rate reaches half the human pass rate measured on the same instances | It scales with how hard the design is for people, and is the literal "half" in half-life. We also publish the date each design first crosses 70% and 90%, for comparison with the literature. |
| Which agents | The best of: current frontier models in a general agent, the best open solver, and an attacker built for that design | A design that only resists off-the-shelf agents has not been tested. |

A design that never collapses within the measurement window gets a lower bound ("more than 14 months"), not a number.

## Why nobody publishes it

The literature contains the raw material but not the measure. Defence papers test once, against the models of their month. Attack papers target different instances, with different harnesses, months later. Only one case we found is the same group re-testing the same puzzle type: no model solved Open CaptchaWorld's "Bingo" in May 2025, and the same group reported up to 90% nine months later ([arXiv 2505.24878](https://arxiv.org/abs/2505.24878), [arXiv 2602.09012](https://arxiv.org/abs/2602.09012), checked 2026-11-01). Our [months-to-collapse table](@/research/literature-map.md) pairs the rest, and it is a summary of papers, not a measurement.

The reason is practical. A one-shot paper is publishable; a standing re-test costs money every cycle and has no natural author. Benchmarks that tried to stay current stalled: Muse CAPTCHA Gym paused *"due to AI token consumption and operational costs"* ([repo](https://github.com/mildchef/Muse-Captcha-Gym), checked 2026-11-01), and Princeton's HAL leaderboard paused new models ([HAL](https://hal.cs.princeton.edu/), checked 2026-11-01).

## How we will measure it

A harness that runs on a timer, not when someone remembers.

1. **Reimplement or host each design.** From its published code where it exists, from the paper otherwise. Designs are run on our own pages, never against live third-party sites.
2. **Keep a population of solvers.** A general agent driven by each new frontier model as it is released; the strongest open-source solvers from the literature; and, for each design, an adaptive attacker built for it.
3. **Re-run every solver against every design each cycle**, monthly and whenever a major model is released. The schedule triggers the run.
4. **Draw fresh instances every cycle** from each design's generator, so a solver cannot memorise answers.
5. **Measure humans on the same instances**, with a documented, ethics-reviewed baseline that includes disabled participants (see [open questions](@/research/open-questions.md)).
6. **Record more than pass rate:** cost per pass, time per pass, pass within the design's own time limit, and whether the trace or timing was rejected.
7. **Publish per design:** the pass-rate curve over time, the date it crossed each threshold, and its half-life or lower bound, with harness version, model identifiers and dates.

{% <coming> %}
The harness, its first designs, and the first published curves. Results will appear on the [scoreboard](@/scoreboard/_index.md), with the method on the [method page](@/scoreboard/method.md).
{% </coming> %}

## Why it matters

| Reader | What the half-life tells them |
|---|---|
| **Site owners and CAPTCHA vendors** | How long a new design will protect them before it needs replacing, and so whether it is worth deploying at all. A design with a three-month half-life is a maintenance contract, not a defence. |
| **AI labs** | How quickly their agents' perception and action skills erode a class of human checks: a capability trend, measured outside their own evaluations. |
| **Researchers** | Whether a published design held up. Today a paper reporting "agents 5%, humans 95%" is the last word on its design; with a half-life it becomes the first point on a curve. |
| **Standards bodies** | Evidence for the shift away from puzzles (towards signed agents and anonymous credentials), with dates rather than opinions. |

## The tension: open method, private test set

Publishing everything helps attackers. An open generator is training data: CaptchaArena trained a 9B policy on 50K generated puzzles ([arXiv 2609.31957](https://arxiv.org/abs/2609.31957), checked 2026-11-01). For detectors the effect is measured: in the Process Turing Test, an agent fine-tuned with full knowledge of the scored features and objective closed the human-agent gap, which reopened when features were withheld or the task changed ([arXiv 2605.06524](https://arxiv.org/abs/2605.06524), checked 2026-11-01). Security practice says a defence should survive its design being public (Kerckhoffs's principle); benchmark practice says the test set should stay private.

Our resolution is the benchmark one:

- **Published:** the method, the harness code, the scoring, every result, and retired instances.
- **Kept private and rotated:** the live task families for the current cycle, their instance seeds, and the thresholds and feature subsets of any detector under test, like a held-out test set.
- **Shared with authors first:** a design's results go to its authors before publication.

This keeps results reproducible in method while denying a solver the exact test it will face.
