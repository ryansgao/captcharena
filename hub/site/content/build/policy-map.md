+++
title = "Policy and legal map for agents that meet CAPTCHAs"
description = "Vendor terms, AI-provider policies, GitHub rules and US and EU law that apply when an AI agent meets a CAPTCHA, each dated and linked to its source."
weight = 30
[extra]
checked = "2026-11-01"
+++

Which rules apply when an AI agent passes, hands off or refuses a CAPTCHA? Four layers: the CAPTCHA vendor's terms, the AI provider's usage policy, the code host's rules (for anyone publishing solver code), and the law. This page maps each one, with the date we read it.

{% <note> %}
**This is not legal advice.** It is a map of published texts, read on the dates shown, by people who are not lawyers. Terms change often; read the current text yourself, and ask a lawyer about your own situation. Laws outside the US and the EU were not researched.
{% </note> %}

## At a glance

| Layer | Clear ban on agents passing CAPTCHAs? | Strongest text |
|---|---|---|
| hCaptcha terms | **Yes** | Bans bots, scripts and *"any other form of artificial intelligence"* attempting to pass challenges |
| Google and Cloudflare terms | **No explicit clause; a grey area** | General "do not circumvent limitations" language |
| Anthropic Usage Policy | **No CAPTCHA clause; close to the line** | Bans circumventing *"the guardrails or terms of other platforms"* |
| GitHub (for solver code) | No | No CAPTCHA clause; takedowns target copied vendor code |
| US law | Only for ticketing | BOTS Act 2016 |
| EU law | No CAPTCHA rule found | AI Act disclosure duty from 2026-08-02 |

## CAPTCHA and bot-defence vendors

| Rule | What it says | Applies to | Checked | Source |
|---|---|---|---|---|
| **hCaptcha Master Terms** (last updated 2025-11-17) | You *"WILL NOT: … perform any task with the use of Internet bots, web robots, bots, scripts, or any other form of artificial intelligence or otherwise attempt to pass challenges"*. Also bans using *"artificial intelligence to complete any portion of any task … which requires human intelligence"*, access *"through any proxy web server or other device designed to obfuscate your true location"*, and reverse engineering. Bot scores and detection details are confidential. | Anyone using the service, including a site owner testing on their own site. A breach is a contract matter, not a crime. | 2026-11-01 | [hcaptcha.com/terms](https://www.hcaptcha.com/terms) |
| **Google APIs Terms** (cover reCAPTCHA) | You may not *"Interfere with or disrupt the APIs"*, reverse engineer them, and *"will not attempt to circumvent"* documented limits. No clause names automated solving. | Developers using Google APIs | 2026-11-01 | [developers.google.com/terms](https://developers.google.com/terms) |
| **Cloudflare Website and Online Services Terms** §7 | *"You may not exceed or circumvent, or try to exceed or circumvent, limitations on the Websites or Online Services"*. Separately, service-specific terms forbid using *"Botnet Threat Data for the purpose of: (i) benchmarking or competitive analysis"* (threat data, not Turnstile). | Users of Cloudflare services | 2026-11-01 | [website terms](https://www.cloudflare.com/website-terms/), [service-specific terms](https://www.cloudflare.com/service-specific-terms-application-services/) |
| **Arkose Labs** | Its terms-of-service URL returned 404. | — | 2026-11-01 | Not checked further |

Reading: for Google and Cloudflare, an agent solving a widget is not named as a breach; whether "circumvent" covers it is untested. For hCaptcha, an AI agent passing a challenge is a breach as written, even on your own site, unless hCaptcha agrees in writing.

## AI providers

| Rule | What it says | Checked | Source |
|---|---|---|---|
| **Anthropic Usage Policy**, effective 2026-11-12 | No CAPTCHA mention, but bans: *"Engage in actions or behaviors that circumvent the guardrails or terms of other platforms or services"*; *"Bypass security controls such as authentication systems, endpoint protection, or monitoring tools without authorization"*; *"Utilize automation in account creation or to engage in spammy behavior"*; *"bots that claim to be human"*. On agents: *"Agentic use cases must comply with the Usage Policy"*, and users are responsible for agents they build or deploy, *"including actions those agents take through tools, browsers, or connected systems"*. | 2026-11-01 | [anthropic.com/legal/aup](https://www.anthropic.com/legal/aup) |
| **Anthropic crawler page** | *"we will not attempt to bypass CAPTCHAs for the sites we crawl"* (dated 2026-04-07). | 2026-11-01 | [Anthropic support](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler) |
| **OpenAI, ChatGPT agent** | ChatGPT agent declines CAPTCHAs by policy (reported by researchers who got past it). The Operator system card (2025-01-23) does not mention CAPTCHAs. OpenAI's general usage policies were **not** reviewed for this page. | 2026-11-01 | [SPLX](https://splx.ai/blog/chatgpt-agent-solves-captcha), [Operator system card](https://cdn.openai.com/operator_system_card.pdf) |

Reading: under the Anthropic policy, the person who deploys an agent answers for what it does in a browser. If a site's terms forbid bots, an agent that solves its CAPTCHA anyway is close to "circumvent the terms of other platforms". Hand-off keeps the human in the step the site reserved for humans ([hand-off patterns](@/build/hand-off.md)).

## Code hosting: GitHub

| Rule | What it says | Checked | Source |
|---|---|---|---|
| **GitHub Acceptable Use Policies** | The words "circumvention", "CAPTCHA" and "anti-bot" do not appear. Nearest clauses: no *"software for bypassing checks for product licensing keys"*; no *"automated inauthentic activity"* on GitHub itself; no content that *"directly supports unlawful active attack or malware campaigns"*, with a dual-use carve-out. | 2026-11-01 | [GitHub AUP](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) |
| **GitHub DMCA policy** | *"GitHub will review circumvention claims closely"*; where unsure, *"we will err on the side of the developer, and leave the content up"*; owners are contacted first. | 2026-11-01 | [DMCA Takedown Policy](https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy) |
| **DMCA notice pattern** (GitHub's public notice archive, 2011–2026) | Anti-bot takedowns that succeeded were based on copyright in the **vendor's own JavaScript** copied into the repo (Cloudflare 2025-05-20; Kasada, six notices 2025-03 to 2026-05; Imperva 2023-04; Akamai 2018–2021). Anti-circumvention (§1201) claims against bypass *techniques* were rejected (MarineTraffic 2026-03-25, a dictionary site 2026-02-05, piracy tools 2026-04-13). No well-known open solver appeared in any notice. | 2026-11-01 | [github/dmca](https://github.com/github/dmca), e.g. [2025-05-20 Cloudflare notice](https://github.com/github/dmca/blob/master/2025/05/2025-05-20-cloudfare.md) |

Reading: for researchers publishing CAPTCHA work, the line GitHub enforces is copied vendor code (scripts, deobfuscated payloads), and plausibly scraped vendor challenge images. Open solver projects that died, died of upkeep, not law.

## United States law

| Rule | What it says | Checked | Source |
|---|---|---|---|
| **Computer Fraud and Abuse Act** after *Van Buren* (2021) | The Supreme Court's "gates-up-or-down" reading: misusing access you have is not a violation. Whether a CAPTCHA is a "gate" is open. | 2026-11-01 | [Apify summary](https://blog.apify.com/van-buren-v-united-states/), [Cooley](https://investigations.cooley.com/?p=849) |
| *hiQ v. LinkedIn* (9th Cir., 2022, on remand) | Scraping publicly available data is not "without authorization"; a cease-and-desist alone does not withdraw authorization for a public system. Whether code-based anti-scraping measures are "gates" was left open. One scraping vendor's reading that CAPTCHAs are "selective denial" was not checked against the opinion. | 2026-11-01 | [Haynes Boone](https://www.haynesboone.com/news/publications/the-shifting-legal-landscape-surrounding-web-scraping) |
| **Wiseguy Tickets** (D.N.J., 2010) | Operators who used "CAPTCHA bots" to beat ticket-purchase limits were indicted on illegal-access and wire-fraud counts; outcome probation and $1.2 M forfeiture. The operators were prosecuted, in a fraud context, not a tool author. | 2026-11-01 | [FBI press release](https://www.fbi.gov/newark/press-releases/2010/nk030110.htm), [Pollstar](https://news.pollstar.com/2011/06/10/wiseguys-get-probation-2/) |
| **BOTS Act** (2016) | Makes it unlawful to *"circumvent a security measure, access control system, or other technological control"* on ticket-sale websites. An FTC complaint lists *"CAPTCHA bypass or solving services"* among the methods. **Ticketing is the one US domain with a statute that names this.** | 2026-11-01 | [FTC complaint (DOJ PDF)](https://www.justice.gov/opa/press-release/file/1358906/download) |
| Lawsuits against solver authors or services | None found in one search (not a docket review). | 2026-11-01 | — |

## European Union

| Rule | What it says | Checked | Source |
|---|---|---|---|
| **EU AI Act, Article 50** (applies from 2026-08-02) | Systems that interact with people must make their AI nature clear *"unless this is obvious"*; generated outputs must be marked as artificially generated. Relevant to an agent that hides that it is an agent. | 2026-11-01 | [Article 50 text](https://artificialintelligenceact.eu/article/50/) |
| **WCAG 2.2 SC 3.3.8** and the **European Accessibility Act** | For sites, not agents: a login step may not rely on a cognitive puzzle without an alternative (object recognition is allowed at Level AA). The EAA gives accessibility legal weight in the EU; one CAPTCHA vendor markets compliance with it. | 2026-11-01 | [W3C Understanding SC 3.3.8](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html) |
| EU or member-state computer-misuse law applied to CAPTCHAs | Not researched. | — | — |

## What this means in practice

- **On someone else's site:** prefer [signing](@/build/signing.md) or [hand-off](@/build/hand-off.md). Read the site's own terms; they bind your users too.
- **On your own site, with real widgets:** humans solving them is intended use. Agents solving them is a grey area for Google and Cloudflare and a written breach for hCaptcha without permission. Ask the vendor first.
- **In ticketing:** do not automate CAPTCHAs at all. That is the one place US law names it.
- **Publishing research code:** no vendor code, no deobfuscated vendor scripts, no scraped vendor images, and no token-selling service.

The defender's side of these rules (choosing a CAPTCHA that is lawful and accessible) is in [Defend](@/defend/_index.md).
