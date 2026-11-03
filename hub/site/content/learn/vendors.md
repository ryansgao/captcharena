+++
title = "Every major CAPTCHA and bot-defence vendor, and how each works"
description = "What each vendor shows visitors, what it checks, what the site receives and who can sign up: reCAPTCHA, hCaptcha, Turnstile, Arkose, DataDome and more."
weight = 30
[extra]
checked = "2026-11-01"
+++

This page describes each vendor from its own documentation and from published research. It does not rank them. To choose one for your site, use the [chooser](@/defend/chooser.md). For open-source options, see [Open-source and self-hosted CAPTCHAs](@/learn/open-source.md).

## Summary table

All rows checked 2026-11-01 against the sources in each vendor's section below.

| Vendor | What visitors usually see | Main approach | What the site receives | Who can use it |
|---|---|---|---|---|
| Google reCAPTCHA (v2, v3, Enterprise; now Google Cloud Fraud Defense) | v2: a checkbox, sometimes a picture grid. v3: nothing | Risk score from Google's model; grid as fallback (v2) | Token; v3 adds a score 0.0–1.0 (four levels without billing, 11 with) | Self-serve; 10,000 free assessments a month |
| hCaptcha | Publisher: picture puzzles. Pro/Enterprise: mostly nothing | Risk score, proof of work, image challenges | Token; Enterprise adds a 0–1 risk score with reasons | Self-serve free tier; Pro $99/month (annual); Enterprise by sales |
| Cloudflare Turnstile and challenge pages | A box that usually ticks itself; full-page "Just a moment…" checks | Non-interactive browser challenges, proof of work, Cloudflare's network data | Token; Bot Management customers get a 1–99 bot score | Turnstile free for all; Bot Management by plan |
| Arkose Labs | Nothing for low risk; puzzle "games" for higher risk | Risk bands, then interactive or proof-of-work challenges | Verify API with risk score 0–100, telltales, IP data | Sales only |
| DataDome | Usually nothing; an invisible Device Check; a slider; a block | Signature, behavioural and reputation models | Allow, challenge or block; some sites expose a risk-score header | Sales; 30-day trial |
| HUMAN (PerimeterX) | Usually nothing; a "press and hold" challenge | Client sensor, behaviour, fingerprints | Risk score in a cookie; enforcement at the edge | Sales (enterprise; not confirmed) |
| Akamai Bot Manager | Usually nothing; sometimes an interaction | Request anomalies, browser interaction, behaviour (Premier) | Edge decisions and risk scoring | Akamai customers |
| Kasada | Usually nothing | Closed; reported proof of work | Edge decisions | Sales; no public developer docs |
| AWS WAF Bot Control | A silent challenge page, sometimes a CAPTCHA | Labels from browser interrogation, fingerprints, ML | Labels on each request; rule actions | AWS customers |
| GeeTest | Sliders, icon clicks, visual reasoning puzzles | Puzzle plus behaviour | Token for server validation | Not checked |
| Friendly Captcha | A progress bar while the browser computes | Proof of work | Token checked by Friendly Captcha's service | Account required; free-tier terms conflict between sources |
| MTCaptcha | Text CAPTCHA | Not checked | Not checked | Not checked |
| Prosopo (Procaptcha) | Nothing, proof of work, or an image puzzle | Three modes: frictionless, pow, puzzle | Token | Hosted service, or self-host (Apache-2.0) |

{% <note> %}
Market share, for scale: a compilation of BuiltWith data for July 2026 puts reCAPTCHA at about 76% of CAPTCHA widget detections, hCaptcha about 14% and Turnstile about 5% ([comparecheapssl](https://comparecheapssl.com/captcha-statistics), checked 2026-11-01). These are third-party figures, not from BuiltWith directly.
{% </note> %}

## Google reCAPTCHA (v2, v3, Enterprise) and Google Cloud Fraud Defense

- **What the visitor sees.** v2: the "I'm not a robot" checkbox; a picture grid appears "only … when the risk score is high" ([Broken Gates](https://arxiv.org/abs/2607.18659)). Invisible v2: nothing unless challenged. v3: nothing, ever.
- **What it checks.** Google does not publish the model's inputs; the v3 score "is based on interactions with your site" ([Google](https://developers.google.com/recaptcha/docs/v3)). Research points to cookies and history: a nine-day-old Google cookie earned the checkbox pass in 2016 ([Sivakorn et al.](https://www.blackhat.com/docs/asia-16/materials/asia-16-Sivakorn-Im-Not-a-Human-Breaking-the-Google-reCAPTCHA-wp.pdf)), and reCAPTCHA v2 "relies heavily on cookies and browser history" ([Plesner et al., 2024](https://arxiv.org/abs/2409.08831)).
- **What the site receives.** A token to check with siteverify. v3 adds a score from 0.0 to 1.0, default threshold 0.5. Without billing only 0.1, 0.3, 0.7 and 0.9 are returned; with billing, 11 levels and reason codes such as `AUTOMATION` and `UNEXPECTED_ENVIRONMENT` ([Google](https://docs.cloud.google.com/recaptcha/docs/interpret-assessment-website)).
- **Who can use it.** Self-serve. All keys now live in Google Cloud projects, with 10,000 free assessments a month; since 2026-04-02 the badge drops Google's privacy and terms links and the site owner becomes the data controller ([migration overview](https://docs.cloud.google.com/recaptcha/docs/migration-overview)).
- **Fraud Defense.** reCAPTCHA is now "a part of Google Cloud Fraud Defense" ([Google](https://docs.cloud.google.com/recaptcha/docs/interpret-assessment-website)). Announced at Google Cloud Next in April 2026, it adds a policy engine over "risk scores, automation types, and agent identity", an agent dashboard with Web Bot Auth support, and a QR-code challenge scanned with a phone ([Google Cloud blog](https://cloud.google.com/blog/products/identity-security/introducing-google-cloud-fraud-defense-the-next-evolution-of-recaptcha)). The policy engine was still in Preview in July 2026 ([release notes](https://docs.cloud.google.com/recaptcha/docs/release-notes)).

All checked 2026-11-01.

## hCaptcha

- **What the visitor sees.** On free Publisher accounts, a picture challenge ("Always Challenge" mode) at Easy, Medium, Difficult or Auto difficulty. Pro accounts default to "99.9% Passive", which aims to challenge fewer than 0.1% of real people; Enterprise "Passive" mode never shows a visible challenge ([FAQ](https://docs.hcaptcha.com/faq); [Pro](https://docs.hcaptcha.com/pro)).
- **What it checks.** "Thousands of factors", plus "advanced dynamic proofs of work" on every request ([Pro docs](https://docs.hcaptcha.com/pro)). Enterprise adds Risk Insights including "VPN or proxy usage", a rules engine, and AI-agent controls with Web Bot Auth ([Enterprise overview](https://docs.hcaptcha.com/ent_overview)). Researchers describe Easy as "relatively unambiguous object-recognition tasks" and Hard as "more ambiguous, fine-grained image classification and puzzles" ([Broken Gates](https://arxiv.org/abs/2607.18659)).
- **What the site receives.** A token; Enterprise adds a risk score from 0 to 1 with reasons.
- **Who can use it.** Free Publisher tier; Pro at $99/month billed annually, with a two-week trial; Enterprise by sales ([Pro docs](https://docs.hcaptcha.com/pro)).
- **Terms.** hCaptcha's terms forbid passing challenges with "bots, scripts, or any other form of artificial intelligence" ([terms, updated 2025-11-17](https://www.hcaptcha.com/terms)). For agents, its Enterprise product says that if a challenge is required, "the agent pauses for the person who initiated the task" ([Enterprise overview](https://docs.hcaptcha.com/ent_overview)).

All checked 2026-11-01.

## Cloudflare Turnstile, challenge pages and Bot Management

- **What the visitor sees.** Turnstile has three modes: Managed (a checkbox "only … if a further check is necessary"), Non-Interactive (never asks) and Invisible (shows nothing) ([widget docs](https://developers.cloudflare.com/turnstile/concepts/widget/)). Sites behind Cloudflare can also show a full-page challenge.
- **What it checks.** "Proof-of-work, proof-of-space, probing for web APIs, and various other challenges for detecting browser-quirks and human behavior", and Private Access Tokens on Apple devices ([Cloudflare blog, 2022](https://blog.cloudflare.com/turnstile-private-captcha-alternative/)). Bot Management adds heuristics, machine learning on "headers, session characteristics, and browser signals", JA3/JA4 fingerprints and a residential-proxy detection that sets the bot score to 29 ([bot score](https://developers.cloudflare.com/bots/concepts/bot-score/); [detection IDs](https://developers.cloudflare.com/bots/additional-configurations/detection-ids/additional-detections/)). Precursor (2026) scores pointer and keyboard rhythm across a whole session ([blog](https://blog.cloudflare.com/introducing-precursor/)).
- **What the site receives.** A Turnstile token to check server-side. Bot Management customers see a bot score from 1 to 99; granular scores are Enterprise only.
- **Who can use it.** Turnstile is free for everyone ([Turnstile GA post](https://blog.cloudflare.com/turnstile-ga)). Bot Management depends on the Cloudflare plan.
- **Agents.** Since 2026-07-01 signed agents are "Verified", in a new category "Agent": "User-directed agents visiting a page on behalf of a human" ([verified bots](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/)). Cloudflare also says "Automated browsers are not supported for solving production challenges" ([supported browsers](https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/)).

All checked 2026-11-01.

## Arkose Labs

- **What the visitor sees.** Low-risk sessions see nothing ("transparent mode"). Others get a visual or audio puzzle, often an interactive game, or a proof-of-work challenge ([Verify API fields](https://developer.arkoselabs.com/docs/verify-api-v4-response-fields)). Its newer challenge suite is called MatchKey ([launch](https://arkoselabs.com/latest-news/arkose-labs-launches-arkose-matchkey)).
- **What it checks.** A risk score from 0 to 100 in three bands (Low 0–40, Medium 41–80, High 81–100), with categories including "Fraud farms (Captcha solvers)" ([risk score](https://developer.arkoselabs.com/docs/risk-score.md)). The sample Verify response shows telltales such as `g-reputation-hosting` and `g-reputation-vpn`, IP intelligence (`is_vpn`, `is_proxy`), a canvas fingerprint and a JA4 hash.
- **What the site receives.** The Verify API response: score, band, telltales, challenge type and device ID data.
- **Who can use it.** Sales only; no self-serve keys found ("book a demo").
- **Agents.** Agent Trust Manager sorts agents into "self-disclosing good", "non-disclosing good" and malicious ([docs](https://developer.arkoselabs.com/docs/agent-trust-manager-overview.md)).

All checked 2026-11-01.

## DataDome

- **What the visitor sees.** Usually nothing. Then a ladder: an invisible Device Check, a slider CAPTCHA, a block ([threat detection](https://docs.datadome.co/docs/threat-detection.md)). The slider is advertised as WCAG 2.2 AA with audio in 58 languages ([CAPTCHA docs](https://docs.datadome.co/docs/datadome-captcha.md)).
- **What it checks.** Signature models ("TLS fingerprints, browser fingerprints, and HTTP headers"), behavioural models, and reputation models for "a data center or residential proxy". Device Check collects "hundreds of signals" (screen, codecs, plugins, CPUs, GPUs, canvas rendering, execution times) "to spot any type of automation frameworks, spoofed environments or programmatic access" ([Device Check](https://docs.datadome.co/docs/device-check.md)).
- **What the site receives.** An allow, challenge or block decision at the edge. Some DataDome sites return an `x-datadome-riskscore` header.
- **Who can use it.** Sales; third-party sources report no free tier, a 30-day trial and Essentials around $45,960 a year on AWS Marketplace ([cside](https://cside.com/blog/datadome-pricing)).
- **Agents.** An Agent Trust Score from 0 to 100, and identification strengths where Web Bot Auth counts as High ([agent identification](https://docs.datadome.co/docs/ai-agent-identification.md); [trust score](https://docs.datadome.co/docs/agent-trust-score.md)).

All checked 2026-11-01.

## HUMAN Security (formerly PerimeterX)

- **What the visitor sees.** Usually nothing; sometimes the HUMAN Challenge, a "press and hold" button ([challenge docs](https://docs.humansecurity.com/applications/human-challenge.md)).
- **What it checks.** "Hundreds of live signals collected on the client by the HUMAN Sensor", including "mouse clicks, screen touches, cadence and timing", rendering capabilities, plugins and extensions ([detection overview](https://docs.humansecurity.com/applications/bd-detection-overview.md)). The challenge uses "honeypots such as fake CAPTCHA tokens, multiple iframes and fake events".
- **What the site receives.** A per-request risk score "embedded into a cookie", enforced by HUMAN's enforcer.
- **Who can use it.** Enterprise sales (not confirmed by us).
- **Agents.** Agent trust levels: High means "verify the agent via cryptographic key on each request"; Low means "unverified, easily spoofable" ([trust levels](https://docs.humansecurity.com/applications/about-agent-trust-levels.md)).

All checked 2026-11-01.

## Akamai Bot Manager

- **What the visitor sees.** Usually nothing; sometimes an interaction to confirm a real browser.
- **What it checks.** Transparent detection of "dozens of request anomalies like out-of-order headers and browser version mismatches", active detection, and behavioural detection on login and checkout pages in the Premier tier ([detection methods](https://techdocs.akamai.com/cloud-security/docs/detection-methods.md)). Akamai researchers published the HTTP/2 fingerprinting method in 2017 ([white paper](https://www.blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf)).
- **What the site receives.** Decisions at Akamai's edge and calibrated risk scores.
- **Who can use it.** Akamai customers; pricing not checked.
- **Agents.** Akamai calls Web Bot Auth "key to achieving strong and accurate identification of the so-called 'known bots'" ([Akamai blog](https://www.akamai.com/blog/security/bot-management-agentic-era)).

All checked 2026-11-01.

## Kasada

- **What the visitor sees.** Usually nothing.
- **What it checks.** Closed. No public developer documentation was found; the docs site is a login portal. Third-party write-ups report request headers carrying a proof-of-work answer ([DeepWiki summary](https://deepwiki.com/Hyper-Solutions/hyper-sdk-go/3.3-kasada-integration), secondary source).
- **What the site receives.** Edge decisions.
- **Who can use it.** Sales.

Checked 2026-11-01.

## AWS WAF Bot Control

- **What the visitor sees.** A silent JavaScript challenge (HTTP 202), sometimes a CAPTCHA (HTTP 405), or a block ([CAPTCHA and challenge actions](https://docs.aws.amazon.com/waf/latest/developerguide/waf-captcha-and-challenge-actions.html)).
- **What it checks.** Two levels: Common ("static request data analysis") and Targeted ("browser interrogation, fingerprinting, and behavior heuristics" plus ML models). AWS publishes its labels, which makes it the most transparent vendor here: `signal:automated_browser`, `TGT_SignalBrowserInconsistency`, `SignalKnownBotDataCenter`, token reuse across IPs, and `bot:web_bot_auth:verified` ([Bot Control rule group](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html)).
- **What the site receives.** Labels on each request, which its own WAF rules turn into Count, Challenge, CAPTCHA or Block.
- **Who can use it.** AWS customers using AWS WAF; pricing not checked.

All checked 2026-11-01.

## GeeTest

- **What the visitor sees.** Sliders, icon-click puzzles and visual-reasoning puzzles. Halligan's benchmark includes GeeTest slide, gobang, icon and icon-crush replicas ([Halligan](https://github.com/code-philia/Halligan)).
- **What it checks.** Not documented in the sources we read.
- **How it fares.** A general research solver passed 25.4% of 390 live GeeTest tasks ([Halligan, USENIX Security 2025](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh)). Visual-reasoning CAPTCHAs from GeeTest and five other Chinese vendors were solved at up to 93.2% in 2026 ([ViPer](https://arxiv.org/abs/2601.06461)).
- **Who can use it.** Not checked.

Checked 2026-11-01.

## Friendly Captcha

- **What the visitor sees.** A widget that works in the background while the browser computes a proof of work.
- **What it checks.** A proof of work; the widget is open source (MIT, SDK MPL-2.0), but "verification is a SaaS": there is no server in the repositories ([friendly-challenge](https://github.com/FriendlyCaptcha/friendly-challenge); [SDK](https://github.com/FriendlyCaptcha/friendly-captcha-sdk)).
- **What the site receives.** A token checked against Friendly Captcha's service.
- **Who can use it.** Account required. Comparison pages disagree on whether a free non-commercial plan exists; we did not confirm either way.

Checked 2026-11-01.

## MTCaptcha

We found no current primary documentation in our sources. It appears in research only as a replica type in Halligan's benchmark and as 4 of 3,000 live solve tasks ([Halligan](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh), checked 2026-11-01). We will add a full entry once checked.

## Prosopo (Procaptcha)

- **What the visitor sees.** Depending on mode: nothing ("frictionless"), a proof of work ("pow"), or an image puzzle ("puzzle").
- **What it checks.** The frictionless mode uses a client-side detection library that is closed; the rest of the code is open under Apache-2.0 and self-hostable as four containers ([prosopo/captcha](https://github.com/prosopo/captcha)).
- **How it fares.** A general research solver passed 85.9% of 652 live Prosopo tasks ([Halligan](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh)).
- **Who can use it.** Hosted service or self-host. It markets itself as a drop-in replacement for reCAPTCHA, hCaptcha and Turnstile. Its own comparison page ranks Procaptcha first ([Prosopo blog](https://www.prosopo.io/blog/best-captcha/)).

All checked 2026-11-01.

## Others named in research

- **Fingerprint** (fingerprint.com): bot detection that labels traffic `bot: good|bad|not_detected`, with `bot_type: ai_agent` and Web Bot Auth verification ([docs](https://docs.fingerprint.com/docs/ai-agents), checked 2026-11-01).
- **Proof of Human** (formerly Roundtable): a closed behaviour-based detection API ([research.poh.org](https://research.poh.org/), checked 2026-11-01). It also publishes benchmarks in which its own product ranks first.
- **NetEase, Dingxiang, Shumei, Xiaodun and VTT**: Chinese visual-reasoning CAPTCHA vendors attacked alongside GeeTest in [ViPer](https://arxiv.org/abs/2601.06461) (checked 2026-11-01).
- **Lemin, Tencent, Yandex, BotDetect and Baidu**: present as local replicas in Halligan's 26-type benchmark ([repo](https://github.com/code-philia/Halligan), checked 2026-11-01). We have not checked their current products.

## How vendors now treat AI agents

Every large vendor added an agent feature between 2025 and 2026. All checked 2026-11-01.

| Vendor | Agent feature | Source |
|---|---|---|
| Cloudflare | Signed agents listed as Verified (2026-07-01); "Agent" bot category | [docs](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/) |
| Google | Fraud Defense agent dashboard, Web Bot Auth, policy by agent identity | [blog](https://cloud.google.com/blog/products/identity-security/introducing-google-cloud-fraud-defense-the-next-evolution-of-recaptcha) |
| hCaptcha | Enterprise agent detection; the agent pauses for its person when a challenge is needed | [docs](https://docs.hcaptcha.com/ent_overview) |
| Arkose Labs | Agent Trust Manager | [docs](https://developer.arkoselabs.com/docs/agent-trust-manager-overview.md) |
| DataDome | Agent Trust Score 0–100 | [docs](https://docs.datadome.co/docs/agent-trust-score.md) |
| HUMAN | Agent trust levels High / Medium / Low | [docs](https://docs.humansecurity.com/applications/about-agent-trust-levels.md) |
| AWS WAF | `web_bot_auth` labels | [docs](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html) |

What this means for agent builders is covered in [Build](@/build/_index.md) and [Signing your agent](@/build/signing.md). What each vendor weighs in its score is in [What vendors weigh](@/browser-score/what-vendors-weigh.md).

{% <note> %}
Every comparison page we found before writing this one was published by a vendor or by a company selling a related product. If you find an error here, or a vendor's documentation has changed, [tell us](@/about/_index.md).
{% </note> %}
