+++
title = "What each vendor weighs in its score"
description = "Which signals reCAPTCHA, hCaptcha, Cloudflare, Arkose, DataDome, HUMAN, Akamai, Kasada and AWS WAF document or are known to use, and what each score band means."
weight = 10
[extra]
checked = "2026-11-01"
+++

No vendor publishes its full model, and each one changes often. What we can say is which signals a vendor **documents** using, which ones have been **reverse-engineered** or reported by practitioners, and where we found **no evidence** either way. This page sets that out, then shows what a visitor sees at each score band.

{% <note> %}
"Documented" means the vendor's own documentation names the signal. "Reverse-engineered" means a published analysis of the vendor's script, a paper's measurement, or a practitioner report; these are less certain and can be out of date. "No evidence" does not mean the vendor ignores a signal, only that we found no public source. All sources checked 2026-11-01.
{% </note> %}

## The shared model

Every vendor below runs roughly the same pipeline with different weights. Signals from several layers feed one risk estimate, and the site's policy turns that estimate into an outcome.

| Layer | What is looked at |
|---|---|
| Network | Address reputation, network type (home, mobile, hosting), VPN and proxy lists, residential-proxy membership, location, and whether the address changes mid-session |
| Connection fingerprint | How the browser opens a secure connection (TLS) and speaks HTTP/2, which differs between browser builds and scripts |
| Headers | Order of headers, missing or odd headers, browser hints |
| Browser description | Screen, fonts, graphics card, codecs, plugins, and whether these agree with each other and with the claimed browser |
| Automation traces | Signs that a browser is being driven by automation software |
| Behaviour | Pointer paths, typing rhythm, scrolling, time between seeing and clicking, the path through the site |
| State and history | Cookie age, stored data, earlier passes, device identifiers, signed-in account |
| Identity | Signed agent requests (Web Bot Auth), Apple's Private Access Tokens, device attestation |
| Proof of work | CPU time spent on a small calculation |

## Vendor by signal

D = documented by the vendor. R = reverse-engineered, measured by researchers or reported by practitioners. – = no public evidence found.

| Signal | reCAPTCHA | hCaptcha | Cloudflare | Arkose | DataDome | HUMAN | Akamai | Kasada | AWS WAF |
|---|---|---|---|---|---|---|---|---|---|
| Address reputation, data centre or VPN | R | D | D | D | D | D | – | – | D |
| Residential-proxy detection | – | D | D | D | D | D | – | – | D |
| TLS fingerprint | – | – | D | D | D | – | R | – | – |
| HTTP/2 fingerprint | – | – | D | – | – | – | D | – | – |
| Header anomalies | – | – | D | – | D | D | D | – | D |
| Browser fingerprint | R | D | D | D | D | D | D | R | D |
| Consistency of the browser's description | R | – | D | – | D | D | D | – | D |
| Automation traces | R | – | D | – | D | D | D | – | D |
| Behaviour (pointer, keys, timing) | R | – | D | R | D | D | D | – | D |
| Cookies, history, device ID | R | – | D | D | D | D | R | – | D |
| Signed-in account | R | – | – | – | – | D | – | – | – |
| Proof of work | – | D | D | D | D | – | – | R | D |
| Device attestation (e.g. Private Access Tokens) | – | – | D | – | – | – | – | – | D |
| Agent identity (Web Bot Auth) | D (secondary source) | D | D | D | D | D | – | – | D |

### Sources and notable details, per vendor

**reCAPTCHA (Google).** Google says only that the v3 score "is based on interactions with your site" ([Google docs](https://developers.google.com/recaptcha/docs/v3)). The only published test of one signal at a time is from 2016: a Google cookie aged nine days earned the tick-box pass with no browsing, a user agent that did not match the real browser forced the fallback CAPTCHA, and screen size and mouse behaviour made no difference ([Sivakorn et al., Black Hat Asia 2016](https://www.blackhat.com/docs/asia-16/materials/asia-16-Sivakorn-Im-Not-a-Human-Breaking-the-Google-reCAPTCHA-wp.pdf)). In 2026, of ten agent setups tested on v3, the only one to pass ran inside a real browser profile with "cookies, browsing history" ([Broken Gates, arXiv 2607.18659](https://arxiv.org/abs/2607.18659)). ETH Zürich researchers found reCAPTCHA v2 "relies heavily on cookies and browser history data" ([arXiv 2409.08831](https://arxiv.org/abs/2409.08831)). Google's 2026 Fraud Defense launch adds agent identity through Web Bot Auth, as reported in the press ([heise](https://heise.de/-11273871)).

**hCaptcha.** Difficulty depends on "computed confidence in the visitor's humanity, the site difficulty setting, and other security factors" ([hCaptcha FAQ](https://docs.hcaptcha.com/faq)). The Enterprise risk score includes "VPN or proxy usage" and AI-agent detection, and states that "a known platform can carry both legitimate users and attackers" ([hCaptcha Enterprise docs](https://docs.hcaptcha.com/ent_overview)). "Advanced dynamic proofs of work" run on every request ([hCaptcha docs](https://docs.hcaptcha.com/pro)).

**Cloudflare.** The bot score uses heuristics, machine learning over "headers, session characteristics, and browser signals", and JavaScript detections ([Cloudflare docs](https://developers.cloudflare.com/bots/concepts/bot-detection-engines/)). Traffic from residential-proxy networks gets score 29 ([Cloudflare docs](https://developers.cloudflare.com/bots/additional-configurations/detection-ids/additional-detections/)). Cloudflare added 50 heuristics using "HTTP/2 fingerprints and Client Hello extensions" ([Cloudflare blog](https://blog.cloudflare.com/per-customer-bot-defenses/)). Its Precursor feature (2026) scores pointer and keyboard rhythm over a whole session, looking for "physiological hand tremor" and noting that bots move "in linear interpolations or mathematically ideal Bézier curves" ([Cloudflare blog](https://blog.cloudflare.com/introducing-precursor/)). Turnstile runs "proof-of-work, proof-of-space, probing for web APIs" and uses Private Access Tokens on Apple devices ([Cloudflare blog](https://blog.cloudflare.com/turnstile-private-captcha-alternative/)). Signed agents became "Verified" on 2026-07-01 ([Cloudflare docs](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/)).

**Arkose Labs.** The verify response documents address intelligence (VPN, proxy, Tor, data centre, network owner), a canvas fingerprint, a TLS fingerprint hash, device reuse, and challenge types including proof of work; its sample shows "hosting" and "VPN" reputation flags at weight 20 each ([Arkose docs](https://developer.arkoselabs.com/docs/verify-api-v4-response-fields)). Behaviour is collected in an encrypted fingerprint blob, per reverse-engineering work ([unfuncaptcha/bda](https://www.github.com/unfuncaptcha/bda)).

**DataDome.** Models are signature-based ("TLS fingerprints, browser fingerprints, and HTTP headers"), behavioural, and reputational (data-centre and residential-proxy addresses) ([DataDome docs](https://docs.datadome.co/docs/threat-detection.md)). Its invisible Device Check looks for "automation frameworks, spoofed environments or programmatic access" and remembers a pass ([DataDome docs](https://docs.datadome.co/docs/device-check.md)).

**HUMAN (formerly PerimeterX).** Its sensor reads "mouse clicks, screen touches, cadence and timing", rendering capabilities, plugins and extensions, and a cookie-based ID ([HUMAN docs](https://docs.humansecurity.com/applications/bd-detection-overview.md)). Account protection adds "Evidence of proxying" and "anomalous ASNs" ([HUMAN docs](https://docs.humansecurity.com/applications/risk-triggers-and-attack-patterns.md)).

**Akamai.** Documents "out-of-order headers and browser version mismatches", an active browser check, and behavioural detection on login and checkout in its top tier ([Akamai docs](https://techdocs.akamai.com/cloud-security/docs/detection-methods.md)). Its engineers published the HTTP/2 fingerprinting method in 2017 ([Black Hat EU 2017](https://www.blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf)).

**Kasada.** No public developer documentation; its documentation site is a login portal (checked 2026-11-01). The two R marks come from material published by solving vendors, which we do not link. We describe Kasada only from public behaviour.

**AWS WAF Bot Control.** The most transparent vendor: its rule labels form a public list of signals, including known data-centre addresses, automated browsers, browser inconsistency, automation extensions, tokens moved from a data-centre or VPN address to a home address, and verified Web Bot Auth signatures ([AWS docs](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html)).

## Score scale and what the visitor sees

| Vendor | Score scale | Who decides the outcome | What the visitor sees, low risk to high |
|---|---|---|---|
| reCAPTCHA v3 | 0.0–1.0. Without billing only 0.1, 0.3, 0.7, 0.9; 11 levels with billing. Default threshold 0.5 | The site's own threshold | Nothing; the site chooses what to do with a low score, and Google suggests two-factor or email verification |
| reCAPTCHA v2 tick box | Hidden | Google | Tick passes alone → picture grid → more or harder grids → a fallback text CAPTCHA when the browser fails checks |
| hCaptcha | 0–1 (Enterprise only) | Site difficulty setting and hCaptcha's confidence | Passive pass (Pro and Enterprise) → tick box → easy picture task → ambiguous, fine-grained images and puzzles |
| Cloudflare Turnstile | Hidden | Cloudflare | Silent pass → a click → a loop or a failure |
| Cloudflare bot score | 1–99; 1 = automated, 2–29 likely automated, 30–99 likely human | The site's firewall rules | Pass → managed challenge → block |
| Arkose Labs | 0–100: low 0–40, medium 41–80, high 81–100 | The customer's strategy | No visible challenge → proof of work, picture or audio game → more rounds and harder games → block |
| DataDome | 0–1, sometimes visible in a response header | DataDome's models | Pass → invisible device check → slider → block |
| HUMAN | Risk score carried in a cookie | HUMAN's enforcer | Pass → "Press and Hold" → block |
| AWS WAF | Named labels and machine-learning levels | The site's rules | Pass → silent challenge → CAPTCHA → block |

Sources: [Google](https://docs.cloud.google.com/recaptcha/docs/interpret-assessment-website), [Sivakorn et al.](https://www.blackhat.com/docs/asia-16/materials/asia-16-Sivakorn-Im-Not-a-Human-Breaking-the-Google-reCAPTCHA-wp.pdf), [hCaptcha](https://docs.hcaptcha.com/faq), [Broken Gates](https://arxiv.org/abs/2607.18659) (hCaptcha easy versus hard), [Cloudflare bot score](https://developers.cloudflare.com/bots/concepts/bot-score/), [Turnstile outcomes](https://developers.cloudflare.com/turnstile/turnstile-analytics/challenge-outcomes/), [Arkose](https://developer.arkoselabs.com/docs/risk-score.md), [DataDome](https://docs.datadome.co/docs/threat-detection.md), [HUMAN](https://docs.humansecurity.com/applications/human-challenge.md), [AWS](https://docs.aws.amazon.com/waf/latest/developerguide/waf-captcha-and-challenge-actions.html); all checked 2026-11-01.

## What matters most, by the evidence

1. **The address and the history come first.** Vendors document scoring the network type, and the only measured results for reCAPTCHA point to cookies and history (Sivakorn 2016; Broken Gates 2026). One 2026 study found the address layer alone a weak classifier of agents (0.596 accuracy) against 0.931 for the browser layer, so the weight differs by vendor ([Fayolle et al., arXiv 2606.30119](https://arxiv.org/abs/2606.30119)).
2. **A browser that describes itself inconsistently is penalised.** DataDome and AWS name this check; Cloudflare warns that fingerprint-protection and canvas-blocking extensions "can interfere" ([Cloudflare docs](https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/)).
3. **Automation is detectable, and agents move differently.** In one 2026 study, behaviour features alone told AI agents from people at an F1 score of 0.999; agents "paste text instead of typing it" and their pointer "jumps to click targets" ([FP-Agent, arXiv 2605.01247](https://arxiv.org/abs/2605.01247)).
4. **Agents are now a category of their own.** Cloudflare, Arkose, DataDome, HUMAN, hCaptcha, AWS and Google all describe agent detection or agent identity features in 2026. A signed agent can be recognised and allowed; an unsigned one is judged on its other signals. See [signing agents](@/build/signing.md).

What none of these vendors publishes is how much each signal moves the score. That is what [our experiment](@/browser-score/experiment.md) is designed to measure.
