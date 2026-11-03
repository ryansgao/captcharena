+++
title = "Match the defence to the threat"
description = "What attackers do in each kind of bot abuse, which defensive layers help, which do not, and how to tell whether yours is working."
weight = 20
[extra]
checked = "2026-11-01"
+++

A CAPTCHA answers one question: is this request worth letting through? Attackers differ in what they want, how much each success earns them, and what tools they can afford. A defence that stops one kind of bot does nothing against another. This page goes threat by threat.

## Three facts that shape every threat

1. **Paid solving services pass common widgets cheaply.** A 2026 study put real widgets on its own domains and checked every token with the vendor's server. Seven commercial services passed reCAPTCHA v2 and Turnstile close to 100% of the time, at $0.10–5.00 per 1,000 solves. Two exceptions held better: hCaptcha on its hard setting (58% for one service) and reCAPTCHA v3, where the services averaged 23% above a 0.5 score ([Broken Gates, arXiv 2607.18659](https://arxiv.org/abs/2607.18659), checked 2026-11-01).
2. **AI models now solve most visible puzzles.** Free local models with no training passed 92.6% of 500 real reCAPTCHA sessions; the authors conclude that "challenge-based visual CAPTCHAs may have reached the end of their useful life" ([Robot Visions, ISC 2026](https://arxiv.org/abs/2609.18518), checked 2026-11-01). The research trend is on [what lasts](@/learn/what-lasts.md).
3. **The invisible score decides most outcomes.** For reCAPTCHA v3 and Turnstile, the same study found that whether an agent passed depended on "execution-environment authenticity": its address, browser and history, not its mouse movements ([Broken Gates](https://arxiv.org/abs/2607.18659), checked 2026-11-01). See [Browser score](@/browser-score/_index.md).

The consequence: **price the action, not the visitor.** Work out what one abusive action is worth, then limit how often it can happen. [What it costs an attacker](@/defend/attacker-cost.md) shows the arithmetic.

## Form spam

**What attackers do.** Scripts post to contact and comment forms at volume, usually without running a full browser. Some spam is posted through real browsers or by people.

**What helps.**
- A **honeypot field** (hidden from people, filled in by naive scripts) and a **rate limit** per address. Owners on Hacker News list hidden fields among the measures that still work for small sites ([Ask HN](https://news.ycombinator.com/item?id=41785574), checked 2026-11-01).
- **Proof of work** on submit. The W3C accessibility note rates it as acceptable: it "poses no direct accessibility problems, though it may slow older hardware" ([W3C APA note](https://www.w3.org/TR/turingtest/), checked 2026-11-01).
- **Content filtering or moderation** for what gets through.

**What does not.** No single widget. One owner tried a spam-filtering service, Turnstile ("bots seem to be solving it"), reCAPTCHA v2 and v3, and honeypots, and still got contact-form spam ([Ask HN](https://news.ycombinator.com/item?id=44160979), checked 2026-11-01).

## Fake sign-ups

**What attackers do.** Create accounts in bulk for spam, referral credits, free-tier abuse or later resale. As one owner put it, "the choice is between 'use a captcha' and 'have your service spammed with 3000 new users per second'" ([r/webdev](https://www.reddit.com/r/webdev/comments/1q7t8ed/), checked 2026-11-01).

**What helps.**
- **Rate limits** per address and device on the sign-up action.
- An **invisible score** at sign-up, used to decide how much extra checking a new account gets. Google suggests two-factor or email verification for low reCAPTCHA v3 scores rather than a hard block ([Google reCAPTCHA v3 docs](https://developers.google.com/recaptcha/docs/v3), checked 2026-11-01).
- **Limits on what a new account can do** until it has a history. This lowers what each fake account is worth.

**What does not.** A visible puzzle alone. Token services and human farms sell passes for common widgets at a fraction of a cent each ([Broken Gates](https://arxiv.org/abs/2607.18659), checked 2026-11-01).

## Credential stuffing

**What attackers do.** Try usernames and passwords leaked elsewhere against your login, often through real browsers and many addresses.

**What helps.**
- **Per-account and per-address limits** on login attempts, and second factors. These stop the payoff even when the bot gets through.
- **Bot management with behaviour and network signals** on the login route. HUMAN documents risk triggers for proxying and "anomalous ASNs" ([HUMAN docs](https://docs.humansecurity.com/applications/risk-triggers-and-attack-patterns.md), checked 2026-11-01). AWS WAF escalates when one token is used from many addresses (`TGT_TokenReuseIp`) ([AWS docs](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html), checked 2026-11-01).

**What does not.** A checkbox widget on its own. An owner moving off Turnstile because of credential stuffing reported that "anything using headless browsers with realistic JS execution just sails through" ([r/webdev](https://www.reddit.com/r/webdev/comments/1sl2zme/), checked 2026-11-01). That is one owner's report, not a measurement, but it matches the solver study above.

## Card testing

**What attackers do.** Run many small payments with stolen card numbers to find out which ones work.

**What helps.** Limits on the payment action itself: attempts per account, per card and per address. Your payment provider's fraud screening sees signals across many shops that you cannot. An invisible score on checkout is one more signal.

**What does not.** Relying on a CAPTCHA at the start of checkout. The attacker needs only to pass it once per session, and a pass costs a fraction of a cent.

{% <note> %}
We found no published measurement of CAPTCHAs against card testing specifically. The advice in this section applies the general principle (limit the abusive action) and is not drawn from a study.
{% </note> %}

## Scraping and AI crawlers

**What attackers do.** Fetch large numbers of pages, often ignoring robots.txt. Large crawlers spread their requests over residential proxy networks: Cloudflare reported linking "11 billion requests from millions of unique IP addresses" to such networks in seven days ([Cloudflare blog](https://blog.cloudflare.com/per-customer-bot-defenses/), checked 2026-11-01). Some hide who they are; Cloudflare documented one AI company's undeclared crawler rotating user agents and networks ([Cloudflare blog](https://blog.cloudflare.com/perplexity-is-using-stealth-undeclared-crawlers-to-evade-website-no-crawl-directives/), checked 2026-11-01).

**What helps.**
- **Proof of work** in front of expensive pages. It filters clients that do not run JavaScript or keep cookies. In one 2026 study, Anubis stopped every plain HTTP scraper tested but no browser-based tool ([Fayolle et al., arXiv 2606.30119](https://arxiv.org/abs/2606.30119), checked 2026-11-01).
- **Crawler controls** from your host or CDN. Since 2026-09-15, Cloudflare blocks bots it classes as Training or Agent on pages that show ads, for new domains ([Cloudflare changelog](https://developers.cloudflare.com/changelog/post/2026-07-01-ai-traffic-options/), checked 2026-11-01).
- **Residential-proxy detection** in bot management. Cloudflare sets the bot score of such traffic to 29, one point below its "likely human" line ([Cloudflare docs](https://developers.cloudflare.com/bots/additional-configurations/detection-ids/additional-detections/), checked 2026-11-01).

**What does not.** Proof of work as a wall. It prices cheap scraping; it does not block a funded crawler. One analysis found that solving the default Anubis challenge for all of its roughly 11,500 deployments for a week takes about six minutes on a free cloud machine: "the cost of unrestricted crawler access to the internet for a week is approximately $0" ([Ormandy](https://lock.cmpxchg8b.com/anubis.html), checked 2026-11-01). Codeberg reported in August 2025 that AI scrapers had "learned how to solve the Anubis challenges" ([The Register](https://www.theregister.com/software/2025/08/16/codeberg-beset-by-ai-bots-that-now-bypass-anubis-defense/1023101), checked 2026-11-01).

## Ticket and inventory bots

**What attackers do.** Buy scarce items (tickets, limited releases, appointment slots) the moment they go on sale, to resell them.

**What helps.** Purchase limits per account and per payment method, queues or lotteries for launches, account-history requirements, and bot management on the purchase route. In some countries ticket bots are also regulated; see the [policy map](@/build/policy-map.md).

**What does not.** A puzzle at the door. The value of one ticket can be far higher than the price of one solve, so the attacker will pay for it.

## How to tell it is working

Owners of invisible CAPTCHAs ask this most, because "the response codes are so vague" ([r/webdev](https://www.reddit.com/r/webdev/comments/1qg3q3g/), checked 2026-11-01). Five checks you can run from your own data:

1. **Log the verdict on your server.** Record pass or fail, and the score where there is one, for every form submit. Compare the distribution before and after a change.
2. **Watch the first week.** Google warns that reCAPTCHA v3 scores "within 7 days of implementation might differ from the long-term production scores" ([Google docs](https://docs.cloud.google.com/recaptcha/docs/interpret-assessment-website), checked 2026-11-01). Set thresholds after that.
3. **Use the vendor's own analytics.** Turnstile, for example, splits solves into non-interactive, interactive and pre-clearance ([Cloudflare docs](https://developers.cloudflare.com/turnstile/turnstile-analytics/challenge-outcomes/), checked 2026-11-01). A rising interactive share means more visitors look risky.
4. **Measure the outcome, not the widget.** Count fake accounts, spam posts or chargebacks per week. A widget can pass everything and still be useless if the abuse continues.
5. **Watch the false positives.** Count support messages and drop-offs at the protected step. Real people behind VPNs and shared addresses are scored down too; see [why am I getting so many CAPTCHAs](@/browser-score/why-am-i-getting-captchas.md).

{% <coming> %}
An ownership-verified [self-test](@/defend/self-test.md) that runs real AI agents against your own site and reports only to you.
{% </coming> %}
