+++
title = "Practice puzzles: the open research puzzles we will host"
description = "Which open-source CAPTCHA research puzzles the Play section will host, under which licences, and how human and agent results will be compared."
weight = 10
[extra]
checked = "2026-11-01"
status = "coming"
+++

{% <coming> %}

These puzzles are not live yet. They arrive with the clone benchmark runs that also feed the [Scoreboard](@/scoreboard/_index.md). Until then you can play real widgets on the [measurement page](https://measure.captcharena.org).

{% </coming> %}

## What a practice puzzle page will show

- The puzzle itself, clearly labelled **"practice puzzle, not a real CAPTCHA"**, with no vendor name, logo or look.
- Your time and whether you got it right.
- On the same instance: how the best AI agent we tested did, its time and its cost.
- How the puzzle type works, how agents solve or fail it according to the published research, and its accessibility notes.

Humans and agents scored on the same instances is what no public benchmark offers today. Benchmarks report agent scores against a small, separate human sample, if any.

## Sources we plan to host, and their licences

Licences were read from each repository on 2026-11-01. Not legal advice.

| Project | What it is | Licence | Conditions we follow |
|---|---|---|---|
| [Open CaptchaWorld](https://github.com/MetaAgentX/OpenCaptchaWorld) | Web benchmark of interactive logic puzzles for multimodal agents ([paper](https://arxiv.org/abs/2505.24878)) | README says MIT; no LICENSE file was found | Keep the MIT notice and citation; ask the authors to add the file first |
| [Next-Gen CAPTCHAs](https://github.com/MetaAgentX/NextGen-CAPTCHAs) | 27 new puzzle families with a procedural generator ([paper](https://arxiv.org/abs/2602.09012)) | MIT | Notice; its generator gives fresh instances each cycle |
| [HLL](https://github.com/XinhaoS0101/HLL) | Image puzzles built from photo APIs at run time | MIT | Use our own photo-API keys and follow their attribution rules |
| [Halligan](https://github.com/code-philia/Halligan) | Benchmark of 26 CAPTCHA types from a USENIX Security 2025 solver paper ([paper](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh)) | MIT | Only types whose images are clearly not taken from vendors; never vendor logos |
| [Muse CAPTCHA Gym](https://github.com/mildchef/Muse-Captcha-Gym) | Puzzle gym with a failure taxonomy | MIT; images CC-BY / CC-BY-SA | Keep its per-image credits |

Not hosted: the [CaptchaArena](https://github.com/X0X0X00/CaptchaArena) datasets. Their licence (CC BY-NC 4.0, gated, "for non-commercial academic research only") rules out a public mirror, so we link to them instead.

## Why practice puzzles are unbranded

Fake CAPTCHAs that tell people to paste a command ("ClickFix") were among the most common malware lures of 2025–26. Google Safe Browsing treats pages that "look and feel like a trusted entity" as social engineering ([policy](https://developers.google.com/search/docs/monitor-debug/security/social-engineering), checked 2026-11-01). A practice site full of convincing vendor lookalikes would teach the wrong reflex. Read [how to spot a fake CAPTCHA](@/learn/is-this-captcha-real.md).
