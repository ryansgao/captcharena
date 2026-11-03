+++
title = "CAPTCHA fact sheets: price, free tier, privacy, hosting"
description = "Dated, sourced facts for each CAPTCHA product: what it costs, what the free tier covers, where data goes, and whether you can host it yourself."
weight = 30
[extra]
checked = "2026-11-03"
+++

One table per product, in alphabetical order within each group. Every cell carries the date it was checked and its source. Prices and free tiers change often, so check the vendor's page before you buy. Where two sources disagree, the cell says **conflicting**. Where we did not check something, the cell says **not checked**.

{% <note> %}
Prices are list prices as published by the vendor. "Claims" are the vendor's own statements, not our measurements. Measured resistance against AI agents and paid solvers will be added from the [Scoreboard](@/scoreboard/_index.md) after the first runs. For what each product is and how it works, see [Vendors](@/learn/vendors.md) and [open-source CAPTCHAs](@/learn/open-source.md).
{% </note> %}

## Hosted services

### reCAPTCHA

Google's CAPTCHA, now part of Google Cloud Fraud Defense.

| Fact | Detail | Checked | Source |
|---|---|---|---|
| Free tier | 10,000 free assessments per month after the move to Google Cloud projects | 2026-11-01 | [Google migration overview](https://docs.cloud.google.com/recaptcha/docs/migration-overview) |
| Over the free tier | Keys that are not migrated or not billed return errors; SiteVerify fails open over quota | 2026-11-01 | [Google migration overview](https://docs.cloud.google.com/recaptcha/docs/migration-overview), [Google FAQ](https://docs.cloud.google.com/recaptcha/docs/faq?hl=de) |
| Migration | Classic keys stopped in Q3 2024; automated migration to Google Cloud projects ran from Q4 2025 and completed in Q1 2026 | 2026-11-01 | [Google migration overview](https://docs.cloud.google.com/recaptcha/docs/migration-overview) |
| Privacy role | From 2026-04-02 the badge drops Google's privacy and terms links; the site owner becomes the data controller | 2026-11-01 | [Google FAQ](https://docs.cloud.google.com/recaptcha/docs/faq?hl=de) |
| Score detail without billing | Four score levels only (0.1, 0.3, 0.7, 0.9); 11 levels and reason codes need billing | 2026-11-01 | [Google docs](https://docs.cloud.google.com/recaptcha/docs/interpret-assessment-website) |
| Rebrand | Google Cloud Fraud Defense announced 2026-04-22; existing keys keep working (secondary source) | 2026-11-01 | [heise](https://heise.de/-11273871) |
| Hosting | Google-hosted only | 2026-11-01 | [Google docs](https://developers.google.com/recaptcha/docs/v3) |
| Mainland China | Site owners report Google products are blocked there | 2026-11-01 | [r/webdev](https://www.reddit.com/r/webdev/comments/1ncqret/) (owner reports) |
| Accessibility grade | v2: E; v3: B (a11yboost 2025, manual audit, see [accessibility](@/defend/accessibility.md)) | 2026-11-01 | [a11yboost](https://a11yboost.com/articles/are-captcha-systems-failing-accessibility) |

### Cloudflare Turnstile

| Fact | Detail | Checked | Source |
|---|---|---|---|
| Free tier | "Up to 20 widgets" per account, 10 hostnames per widget, no published limit on challenges | 2026-11-01 | [Cloudflare plans](https://developers.cloudflare.com/turnstile/plans/) |
| Needs other Cloudflare services? | No; usable "independently without requiring other Cloudflare services" | 2026-11-01 | [Cloudflare plans](https://developers.cloudflare.com/turnstile/plans/) |
| Paid tier | Not checked | — | — |
| Modes | Managed (a click only "if a further check is necessary"), Non-interactive, Invisible | 2026-11-01 | [Cloudflare docs](https://developers.cloudflare.com/turnstile/concepts/widget/) |
| Apple devices | Uses Private Access Tokens | 2026-11-01 | [Cloudflare blog](https://blog.cloudflare.com/eliminating-captchas-on-iphones-and-macs-using-new-standard) |
| Automation | "Automated browsers are not supported for solving production challenges" | 2026-11-01 | [Cloudflare docs](https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/) |
| Accessibility | Claims "WCAG 2.2 AAA compliance"; a11yboost 2025 grade A+ | 2026-11-01 | [Cloudflare plans](https://developers.cloudflare.com/turnstile/plans/), [a11yboost](https://a11yboost.com/articles/are-captcha-systems-failing-accessibility) |
| Hosting | Cloudflare-hosted only | 2026-11-01 | [Cloudflare plans](https://developers.cloudflare.com/turnstile/plans/) |

### hCaptcha

| Fact | Detail | Checked | Source |
|---|---|---|---|
| Free tier | "Basic (Free)", $0; no request limit stated | 2026-11-03 | [hCaptcha pricing](https://www.hcaptcha.com/pricing) |
| Pro | $139 per month billed monthly, or $99 per month billed yearly; "100K monthly evals included, then $0.99/1K"; adds "99.9% Passive Mode", analytics; free trial | 2026-11-03 | [hCaptcha pricing](https://www.hcaptcha.com/pricing) |
| Enterprise | "Talk to Sales"; adds risk scores and a fully passive (no-CAPTCHA) mode | 2026-11-03 | [hCaptcha pricing](https://www.hcaptcha.com/pricing) |
| Passive mode | "99.9% Passive" aims to show challenges to "less than 0.1% of users" | 2026-11-01 | [hCaptcha docs](https://docs.hcaptcha.com/pro) |
| Privacy claim | "Complies with GDPR, CCPA, LGPD, PIPL, and more" (vendor claim) | 2026-11-03 | [hCaptcha pricing](https://www.hcaptcha.com/pricing) |
| Terms | Forbid passing challenges with "bots, scripts, or any other form of artificial intelligence"; also bind visitors | 2026-11-01 | [hCaptcha terms](https://www.hcaptcha.com/terms) (updated 2025-11-17) |
| Hosting | hCaptcha-hosted only | 2026-11-01 | [hCaptcha docs](https://docs.hcaptcha.com/) |
| Accessibility grade | C (a11yboost 2025) | 2026-11-01 | [a11yboost](https://a11yboost.com/articles/are-captcha-systems-failing-accessibility) |

### Friendly Captcha

| Fact | Detail | Checked | Source |
|---|---|---|---|
| Free tier | **Conflicting.** Third-party comparison pages disagree: some say "No free plan", others describe a non-commercial free plan. The vendor's pricing page was not reachable at the address we tried | 2026-11-01 (comparison pages), 2026-11-03 (vendor page) | Vendor-written comparison pages, among them [Prosopo](https://prosopo.io/blog/top-hcaptcha-alternatives/), [Cap](https://capjs.js.org/guide/best-captcha-alternatives.html) and [cside](https://cside.com/blog/best-captcha-alternatives) |
| Type | Proof of work | 2026-11-01 | [GitHub](https://github.com/FriendlyCaptcha/friendly-challenge) |
| Open source | Widget MIT (v1) and SDK MPL-2.0 (v2); verification is a hosted service, so not self-hostable end to end | 2026-11-01 | [friendly-challenge](https://github.com/FriendlyCaptcha/friendly-challenge), [friendly-captcha-sdk](https://github.com/FriendlyCaptcha/friendly-captcha-sdk) |
| Price, data location | Not checked | — | — |

### Procaptcha (Prosopo)

| Fact | Detail | Checked | Source |
|---|---|---|---|
| Free tier | "Free forever", up to 10,000 requests per month | 2026-11-03 | [Prosopo pricing](https://prosopo.io/pricing/) |
| Paid | Professional $39 per month (100,000 requests) to $139 per month (1 million); 30-day trial; above that, an enterprise plan from $1,990 per month | 2026-11-03 | [Prosopo pricing](https://prosopo.io/pricing/) |
| Privacy | "GDPR-compliant, no cross-site tracking" on Free and Professional (vendor claim); EU-only processing only on Enterprise; storage location for lower plans not stated | 2026-11-03 | [Prosopo pricing](https://prosopo.io/pricing/) |
| Self-hosting | Open source (Apache-2.0), self-hostable in four containers for the proof-of-work and puzzle modes; the "frictionless" detection library is closed | 2026-11-01 | [GitHub](https://github.com/prosopo/captcha) |
| Note | Prosopo publishes a "Best CAPTCHA" ranking that places Procaptcha first | 2026-11-01 | [Prosopo blog](https://www.prosopo.io/blog/best-captcha/) |

## Open-source and self-hosted

These run on your own server. "Free" means no licence fee; you pay for hosting and upkeep.

| Product | Type | Licence | Price | Last code push | Checked | Source |
|---|---|---|---|---|---|---|
| **ALTCHA** | Proof of work; v3 adds memory-hard Argon2 and scrypt | MIT | Open-source core free. Paid: ALTCHA Cloud from €47 per month (EU-hosted), Sentinel (self-hosted) from €99 per month, WordPress plugin free plan or €18.90 per month | 2026-10-22 | 2026-11-03 (prices), 2026-11-01 (code) | [ALTCHA pricing](https://altcha.org/pricing/), [GitHub](https://github.com/altcha-org/altcha) |
| ALTCHA v3 change | Users report free features from v2.x were removed in v3; the vendor's pricing page does not say which | — | — | — | 2026-11-03 | [r/Wordpress](https://www.reddit.com/r/Wordpress/comments/1tbb644/), [ALTCHA pricing](https://altcha.org/pricing/) |
| **Anubis** | SHA-256 proof-of-work reverse proxy against AI scrapers | MIT | Free; removing the mascot branding requires payment | 2026-10-29 | 2026-11-01 | [GitHub](https://github.com/TecharoHQ/anubis) |
| **Cap** | Proof of work plus optional "instrumentation challenges" | Apache-2.0 (LICENSE file) | Free | 2026-10-29 | 2026-11-01 | [GitHub](https://github.com/tiagozip/cap) |
| **mCaptcha** | SHA-256 proof of work, difficulty rises under load | AGPL-3.0 (modified versions must offer source to users) | Free | 2025-10-07 (no push in about 13 months; treat as slowing) | 2026-11-01 | [GitHub](https://github.com/mCaptcha/mCaptcha) |
| **PrivateCaptcha** | Proof of work with adaptive difficulty (Go) | PolyForm Noncommercial: source-available, not open source; commercial use needs another licence | Hosted pricing not checked (the pricing page did not load for us) | 2026-10-31 | 2026-11-01 (licence), 2026-11-03 (pricing attempt) | [GitHub](https://github.com/PrivateCaptcha/PrivateCaptcha) |
| **Procaptcha** | See above | Apache-2.0 | Free self-hosted | 2026-10-31 | 2026-11-01 | [GitHub](https://github.com/prosopo/captcha) |

{% <note> %}
Proof-of-work cost needs tuning per device. One owner reported that with ALTCHA, "mobile users were waiting seconds or desktop/server users were finishing in a few milliseconds" ([r/webdev](https://www.reddit.com/r/webdev/comments/1v0s4kf/), checked 2026-11-01). Test on a low-end phone before you raise the difficulty.
{% </note> %}

## Bot management (sales-led)

These vendors score all traffic, not only one form. None offers a free self-serve plan that we found.

| Vendor | How you buy | What we know about price | Checked | Source |
|---|---|---|---|---|
| **Arkose Labs** | Sales; no self-serve keys found | Not published | 2026-11-01 | [Arkose Labs](https://arkoselabs.com/latest-news/arkose-labs-launches-arkose-matchkey) |
| **DataDome** | Sales; 30-day trial; no ongoing free tier | About $45,960 per year for an "Essentials" listing on AWS Marketplace, as reported by third parties (not confirmed with DataDome) | 2026-11-01 | [cside](https://cside.com/blog/datadome-pricing), [GetApp](https://www.getapp.com/security-software/a/datadome-bot-mitigation/) |
| **HUMAN** (formerly PerimeterX) | Sales-led, as far as we know (not verified) | Not checked | 2026-11-01 | [HUMAN docs](https://docs.humansecurity.com/applications/bd-detection-overview.md) |

## Not yet covered

GeeTest, MTCaptcha, Yandex SmartCaptcha, AWS WAF CAPTCHA, Akamai, Kasada and mosparo are not on this page yet. Their free tiers and prices were not checked.
