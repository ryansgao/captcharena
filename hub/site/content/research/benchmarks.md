+++
title = "CAPTCHA benchmarks and datasets, with licences"
description = "Every open CAPTCHA benchmark and dataset for AI agents, with licence, status and method limits, plus solver-service benchmarks and lessons from other leaderboards."
weight = 30
[extra]
checked = "2026-11-01"
+++

At least eight open CAPTCHA benchmarks for AI agents appeared between mid-2025 and October 2026. Each is a research repository tied to one paper, with its own harness, action format and step limits, and most stopped changing after publication. This page lists them with their licences and status, then the solver-service benchmarks, then what other agent leaderboards have learned about staying honest and current.

## Research benchmarks

Repository figures (stars, last push) are from GitHub on 2026-11-01.

| Benchmark | What it covers | Real widgets or clones | Licence | Status | Source |
|---|---|---|---|---|---|
| **Open CaptchaWorld** (NeurIPS 2025 Datasets and Benchmarks) | 20 puzzle types (dice count, slide puzzle, hold button, path finder, Bingo and others) in a Flask app; grew from 225 to 463 puzzles in 2025. Best agent 40.0% against humans' 93.3%. | Original designs in the style of modern CAPTCHAs | README says MIT, but the repository has no LICENSE file; the Hugging Face dataset is tagged Apache-2.0 | **Frozen.** Last push 2026-02-19; superseded by the same group's Next-Gen CAPTCHAs. Its Hugging Face Space was last modified 2025-05-15. | [repo](https://github.com/MetaAgentX/OpenCaptchaWorld), [paper](https://arxiv.org/abs/2505.24878) |
| **Next-Gen CAPTCHAs** (ICML 2026 per its repository) | A procedural generator plus a 519-puzzle snapshot in 27 families; command-line runners for Browser-Use and CrewAI. Agents 0.9–5.9%, humans 98.8%. | Original anti-agent designs | MIT | **Active**: last push 2026-10-23 | [repo](https://github.com/MetaAgentX/NextGen-CAPTCHAs), [paper](https://arxiv.org/abs/2602.09012) |
| **Halligan** (USENIX Security 2025) | A solver plus a benchmark server: 26 types, 2,600 challenges, in Docker. Includes 11 Arkose-style types, AWS WAF, MTCaptcha, GeeTest, Tencent and Yandex: vendors with no public demo. | Local replicas of real vendor challenges; image provenance unclear | MIT (code); README asks users not to use it on real-world services | **Research artefact**: code static since 2025, last push 2026-09-07 | [repo](https://github.com/code-philia/Halligan), [paper](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh), [artefact](https://zenodo.org/records/15709075) |
| **MCA-Bench** (AAAI 2026, oral) | 20 tasks, from point-and-click to sliders; human and model pass rates per task. Predicts answers rather than acting in a live browser. | Reimplemented styles | Apache-2.0 | **Light activity**: last push 2026-10-13. Dataset on Kaggle. | [repo](https://github.com/noheadwuzonglin/MCA-Bench), [paper](https://ojs.aaai.org/index.php/AAAI/article/view/41141) |
| **HLL: Humanity's Last Line of Verification** | Local CAPTCHA server, 10 families with dynamic variants, configurable page clutter, and action-trace validation. Evaluation scripts drive a mobile agent on an Android emulator. | Clones of common (mostly Chinese-market) styles | MIT | **Frozen**: one push, 2026-05-19 | [repo](https://github.com/XinhaoS0101/HLL), [paper](https://arxiv.org/abs/2606.02449) |
| **CaptchaArena** | 50K execution-verified puzzles in 20 types, 50K screenshot-and-action trajectories, a live server and a 9B policy (71.7 Pass@1). Human baseline 94.1 (two annotators, median 8.5 s). | Original images (generated, rendered, or openly licensed); *"No proprietary CAPTCHA assets are scraped or redistributed"* | Code MIT; **datasets CC BY-NC 4.0, gated**, *"for non-commercial academic research only"* | **New**: last push 2026-09-29 | [repo](https://github.com/X0X0X00/CaptchaArena), [paper](https://arxiv.org/abs/2609.31957), [dataset](https://huggingface.co/datasets/ZHEN-04/CaptchaArena) |
| **Muse CAPTCHA Gym** | Self-hosted reCAPTCHA-v2-style gate with a mock risk engine; grids over synthetic scenes and openly licensed photos; server-side scoring with a failure taxonomy and two clocks (round and token expiry). The most careful scoring design we found. | Clone of the reCAPTCHA v2 shape | MIT; photos limited to CC-BY and CC-BY-SA with per-image credits | **Paused**: *"Testing paused indefinitely as of October 2026 due to AI token consumption and operational costs"* | [repo](https://github.com/mildchef/Muse-Captcha-Gym) |
| **Agentified Open CaptchaWorld** (AgentBeats) | Open CaptchaWorld wrapped in the A2A protocol, with a leaderboard repository | Same as Open CaptchaWorld | MIT | **Dormant** since 2026-01-07 | [repo](https://github.com/gmsh/agentified-opencaptchaworld) |

Further datasets reported in papers without a runnable release we could find: CAPTCHA-X (1,839 puzzles, 7 types), CAPTURE (61,464 items, 25 subtypes), MirrorCAPTCHA (370K, 18 types), ReCAP (160K, 7 types), CaptchaMind (16K, 8 types) and MVCAP-Bench (600 motion-defined instances). Details and sources are in the [literature map](@/research/literature-map.md).

{% <note> %}
Scores across these benchmarks are not comparable. CaptchaArena's own authors warn that its cross-benchmark scores are "not directly comparable": harness, viewport, action format and step caps all differ. A model trained on one benchmark's synthetic types can transfer poorly to another's: CaptchaArena's policy went from 0.9 to 20.0 on Halligan's replicas, against 9.8 to 51.0 on Open CaptchaWorld ([arXiv 2609.31957](https://arxiv.org/html/2609.31957v1), checked 2026-11-01).
{% </note> %}

## Measurements against real widgets

Clones measure puzzle solving. Real widgets also measure the invisible score, the clock and the vendor's server verdict.

| Study | Method | Released? | Source (checked 2026-11-01) |
|---|---|---|---|
| **Broken Gates** (2026-07) | Real hCaptcha, reCAPTCHA v2 and v3, and Turnstile on the authors' own public subdomains for about six months; every token checked with the vendor; 100 instances per service and target. | **No harness**: *"We do not release exploit-ready automation scripts"* | [arXiv 2607.18659](https://arxiv.org/abs/2607.18659) |
| **Roundtable / Proof of Human** reCAPTCHA v2 benchmark (2025-11) | Browser Use on Google's public demo; 75 trials. | Not stated | [research.poh.org](https://research.poh.org/captcha-benchmarking/) |
| **Proof of Human** bot-detection benchmark | Five invisible systems, 750 sessions; the authors' product ranks first (conflict of interest not addressed). | Code "in the future" | [research.poh.org](https://research.poh.org/bot-benchmarking/) |
| **techstackups** hosted-browser benchmark (2026-03-06, updated 2026-05-31) | Six hosted browsers against detection test sites and Google's reCAPTCHA v2 demo. | — | [techstackups](https://techstackups.com/comparisons/hosted-browser-benchmarks/) |

Our own real-widget measurements are on the [scoreboard](@/scoreboard/_index.md); the method is on [its method page](@/scoreboard/method.md).

## Solver-service benchmarks

Several sites rank commercial CAPTCHA-solving services. We list them for their method, not their rankings, and we do not link affiliate pages.

| Benchmark | Method as stated | Limits we found | Checked |
|---|---|---|---|
| [HasData](https://hasdata.com/blog/captcha-solving), "Top 5 CAPTCHA Solving Services in 2026" (updated 2026-09-25) | 5 services × 6 types × *"50 distinct CAPTCHA challenges per type"*; success = *"Percentage of tokens accepted by the target site on first attempt"*; list prices | Test URLs not disclosed; no per-run dates or traces; internal inconsistencies (94% against 100%; an audio rate of 27% that cannot come from 50 attempts); describes itself as independent while selling scraping APIs | 2026-11-01 |
| [CaptchaTheCat](https://captchathecat.com) | 24 services, about 34 types, daily to monthly tables; *"The review service sends requests to each solver and collects data"* | No operator named; no method; an "Add service" form pitched as *"Boost your website's visibility"*; outbound redirect links; unexplained 0%-accuracy rows | 2026-11-01 |
| [Scrapeway](https://scrapeway.com) | 7 scraping APIs × 11 protected targets; *"No affiliate links. No sponsors. Just data."* | Scraping APIs, not CAPTCHA solvers; operator not named; update cadence stated three different ways; latest window 2026-09-11 to 09-25; a scraping vendor cites it for its own success rates | 2026-11-01 |

The common gaps: each covers one slice (solver APIs, scraping APIs, hosted browsers or clone puzzles), operators are hidden or commercially interested, no traces are published, and nobody can re-check a result. Solving services also rely heavily on low-paid human workers; Anti-Captcha states *"100% of captchas are solved by human workers"* ([anti-captcha.com](https://anti-captcha.com/), checked 2026-11-01).

## Lessons from other agent leaderboards

| Leaderboard | Lesson | Source (checked 2026-11-01) |
|---|---|---|
| **OSWorld-Verified** (2025-07-28) | The maintainers run every submitted agent on their own infrastructure; the agent's code must be disclosed, the model API can stay private. Volatile tasks carry a flag; tasks that need human verification run from fixed IPs. The step budget changes results a lot (one model 9.1% to 23.0%). | [xlang.ai](https://xlang.ai/blog/osworld-verified) |
| **SWE-bench** | Submissions come with predictions, logs and trajectories, and anyone can re-check them. Since 2025-11-18 the Verified board accepts only academic teams with open methods, *"rather than as a product validation platform"*: they narrowed the board rather than police it. | [SWE-bench/experiments](https://github.com/SWE-bench/experiments) |
| **HAL (Holistic Agent Leaderboard)**, Princeton | Dollar cost on every entry and a cost-accuracy chart (*"Agents can be 100x more expensive while only being 1% better"*); traces published encrypted against scraping. Then: *"We have paused updating HAL leaderboard with new models"*. Even a funded academic board stalls. | [hal.cs.princeton.edu](https://hal.cs.princeton.edu/) |
| **LiveBench** | Fresh questions from recent sources, added monthly, with objective answers: freshness as the defence against contamination. | [arXiv 2406.19314](https://arxiv.org/abs/2406.19314) |
| **Papers with Code** | Meta retired it in July 2025; the site and API are gone, and only JSON dumps survive. A board hosted by one sponsor dies with the sponsor; open data dumps outlive it. | [shutdown notes (a competitor's page)](https://www.codesota.com/papers-with-code/shutdown), [data dumps](https://github.com/paperswithcode/paperswithcode-data) |
| **Leaderboard Illusion** (on LMArena) | *"undisclosed private testing practices benefit a handful of providers who are able to test multiple variants before public release and retract scores"*. The fix: register a version before the run and publish every run. | [arXiv 2504.20879](https://arxiv.org/abs/2504.20879) |

For CAPTCHA benchmarks, these add up to a short list: one fixed harness run by the maintainer; cost and time next to every pass rate; fresh instances each cycle with a private held-out set; real-widget lanes scored by the vendor's verdict; every run published; and open data that outlives the host. Our [scoreboard method](@/scoreboard/method.md) follows them.

{% <coming> %}
A single runner that drives the open benchmarks above (Open CaptchaWorld, Next-Gen CAPTCHAs, Halligan) through one action interface, so the same agent can be scored on all of them, with results on the scoreboard.
{% </coming> %}
