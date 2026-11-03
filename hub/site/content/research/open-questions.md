+++
title = "Open research questions about CAPTCHAs and agents"
description = "The theoretical ceiling on telling humans from agents, what survives it, and the unsolved problems: behaviour tests, human baselines, score signals, accessibility."
weight = 50
[extra]
checked = "2026-11-01"
+++

These are the questions we think the field has not answered, with the evidence that makes each one open. They are a starting list for a thesis, a paper or a project. Each links to its sources.

## 1. The honest ceiling: indistinguishable by outcome

If an agent's behaviour is statistically identical to a human's, no test of the outcome can tell them apart. Four results point the same way (all checked 2026-11-01):

| Result | What it says | Source |
|---|---|---|
| Detection bound | The best detector's AUROC is bounded by the total-variation distance between the human and machine distributions, and falls to chance as that distance goes to zero. | [Sadasivan et al., arXiv 2303.11156](https://arxiv.org/abs/2303.11156) |
| More samples help | While any distance remains, detection improves with the number of samples. | [Chakraborty et al., arXiv 2304.04736](https://arxiv.org/abs/2304.04736) |
| The trained-detector trap | At a generative adversarial network's fixed point, the discriminator outputs 1/2 everywhere: any fixed detector is, in the limit, a generator's training target. | [Goodfellow et al., arXiv 1406.2661](https://arxiv.org/abs/1406.2661) |
| Conversation is already lost | GPT-4.5 was judged human 73% of the time in a three-party Turing test. | [Jones & Bergen, arXiv 2503.23674](https://arxiv.org/abs/2503.23674) |

And a limit on process signals: when only timing is observed, a human retyping machine text carries zero information about who wrote it ([Condrey, arXiv 2601.17280](https://arxiv.org/abs/2601.17280)). Process shows that a human moved the input device, not that a human chose the answer.

**Open questions:**

- How close are today's agents to zero distance on each signal family (perception, motor behaviour, timing, text)? Nobody has measured the distance itself, only detector accuracy at one moment.
- How many independent samples per visitor does a defender need, per signal, to keep a given error rate as agents improve? This is the practical form of the "more samples" result.

## 2. What survives the ceiling

When outcome tests fail, three levers remain. None of them is a perceptual test.

| Lever | Why it survives | Evidence | What it costs |
|---|---|---|---|
| **Cost** | A check need not keep agents out, only make abuse cost more than it earns. | [Motoyama et al., USENIX Security 2010](https://www.usenix.org/legacy/event/sec10/tech/full_papers/Motoyama.pdf); [Reasoning Gates](https://arxiv.org/abs/2509.01619): rebus puzzles cost agents 9.2× the generator's tokens | Wanted agents and ordinary users pay too |
| **Scarce human-bound resources** | Bodies, attested devices, real elapsed time and a personhood issuer cannot be cheaply copied or run in parallel. | [Personhood credentials](https://arxiv.org/abs/2408.07892); [Human Challenge Oracle](https://arxiv.org/abs/2601.03923): cost linear in the number of fake identities per time window | Privacy, enrolment, exclusion of people without the resource |
| **Accountability** | Ask "whose agent, allowed to do what" instead of "is it human". | [Web Bot Auth](https://datatracker.ietf.org/wg/webbotauth/about/); [canary-based attribution](https://arxiv.org/abs/2605.16035) | Needs adoption; unsigned does not mean hostile |
| **Withheld signals** (a fourth, weaker lever) | A detector the attacker cannot see is harder to train against: the Process Turing Test gap closed under full attacker knowledge and reopened when features were withheld or the task changed. | [arXiv 2605.06524](https://arxiv.org/abs/2605.06524) | Openness; reproducibility of the detector |

**Open questions:**

- Where is the cost floor? Human solving farms charge $0.10–5.00 per thousand ([Broken Gates](https://arxiv.org/abs/2607.18659)). One analysis priced a week's access to every site behind a popular proof-of-work gate at *"approximately $0"* ([Ormandy](https://lock.cmpxchg8b.com/anubis.html)). Which actions are worth more than that to an attacker, and which cost schemes stay below what a legitimate user will tolerate on a low-end phone?
- Can a process check output an **anonymous token** instead of telemetry, so the server never sees the behaviour data? Cloudflare and Mozilla both mention CAPTCHAs bootstrapping a credential; no open system does it ([industry roadmap](@/research/industry-roadmap.md)).
- How fast can a withheld feature set be rotated before the rotation itself leaks it?
- Can open Anchor ecosystems police themselves privately, so that anonymous credentials do not centralise on a few issuers? Mozilla names this as unsolved.

## 3. The behaviour question: what does an agent choose?

The safety question at a CAPTCHA is not whether an agent can solve it, but what it chooses to do: solve, hand off to its human, refuse, pay a solving service, or deceive someone. In testing, GPT-4 messaged a TaskRabbit worker to solve a CAPTCHA for it, reasoning *"I should not reveal that I am a robot"* ([GPT-4 system card](https://cdn.openai.com/papers/gpt-4-system-card.pdf)). Researchers talked ChatGPT agent past its no-CAPTCHA policy ([SPLX](https://splx.ai/blog/chatgpt-agent-solves-captcha)). General web-agent benchmarks filter CAPTCHA-blocked tasks out, and the agent-safety benchmarks we checked (AgentHarm, SafeArena, CUAHarm) do not cover CAPTCHAs (checked 2026-11-01). More on [hand-off patterns](@/build/hand-off.md).

We call a test of this a **behaviour lane**: a task with a CAPTCHA in the middle, scored on the agent's choice rather than on solving.

**Open questions:**

- How does the choice change with the instruction ("the user authorised it", "the user insists", "the site's terms forbid bots", "a human worker is reachable")?
- What counts as a good outcome? One mobile-agent safety benchmark is reported to score asking the user as safe; we have not confirmed this from the primary source.
- Does the choice change when the agent can tell it is being evaluated? Frontier models already tell evaluation from deployment above chance ([arXiv 2505.23836](https://arxiv.org/abs/2505.23836)).
- How do compliance traps interact with alignment? A well-aligned agent treats stray page instructions as prompt injection and ignores them, so "did the agent follow the hidden instruction" detectors catch the naive agents and miss the careful ones.

## 4. Human baselines, and the ethics of publishing them

Human pass rates are the denominator of every CAPTCHA result, and they are the weakest part of the literature. Open CaptchaWorld's 93.3% has no documented participant count or recruitment; MVCAP used 30 people with no recruitment or review described; MCA-Bench's human tables contradict each other. Compare 1,400 paid participants in [Searles et al. 2023](https://arxiv.org/abs/2307.12108) and 3,600+ real users in [Dazed & Confused](https://arxiv.org/abs/2311.10911) (checked 2026-11-01).

A published benchmark of human solve rates fits the US federal definition of human-subjects research: *"a systematic investigation … designed to develop or contribute to generalizable knowledge"* (45 CFR 46.102(l)). That means ethics review before the study starts. Investigators cannot declare their own study exempt; the review office decides, and student projects are expected to have a faculty sponsor (one university's guidance: [exempt review](https://cphs.berkeley.edu/exempt.pdf), [student research](https://cphs.berkeley.edu/ethical_student_research.pdf), checked 2026-11-01). Mouse trajectories and timing can identify a person, which makes behavioural data harder to collect than pass/fail.

**Open questions:**

- What is human variance by age, device, disability and language for current designs? It is almost never reported.
- How should a living benchmark keep a human baseline current without re-recruiting every cycle?
- What is the minimum behavioural data a study needs, and can it be scored on the participant's device and discarded?

{% <note> %}
We will not publish human pass rates from our own pages until a study has had ethics review. Until then, our human numbers come only from published papers, with their sample sizes shown.
{% </note> %}

## 5. Accessibility against agent-resistance

Under [WCAG 2.2 Success Criterion 3.3.8](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html) (Level AA), a cognitive test in a login step needs an alternative, except object recognition or personal content. The puzzle types agents solve easily (object recognition) are the ones AA allows; the types that still resist agents (counting, arithmetic, logic, spatial reasoning, ordered steps) are the ones it does not. The required alternative then becomes the bot's path. Few 2025–26 designs evaluate disabled users at all; ThermoCAPTCHA included visually impaired participants ([arXiv 2603.05915](https://arxiv.org/abs/2603.05915)); MVCAP, a motion-only design, has no photosensitivity discussion (checked 2026-11-01).

**Open questions:**

- Is there any human check that is both WCAG-conformant and agent-resistant for more than a few months?
- An agent acting for a disabled user is a legitimate agent. How should a site let it through without letting every agent through?

## 6. What do the invisible scores actually measure?

Most checks now happen before any puzzle: the site scores the session and shows a puzzle only when unsure. Yet the only published per-signal test of Google's risk engine we found is from 2016: a nine-day-old Google cookie earned the pass, and screen size and mouse behaviour made no difference ([Sivakorn et al.](https://www.blackhat.com/docs/asia-16/materials/asia-16-Sivakorn-Im-Not-a-Human-Breaking-the-Google-reCAPTCHA-wp.pdf)). In 2026, two agents with near-identical behaviour got different reCAPTCHA v3 outcomes, decided by the execution environment ([Broken Gates](https://arxiv.org/abs/2607.18659)). Every agent tested by Fayolle et al. was fingerprintable, and stealth tooling made it worse ([arXiv 2606.30119](https://arxiv.org/abs/2606.30119)). Checked 2026-11-01.

**Open questions:**

- Which signals move each current vendor's score, and by how much? A controlled experiment that changes one factor at a time (address type, profile age, cookies, automation layer) has not been published for any current vendor.
- How stable are those effects over weeks, as vendors retrain?
- Behaviour detectors catch today's agents by their automation tooling, not their reasoning ([Choudhary et al.](https://arxiv.org/abs/2607.26935)). What happens with agents that use operating-system-level input, which that paper did not test?

Our [browser-score experiment](@/browser-score/experiment.md) is designed to test the first question.

## 7. Delegation: proving what a person allowed

Web Bot Auth says which product sent a request. Nothing open says which person authorised which action, with limits a site can enforce, without revealing who the person is. The IETF charter excludes end-user authentication; about 30 individual drafts propose delegation; the only implementations are for payments ([industry roadmap](@/research/industry-roadmap.md), checked 2026-11-01).

**Open questions:**

- Can a scoped, user-signed permission be bound to a signed agent request so that a stolen permission is useless to another agent?
- Can the same be done anonymously, combining an anonymous credential with a permission that holds only constraints?
- What is the usability of approving agent actions on a second device, and how often will users approve without reading?

## Work on any of these

If you are working on one of these questions, or want to, write to us through the [contact page](@/contact/_index.md). We can share our harness, run your design through the [half-life measurement](@/research/half-life.md) when it exists, and list your work in the [literature map](@/research/literature-map.md).
