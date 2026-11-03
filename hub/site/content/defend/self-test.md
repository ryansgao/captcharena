+++
title = "Self-test your own site against agents (coming)"
description = "How CAPTCHArena's planned self-test will run real AI agents against a site you prove you own, at low volume, signed, and reported only to you."
weight = 60
[extra]
checked = "2026-11-01"
status = "coming"
+++

{% <coming> %}
This tool is not built yet. This page describes how it will work, so owners and vendors can comment on the design before it runs against anyone's site. It will open after the [Scoreboard](@/scoreboard/_index.md) has published its first runs, because it reuses the same agents and the same method.
{% </coming> %}

The most common question owners of invisible CAPTCHAs ask is "how do you know it's working?" ([r/webdev](https://www.reddit.com/r/webdev/comments/1qg3q3g/), checked 2026-11-01). Today the honest answer is: you mostly do not. The self-test is meant to change that. You prove you own a site, and we run current AI agents against your real sign-up, login or contact form, then tell you what got through.

## Why vendor scanners do not answer the question

Free "test your bot protection" tools exist, but none we found runs a real AI agent or a paid solving service against your site. Each one comes from a company selling bot protection.

| Tool | What it sends | Checked | Source |
|---|---|---|---|
| IntelliFend Bot Tester | A simulated curl client and a fake Googlebot; "only runs tests when the website and email domain match" | 2026-11-01 | [IntelliFend](https://www.intellifend.com/?p=11689) |
| BotGuard "Test Your Anti-Bot Protection" | Checks data-centre reachability, CAPTCHA use and firewall; fake search engines and browser emulators | 2026-11-01 | [BotGuard](https://botguard.net/en/tools) |
| Radware Bad Bot Vulnerability Scanner | Vendor scanner; what it sends was not checked | 2026-11-01 | [Radware](https://gbl.radware.com/vulnerability-test) |

A fake Googlebot tells you whether you check crawler identity. It does not tell you whether an AI agent driving a real browser can create an account on your site. That is the threat the research now describes (see [match the defence to the threat](@/defend/threats.md)).

## How it will work

### 1. Prove you own the site first

No test runs against a host until its owner proves control of it, by one of two methods that search engines and certificate authorities already use:

- a **DNS TXT record** with a token we give you, on the exact host to be tested; or
- a **file at a `/.well-known/` path** on that host, containing the token.

One verified host per account. We check the proof again before every run, so removing the record or the file stops all testing. An email address at the same domain is not enough on its own: it proves you can receive mail there, not that you control the site.

### 2. Low, fixed volume

- A small fixed number of attempts per lane per day (the current plan is at most 50).
- No proxy rotation, no stealth patches, and only our own published egress addresses.
- You pick the pages and forms in scope. Nothing else on your site is touched.

### 3. Every request is signed

Every test request will carry a signature under **Web Bot Auth**, the IETF draft for signing bot and agent traffic with HTTP Message Signatures ([IETF webbotauth working group](https://datatracker.ietf.org/wg/webbotauth/about/), checked 2026-11-01; [Cloudflare's open-source libraries](https://github.com/cloudflare/web-bot-auth), checked 2026-11-01). We will publish our public key directory. This lets you, and your bot-protection vendor, pick out exactly which requests in your logs were the test.

It also makes the test a working example of the accountable-agent path. See [signing agents](@/build/signing.md).

### 4. A report only you can see

The report goes only to the verified owner. It lists, per lane: attempts, how many your site accepted, what the agent saw (no challenge, a tick box, a puzzle, a block), time taken, and the cost of the attempt. It contains outcomes, not working bypass code.

### 5. What the lanes will be

- **AI agents** driving a real browser, the same set the [Scoreboard](@/scoreboard/_index.md) uses.
- **Paid solving services**, only where the CAPTCHA vendor's terms allow it.
- **A control**: a plain scripted client, so you can see what your cheapest layer already stops.

## Sites we will not test

- **Sites protected by hCaptcha**, unless hCaptcha agrees in writing. Its terms forbid passing its challenges with "bots, scripts, or any other form of artificial intelligence", and they bind anyone who uses the service, not only the site owner ([hCaptcha terms](https://www.hcaptcha.com/terms), updated 2025-11-17, checked 2026-11-01). The tool will detect hCaptcha and stop with an explanation.
- **Hosts whose ownership proof fails or lapses** during a run.
- **Anything outside the pages you put in scope.**

For reCAPTCHA and Turnstile, we found no clause that names automated solving by the site owner. Google's terms forbid trying to "circumvent" documented limits ([Google APIs terms](https://developers.google.com/terms), checked 2026-11-01) and Cloudflare's forbid trying to "exceed or circumvent" limitations ([Cloudflare terms](https://www.cloudflare.com/website-terms/), checked 2026-11-01). Testing your own site with your own keys is a grey area, not a clear permission. We will ask each vendor before the tool opens. See the [policy map](@/build/policy-map.md).

## Abuse we have thought about

| Risk | What limits it |
|---|---|
| Someone tests a site they do not own | DNS or file proof on the exact host, checked before every run |
| Someone who has broken into a site uses the tool against it | Low fixed volume; the report holds outcomes, not working bypass code |
| The test is mistaken for an attack | Signed requests, a published key directory and published egress addresses |
| The tool becomes a free solving service | No tokens are returned to the user; attempts are capped per day |

Questions about the design, or a vendor who would like to be consulted before launch: see [contact](@/contact/_index.md).
