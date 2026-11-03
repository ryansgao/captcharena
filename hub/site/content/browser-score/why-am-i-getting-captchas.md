+++
title = "Why am I getting so many CAPTCHAs?"
description = "The usual reasons a person, an office or an agent gets flagged: VPNs, shared addresses, blocked cookies, fresh profiles, privacy tools. What helps and what backfires."
weight = 20
[extra]
checked = "2026-11-01"
+++

If you see CAPTCHAs on every site, the cause is almost never that you look like a robot when you click. It is that the **invisible score** the site computed before you clicked was low. That score is built mostly from things about your connection and your browser, not from you. The common causes are below, then what helps and what makes it worse.

## The usual causes

### 1. A VPN or a data-centre address

Most VPN servers sit in hosting networks, the same networks that bots run from. Vendors document scoring exactly that:

- Arkose Labs' sample verify response flags "hosting" and "VPN" reputation ([Arkose docs](https://developer.arkoselabs.com/docs/verify-api-v4-response-fields), checked 2026-11-01).
- DataDome runs a "reputational" model for data-centre and residential-proxy addresses ([DataDome docs](https://docs.datadome.co/docs/threat-detection.md), checked 2026-11-01).
- AWS WAF has a known-data-centre bot rule that blocks by default in its bot rule group ([AWS docs](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html), checked 2026-11-01).
- hCaptcha's risk insights include "VPN or proxy usage" ([hCaptcha docs](https://docs.hcaptcha.com/ent_overview), checked 2026-11-01).

None of these signals says anything about you as a person. They describe the address your traffic comes from, which you share with everyone else on that VPN server.

### 2. Many people behind one address

Offices, schools, mobile carriers and virtual-desktop (VDI) setups often send thousands of people out through one or a few public addresses. To a vendor, that address looks like one very busy client. An admin of a virtual-desktop service with 5,000 customers described Google showing CAPTCHAs to "thousands of users behind shared public IPs" ([r/sysadmin](https://www.reddit.com/r/sysadmin/comments/1x29dxg/), checked 2026-11-01).

### 3. Blocked or cleared cookies

Scores rely on history. Researchers found reCAPTCHA v2 "relies heavily on cookies and browser history data" ([Plesner et al., arXiv 2409.08831](https://arxiv.org/abs/2409.08831), checked 2026-11-01). In 2016, a Google cookie aged nine days was enough for the tick box to pass alone ([Sivakorn et al.](https://www.blackhat.com/docs/asia-16/materials/asia-16-Sivakorn-Im-Not-a-Human-Breaking-the-Google-reCAPTCHA-wp.pdf), checked 2026-11-01). Cloudflare uses a cookie to smooth one user's score across requests ([Cloudflare docs](https://developers.cloudflare.com/bots/concepts/bot-score/), checked 2026-11-01). If your browser deletes cookies on every close, or blocks third-party cookies, each visit starts with no history.

### 4. A fresh browser profile

A new profile, a private window or a virtual desktop that resets at every login has the same problem: nothing to vouch for it. In a 2026 test of ten AI-agent setups on reCAPTCHA v3, the only one that passed ran inside a real, long-used browser profile; the others got "low trust scores (0.1–0.3)" ([Broken Gates, arXiv 2607.18659](https://arxiv.org/abs/2607.18659), checked 2026-11-01).

### 5. Privacy extensions and anti-fingerprinting settings

Cloudflare states that "fingerprinting protection, or canvas blockers can interfere" with its challenges, and that "VPN or proxy extensions might trigger additional security checks" ([Cloudflare docs](https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/), checked 2026-11-01). Privacy tools are a legitimate choice. The cost is that a browser hiding its details looks less like the ordinary browsers the score was trained on.

### 6. Automation, including AI agents

If a browser is driven by automation software, many vendors can tell. Cloudflare says plainly: "Automated browsers are not supported for solving production challenges" ([Cloudflare docs](https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/), checked 2026-11-01). AI agents also move differently from people. One study told agents from people by behaviour alone at an F1 score of 0.999 ([FP-Agent, arXiv 2605.01247](https://arxiv.org/abs/2605.01247), checked 2026-11-01).

## What legitimately helps

| If you are… | What helps | Why |
|---|---|---|
| A person on a VPN | Turn the VPN off for the site that keeps challenging you, if your situation allows it, or try another server | The address is often the biggest single factor |
| A person who clears everything | Keep one normal browser profile with cookies for everyday sites | History is what the score rewards |
| On an iPhone, iPad or Mac | Keep the system up to date; Apple devices can present **Private Access Tokens**, a privacy-preserving proof from the device that some sites accept instead of a CAPTCHA ([Cloudflare blog](https://blog.cloudflare.com/eliminating-captchas-on-iphones-and-macs-using-new-standard), checked 2026-11-01) | The site gets an attestation without learning who you are |
| An IT admin with shared addresses | Our reading, not a measured result: look at how many users share each public address, whether your egress addresses are listed as hosting, and whether virtual-desktop profiles keep cookies between sessions. Contact the vendor or the affected site with your address ranges | These are the levers the documented signals point to |
| An agent builder | Sign your agent's requests with **Web Bot Auth** and publish your key directory; keep a persistent, honest browser identity; hand the CAPTCHA to the person when one appears | Cloudflare lists signed agents as "Verified" since 2026-07-01 ([Cloudflare docs](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/), checked 2026-11-01); HUMAN gives cryptographically verified agents its "High" trust level ([HUMAN docs](https://docs.humansecurity.com/applications/about-agent-trust-levels.md), checked 2026-11-01). See [signing agents](@/build/signing.md) |

A signature does not guarantee access. As one hosted-browser company puts it, "a valid signature identifies traffic; the website still decides" ([Browserbase docs](https://docs.browserbase.com/welcome/identity-and-access.md), checked 2026-11-01). Some sites block declared agents on purpose; that is their choice to make.

## What backfires

### Stealth and anti-detection plugins

Plugins that disguise an automated browser as an ordinary one often make it easier to spot, not harder. A 2026 study of AI agents found that "stealth and anti-detection mechanisms often increase detectability" ([Fayolle et al., arXiv 2606.30119](https://arxiv.org/abs/2606.30119), checked 2026-11-01). Vendors check whether a browser's account of itself is consistent; AWS has a rule named for it, browser inconsistency ([AWS docs](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html), checked 2026-11-01). A disguise that fixes one test page can create the very contradiction the real detector punishes.

### Residential proxy pools

Paid "residential proxy" networks route your traffic through other people's home connections. We do not recommend them, for two reasons:

- **Consent.** Researchers measuring six million residential-proxy addresses found that "none of the 5 RESIP providers is a completely consent-based" network, and that compromised devices were among the hosts ([Mi et al., IEEE S&P 2019](https://cse.buffalo.edu/faculty/xmi/files/resi_paper.pdf), checked 2026-11-01).
- **They are detected.** Cloudflare sets traffic from residential-proxy networks to bot score 29, just under its "likely human" line ([Cloudflare docs](https://developers.cloudflare.com/bots/additional-configurations/detection-ids/additional-detections/), checked 2026-11-01). AWS flags a token obtained from a data-centre or VPN address and then used from a home or mobile address ([AWS docs](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html), checked 2026-11-01).

### Rotating addresses mid-session

Changing address in the middle of a visit breaks the link between your challenge and your session. Cloudflare will not accept a managed challenge solved "from a different IP than the original IP" ([Cloudflare docs](https://developers.cloudflare.com/cloudflare-challenges/concepts/how-challenges-work/), checked 2026-11-01).

### Judging yourself by a "bot test" page

A clean result on a public fingerprint test page does not mean a high score. A low score can occur "even when every fingerprint check it faces comes back clean", in one practitioner's words ([dev.to](https://dev.to/bshahin/why-your-recaptcha-v3-score-is-low-and-how-to-actually-raise-it-5554), checked 2026-11-01; the author runs a solving service). The only score that counts is the vendor's own, on a real key. [Our measurement page](https://measure.captcharena.org) shows you that.

## Fake CAPTCHAs: a different problem

If a "CAPTCHA" asks you to press keys, open a Run box, or paste a command into a terminal, it is not a CAPTCHA. It is malware. See [is this CAPTCHA real?](@/learn/is-this-captcha-real.md).
