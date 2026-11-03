+++
title = "CAPTCHA literature map, 2023–2026: every attack and defence"
description = "Every CAPTCHA attack, defence, agent-detection, benchmark, theory and survey paper we found for 2023–2026, with its key number, source and check date."
weight = 10
[extra]
checked = "2026-11-01"
+++

This is a map of the published work on CAPTCHAs and AI agents, mostly from 2023 to 2026, with the earlier papers it still leans on. Each row gives the work, when it appeared, the venue if one is stated, what kind of work it is, its key claim or number, and the date we checked it. "Our re-test" will hold the result when we re-run a design or attack against current agents; for now every row says *coming*.

How to read it:

- **Date** is the arXiv month (from the paper's identifier) or the conference year. **Venue** is left as "arXiv" when no peer-reviewed venue is stated on the paper or its repository.
- **Key claim** is the paper's own number, in its own terms. Numbers from different papers are rarely comparable: harnesses, models, step limits and scoring differ.
- Authors' affiliations are given where they help find the group. Company research is marked, because several authors sell a related product.

{% <note> %}
We found these papers through the arXiv listing for "captcha" (the 150 newest results on 2026-11-01), conference pages, and the related-work sections of the papers themselves. If a paper is missing, or a number is wrong, tell us through the [contact page](@/contact/_index.md).
{% </note> %}

## Attacks, solvers and measurement studies

| Work | Date | Venue | Type | Key claim or number | Checked | Our re-test |
|---|---|---|---|---|---|---|
| [Motoyama et al., CAPTCHA-solving services in an economic context](https://www.usenix.org/legacy/event/sec10/tech/full_papers/Motoyama.pdf) | 2010 | USENIX Security 2010 | Measurement (economics) | CAPTCHAs are best judged *"in purely economic terms"*: the market price of a solution against the value of what it protects. Human solving was already cheap and fast. | 2026-11-02 | coming |
| [Xu et al., moving-object CAPTCHAs](https://www.usenix.org/biblio/security-and-usability-challenges-moving-object-captchas-decoding-codewords-motion) | 2012 | USENIX Security 2012 | Attack | Broke NuCaptcha-style moving-object CAPTCHAs by tracking motion. The precedent for today's motion-based designs. | 2026-11-01 | coming |
| [Sivakorn et al., "I'm Not a Human: Breaking the Google reCAPTCHA"](https://www.blackhat.com/docs/asia-16/materials/asia-16-Sivakorn-Im-Not-a-Human-Breaking-the-Google-reCAPTCHA-wp.pdf) | 2016 | Black Hat Asia 2016 | Attack (per-signal test) | The only published per-signal test of Google's risk engine we found: a Google cookie aged nine days earned the tick-box pass with no browsing; screen size and mouse behaviour made no difference. | 2026-11-01 | coming |
| [Searles, Nakatsuka, Ozturk, Paverd, Tsudik, Enkoji, "An Empirical Study & Evaluation of Modern CAPTCHAs"](https://arxiv.org/abs/2307.12108) | 2023-07 | USENIX Security 2023 | Measurement (human study) | 1,400 paid participants, 14,000 CAPTCHAs. Using bot figures from earlier literature, *"bots can outperform humans, both in terms of solving time and accuracy"* (distorted text: humans 9–15 s and 50–84%; bots under 1 s and 99.8%). The bot figures were not measured in this study. | 2026-11-01 | coming |
| [Dong et al., adversarial attacks on closed vision-language models](https://arxiv.org/abs/2309.11751) | 2023-09 | arXiv | Attack analysis | Adversarial images transfer weakly to closed models: 22% on Bard, 26% on Bing Chat. Relevant to adversarial-noise CAPTCHAs, whose designers cannot see inside frontier models. | 2026-11-01 | coming |
| [Searles, Prapty, Tsudik, "Dazed & Confused"](https://arxiv.org/abs/2311.10911) | 2023-11 | arXiv (UC Irvine) | Measurement (field study) | 13 months, 3,600+ real users of a university service. reCAPTCHA v2 has *"an immense cost and no security"*; recommends deprecation. | 2026-11-01 | coming |
| [Deng, Ou, Liu, Zhang, Zhang, Liu, "Oedipus"](https://arxiv.org/abs/2405.07496) | 2024-05 | arXiv (NTU Singapore) | Attack | Breaks "reasoning CAPTCHAs" by decomposing them into steps that are easy for AI, via a small task language and chain-of-thought; 63.5% on average. | 2026-11-01 | coming |
| [Plesner, Vontobel, Wattenhofer, "Breaking reCAPTCHAv2"](https://arxiv.org/abs/2409.08831) | 2024-09 | COMPSAC 2024 (ETH Zürich) | Attack | A YOLO model solves 100% of reCAPTCHA v2 image challenges; humans and bots need a similar number of challenges; reCAPTCHA v2 *"relies heavily on cookie and browser history data"*. Code published. | 2026-11-01 | coming |
| [Teoh et al., "Halligan: Are CAPTCHAs Still Bot-hard?"](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh) | 2025 | USENIX Security 2025 (SJTU, NUS, Tel Aviv) | Attack (general solver) | One vision-language agent, no per-type training: 60.7% of 2,600 challenges across 26 types; 70.6% on unseen challenges in the wild over 30 days; Arkose 33.0% in the field (n = 218). Median 21.8 s and $0.024 per challenge; reusing generated code cut cost to $0.006. | 2026-11-01 | coming |
| [Song et al., "Reasoning under Vision" (CAPTCHA-X)](https://arxiv.org/abs/2510.06067) | 2025-10 | arXiv (Columbia) | Attack and benchmark | Commercial models solve about 21.9% without reasoning; a step-by-step reasoning agent reaches 83.9% on five hard types. 1,839 puzzles, 7 types, with reasoning and action annotations. | 2026-11-01 | coming |
| [Roundtable (now Proof of Human), reCAPTCHA v2 benchmark](https://research.poh.org/captcha-benchmarking/) | 2025-11 | Company research | Measurement | Browser Use on Google's reCAPTCHA v2 demo, 75 trials: Claude Sonnet 4.5 60%, Gemini 2.5 Pro 56%, GPT-5 28%; on cross-tile challenges 0–1.9%. The company sells bot detection. | 2026-11-01 | coming |
| [Wang et al., "COGNITION"](https://arxiv.org/abs/2512.02318) | 2025-12 | USENIX Security 2026 | Attack measurement and hardened design | 7 multimodal models × 18 real-world types: recognition and low-interaction tasks are solved *"at human-like cost and latency"*; 42.3% cross-model Pass@1 (GPT-5 59.4%). Fine localisation, multi-step spatial reasoning and cross-frame consistency stay hard. Hardening one type cut success *"from over 95% to 0%"*. | 2026-11-01 | coming |
| [Qi, He, Wang, Zhang, "ViPer"](https://arxiv.org/abs/2601.06461) | 2026-01 | USENIX Security 2026 | Attack | Visual-reasoning CAPTCHAs from six Chinese vendors (Geetest, NetEase, Dingxiang, Shumei, Xiaodun, VTT): up to 93.2%, above 90% across GPT, Grok, DeepSeek and Kimi backbones. Proposes Template-Space Randomization as a defence. | 2026-11-01 | coming |
| [Chen et al., "ReCAP"](https://arxiv.org/abs/2603.23559) | 2026-03 | ICML 2026 (UIUC) | Attack (trained agent) | A native GUI agent trained on synthetic CAPTCHA trajectories with self-correction: about 30% to above 80% on its synthetic set; uneven gains on a real-world set. | 2026-11-01 | coming |
| [Wang et al., "CaptchaMind" (CaptchaBench)](https://arxiv.org/abs/2605.19538) | 2026-05 | arXiv | Attack (trained agent) | RL-trained solver with reasoning supervision: 82.9% on 8 synthetic categories, 71.0% on real-world instances (vendors' public demo pages). | 2026-11-01 | coming |
| [Ousat, Turkmen, Rampersaud, Bailey, Kharraz, "Broken Gates"](https://arxiv.org/abs/2607.18659) | 2026-07 | arXiv (FIU; venue not stated) | Measurement on real widgets | Real hCaptcha, reCAPTCHA v2 and v3, and Turnstile on the authors' own subdomains for about six months; tokens checked with the vendors. Seven solving services pass nearly everything except hCaptcha's hard setting (58% for one service) and reCAPTCHA v3 (0–63%), at $0.10–5.00 per thousand. Two agents with near-identical behaviour got different v3 outcomes: the execution environment decided it. No scripts released. | 2026-11-01 | coming |
| [Fehrensen, Hubler](https://arxiv.org/abs/2608.28794) | 2026-08 | arXiv | Attack | LLM agents break the CAPTCHA gates of dark-web sites. | 2026-11-01 | coming |
| [Salman, Bicakci, "CAPTCHAs in the Agentic Era: Solvers That Learn from Every Encounter"](https://arxiv.org/abs/2609.02393) | 2026-09 | arXiv (Istanbul Tech.) | Attack (adaptive) | A fast detector plus an open vision-language model behind a router; the model's answers retrain the detector, which learns a new class after one or two encounters. In a simulated year where the operator re-perturbs images monthly, the solver recovers every round. A trained detector scores 0% on classes it never saw. | 2026-11-01 | coming |
| [Sivakorn, Gottlieb, "Robot Visions"](https://arxiv.org/abs/2609.18518) | 2026-09 | ISC 2026 | Attack | Free local CLIP and OWLv2 models, zero-shot: 92.6% per session on 500 real reCAPTCHA sessions; a non-technical user can do it by instructing a commodity assistant. *"challenge-based visual CAPTCHAs may have reached the end of their useful life"*. | 2026-11-01 | coming |
| [Sun et al., "CaptchaAgent"](https://arxiv.org/abs/2610.12866) | 2026-10 | arXiv | Attack | +21–26 percentage points on Open CaptchaWorld through an explicit visual intermediate representation. Remaining failures: *"exact counting, continuous geometry, and ordered execution"*. | 2026-11-01 | coming |
| [DarKnight](https://arxiv.org/abs/2610.19830) | 2026-10 | APWG eCrime 2026 | Attack | LLM agents break dark-web CAPTCHA gates. | 2026-11-01 | coming |
| [Song et al., "SolveBind"](https://arxiv.org/abs/2610.32223) | 2026-10 | arXiv | Attack | Agents that find the right answer still fail behavioural binding (trajectory and timing); a runtime supervisor raises success to 82% across 9 CAPTCHA families. Removing recovery limits bought +1.3 points for 3.7× the latency. | 2026-11-01 | coming |
| [SemVink](https://arxiv.org/abs/2506.02803) | 2025-06 | arXiv | Attack analysis | Hidden-content illusion images become readable to vision-language models when downscaled to 32–128 px: accuracy above 99%. | 2026-11-01 | coming |
| [Tool-using models on modified illusions](https://arxiv.org/abs/2603.29428) | 2026-03 | arXiv | Attack analysis | Vision-language models with tools handle counterfactually modified classic illusions without training. | 2026-11-01 | coming |

## Defences and "AI-hard" designs

| Work | Date | Venue | Type | Key claim or number | Checked | Our re-test |
|---|---|---|---|---|---|---|
| [FLAIR](https://arxiv.org/abs/2305.06424) | 2023-05 | arXiv | Reverse Turing test | One question easy for humans and hard for bots (counting, substitution, ASCII reasoning): humans near-perfect, LLMs near zero in 2023. Reasoning models have since improved on several of these categories. | 2026-11-01 | coming |
| [Jiang et al., "Diff-CAPTCHA"](https://arxiv.org/abs/2308.08367) | 2023-08 | arXiv | Generated image CAPTCHA | Diffusion fuses characters into the background; lower success for two attack styles than three baselines (self-tested). | 2026-11-01 | coming |
| [Geng, Park, Owens, "Visual Anagrams"](https://arxiv.org/abs/2311.17919) | 2023-11 | CVPR 2024 | Technique | Diffusion images that change meaning when flipped or rotated. A generation method, not a deployed CAPTCHA. | 2026-11-01 | coming |
| [Jabary, Plesner, Wattenhofer, "Seeing Through the Mask"](https://arxiv.org/abs/2409.05558) | 2024-09 | arXiv (ETH Zürich) | Adversarial perturbation | Image masks drop top-1 accuracy by more than 50 points; vision transformers by 80. | 2026-11-01 | coming |
| [BounTCHA](https://arxiv.org/abs/2501.18565) | 2025-01 | arXiv | Video timing | Uses humans' timing bias when spotting cuts in AI-extended video. | 2026-11-01 | coming |
| [Ding, Deng, … Li, "IllusionCAPTCHA"](https://arxiv.org/abs/2502.05461) | 2025-02 | Reported as WWW 2025 by one source; unconfirmed (UNSW, NTU) | Visual illusion | GPT-4o and Gemini 1.5 Pro fooled 100%; humans 86.95% on the first try. No published re-test on newer models found. | 2026-11-01 | coming |
| [DAC: Defensive Adversarial CAPTCHA](https://arxiv.org/abs/2506.10685) | 2025-06 | arXiv | Adversarial perturbation | LLM-guided semantic adversarial generation, white- and black-box. | 2026-11-01 | coming |
| [Chandra et al., "Aura-CAPTCHA"](https://arxiv.org/abs/2508.14976) | 2025-08 | arXiv | Generated, adaptive | GAN-generated visual stimuli plus audio; an RL agent tunes difficulty from interaction. The authors concede it *"remains vulnerable to emerging large-model agents"*. | 2026-11-01 | coming |
| [Kumar, Roh, Naseh, Houmansadr, Bagdasarian, "Reasoning Gates"](https://arxiv.org/abs/2509.01619) | 2025-09 | arXiv (UMass Amherst) | Cost (throttle, not block) | Rebus puzzles cost an agent 9.2× the tokens it took to generate them. Slows agents; does not try to exclude them. | 2026-11-01 | coming |
| [Aghaei Nia, generative questions plus keystroke rhythm](https://arxiv.org/abs/2510.02374) | 2025 | arXiv | Hybrid | LLM-generated questions with a typing-rhythm check; claims to stop paste and script attacks. Six pages, single author, not replicated. | 2026-11-01 | coming |
| [Kharlamova, He, Ma, Liu, "Spatial CAPTCHA"](https://arxiv.org/abs/2510.03863) | 2025-10 | Submitted to ICLR 2026; outcome not checked (McGill) | Spatial reasoning | Mental rotation, perspective and occlusion tasks: the best of 10 multimodal models reaches 31.0% Pass@1. | 2026-11-01 | coming |
| [CAHICHA](https://arxiv.org/abs/2511.07841) | 2025-11 | arXiv | Hardware signal | Uses the WebAuthn user-presence flag as the human signal. | 2026-11-01 | coming |
| [NGCaptcha](https://arxiv.org/abs/2512.16223) | 2025-12 | arXiv (UNSW group) | Hybrid | Proof of work combined with an AI-hard image task. | 2026-11-01 | coming |
| [IllusionAudio / AI-CAPTCHA](https://arxiv.org/abs/2601.08516) | 2026-01 | arXiv (UNSW group) | Audio illusion | Defeats every audio-language and speech-recognition solver tested; 100% human pass. Sample size and hearing-impaired users not addressed in the abstract. | 2026-11-01 | coming |
| [Maleki et al., "Human Challenge Oracle"](https://arxiv.org/abs/2601.03923) | 2026-01 | arXiv | Time-bound human effort | Cost grows linearly with the number of fake identities kept per time window. | 2026-11-01 | coming |
| [Liu, Luo, Cui, Shang, Zhao, Shen, "Next-Gen CAPTCHAs"](https://arxiv.org/abs/2602.09012) | 2026-02 | arXiv; ICML 2026 per its repository (MBZUAI) | Generated "cognitive gap" puzzles | 519 puzzles in 27 families from an open generator; agents 0.9–5.9% against humans' 98.8%. Also reports that frontier models now reach 90% on Open CaptchaWorld's "Bingo". Hardest puzzles took models 16–77 minutes. | 2026-11-01 | coming |
| [ThermoCAPTCHA](https://arxiv.org/abs/2603.05915) | 2026-03 | arXiv (Xiali Hei's group) | Hardware signal | Thermal-camera check; 50 participants, including visually impaired people. One of very few 2025–26 designs with any disability evaluation. | 2026-11-01 | coming |
| [Xu, Li et al., "aCAPTCHA"](https://arxiv.org/abs/2603.07116) and ["Proof-of-Agentness"](https://arxiv.org/abs/2610.35288) | 2026-03; 2026-10 | arXiv | Inverse: prove you are an agent | A timing threshold admits agents: 8 language models 96.5% at about 1,647 tokens; an approved study with 12 humans, 95.8% classification. | 2026-11-01 | coming |
| [Chong, "Perceptual Gaps"](https://arxiv.org/abs/2604.03612) | 2026-04 | arXiv | Text and audio | Strings drawn as ASCII art and questions over overlapping speech: no frontier model tested (GPT 5.2, Gemini 3) solved an ASCII CAPTCHA; audio near chance. | 2026-11-01 | coming |
| [Zhang, … Zhai, "MVCAP"](https://arxiv.org/abs/2609.27461) | 2026-09 | ACM Multimedia 2026 (SJTU) | Motion-defined shapes | Humans 99.6% against the best GUI agent's 16.8% (near the 1-in-6 chance level), with GPT-5.4, Claude Sonnet and Opus 4.6 and Gemini 3.1 Pro tested. Human baseline n = 30; no adaptive attack (offline frame analysis is excluded by the threat model); no photosensitivity discussion. | 2026-11-01 | coming |

## Behaviour and agent detection

| Work | Date | Venue | Type | Key claim or number | Checked | Our re-test |
|---|---|---|---|---|---|---|
| [Acien et al., "BeCAPTCHA-Mouse"](https://arxiv.org/abs/2005.00890) | 2020 | arXiv | Mouse dynamics | 93% from a single trajectory; 15,000 trajectories from 58 users; GAN-synthesised trajectories train the detector. | 2026-11-01 | coming |
| [DeAlcala et al., "BeCAPTCHA-Type"](https://arxiv.org/abs/2207.13394) | 2022-07 | CVPR Workshops 2023 | Keystroke dynamics | Synthetic keystrokes are detectable with large labelled data (136M keystrokes, 168K subjects); few-shot detection is hard. | 2026-11-01 | coming |
| [Reworr, Volkov, "LLM Agent Honeypot"](https://arxiv.org/abs/2410.13919) | 2024-10 | arXiv (Palisade Research) | Honeypot | About three months public: 8,130,731 attempts, 8 likely AI agents. | 2026-11-01 | coming |
| [Pasquini, Kornaropoulos, Ateniese, "Mantis"](https://arxiv.org/abs/2410.20911) | 2024-10 | arXiv | Decoy and counter-prompt | Decoy services plant prompts that derail an attacking LLM: above 95% effective against automated LLM attacks. | 2026-11-01 | coming |
| [DMTG](https://arxiv.org/abs/2410.18233) | 2024-10 | arXiv | Attack on detection | Entropy-controlled diffusion generates human-like mouse trajectories that cut bot-detection accuracy by 4.75–9.73%. | 2026-11-01 | coming |
| [Carlini, Nasr, remote timing attacks on LLMs](https://arxiv.org/abs/2410.17175) | 2024-10 | arXiv | Timing side channel | Encrypted traffic timing reveals topics (above 90%) on ChatGPT and Claude. Round-trip timing on an interactive check may carry model signal. | 2026-11-01 | coming |
| [Jones, Bergen, Turing test](https://arxiv.org/abs/2503.23674) | 2025-03 | arXiv | Turing test | In a three-party test, GPT-4.5 was judged human 73% of the time. Telling humans from models by conversation is already lost. | 2026-11-01 | coming |
| [Evaluation awareness](https://arxiv.org/abs/2505.23836) | 2025-05 | arXiv | Model behaviour | Frontier models tell evaluation from deployment above chance (Gemini 2.5 Pro AUC 0.83). A check that looks like a known benchmark may be recognised. | 2026-11-01 | coming |
| [Zychlinski, parallel-poisoned web](https://arxiv.org/abs/2509.00124) | 2025-09 | arXiv | Attack (cloaking) | Because agents are fingerprintable, a site can serve them different content. The same signal lets a defender route agents. | 2026-11-01 | coming |
| ["Artificial Hivemind"](https://arxiv.org/abs/2510.22954) | 2025-10 | NeurIPS 2025 Datasets and Benchmarks (oral) | Population signal | Language-model outputs repeat within a model and converge across models. Usable as a check across many submissions, not one visitor. | 2026-11-01 | coming |
| [Computational Turing test](https://arxiv.org/abs/2511.04195) | 2025-11 | arXiv | Text signal | Even after calibration, model text stays distinguishable from human text, especially in emotional tone; larger models did not help. | 2026-11-01 | coming |
| [Kumar group, LLM-assisted typing](https://arxiv.org/abs/2511.12468) | 2025-11 | IEEE TBIOM 2026 | Keystroke dynamics | Separates composing from transcribing via keystrokes. | 2026-11-01 | coming |
| [Leiva et al., human vs machine handwriting](https://arxiv.org/abs/2601.11700) | 2026-01 | arXiv | Trajectory | A raw-trajectory network against seven synthesisers: AUC 98.3%, EER 1.4%; holds with 10% of training data. | 2026-11-01 | coming |
| [Wang, Shafiq, Vekaria, "FP-Agent"](https://arxiv.org/abs/2605.01247) | 2026-05 | arXiv | Fingerprint and behaviour | On a honey site with seven AI browsing agents, typing, scroll and mouse separate agents from humans and from each other; FP-Agent flags all seven, Cloudflare flagged one. F1 0.999. | 2026-11-01 | coming |
| [Rmus, Hardy, Griffiths, Agrawal, "Process Turing Test"](https://arxiv.org/abs/2605.06524) | 2026-05 | arXiv (Proof of Human PBC and Princeton) | Process detection | A 30-task battery including CAPTCHAs: process features reach AUC 0.88 even when accuracy matches. Fine-tuning on process closes the gap when the attacker knows the full feature set; the gap returns when features are withheld or the task changes. Company research. | 2026-11-01 | coming |
| [Chocron et al., agent attribution via canaries](https://arxiv.org/abs/2605.16035) | 2026-05 | arXiv | Attribution | Task-relevant semantic canaries: removing them also removes information the task needs, so evading costs the agent. The vendor can then search its logs. | 2026-11-01 | coming |
| [Gharib, Burns, Zizi, "A-Live"](https://arxiv.org/abs/2606.05126) | 2026-06 | arXiv | Physical signal | Passive phone motion-sensor micro-motion of muscles: above 99.5%, including against a built micro-motion rig. | 2026-11-01 | coming |
| [Fayolle, … Laperdrix, Maurice, Rudametkin, "On the Internet, Nobody Knows You're an LLM Bot"](https://arxiv.org/abs/2606.30119) | 2026-06 | arXiv (Univ. Rennes, Inria, CNRS, Lille) | Fingerprinting | Honey sites behind robots.txt, CAPTCHAs, proof of work and Cloudflare: some agents got past everything, but every agent was distinguishable from humans and from each other by network, HTTP and browser fingerprints. *"Stealth and anti-detection mechanisms often increase detectability."* | 2026-11-01 | coming |
| [Xu, Malkin, "A Penny for Your Prompts"](https://arxiv.org/abs/2607.00403) | 2026-07 | SOUPS 2026 | Survey-fraud detection | LLM use by survey takers below 10% on Prolific, above 80% on MTurk; LLM answers more uniform (embedding self-similarity about 0.54 against 0.35 for humans). | 2026-11-01 | coming |
| [Noever, McKee, GPU render timing](https://arxiv.org/abs/2607.23389) | 2026-07 | arXiv (pilot) | Hardware signal | WebGL render-timing patterns: software rendering about 5× slower; 13 GPUs only. | 2026-11-01 | coming |
| [Choudhary et al., "What Does It Take to Detect an AI Agent?"](https://arxiv.org/abs/2607.26935) | 2026-07 | NE AI Agents Day 2026 | Behaviour | Two features (mouse-event rate, ratio of clicks with no cursor travel) give 100% agent recall at all five evasion levels, precision 0.994. The authors say this detects the automation tooling, not the reasoning; agents using operating-system-level input were not tested. | 2026-11-01 | coming |
| [Proof of Human, bot-detection benchmark](https://research.poh.org/bot-benchmarking/) | Not stated | Company research | Measurement | Five invisible systems × five tasks × three bot classes, 750 sessions: detection 33–87%. The authors' own product ranks first; the conflict of interest is not addressed. | 2026-11-01 | coming |
| [Proof of Human, capabilities and humanness](https://research.poh.org/capabilities-humanness/) | 2026-10-08 | Company research | Measurement | Reports detection rates from 9% to 99% across vendors. | 2026-11-01 | coming |
| [AgentMark](https://arxiv.org/abs/2601.03294) | 2026-01 | ACL 2026 | Agent watermark | Embeds a recoverable signal in an agent's planning and action choices; needs a cooperating agent. | 2026-11-01 | coming |
| [In-Context Watermarks](https://arxiv.org/abs/2505.16934) | 2025-05 | ICLR 2026 | Watermark | Watermarking through the prompt alone; relevant when a site plants text an agent reads. | 2026-11-01 | coming |

## Benchmarks and datasets

Full details, licences and status are on the [benchmarks page](@/research/benchmarks.md).

| Work | Date | Venue | Type | Key claim or number | Checked | Our re-test |
|---|---|---|---|---|---|---|
| ["Open CaptchaWorld"](https://arxiv.org/abs/2505.24878) | 2025-05 | NeurIPS 2025 Datasets and Benchmarks (MBZUAI) | Benchmark (20 types) | Best agent 40.0% (o3) against humans' 93.3%; slide, dice count, hold button and path finder solved by none; $66.4 per full o3 evaluation. The human baseline's size and recruitment are not documented. | 2026-11-01 | coming |
| [Wu et al., "MCA-Bench"](https://arxiv.org/abs/2506.05982) | 2025-06 | AAAI 2026 (oral) | Benchmark (20 types) | A fine-tuned Qwen2.5-VL-7B reaches at least 95% on 8 types and under 3% on arithmetic-selection and 3×3 jigsaw-swap. Predicts answers rather than acting in a live browser. Its human tables contradict each other. | 2026-11-01 | coming |
| [CAPTURE](https://arxiv.org/abs/2512.11323) | 2025-12 | arXiv | Benchmark | 61,464 items, 31 vendors, 25 subtypes; vision-language models perform poorly. Not a live-browser benchmark. | 2026-11-01 | coming |
| MirrorCAPTCHA (listed in [CaptchaArena's related work](https://arxiv.org/html/2609.31957v1)) | 2026 | — | Training data | 370K items, 18 types; a browser-use agent scored zero on several types. | 2026-11-01 | coming |
| [Song et al., "HLL: Humanity's Last Line of Verification"](https://arxiv.org/abs/2606.02449) | 2026-06 | arXiv (SJTU, Shanghai AI Lab) | Benchmark (10 families) | Eight frontier agents are brittle under realistic page clutter and drop further when their action traces must be valid. | 2026-11-01 | coming |
| [Zhang et al., "CaptchaArena"](https://arxiv.org/abs/2609.31957) | 2026-09 | arXiv | Benchmark and training data | 50K execution-verified puzzles, 20 types; a 9B policy reaches 71.7 Pass@1; humans 94.1 (two annotators, median 8.5 s). Training on its synthetic types transferred poorly to Halligan's replicas (0.9 to 20.0). | 2026-11-01 | coming |
| [Muse CAPTCHA Gym](https://github.com/mildchef/Muse-Captcha-Gym) | 2026-10 | Independent project | Benchmark (reCAPTCHA v2 shape) | Server-side scoring with a failure taxonomy; 278 runs, agent exact-board 43.7% on photos (1,253 attempts). Paused for cost. | 2026-11-01 | coming |

## Theory, economics and identity

| Work | Date | Venue | Type | Key claim or number | Checked | Our re-test |
|---|---|---|---|---|---|---|
| [Goodfellow et al., generative adversarial nets](https://arxiv.org/abs/1406.2661) | 2014-06 | arXiv | Theory | At the training fixed point, the discriminator outputs 1/2 everywhere. Any fixed learned detector is, in the limit, a generator's training target. | 2026-11-01 | n/a |
| [Sadasivan et al., "Can AI-Generated Text Be Reliably Detected?"](https://arxiv.org/abs/2303.11156) | 2023-03 | TMLR | Theory | The best possible detector's AUROC is bounded by the total-variation distance between human and machine distributions, reaching chance as that distance goes to zero. | 2026-11-01 | n/a |
| [Chakraborty et al.](https://arxiv.org/abs/2304.04736) | 2023-04 | arXiv | Theory | While any distance remains, detection improves with more samples. The defender's lever is more independent evidence per visitor. | 2026-11-01 | n/a |
| [Zhang et al., "Watermarks in the Sand"](https://arxiv.org/abs/2311.04378) | 2023-11 | ICML 2024 | Theory | Strong watermarks on generated output are removable by a bounded attacker with quality and perturbation oracles. "Sign the sender" lasts better than "mark the content". | 2026-11-01 | n/a |
| [Adler, Hitzig, Jain et al., "Personhood credentials"](https://arxiv.org/abs/2408.07892) | 2024-08 | arXiv (32 authors incl. OpenAI, MIT, Microsoft) | Identity | Existing countermeasures *"such as CAPTCHAs — are inadequate against sophisticated AI"*; proposes credentials that prove personhood without identity, one per person per issuer, with agents acting as verified delegates. | 2026-11-01 | n/a |
| [South et al., authenticated delegation to agents](https://arxiv.org/abs/2501.09674) | 2025-01 | arXiv | Delegation | *"authenticated, authorized, and auditable delegation"* by extending OAuth 2.0 and OpenID Connect with agent credentials. | 2026-11-01 | n/a |
| [Chan et al., "Infrastructure for AI Agents"](https://arxiv.org/abs/2501.10114) | 2025-01 | TMLR | Attribution | Shared protocols for *"Attributing an agent's actions to a particular human or other legal entity"*. | 2026-11-01 | n/a |
| [Marro, Chan, … Pentland, Torr, "Permission Manifests for Web Agents"](https://arxiv.org/abs/2601.02371) | 2025-12 | arXiv (Lightweight Agent Standards WG) | Permissions | `agent-permissions.json`: a robots.txt for interactions. | 2026-11-01 | n/a |
| [Condrey, non-identifiability of timing](https://arxiv.org/abs/2601.17280) | 2026-01 | arXiv | Theory | When only timing is observed, a human retyping machine text carries zero information about who wrote it. Process proves a human moved the input device, not that a human chose the answer. | 2026-11-01 | n/a |
| [Benjamin, Jain, Nandakumar, "BIND"](https://arxiv.org/abs/2608.04292) | 2026-08 | IJCB 2026 | Delegation | Binds biometric features to an agent identity and scope with biometric cryptosystems. Research prototype. | 2026-11-01 | n/a |
| [Chowdhury, "terms.txt"](https://arxiv.org/abs/2609.11152) | 2026-09 | Submitted to IEEE Internet Computing | Terms and payment | Machine-readable terms with Web Bot Auth signatures, signed intent, delegation tokens and HTTP 402 negotiation; 0.20–0.65 ms per request. | 2026-11-01 | n/a |

## Surveys and reference notes

| Work | Date | Venue | Type | Key claim or number | Checked | Our re-test |
|---|---|---|---|---|---|---|
| [W3C APA, "Inaccessibility of CAPTCHA"](https://www.w3.org/TR/turingtest/) | 2021-12-16 | W3C Group Draft Note | Accessibility reference | Prefers non-interactive methods; rates proof of work, WebAuthn and Privacy Pass acceptable; *"a variety of alternative challenges must be made available"*. | 2026-11-01 | n/a |
| ["CAPTCHA Types and Breaking Techniques: Design Issues, Challenges, and Future Research Directions"](https://arxiv.org/abs/2307.10239) | 2023-07 | arXiv | Survey | Types and attack techniques up to 2023. | 2026-11-01 | n/a |
| [Xu et al., survey of adversarial CAPTCHAs](https://arxiv.org/abs/2311.13233) | 2023-11 | arXiv | Survey | Taxonomy of adversarial CAPTCHAs and defences. | 2026-11-01 | n/a |
| ["User Perception of CAPTCHAs: A Comparative Study between University and Internet Users"](https://arxiv.org/abs/2405.18547) | 2024-05 | arXiv | Survey and user study | Users' views of CAPTCHA types; cites WebAIM (2017): 90% of 1,792 visually impaired respondents found audio CAPTCHAs difficult. | 2026-11-01 | n/a |
| [Otsuka, Toyoda, Leung, "AI Identity: Standards, Gaps, and Research Directions"](https://arxiv.org/abs/2604.23280) | 2026-04 | arXiv | Survey | Existing identity standards: *"none adequately address the challenge of governing nondeterministic, boundary-crossing entities"*. | 2026-11-01 | n/a |

No survey or systematisation-of-knowledge paper we found covers the agentic era (2025–26): the anti-agent designs, the collapse pattern below, proof of work, anonymous tokens and signed agents (searched 2026-11-01).

## Open-source solvers as research artefacts

Listed because they show how solvers age, not as recommendations. We link no solving service.

| Project | What | Licence, status (checked 2026-11-01) |
|---|---|---|
| [code-philia/Halligan](https://github.com/code-philia/Halligan) | The Halligan paper's solver and 26-type benchmark server | MIT; README asks users not to use it on real-world services |
| [QIN2DIM/hcaptcha-challenger](https://github.com/QIN2DIM/hcaptcha-challenger) | hCaptcha library; replaced its trained models with a general multimodal model because training took *"up to half a week"* and hCaptcha changed faster | GPL-3.0; last push 2026-08-15 |
| [dessant/buster](https://github.com/dessant/buster) | Browser extension framed as a "captcha solver extension for humans" (accessibility) | GPL-3.0; maintained since 2018 |
| [Wikidepia/hektCaptcha-extension](https://github.com/Wikidepia/hektCaptcha-extension) | Local-model hCaptcha extension | Archived 2023-12-19; tagline *"100% Free and Unsustainable"* |

## Months to collapse

*This is our summary of the literature, not a measurement.* It pairs a design, or a family of designs, with the first published report of agents passing it at 70–95%. Only the first row is the same group re-testing the same puzzle type; the others compare different papers, different instances and different models.

| Design or family | Launch | Agent success at launch | First report at 70–95% | When | Gap |
|---|---|---|---|---|---|
| Open CaptchaWorld "Bingo" ([2505.24878](https://arxiv.org/abs/2505.24878)) | 2025-05 | 0% (no model solved it) | Up to 90% for Gemini 3 Pro and GPT-5.2 at high reasoning ([Next-Gen CAPTCHAs, 2602.09012](https://arxiv.org/abs/2602.09012)) | 2026-02 | About 9 months; same group |
| Reasoning CAPTCHAs (vendor designs) | Before 2024-05 | Needed a purpose-built decomposition to reach 63.5% ([Oedipus](https://arxiv.org/abs/2405.07496)) | Up to 93.2% across six vendors ([ViPer](https://arxiv.org/abs/2601.06461)) | 2026-01 | About 20 months between the papers; different CAPTCHA sets |
| Adversarial image noise ([2409.05558](https://arxiv.org/abs/2409.05558), [2506.10685](https://arxiv.org/abs/2506.10685)) | 2024-09; 2025-06 | Accuracy drops of 50–80 points against the models tested | A learning solver recovers in every monthly round of a simulated year ([Salman & Bicakci](https://arxiv.org/abs/2609.02393)) | 2026-09 | One simulated round; not a test of the exact published defences |
| reCAPTCHA v2 image grids (deployed) | Deployed | — | 100% with a trained detector ([Plesner et al.](https://arxiv.org/abs/2409.08831)); 92.6% of real sessions zero-shot ([Robot Visions](https://arxiv.org/abs/2609.18518)) | 2024-09; 2026-09 | Not a design paper; shown for scale |
| COGNITION's hardened type ([2512.02318](https://arxiv.org/abs/2512.02318)) | 2025-12 | Cut from above 95% to 0% | None yet. Agent papers still list exact counting among failures ([CaptchaAgent](https://arxiv.org/abs/2610.12866), 2026-10) | — | Holding after about 11 months (to 2026-11); no adaptive test found |
| IllusionCAPTCHA ([2502.05461](https://arxiv.org/abs/2502.05461)) | 2025-02 | 0% for GPT-4o and Gemini 1.5 Pro | No re-test found | — | Unknown |
| Spatial CAPTCHA ([2510.03863](https://arxiv.org/abs/2510.03863)) | 2025-10 | 31.0% best model | No re-test found | — | Unknown |
| Next-Gen CAPTCHAs' 27 families ([2602.09012](https://arxiv.org/abs/2602.09012)) | 2026-02 | 0.9–5.9% | No re-test found; the generator is open, so attackers can train on it | — | Unknown |
| MVCAP ([2609.27461](https://arxiv.org/abs/2609.27461)) | 2026-09 | 16.8% best agent | No re-test found; motion tracking broke moving-object CAPTCHAs in 2012 ([Xu et al.](https://www.usenix.org/biblio/security-and-usability-challenges-moving-object-captchas-decoding-codewords-motion)) | — | Unknown |

Where a later report exists, the gap runs from one simulated round to about 20 months, and the one same-group re-test took about 9 months. Where no re-test exists, the design's lifetime is simply unknown, which is the problem. Every check date above is 2026-11-01.

A community example of the same pattern: a motion-based "AI-proof" CAPTCHA posted on r/webdev on 2026-07-15 was answered with a working attack in the comments (*"a simple dense optical flow between two frames gave a really clear result"*), and the top reply was *"Neat concept but an accessibility nightmare"* ([thread](https://www.reddit.com/r/webdev/comments/1uxfzav/), checked 2026-11-01).

We plan to replace this table with measured numbers: see [the CAPTCHA half-life](@/research/half-life.md).
