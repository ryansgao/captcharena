+++
title = "Defend your site: choosing and checking a CAPTCHA"
description = "For site owners: which CAPTCHA or bot defence fits your threat, what it costs, whether it is accessible and allowed, and how to tell it works."
sort_by = "weight"
[extra]
checked = "2026-11-01"
+++

This section is for people who run a website and have a bot problem, or expect one: a contact form full of spam, a sign-up page filling with fake accounts, a login page under attack, a shop being used to test stolen cards, or a server buckling under crawlers.

It is written by a party with nothing to sell. CAPTCHArena takes no vendor money, uses no affiliate links and runs no CAPTCHA product of its own. Every comparison page we found when we started this site was written by a CAPTCHA vendor or by a company selling something next to it; the most-cited ranking puts its own product first ([Prosopo, "Best CAPTCHA"](https://www.prosopo.io/blog/best-captcha/), checked 2026-11-01). We wanted one that does not.

## The five questions owners actually ask

The same five questions come up again and again in developer forums. We built this section around them.

| Question | Where it is answered |
|---|---|
| **Which one should I use?** "Which captcha provider do you use and why?" ([r/webdev](https://www.reddit.com/r/webdev/comments/1q7t8ed/), checked 2026-11-01) | [Which CAPTCHA fits my site](@/defend/chooser.md) gives a layered recipe per situation. [Match the defence to the threat](@/defend/threats.md) explains why. |
| **Does it still work against AI?** "I hear captchas have become increasingly ineffective… due to ai being able to defeat it. Is that true?" ([r/webdev](https://www.reddit.com/r/webdev/comments/1r1jyiw/), checked 2026-11-01) | [Match the defence to the threat](@/defend/threats.md) for what the research shows today; the [Scoreboard](@/scoreboard/_index.md) for our own measured numbers once the first runs are published. |
| **What does it cost at my traffic?** A not-for-profit site with 700,000 bot requests a day: "reCAPTCHA and hCaptcha look very expensive" ([r/webdev](https://www.reddit.com/r/webdev/comments/1srpfhq/), checked 2026-11-01) | [CAPTCHA fact sheets](@/defend/fact-sheets.md) for list prices and free tiers. [What it costs an attacker](@/defend/attacker-cost.md) for the other side of the ledger. |
| **Is it accessible, private, and allowed in my market?** Forced moves to Google Cloud, EU consent handling, and "Google products are also blocked… in mainland China" ([r/webdev](https://www.reddit.com/r/webdev/comments/1ncqret/), checked 2026-11-01) | [CAPTCHA accessibility](@/defend/accessibility.md) for WCAG 2.2. The [fact sheets](@/defend/fact-sheets.md) for privacy and hosting. The [chooser](@/defend/chooser.md) has rows for GDPR and for visitors in mainland China. |
| **How do I know it is working?** "How do you know it's working?… the response codes are so vague" ([r/webdev](https://www.reddit.com/r/webdev/comments/1qg3q3g/), checked 2026-11-01) | Read your own logs first: the [threats page](@/defend/threats.md#how-to-tell-it-is-working) lists what to look at. Later, the [self-test](@/defend/self-test.md) will run real agents against your own site, with your consent. |

## What this section will not do

- **Name a winner.** No product is "best". Each one trades friction, privacy, cost and resistance differently, and the right mix depends on the threat.
- **Recommend one product as the whole answer.** The research points the other way. Visible puzzles are now a speed bump for a motivated attacker (see [what lasts](@/learn/what-lasts.md)), so the useful answer is a set of layers.
- **Quote vendor claims as measurements.** Where a number is a vendor's own claim, we say so. Where sources disagree, we mark the cell as conflicting.

## Measured numbers come later

The resistance figures on these pages come from published papers and vendor documents, each with its date and link. Our own measurements of how each defence holds up against current AI agents and paid solving services will go on the [Scoreboard](@/scoreboard/_index.md), and these pages will link to them once the first runs are published. The method is on the [Scoreboard method page](@/scoreboard/method.md).

## Related reading

- [How CAPTCHAs work](@/learn/how-captchas-work.md): the invisible score, the puzzle, and proof of work in plain terms.
- [The economics of CAPTCHAs](@/learn/economics.md): why the price of a solve matters more than its difficulty.
- [Vendors](@/learn/vendors.md) and [open-source CAPTCHAs](@/learn/open-source.md): who makes what.
- [Browser score](@/browser-score/_index.md): what the invisible check looks at, from the visitor's side.
