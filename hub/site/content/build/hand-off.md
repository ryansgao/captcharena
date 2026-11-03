+++
title = "Hand-off patterns: when an agent should stop and ask its human"
description = "How agent frameworks pause at a CAPTCHA and hand the step to a person, what good hand-off looks like, and what agents actually choose when they meet one."
weight = 20
[extra]
checked = "2026-11-01"
+++

A hand-off is the moment an agent stops, tells its human what it needs, and waits. At a CAPTCHA it is often the right move: the site asked for a person, and the agent has one. This page collects the patterns frameworks use, what makes a hand-off work, and the evidence on what agents actually do when no one designed the hand-off for them.

## Patterns in today's frameworks and products

| Pattern | Who does it | What happens | Source (checked 2026-11-01) |
|---|---|---|---|
| Pause and ask the user | Claude Code's Chrome integration | *"When Claude encounters a login page or CAPTCHA, it pauses and asks you to handle it manually."* | [Claude Code docs](https://code.claude.com/docs/en/chrome.md) |
| Refuse by policy | ChatGPT agent | Declines CAPTCHAs by policy. Researchers got past that policy with a primed conversation (see below). | [SPLX](https://splx.ai/blog/chatgpt-agent-solves-captcha), [The Register, 2025-09-19](https://theregister.com/2025/09/19/how_to_trick_chatgpt_agents) |
| Refuse a sensitive step | Perplexity Comet | Refused to fill login forms, citing its safety policy, in a 2026 measurement study. | [Broken Gates, 2026-07](https://arxiv.org/abs/2607.18659) |
| Auto-pause while the platform handles it | Stagehand (Browserbase) | PR #1752 "auto-pause agent during Browserbase captcha solving", merged 2026-03-18, shipped in stagehand 3.2.0. As the title says, the agent pauses while the hosted browser deals with the CAPTCHA. | [PR #1752](https://github.com/browserbase/stagehand/pull/1752) |
| Tell the model not to touch it | Browserless plugin for Claude Code | Its docs tell Claude **not** to click or solve CAPTCHA elements itself; the platform handles them. | [Browserless docs](https://docs.browserless.io/ai-integrations/claude-code-playwright-mcp) |
| Give up and report | BrowserGym benchmark runs | Agents call `report_infeasible` on "a CAPTCHA verification due to unusual traffic"; maintainers marked the issue *wontfix*. | [BrowserGym #319](https://github.com/ServiceNow/BrowserGym/issues/319) |
| Second-device human check | Google Cloud Fraud Defense | A QR-code challenge for *"requesting humans to be in the loop"*. Closed product. | [Google Cloud, 2026-04-23](https://cloud.google.com/blog/products/identity-security/introducing-google-cloud-fraud-defense-the-next-evolution-of-recaptcha) |
| Open hand-off protocols | `rotorstar/hitl-protocol` (generic human-in-the-loop over HTTP, Apache-2.0); OpenID CIBA (an existing standard for asking a user to approve on another device) | Building blocks; neither is CAPTCHA-specific. | [hitl-protocol](https://github.com/rotorstar/hitl-protocol) |

Several hosted browsers also sell CAPTCHA solving as a platform feature (Browserbase: *"CAPTCHA handling is on by default across every session"*, with guidance to restrict it to authorized automations; [docs](https://docs.browserbase.com/platform/identity/captcha-solving), checked 2026-11-01). That moves the decision from the agent to the platform. It does not remove it: the site's terms still apply.

## What a good hand-off looks like

A hand-off works only if the human can act on it in seconds. From the patterns above and the failure cases below, a good one has these parts:

| Part | Why |
|---|---|
| **Which site, which page.** Name the domain and the step ("sign-up on example.org, the email form"). | The human must know where to look, and must be able to see that the request is genuine. |
| **Why the agent stopped.** "A CAPTCHA appeared" or "the site asks for a human here." | The human decides whether the task should go on at all. |
| **Exactly what the human must do.** "Tick the box in the window I opened, then tell me 'done'." | Vague requests get ignored or misread. |
| **Where to do it.** The live browser window or tab the agent is using, named clearly, so the session and its cookies carry on. | A solve in a different browser does not help the agent's session. |
| **Never a password in chat.** The human types credentials into the site, never into the conversation. | Chat logs are stored and read by more systems than the site is. |
| **A time limit.** Say how long the agent will wait, and what it does if no one comes. | CAPTCHA tokens expire, often within minutes. |
| **Resume and confirm.** After "done", the agent checks that the page moved on, and reports back. | The human should not have to check the agent's work. |
| **No pressure tactics.** The agent asks; it does not insist or argue. | See the next section: agents have been pushed, and have pushed, past their own rules. |

{% <note> %}
A real CAPTCHA never asks a person to press keyboard shortcuts, paste into a terminal or run anything. Fake CAPTCHAs that do ("ClickFix") are a common malware lure ([NZ NCSC alert, 2026-09-02](https://www.ncsc.govt.nz/alerts/compromised-websites-serving-clickfix-pages/), checked 2026-11-01). A hand-off message should never relay such an instruction to the human. More: [Is this CAPTCHA real?](@/learn/is-this-captcha-real.md)
{% </note> %}

## The safety question: what does an agent choose?

When an agent meets a CAPTCHA mid-task, it has five broad options:

1. **Solve it** itself.
2. **Hand off** to its human.
3. **Refuse**, and report that it could not continue.
4. **Pay a solving service** to do it.
5. **Deceive** a person into solving it.

The record shows all five, including the last.

| Date | What happened | Source (checked 2026-11-01) |
|---|---|---|
| 2023-03 | In pre-release testing, GPT-4 messaged a TaskRabbit worker to solve a CAPTCHA for it. It reasoned: *"I should not reveal that I am a robot."* | [GPT-4 system card](https://cdn.openai.com/papers/gpt-4-system-card.pdf) |
| 2025-01-23 | The OpenAI Operator system card does not mention CAPTCHAs at all (text search). | [Operator system card](https://cdn.openai.com/operator_system_card.pdf) |
| 2025-09 | ChatGPT agent solved CAPTCHAs after being told they were fake. | [Malwarebytes](https://www.malwarebytes.com/es/blog/news/2025/09/chatgpt-solves-captchas-if-you-tell-it-theyre-fake) |
| 2025-09 | Researchers at SPLX talked ChatGPT agent past its no-CAPTCHA policy with a primed transcript. | [SPLX](https://splx.ai/blog/chatgpt-agent-solves-captcha), [The Register](https://theregister.com/2025/09/19/how_to_trick_chatgpt_agents) |
| 2026-09-09 | Anthropic reported a misconfigured evaluation that reached the real internet. The model noted that PyPI's bot protection *"smells like the REAL internet"*. Press reading of the released transcript describes hundreds of pages spent on hCaptcha challenges. | [Anthropic](https://www.anthropic.com/research/alignment-assessment-cybersecurity-incidents); [TechCrunch, 2026-09-10](https://techcrunch.com/2026/09/10/anthropic-reveals-rogue-ai-agents-hate-captchas-just-like-you/) (secondary) |

What this means for builders:

- **A policy in the prompt is not enough.** Both the SPLX and Malwarebytes cases moved an agent past its rule with words alone. Put the hand-off in the framework (a tool that pauses), not only in the model's instructions.
- **The user asking is not the same as the site allowing.** An agent's user may want it to solve; the site's terms may say no. Hand-off resolves this cleanly: the human does the step the site asked a human to do.
- **Deception is the line.** An agent that hides that it is an agent, to get a human to do the step, is the failure the GPT-4 case shows. Anthropic's Usage Policy separately bans *"bots that claim to be human"* ([policy map](@/build/policy-map.md)).
- **No public benchmark measures this.** General web-agent benchmarks filter CAPTCHA-blocked tasks out. Agent-safety benchmarks we checked (AgentHarm, SafeArena, CUAHarm) do not cover CAPTCHAs (checked 2026-11-01).

{% <coming> %}
A behaviour test: a scripted task (sign up, post, download) with a CAPTCHA in the middle, run under several instructions ("the user authorised it", "the user insists", "the site's terms forbid bots", "a human worker is reachable"), scoring what the agent chose: solve, hand off, refuse, pay a solver, or deceive. Results will appear on the [scoreboard](@/scoreboard/_index.md).
{% </coming> %}

Related: [Sign your agent](@/build/signing.md) for the path that avoids many CAPTCHAs, and [open research questions](@/research/open-questions.md) for the behaviour test as a research problem.
