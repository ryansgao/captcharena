+++
title = "Build: what an AI agent should do when it meets a CAPTCHA"
description = "For agent and framework developers: when a CAPTCHA appears, whether to proceed at all, and the three legitimate paths: sign, ask the site, hand off."
sort_by = "weight"
[extra]
checked = "2026-11-01"
+++

A CAPTCHA is a site saying "I want a person here." An agent that meets one should first ask whether it is wanted on that page, before it asks how to get past. This section is for people who build AI agents, browser-automation frameworks and hosted browsers. It covers the legitimate paths, and the rules and test pages that apply.

## Ask first: is the agent wanted here?

A CAPTCHA does not tell the agent why it appeared. It can mean any of these:

| What the CAPTCHA means | What it implies for the agent |
|---|---|
| The site does not want automated visitors on this page at all. | Stop. Solving it goes against the site's wishes, and often its terms. |
| The site cannot tell a wanted agent from an unwanted one. | Identify the agent, so the site can decide. |
| The site wants a human decision here (a sign-up, a payment, a post). | Hand the step to the agent's human. |
| The visitor's address or browser looks risky, whoever is behind it. | Hand off, or try again later from a normal setup. Do not disguise the agent. |

Industry has moved to the same view. Cloudflare's framing: *"There are wanted bots and there are unwanted humans"* ([Cloudflare, 2026-04-21](https://blog.cloudflare.com/past-bots-and-humans/), checked 2026-11-01). hCaptcha's: *"Legitimate agents should clearly identify themselves"* ([hCaptcha, 2026-02-23](https://www.hcaptcha.com/post/hcaptcha-captchas-are-highly-effective-against-bots-and-agents-in-2026), checked 2026-11-01). Anthropic's crawler page says *"we will not attempt to bypass CAPTCHAs for the sites we crawl"* ([Anthropic support page, 2026-04-07](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler), checked 2026-11-01).

## The three legitimate paths

| Path | What it means | Where it works today | Page |
|---|---|---|---|
| **Sign** | The agent signs its requests with a published key (Web Bot Auth), so sites and bot-defence vendors can verify which product sent them and apply a policy instead of a puzzle. | Verified by Cloudflare, Google, HUMAN, Akamai, Fingerprint and Arkose; used by ChatGPT agent, Google-Agent and Browserbase (checked 2026-11-01). | [Sign your agent](@/build/signing.md) |
| **Ask the site** | Register the agent with the site or its bot-defence vendor, use the site's API, or follow its published rules for bots. | Cloudflare's verified-bot programme takes submissions through a form ([Cloudflare docs](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/), checked 2026-11-03). Many sites offer an API. | [Sign your agent](@/build/signing.md) |
| **Hand off** | Pause, tell the human which site and why, let them complete the step, then continue. | Claude Code's Chrome integration pauses at a CAPTCHA by design; Stagehand pauses the agent while its hosted browser handles a CAPTCHA (sources on the page). | [Hand-off patterns](@/build/hand-off.md) |

Signing says *which software* is acting. It does not say *which person* allowed *which action*. That gap is open, and the [industry roadmap](@/research/industry-roadmap.md) tracks who is working on it.

## What is not on the list

- **Solving the puzzle by default.** Solving can be within the rules: on your own site, with the site owner's permission, or in research on your own pages. As a default for an agent on someone else's site, it runs into vendor terms and model-provider policies. Some terms forbid it outright: hCaptcha's do ([policy map](@/build/policy-map.md)).
- **Paying a solving service.** These services are largely human workers paid per solve. Anti-Captcha states that *"100% of captchas are solved by human workers"* ([anti-captcha.com](https://anti-captcha.com/), checked 2026-11-01). We do not list or recommend them.
- **Disguising the agent.** Stealth tooling tends to make agents *more* detectable, not less: *"Stealth and anti-detection mechanisms often increase detectability"* ([Fayolle et al., 2026](https://arxiv.org/abs/2606.30119), checked 2026-11-01). It also removes the one thing that makes an agent trustworthy: that it is accountable.

{% <note> %}
None of this section is legal advice. Terms and policies change often; each fact carries the date we checked it.
{% </note> %}

Background for this section: [How AI agents fare against CAPTCHAs](@/learn/ai-agents.md) and [What still works](@/learn/what-lasts.md).
