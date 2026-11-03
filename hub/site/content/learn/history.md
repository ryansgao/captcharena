+++
title = "A short history of CAPTCHAs"
description = "From distorted text in 2000 to invisible scores, proof of work, anonymous tokens and signed agents: a dated timeline with sources."
weight = 20
[extra]
checked = "2026-11-01"
+++

## Five eras in one paragraph

CAPTCHAs began as distorted text that programs could not read. reCAPTCHA turned that text into free labour for book digitisation, then replaced it with a checkbox backed by a hidden risk score. The score became the whole product and the puzzle the fallback. When machine vision caught up with the puzzles, the field moved to things that do not depend on perception: proof of work that costs CPU time, anonymous tokens that prove a property without saying who you are, and signed agents that say who they are. Each era is still running somewhere on the web today.

| Era | Roughly | Core idea | Typical example |
|---|---|---|---|
| Distorted text | 2000–2014 | A reading task that humans pass and OCR fails | Wavy letters in a box |
| Human computation | 2007–2018 | Make the reading task useful | reCAPTCHA v1 (two words from scanned books) |
| Risk score plus fallback | 2014 to now | Judge the visitor first; show a puzzle only if unsure | reCAPTCHA v2 checkbox, v3 score, Turnstile |
| Cost instead of recognition | 2025 to now | Make every request cost CPU time | Anubis, ALTCHA, Cap |
| Tokens and identity | 2022 to now | Prove a property or an identity, not humanity | Private Access Tokens, Privacy Pass, Web Bot Auth |

## Timeline

Dates and claims below come from the linked source. Rows marked "checked 2026-11-03" were read from the Wikipedia articles on [CAPTCHA](https://en.wikipedia.org/wiki/CAPTCHA) and [reCAPTCHA](https://en.wikipedia.org/wiki/ReCAPTCHA) and the references they cite; the rest were checked 2026-11-01.

### The text era

| Date | Event | Source | Checked |
|---|---|---|---|
| 2000 | idrive.com protects its sign-up page with a distorted-text test (the "Gausebeck–Levchin" test, per Wikipedia) | [Wikipedia: CAPTCHA](https://en.wikipedia.org/wiki/CAPTCHA) | 2026-11-03 |
| 2001 | PayPal asks users to "retype distorted text that programs have difficulty recognizing" to fight fraud | Wikipedia, citing Stringham (2015), p. 105 | 2026-11-03 |
| 2003 | Luis von Ahn, Manuel Blum, Nicholas J. Hopper and John Langford coin the term CAPTCHA: "Completely Automated Public Turing test to tell Computers and Humans Apart" | [The paper (Springer PDF)](https://link.springer.com/content/pdf/10.1007/3-540-39200-9_18.pdf) | 2026-11-03 |
| 2007-05-27 | reCAPTCHA released, developed at Carnegie Mellon University. Each prompt shows two words from scanned pages: one known word as a control, one uncertain word to be read by the crowd | [Wikipedia: reCAPTCHA](https://en.wikipedia.org/wiki/ReCAPTCHA); [von Ahn, TED talk, 2011](https://www.ted.com/talks/luis_von_ahn_massive_scale_online_collaboration) | 2026-11-03 |
| 2009-09 | Google acquires reCAPTCHA | [Google blog](http://googleblog.blogspot.com/2009/09/teaching-computers-to-read-google.html) | 2026-11-03 |
| 2010 | A UC San Diego study of CAPTCHA farms finds people solving CAPTCHAs for pay, at prices that put a million solves as low as about $1,000, and argues CAPTCHAs must be judged in "purely economic terms" | [Motoyama et al., USENIX Security 2010](https://www.usenix.org/legacy/event/sec10/tech/full_papers/Motoyama.pdf) | 2026-11-03 |
| 2013-10 | Vicarious claims its software reads CAPTCHA characters at "up to 90%" | [The Next Web](https://thenextweb.com/insider/2013/10/28/vicarious-claims-ai-software-can-now-crack-90-captchas-google-yahoo-paypal/) | 2026-11-03 |
| 2014-08 | Bursztein et al. present a generic solver for text CAPTCHAs at USENIX WOOT | [Paper page](https://www.elie.net/publication/the-end-is-nigh-generic-solving-of-text-based-captchas) | 2026-11-03 |
| 2018-10 | Ye et al. (ACM CCS 2018) solve "all 11 text captcha schemes used by the top-50 popular websites" with deep learning | [Paper (PDF)](https://eprints.lancs.ac.uk/id/eprint/126984/1/ccs18.pdf) | 2026-11-03 |

### The risk-score era

| Date | Event | Source | Checked |
|---|---|---|---|
| 2014-12-03 | Google launches "No CAPTCHA reCAPTCHA", the v2 checkbox: a hidden risk analysis decides whether you see a puzzle | [Google security blog](https://security.googleblog.com/2014/12/are-you-robot-introducing-no-captcha.html) | 2026-11-03 |
| 2016 | The only published per-signal test of Google's risk engine: a Google cookie aged nine days earned the checkbox pass without browsing; screen size and mouse behaviour made no difference | [Sivakorn et al., Black Hat Asia 2016](https://www.blackhat.com/docs/asia-16/materials/asia-16-Sivakorn-Im-Not-a-Human-Breaking-the-Google-reCAPTCHA-wp.pdf) | 2026-11-01 |
| 2017-03 | Google introduces "invisible" reCAPTCHA | [Ars Technica](https://arstechnica.com/gadgets/2017/03/googles-recaptcha-announces-invisible-background-captchas/) | 2026-11-03 |
| 2018-03-31 | reCAPTCHA v1 scheduled for shutdown | [ProgrammableWeb notice](https://www.programmableweb.com/news/google-recaptcha-v1-api-shutting-down-march-2018/brief/2017/10/24) | 2026-11-03 |
| Not dated by us | reCAPTCHA v3: a score from 0.0 to 1.0 and no challenge at all; "reCAPTCHA learns by seeing real traffic on your site" | [Google docs](https://developers.google.com/recaptcha/docs/v3) | 2026-11-01 |
| 2021 | Cloudflare estimates the average CAPTCHA takes about 32 seconds to solve | [Cloudflare blog](https://blog.cloudflare.com/introducing-cryptographic-attestation-of-personhood/) | 2026-11-03 |
| 2022 | Cloudflare announces Turnstile: "a series of small non-interactive JavaScript challenges", with Private Access Tokens on Apple devices | [Cloudflare blog](https://blog.cloudflare.com/turnstile-private-captcha-alternative/) | 2026-11-01 |
| 2023 | Searles et al. test 14,000 CAPTCHAs on 1,400 people; a 13-month field study by the same group concludes reCAPTCHA v2 has "an immense cost and no security" | [USENIX Security 2023](https://arxiv.org/abs/2307.12108); [Dazed & Confused](https://arxiv.org/abs/2311.10911) | 2026-11-01 |
| 2024 | ETH Zürich: an off-the-shelf object detector solves 100% of reCAPTCHA v2 challenges | [Plesner et al., COMPSAC 2024](https://arxiv.org/abs/2409.08831) | 2026-11-01 |
| Q3 2024 → Q1 2026 | Classic reCAPTCHA keys stop; all keys migrate to Google Cloud projects, with 10,000 free assessments a month | [Google migration overview](https://docs.cloud.google.com/recaptcha/docs/migration-overview) | 2026-11-01 |

### The cost and identity era

| Date | Event | Source | Checked |
|---|---|---|---|
| 2022 | Apple ships Private Access Tokens (iOS 16, macOS 13): the device attests that it is genuine, so the site can skip the CAPTCHA | [Cloudflare blog](https://blog.cloudflare.com/eliminating-captchas-on-iphones-and-macs-using-new-standard); [WWDC22 session](https://developer.apple.com/videos/play/wwdc2022/10077/) | 2026-11-01 |
| 2024-06 | Privacy Pass published as RFC 9576, 9577 and 9578: anonymous tokens a site can accept without learning who you are | [IETF Privacy Pass documents](https://datatracker.ietf.org/wg/privacypass/documents/) | 2026-11-01 |
| 2025-01-19 | First release of Anubis, an open-source proof-of-work wall against AI scrapers | [Wikipedia: Anubis](https://en.wikipedia.org/wiki/Anubis_(software)) | 2026-11-01 |
| 2025-05 | Open CaptchaWorld benchmark: best AI agent 40% against humans' 93.3% | [arXiv 2505.24878](https://arxiv.org/abs/2505.24878) | 2026-11-01 |
| 2025-08 | Codeberg reports AI scrapers have "learned how to solve the Anubis challenges"; a published analysis prices a week of crawling behind every Anubis site at "approximately $0" | [The Register](https://www.theregister.com/software/2025/08/16/codeberg-beset-by-ai-bots-that-now-bypass-anubis-defense/1023101); [Ormandy](https://lock.cmpxchg8b.com/anubis.html) | 2026-11-01 |
| 2025-08-28 | Cloudflare's "signed agents": AI agents directed by an end user sign their requests with Web Bot Auth | [Cloudflare blog](https://blog.cloudflare.com/signed-agents/) | 2026-11-01 |
| 2025-10-30 | Cloudflare proposes anonymous rate-limited credentials (ARC and ACT) for bots and agents | [Cloudflare blog](https://blog.cloudflare.com/private-rate-limiting/) | 2026-11-01 |
| 2026-02 | The Open CaptchaWorld group reports pass rates "as high as 90%" on its once-unsolved "Bingo" puzzle | [Next-Gen CAPTCHAs](https://arxiv.org/abs/2602.09012) | 2026-11-01 |
| 2026-04-21 | Cloudflare: "There are wanted bots and there are unwanted humans." | [Cloudflare blog](https://blog.cloudflare.com/past-bots-and-humans) | 2026-11-01 |
| 2026-04 (Google Cloud Next) | reCAPTCHA becomes part of Google Cloud Fraud Defense, with an agent dashboard, Web Bot Auth support and a QR-code phone challenge | [Google Cloud blog](https://cloud.google.com/blog/products/identity-security/introducing-google-cloud-fraud-defense-the-next-evolution-of-recaptcha) | 2026-11-01 |
| 2026-06-22 | Cloudflare, Mozilla, Google (Chrome), Microsoft (Edge) and Shopify announce PACT, anonymous tokens showing "a visitor is either a person or an authorized bot" | [The Next Web](https://thenextweb.com/news/cloudflare-pact-browser-privacy-bot-traffic-protocol); [Mozilla Hacks](https://hacks.mozilla.org/2026/06/pact-anonymous-credentials-for-the-web/) | 2026-11-01 |
| 2026-07-01 | Cloudflare lists signed agents as "Verified" | [Cloudflare docs](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/) | 2026-11-01 |
| 2026-07-13 | Cloudflare Precursor: session-long behaviour scoring of pointer and keyboard rhythm | [Cloudflare blog](https://blog.cloudflare.com/introducing-precursor/) | 2026-11-01 |
| 2026-09 | Free local models pass 92.6% of 500 real reCAPTCHA sessions; the authors say such CAPTCHAs "may have reached the end of their useful life" | [Robot Visions, ISC 2026](https://arxiv.org/abs/2609.18518) | 2026-11-01 |
| 2026-10-29 | The IETF Web Bot Auth working group's protocol draft reaches revision -01 | [IETF draft](https://datatracker.ietf.org/doc/draft-ietf-webbotauth-httpsig-protocol/) | 2026-11-01 |

## What the history teaches

- **Every visible test has been broken by the tool of its decade.** Text fell to OCR and deep learning, picture grids to object detectors, logic puzzles to multimodal models. The [AI agents page](@/learn/ai-agents.md) covers the current round.
- **The economics never changed.** Motoyama et al. made the point in 2010: the question is whether a solve costs more than the abuse earns. See [the economics](@/learn/economics.md).
- **The direction since 2022 is away from asking "are you human?"** and toward cost, scarce credentials and declared identity. See [What still works](@/learn/what-lasts.md).

{% <note> %}
Dates we could not confirm from a primary source are left out or marked. We did not confirm launch dates for reCAPTCHA v3 or hCaptcha. Wikipedia also says text tests were "first invented in 1997 by two groups working in parallel", but cites no source, so it is not in the table.
{% </note> %}
