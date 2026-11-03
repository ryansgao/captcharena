+++
title = "What happens when you tick the box"
description = "The full path of a CAPTCHA check: the widget, the signals it collects, the risk score, the optional puzzle, the token and the site's server check."
weight = 10
[extra]
checked = "2026-11-01"
+++

## The short version

Ticking "I'm not a robot" is the least important part of a modern CAPTCHA. By the time you click, the widget has already collected signals about your network, your browser and often your past visits. The vendor turns those into a risk score. If the score is good, you pass with no puzzle. If it is unsure, you get a puzzle. Either way, you end up with a **token**: a short string the site's server must send back to the vendor to check. The site, not the vendor, makes the final decision.

Every major vendor now works this way. The puzzle is the fallback, not the test:

| Vendor | When a visible puzzle appears | Source (checked 2026-11-01) |
|---|---|---|
| Google reCAPTCHA v2 | The picture grid is "only triggered when the risk score is high" | [Broken Gates, 2026](https://arxiv.org/abs/2607.18659) |
| Cloudflare Turnstile | Managed mode shows a checkbox "only … if a further check is necessary" | [Cloudflare docs](https://developers.cloudflare.com/turnstile/concepts/widget/) |
| hCaptcha Pro | Default "99.9% Passive" mode aims to challenge fewer than 0.1% of real people | [hCaptcha docs](https://docs.hcaptcha.com/pro) |
| Arkose Labs | Low-risk sessions get "transparent mode"; others get an interactive challenge | [Arkose docs](https://developer.arkoselabs.com/docs/verify-api-v4-response-fields) |
| DataDome | An invisible Device Check, then a slider, then a block | [DataDome docs](https://docs.datadome.co/docs/threat-detection.md) |

## The check, step by step

### 1. The page loads the widget

The site adds the vendor's script and a public **site key** to the page. The site key says which site the check is for. A matching **secret key** stays on the site's server. See [site key and secret key](@/learn/glossary.md#site-key-and-secret-key).

### 2. The widget collects signals

Before you do anything, the script and the vendor's servers look at several layers. Vendors weight them differently, but the layers are the same everywhere:

| Layer | What is measured | Example of a vendor documenting it (checked 2026-11-01) |
|---|---|---|
| Network | IP reputation, whether the address belongs to a hosting company, VPN or proxy | Arkose's sample response flags `g-reputation-hosting` and `g-reputation-vpn` ([docs](https://developer.arkoselabs.com/docs/verify-api-v4-response-fields)) |
| TLS and HTTP/2 | The fingerprint of the connection handshake (JA3/JA4) and HTTP/2 settings | Cloudflare ([JA3/JA4 docs](https://developers.cloudflare.com/bots/additional-configurations/ja3-ja4-fingerprint/)) |
| Headers | Order and consistency of HTTP headers | Akamai looks for "out-of-order headers and browser version mismatches" ([docs](https://techdocs.akamai.com/cloud-security/docs/detection-methods.md)) |
| Browser environment | Screen, codecs, plugins, CPU and GPU, canvas rendering, execution times | DataDome Device Check ([docs](https://docs.datadome.co/docs/device-check.md)) |
| Automation traces | Signs of automation frameworks or extensions | AWS WAF `SignalAutomatedBrowser` ([docs](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html)) |
| Behaviour | Pointer paths, typing rhythm, timing | Cloudflare Precursor looks for "physiological hand tremor" ([blog](https://blog.cloudflare.com/introducing-precursor/)) |
| State and history | Cookies, stored data, device ID, prior passes | Cloudflare's `__cf_bm` cookie "measures a single user's request pattern" ([docs](https://developers.cloudflare.com/bots/concepts/bot-score/)) |
| Declared identity | Signed agents, Private Access Tokens on Apple devices | Cloudflare lists signed agents as "Verified" since 1 July 2026 ([docs](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/)) |

The [Browser score](@/browser-score/_index.md) section breaks this down per vendor, and [What vendors weigh](@/browser-score/what-vendors-weigh.md) shows which vendor documents which signal.

Consistency matters as much as any single value. A browser whose parts disagree with each other (a user agent that does not match the engine, say) looks worse than a plain one. One 2026 study found that "stealth and anti-detection mechanisms often increase detectability" ([Fayolle et al.](https://arxiv.org/abs/2606.30119), checked 2026-11-01).

### 3. The vendor computes a risk score

The signals go into a model that outputs a score. The scales differ:

| Product | Score | Source (checked 2026-11-01) |
|---|---|---|
| reCAPTCHA v3 | 0.0 ("very likely a bot") to 1.0; default threshold 0.5. Without a billing account only four values are returned: 0.1, 0.3, 0.7, 0.9. With billing, 11 levels and reason codes such as `AUTOMATION` | [Google docs](https://docs.cloud.google.com/recaptcha/docs/interpret-assessment-website) |
| Cloudflare Bot Management | 1–99; 1 = automated, 2–29 likely automated, 30–99 likely human | [Cloudflare docs](https://developers.cloudflare.com/bots/concepts/bot-score/) |
| Arkose Labs | 0–100; Low 0–40, Medium 41–80, High 81–100 | [Arkose docs](https://developer.arkoselabs.com/docs/risk-score.md) |
| hCaptcha Enterprise | 0–1, with score reasons | [hCaptcha docs](https://docs.hcaptcha.com/ent_overview) |

Scores are not stable on day one. Google warns that scores "within 7 days of implementation might differ from the long-term production scores" ([docs](https://docs.cloud.google.com/recaptcha/docs/interpret-assessment-website), checked 2026-11-01).

### 4. Maybe a challenge

If the score is in the middle, the widget shows something you must do. What you get depends on how risky you look:

- **reCAPTCHA v2:** the tick passes alone; then a picture grid; then harder or repeated grids; and a text fallback when the browser fails basic checks ([Sivakorn et al., 2016](https://www.blackhat.com/docs/asia-16/materials/asia-16-Sivakorn-Im-Not-a-Human-Breaking-the-Google-reCAPTCHA-wp.pdf); [Broken Gates](https://arxiv.org/abs/2607.18659), checked 2026-11-01).
- **hCaptcha:** site owners choose Easy, Medium, Difficult or Auto. The difficulty also depends on "computed confidence in the visitor's humanity" ([hCaptcha FAQ](https://docs.hcaptcha.com/faq), checked 2026-11-01).
- **Turnstile:** a non-interactive check first, then a checkbox ([docs](https://developers.cloudflare.com/turnstile/concepts/widget/), checked 2026-11-01). Its background checks include "proof-of-work, proof-of-space, probing for web APIs" ([Cloudflare blog, 2022](https://blog.cloudflare.com/turnstile-private-captcha-alternative/), checked 2026-11-01).
- **AWS WAF:** a silent browser challenge (HTTP 202), then a CAPTCHA (HTTP 405), then a block ([AWS docs](https://docs.aws.amazon.com/waf/latest/developerguide/waf-captcha-and-challenge-actions.html), checked 2026-11-01).

### 5. The widget issues a token

When the vendor is satisfied, the widget puts a token into the page's form or hands it to the page's JavaScript. The token is opaque to the site. It is meant to be used once and soon: Cloudflare's test secrets include one that answers "token already spent" ([docs](https://developers.cloudflare.com/turnstile/troubleshooting/testing/), checked 2026-11-01).

### 6. The site's server checks the token

This is the step that makes the check real. The site's server sends the token and its secret key to the vendor's verification endpoint, usually called **siteverify**. The vendor answers whether the token is valid for this site and, for score products, what the score was. A token that is never checked protects nothing: anyone could post any string.

Some details move the check to this step on purpose. Cloudflare rejects a Managed Challenge solved "from a different IP than the original IP" ([docs](https://developers.cloudflare.com/cloudflare-challenges/concepts/how-challenges-work/), checked 2026-11-01). AWS WAF flags "a token acquired from a data center, proxy, or VPN IP address and presented from a residential or mobile IP address" ([docs](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html), checked 2026-11-01).

### 7. The site decides

The vendor gives evidence; the site makes the call. With reCAPTCHA v3 there is no puzzle at all, and Google suggests the site step up to two-factor or email verification for low scores ([Google docs](https://developers.google.com/recaptcha/docs/v3), checked 2026-11-01). A strict site may block silently. A lenient one may log the score and let everyone through.

## Invisible scoring versus visible puzzles

| | Invisible scoring | Visible puzzle |
|---|---|---|
| What the visitor sees | Nothing, or a box that ticks itself | Images, sliders, text, audio |
| What decides the result | Reputation, environment, history, behaviour | Mostly whether the answer is right (plus the score behind it) |
| Examples | reCAPTCHA v3, Turnstile non-interactive, hCaptcha Passive, DataDome Device Check | reCAPTCHA v2 grid, hCaptcha images, Arkose games, GeeTest sliders |
| Cost to real people | Low; a false positive is silent and hard to appeal | Seconds to minutes per solve; often hard for disabled users |
| Weak point | Bad scores for people on shared or VPN addresses; privacy cost of the signals | Modern vision models and human farms solve the puzzles ([details](@/learn/ai-agents.md)) |

Puzzle accessibility is regulated: under WCAG 2.2, a login step may not depend on most puzzles without an alternative. See [CAPTCHAs and accessibility](@/defend/accessibility.md).

## Test keys test nothing

Vendors publish test keys for development. Google's reCAPTCHA v2 test key means "all verification requests will pass" ([Google FAQ](https://developers.google.com/recaptcha/docs/faq), checked 2026-11-01). hCaptcha says "the test keys provide no anti-bot protection" ([docs](https://docs.hcaptcha.com/), checked 2026-11-01). To see how a real widget judges a real browser, you need a real key on a real domain.

## See it live

Our [measurement page](https://measure.captcharena.org) runs real widgets on our own domain with our own keys: reCAPTCHA v2 and v3, Cloudflare Turnstile, and the self-hosted proof-of-work CAPTCHAs ALTCHA and Cap. Each token goes to the vendor's own siteverify (or our own server for the self-hosted ones), and the page shows you the verdict that came back. It stores no IP address and sets no cookie of ours.

{% <note> %}
Our reCAPTCHA v3 key went live on 2026-11-03. Google says new keys score differently in their first week, so treat v3 scores on the page as provisional until about 2026-11-10.
{% </note> %}

## Next

- [A short history of CAPTCHAs](@/learn/history.md): how we got from distorted text to invisible scores.
- [Every major vendor](@/learn/vendors.md): what each one checks and returns.
- [Glossary](@/learn/glossary.md): [token](@/learn/glossary.md#token), [siteverify](@/learn/glossary.md#siteverify), [risk score](@/learn/glossary.md#risk-score).
