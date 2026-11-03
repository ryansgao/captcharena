+++
title = "Scoreboard method: how we keep the numbers fair"
description = "The ten rules the CAPTCHArena scoreboard follows, borrowed from the agent leaderboards that worked and the ones that were gamed or died."
weight = 10
[extra]
checked = "2026-11-01"
+++

Leaderboards fail in known ways: providers test private variants and publish the best, agents memorise public test items, operators stop updating, sites shut down and take the data with them. Each rule below answers one of those failures, with the leaderboard it comes from.

## The ten rules

| # | Rule | Borrowed from (checked 2026-11-01) |
|---|---|---|
| 1 | **We run it.** One fixed harness per lane: fixed window size, step limit, time limit and action interface. Self-reported results, if accepted at all, sit in a separate labelled tab. | [OSWorld-Verified](https://xlang.ai/blog/osworld-verified) runs submitted agents on its own infrastructure; [HAL](https://hal.cs.princeton.edu/) is "standardized, cost-aware, and third-party" |
| 2 | **Submitter pays, we run.** A lab or framework team can fund its own verified run; the agent code and harness settings are disclosed, the model API can stay private. | OSWorld-Verified's submission model |
| 3 | **One public score per release, no private variants.** A named, dated version is registered before the run, and every run is published, failures included. | The [Leaderboard Illusion](https://arxiv.org/abs/2504.20879) found undisclosed private testing let a few providers test many variants and retract scores |
| 4 | **Cost and time next to accuracy, always.** | HAL: "Agents can be 100x more expensive while only being 1% better" |
| 5 | **Fresh instances every cycle.** Practice-puzzle lanes draw new instances from generators; a private held-out set is never published. | [LiveBench](https://arxiv.org/abs/2406.19314) refreshes its questions monthly; HAL encrypts its traces against scraping |
| 6 | **Real widgets are scored by the vendor's server**, not by whether a puzzle looked solved: reCAPTCHA and Turnstile `siteverify`, and each open CAPTCHA's own verifier. | [Broken Gates](https://arxiv.org/abs/2607.18659) did this for one paper |
| 7 | **Flag volatility.** Lanes whose difficulty depends on the vendor's risk model or the network address are marked, and every run records its network type (residential, data centre, VPN). | OSWorld-Verified's flag for tasks whose environment may change |
| 8 | **Open data that outlives the host.** Results as CSV and JSON in a public repository, plus a dated quarterly snapshot with a DOI. | Papers with Code was retired in July 2025; its [data dumps](https://github.com/paperswithcode/paperswithcode-data) are what survived ([CodeSOTA](https://www.codesota.com/papers-with-code/shutdown)) |
| 9 | **Version everything:** harness, lane, model id, scaffold, date, network type. | [SWE-bench](https://github.com/SWE-bench/experiments) publishes trajectories and a re-check command |
| 10 | **When gamed, narrow the scope and say so**, rather than police it. | SWE-bench limited Verified submissions to academic teams with open methods from 2025-11-18 |

## How real-widget results are produced

1. A real widget runs on our own domain with our own key. The live page is [measure.captcharena.org](https://measure.captcharena.org).
2. The browser (a person's or an agent's) completes it and receives a token.
3. Our server sends the token to the vendor's verification endpoint, or to the self-hosted CAPTCHA's own verifier, and records the verdict, the time and, for reCAPTCHA v3, the score.
4. Each attempt is one line in a run log: lane, verdict, time, the run's condition label, browser details and country. No IP address and no cookie of ours.
5. A global daily cap on verification calls keeps public traffic from exhausting the free tiers.
6. Results made with a vendor's test key are marked and dropped from analysis.

## Paid solving services: the mystery-shopper method

To measure commercial solving services fairly, we will buy credit at list price as an ordinary customer, generate fresh widget pages on fresh subdomains with fresh keys each month, and accept or reject each answer by our own server check. Fresh domains and keys make the benchmark look like ordinary customer traffic, so a service cannot quietly route it to its best workers.

We will publish acceptance rate, median and slow-case time, list price, effective price per accepted solve, and the rate of answers received but rejected. hCaptcha is excluded from this lane: its [terms](https://www.hcaptcha.com/terms) (updated 2025-11-17) forbid using bots or AI to pass its challenges, which would include paying a service to do so on our own site, unless hCaptcha agrees in writing. Many solving services rely on low-paid human workers; one says "100% of captchas are solved by human workers" ([Anti-Captcha](https://anti-captcha.com/), checked 2026-11-01). We link to no service with an affiliate code.

## Threats to fairness and our counter for each

| Threat | Counter |
|---|---|
| A lab tests many private versions and publishes the best | Registered, dated version; all runs published |
| An agent is trained on our public instances | Regenerated instances each cycle; private held-out set |
| A solving service treats our domain specially | Rotating subdomains and keys |
| A submitter's harness differs from ours | We run every verified entry on our harness |
| A cheap win by spending more money | Cost on every row |
| A vendor throttles or revokes our key | Separate keys for public play pages and agent runs; vendors told before a lane launches |
| Results die with the host | Open dumps and DOI snapshots |

## What we will not do

- Sell, broker or give out CAPTCHA tokens or solving code.
- Test a vendor's real widget with agents where its terms forbid it, without written permission.
- Take money from vendors, solving services or agent companies for placement.
