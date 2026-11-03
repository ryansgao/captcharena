+++
title = "What it costs an attacker to get past your CAPTCHA"
description = "The published prices of human solving farms, token services, AI models and proof of work, with a worked example of when a CAPTCHA is no barrier."
weight = 50
[extra]
checked = "2026-11-01"
+++

A CAPTCHA does not have to keep every bot out. It has to make abuse cost more than it earns. Researchers framed CAPTCHAs in "purely economic terms" as early as 2010, when they studied the human solving farms that already sold passes in bulk ([Motoyama et al., USENIX Security 2010](https://www.usenix.org/legacy/event/sec10/tech/full_papers/Motoyama.pdf), checked 2026-11-02). Arkose Labs now describes its own goal the same way: make abuse economically unattractive, not impossible ([Xataka](https://www.xataka.com/robotica-e-ia/agentes-ia-parecen-haber-amenazado-muerte-a-captcha-solo-les-han-puesto-cosas-dificiles), checked 2026-11-01).

So the useful question for a site owner is: **what does one pass cost the attacker, and what does one abusive action earn?**

## The four ways an attacker pays

### 1. Human solving farms

People, often paid very little, solve CAPTCHAs sent to them through an API. One large service states that "100% of captchas are solved by human workers" ([Anti-Captcha](https://anti-captcha.com/), checked 2026-11-01). Researchers who signed up as workers on another called it "a human-driven CAPTCHA farm" ([Halligan, USENIX Security 2025](https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf), checked 2026-11-01). Because a person does the work, any puzzle a person can solve can be bought.

- **Price.** In early 2025, list prices ran from a twentieth of a cent to five cents per CAPTCHA, depending on the service and type ([Halligan, appendix A.1](https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf), checked 2026-11-01).

### 2. Token services

A **token service** returns a valid pass token for a site key you send it. The buyer never sees a puzzle. A 2026 study bought solves from seven services and checked every token with the vendor's own server, on real widgets on the authors' own domains ([Broken Gates, arXiv 2607.18659](https://arxiv.org/abs/2607.18659), checked 2026-11-01; some prices are from the services' own price pages as cited there):

| Widget | Price range per 1,000 | Time per solve | Accepted by the vendor's server |
|---|---|---|---|
| reCAPTCHA v2 tick box | about $0.60–2.99 | about 8–132 s across services | about 100% |
| Cloudflare Turnstile | about $1.20–2.00 | about 4–89 s | about 100% |
| hCaptcha, easy setting | about $1.45–2.99 | about 42–67 s | 100% (only 2 of 7 services offered it) |
| hCaptcha, hard setting | about $1.45–2.99 | about 83–103 s | 58% for one service, 100% for the other |
| reCAPTCHA v3 (score only) | about $0.90–3.00 | about 2–40 s | 0–63% scored above 0.5 (average 23%) |

Across all targets the study puts the price at $0.10–5.00 per 1,000. Its reading of the v3 result: services "merely inject a valid token without reproducing the behavioral signals" that the score depends on.

{% <note> %}
These are one study's numbers on one set of keys in 2026. Prices change, and a service's success on your site depends on your settings. We do not name or link the services here, and we never recommend them.
{% </note> %}

### 3. AI models

Model-based solving is now cheap enough to matter, and it handles new puzzle types that a farm's workers would need to learn first.

| Approach (source) | Cost per challenge | Time | Success |
|---|---|---|---|
| General vision-model solver, on a benchmark and for 30 days in the wild ([Halligan](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh), checked 2026-11-01) | $0.024; $0.006 when its generated code is reused | median 21.8 s | 60.7% on 26 benchmark types; 70.6% on challenges seen in the wild |
| Free local models, no training, real reCAPTCHA sessions ([Robot Visions, arXiv 2609.18518](https://arxiv.org/abs/2609.18518), checked 2026-11-01) | $0 beyond the attacker's own computer | mean 81 s per successful session | 92.6% of 500 sessions |
| Seven multimodal models on 18 real-world types ([COGNITION, USENIX Security 2026](https://arxiv.org/abs/2512.02318), checked 2026-11-01) | under 10 cents per success on the types models already handle; 10–100× more on hard types | "tens of seconds" on easy types | 42.3% across models |
| Frontier models on the hardest research puzzles ([Next-Gen CAPTCHAs, arXiv 2602.09012](https://arxiv.org/abs/2602.09012), checked 2026-11-01) | high; not comparable to the rows above | "16 to 77 minutes to attempt a single complex puzzle" | 0.9–5.9%, against 98.8% for humans |

The last row is the exception that proves the rule: very hard puzzles do cost models a lot, but they are new research designs, not deployed widgets, and the same group's earlier "unsolved" type reached 90% nine months later. See [what lasts](@/learn/what-lasts.md).

### 4. Proof of work

**Proof of work** asks the browser to spend CPU time before the request is accepted. It costs a real visitor a moment. It costs an attacker the same, multiplied by the number of requests, so it prices volume rather than testing for a human.

The best-known analysis is of Anubis's default setting, about 2^16 hashes per token with a 7-day validity. Solving it for all of the roughly 11,500 Anubis deployments for a week took about six minutes on a free cloud machine, and a C solver did a real challenge in 0.017 s. The author's conclusion: "the cost of unrestricted crawler access to the internet for a week is approximately $0" ([Ormandy](https://lock.cmpxchg8b.com/anubis.html), checked 2026-11-01).

Proof of work still helps in practice. It turns away clients that do not run JavaScript or keep cookies. Tokens bound to an address force crawlers that rotate addresses to solve again. Memory-hard variants (Argon2 and scrypt in ALTCHA v3) target the speed-up attackers get from native code and GPUs ([GitHub](https://github.com/altcha-org/altcha), checked 2026-11-01). Raising the difficulty also slows real visitors on old phones, so it cannot be raised far.

## A worked example: when is a CAPTCHA no barrier?

Take the published range for token services: **$0.10 to $5.00 per 1,000 solves**, which is $0.0001 to $0.005 per solve. Compare it with what one abusive action earns. The values in the first column are illustrations, not measurements: put in your own.

| One abusive action earns the attacker… | Cost of one solve at $0.10 per 1,000 | Cost of one solve at $5.00 per 1,000 | Is the CAPTCHA a barrier? |
|---|---|---|---|
| $0.001 (one spam comment) | $0.0001 (earns 10× the cost) | $0.005 (costs 5× what it earns) | Only at the top of the price range |
| $0.01 (one fake sign-up for a small referral credit) | $0.0001 (100×) | $0.005 (2×) | No |
| $0.10 (one scraped page of priced data) | $0.0001 (1,000×) | $0.005 (20×) | No |
| $1.00 (one working stolen card found) | $0.0001 (10,000×) | $0.005 (200×) | No |
| $10.00 (one resold concert ticket) | $0.0001 (100,000×) | $0.005 (2,000×) | No |

Two adjustments make the picture more exact, and neither changes the conclusion for most rows:

- **Divide by the acceptance rate.** If only 23% of bought tokens pass (the average on reCAPTCHA v3 in the study above), each accepted pass costs about 4.3 times the list price.
- **Add everything else you require per action.** An email address, a phone number, an aged account or a payment card each costs the attacker money. These, not the CAPTCHA, are usually what makes abuse unprofitable.

The lesson: **a visible CAPTCHA is a speed bump for anything worth more than a fraction of a cent.** It still removes the cheapest, most automated traffic, which is worth doing. It does not protect anything valuable on its own.

## Price the action, not the visitor

If one pass costs a fraction of a cent, the defence that scales is to limit how many times the abusive action can be taken, so each attacker needs more of the expensive things (accounts, cards, addresses, time).

1. **List your abusable actions.** Sign up, log in, post, send a message, add a payment method, check out, claim a reward, call an expensive API.
2. **Estimate what one abusive action is worth** to an attacker. Use the table above.
3. **Set a limit per account and per action**, in proportion to that value. A free trial might allow one per payment card. A comment form might allow a few per hour per account.
4. **Add limits per address and per device** as a second line, knowing that crawlers and farms spread over many addresses. AWS WAF, for example, challenges an address that makes five or more requests in five minutes without a token, and escalates when one token is reused from several addresses ([AWS docs](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html), checked 2026-11-01).
5. **Make new accounts earn trust.** Lower limits for new accounts, rising with history.
6. **Escalate on risk, not by default.** Show a challenge or ask for a second factor only when a limit is close or the invisible score is low.

New standards aim to do this without tracking people. **Anonymous Rate-Limited Credentials** (ARC, an IETF draft) let a client prove it has not exceeded a fixed number of uses per site, without revealing who it is ([IETF draft](https://datatracker.ietf.org/doc/html/draft-ietf-privacypass-arc-crypto-01), checked 2026-11-01). Cloudflare describes the trade-off as a trilemma: "decentralized, anonymous, accountable — pick two" ([Cloudflare blog](https://blog.cloudflare.com/past-bots-and-humans), checked 2026-11-01). More on the economics: [the economics of CAPTCHAs](@/learn/economics.md).

{% <coming> %}
An interactive attacker-cost calculator. Enter what one abusive action is worth, the CAPTCHA you use and your limits per account, and it will show the attacker's cost per success using the latest measured prices and acceptance rates from the [Scoreboard](@/scoreboard/_index.md).
{% </coming> %}
