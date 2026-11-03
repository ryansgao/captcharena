+++
title = "Which CAPTCHA fits my site: a neutral decision table"
description = "A layered bot-defence recipe for each threat and constraint, with the reason and the trade-off, from a party with nothing to sell."
weight = 10
[extra]
checked = "2026-11-01"
+++

Find the row that matches your situation. Each row gives a **recipe**: several layers that work together, never a single product. If two rows apply (say, fake sign-ups on a hobby site), combine them and keep the stricter constraint.

{% <note> %}
**Who wrote this.** CAPTCHArena has no product, takes no vendor money and uses no affiliate links. Product names below are examples of a kind of tool, listed alphabetically where there are several; none is a recommendation over the others. The table is based on published research and vendor documents (linked on the [threats page](@/defend/threats.md) and the [fact sheets](@/defend/fact-sheets.md)). Our own measured resistance numbers will be linked from the [Scoreboard](@/scoreboard/_index.md) after the first runs.
{% </note> %}

## Terms used in the table

- **Honeypot field**: a form field hidden from people with CSS. A person leaves it empty; a simple form-filling script fills it in. Free, invisible, and only stops naive bots.
- **Rate limit**: a cap on how often one account, address or session may do one action (for example, five sign-ups per address per hour).
- **Proof of work**: the visitor's browser spends a moment of CPU time on a small calculation before the form is accepted. It costs a real browser very little and makes each request cost something. Examples: ALTCHA, Anubis, Cap, mCaptcha.
- **Invisible score**: the vendor judges the session from signals such as the address, the browser and its history, and either passes it silently or shows a challenge. Examples: reCAPTCHA v3, Cloudflare Turnstile, hCaptcha in its passive modes. See [Browser score](@/browser-score/_index.md).
- **Bot management**: a paid service that scores every request, not only one form, and adds behaviour and fingerprint models. Examples: Akamai, Arkose Labs, AWS WAF Bot Control, Cloudflare Bot Management, DataDome, HUMAN.

## By threat

| Situation | Recipe (layers, cheapest first) | Why | Trade-off |
|---|---|---|---|
| **Contact form or comment spam** | Honeypot field → rate limit per address → proof of work or an invisible score on submit → content filtering or moderation for what still gets through | Most form spam is cheap and automated; the first layers remove it at no cost to people. A determined spammer passes any widget, so the last layer is a filter, not a test | Honeypots and proof of work do nothing against a real browser driven by a person or an AI agent. See [form spam](@/defend/threats.md#form-spam) |
| **Fake sign-ups** | Rate limit per address and per device → invisible score at sign-up → email or phone confirmation → limits on what a new account may do until it has a history | Paid solving services return valid tokens for common widgets at a fraction of a cent each, so the widget alone does not stop a farm. Limiting what a new account can *do* lowers what each fake account is worth | Confirmation steps add friction for real users; phone checks exclude people without a phone. See [fake sign-ups](@/defend/threats.md#fake-sign-ups) |
| **Credential stuffing** (trying leaked passwords on your login) | Rate limits per account and per address → breached-password checks and multi-factor sign-in → bot management with behaviour signals on the login route → step-up challenge only when risk is high | The attacker already has working passwords; a puzzle on the login page is solved or skipped. Per-account limits and second factors stop the payoff | Bot management is paid and sales-led for most vendors. Behaviour signals are collected data and need a privacy notice. See [credential stuffing](@/defend/threats.md#credential-stuffing) |
| **Card testing** (trying stolen card numbers on checkout) | Rate limits per account, card and address on the payment step → your payment provider's own fraud screening → invisible score on checkout → step-up only for high risk | The abuse is the payment attempt, so the limit belongs on the payment attempt. A CAPTCHA is only one signal | Strict limits can block a real customer retrying a declined card. See [card testing](@/defend/threats.md#card-testing) |
| **Scraping and AI crawlers** | robots.txt and the crawler controls your host offers → proof of work in front of expensive pages (Anubis-style) → rate limits per address range → for high-value content, bot management that detects residential-proxy traffic | Proof of work turns away clients that do not run JavaScript and makes repeat requests cost something. It does not stop a real browser | One analysis put the cost of crawling every site behind a popular proof-of-work gate for a week at "approximately $0". Proof of work prices cheap scraping; it does not block. See [scraping](@/defend/threats.md#scraping-and-ai-crawlers) |
| **Ticket or inventory bots** | Purchase limits per account and per payment method → queue or lottery for launches → bot management on the purchase route → account history requirements | The bot wants a scarce item, so the limit on *how many per buyer* matters more than any test at the door | Queues and limits annoy real fans; bot management is paid. Ticket sales may also be covered by law: see the [policy map](@/build/policy-map.md). See [ticket bots](@/defend/threats.md#ticket-and-inventory-bots) |

## By constraint

| Situation | Recipe | Why | Trade-off |
|---|---|---|---|
| **Hobby site, no budget** | Honeypot field + rate limit + self-hosted proof of work (ALTCHA, Anubis, Cap, mCaptcha: open-source, free to run) | No account, no third-party scripts, no bill. Enough for the cheap, automated spam most small sites get | You run and update the software. It will not stop a real browser driven by an agent or a person |
| **Already on Cloudflare** | Turnstile on forms (free plan) + Cloudflare's rate limiting and bot settings for your plan | It is already in the request path, the free plan has no published challenge limit, and it can run without other Cloudflare services | Ties more of your stack to one provider. Cloudflare's agent and AI-crawler defaults change; check them after each announcement |
| **EU visitors, GDPR consent** | Self-hosted proof of work, or a provider that documents EU processing and offers a data processing agreement; add an invisible score only after a consent review | Self-hosted proof of work sends no visitor data to a third party. Invisible scoring depends on collecting signals about the visitor | Not legal advice. Since 2026-04-02 a reCAPTCHA site owner is the data controller (see the [fact sheets](@/defend/fact-sheets.md#recaptcha)). Check each provider's terms with whoever handles your privacy compliance |
| **Visitors in mainland China** | A widget not served from Google (self-hosted proof of work, or a provider that states it works there) + rate limits | Site owners report that Google products are blocked in mainland China, so a Google-served widget can block real visitors | Test from the region before relying on any provider's claim; we have not measured this |
| **Strict accessibility duty** (WCAG 2.2 AA, European Accessibility Act) | Non-interactive checks (proof of work, invisible score) first, with a non-puzzle fallback such as an email link; no transcription, maths or logic puzzle without an alternative | WCAG 2.2 SC 3.3.8 does not allow those puzzles in a sign-in step at AA unless there is an alternative; the W3C accessibility note rates proof of work as acceptable | The types that still resist AI agents are the ones AA rules out, and the required alternative becomes the bot's path. See [accessibility](@/defend/accessibility.md) |
| **Must self-host** | ALTCHA, Anubis, Cap or mCaptcha (open-source proof of work); Procaptcha has self-hostable modes; plus rate limits | No vendor sees your traffic and nothing stops working if a provider changes its terms | Licences differ: mCaptcha is AGPL-3.0, PrivateCaptcha is non-commercial only. See the [fact sheets](@/defend/fact-sheets.md#open-source-and-self-hosted) |
| **Page weight matters** | Load the widget only on the form page, or only on submit; prefer a check that runs in the background | One shop owner reported reCAPTCHA v2 adding 831 ms to every page load | Loading late gives the score less to work with on some products |

## How to read a recipe

1. **Start with the free, invisible layers.** A honeypot and a rate limit cost nothing and never annoy a person.
2. **Put the limit on the action, not the visitor.** Ask what one abusive action is worth to the attacker. Then cap how often one account can take it. [What it costs an attacker](@/defend/attacker-cost.md) has a worked example.
3. **Add a widget for the cheap automated traffic that remains.** Treat it as a speed bump. Visible puzzles are solved by paid services for less than a cent and, increasingly, by AI models.
4. **Escalate only where the money is.** Paid bot management makes sense on login, checkout and launches, not on every page.
5. **Check it works.** See [how to tell it is working](@/defend/threats.md#how-to-tell-it-is-working).

## Sources for the numbers above

- "Approximately $0" for a week of crawling past Anubis: Tavis Ormandy's analysis ([lock.cmpxchg8b.com](https://lock.cmpxchg8b.com/anubis.html), checked 2026-11-01).
- Paid solving services at $0.10–5.00 per 1,000 solves, near 100% on reCAPTCHA v2 and Turnstile: Broken Gates ([arXiv 2607.18659](https://arxiv.org/abs/2607.18659), checked 2026-11-01).
- Turnstile free plan, usable without other Cloudflare services ([Cloudflare docs](https://developers.cloudflare.com/turnstile/plans/), checked 2026-11-01).
- Google blocked in mainland China and the move to reCAPTCHA Enterprise, as reported by site owners ([r/webdev](https://www.reddit.com/r/webdev/comments/1ncqret/), checked 2026-11-01).
- reCAPTCHA v2 and 831 ms per page load, one WooCommerce owner's report ([r/Wordpress](https://www.reddit.com/r/Wordpress/comments/1rf8o2a/), checked 2026-11-01).
- WCAG 2.2 SC 3.3.8 ([W3C](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html), checked 2026-11-01); W3C APA note on CAPTCHA ([W3C](https://www.w3.org/TR/turingtest/), checked 2026-11-01).
