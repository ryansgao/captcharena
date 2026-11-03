+++
title = "Glossary"
description = "Short definitions of the terms used across CAPTCHArena, from ACT and attestation to Web Bot Auth, each with its own link anchor."
weight = 100
[extra]
checked = "2026-11-01"
+++

Terms in alphabetical order. Each heading has its own anchor, so other pages link straight to a definition.

### ACT

Anonymous Credit Tokens: a proposed credential holding a balance of "credit" that a site can lower when a visitor misbehaves, without learning who the visitor is. Proposed by Cloudflare in 2025 as a companion to [ARC](#arc) ([blog](https://blog.cloudflare.com/private-rate-limiting/), checked 2026-11-01).

### Agent

Short for AI agent: software driven by a language model that acts on the web for a person, for example by opening pages, filling forms and clicking. Cloudflare's category "Agent" means "User-directed agents visiting a page on behalf of a human" ([docs](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/), checked 2026-11-01).

### ARC

Anonymous Rate-Limited Credentials: an IETF draft that lets one credential be shown a fixed number of times per site, with each showing unlinkable to the others ([draft](https://datatracker.ietf.org/doc/html/draft-ietf-privacypass-arc-crypto-01), checked 2026-11-01). Part of the [Privacy Pass](#privacy-pass) family.

### Attestation

A signed statement from a device or platform that it is genuine and unmodified. [Private Access Tokens](#private-access-token) rely on it. Critics argue it ties web access to owning particular hardware.

### Bot score

A vendor's number for how likely a request is automated. Cloudflare's runs from 1 (automated) to 99 (likely human) ([docs](https://developers.cloudflare.com/bots/concepts/bot-score/), checked 2026-11-01). See [risk score](#risk-score).

### CAPTCHA

"Completely Automated Public Turing test to tell Computers and Humans Apart", a term coined in 2003 by von Ahn, Blum, Hopper and Langford ([paper](https://link.springer.com/content/pdf/10.1007/3-540-39200-9_18.pdf), checked 2026-11-03). Today the word covers any human check on a website, visible or not.

### CAPTCHA farm

A business where people are paid per solve to answer CAPTCHAs for customers, often sold as an API. Prices run from about $0.10 to $5.00 per thousand solves ([Broken Gates](https://arxiv.org/abs/2607.18659), checked 2026-11-01). See [the economics](@/learn/economics.md).

### Challenge page

A full-page check shown before a site loads, such as Cloudflare's "Just a moment…" page or AWS WAF's silent challenge. It runs browser checks and may show a CAPTCHA.

### ClickFix

A scam in which a fake CAPTCHA page tells the visitor to press keys and paste a command that installs malware. A real CAPTCHA never does this. See [Is this CAPTCHA real?](@/learn/is-this-captcha-real.md)

### Device Check

DataDome's invisible check that collects browser and hardware signals to spot automation, shown when evidence is too weak to block or challenge ([docs](https://docs.datadome.co/docs/device-check.md), checked 2026-11-01).

### Fingerprint

A set of measurements of a browser or connection (screen, fonts, graphics rendering, installed features, handshake details) that together identify it or show what it is. Vendors use fingerprints to spot automation and inconsistency. Also the name of a bot-detection company, Fingerprint.

### Half-life

On this site: the number of months from the publication of a CAPTCHA design that agents mostly fail to the first published report of agents mostly passing it. Published examples range from about 3 to 12 months (our summary of the literature; see [How AI agents fare](@/learn/ai-agents.md)). Nobody else tracks this number.

### Headless browser

A browser run without a visible window, usually by automation code. Vendors look for signs of it.

### Honeypot

A trap only a bot would fall into, such as a form field hidden from people that naive bots fill in. Some vendors also plant fake tokens and events in their widgets ([HUMAN docs](https://docs.humansecurity.com/applications/human-challenge.md), checked 2026-11-01).

### Invisible CAPTCHA

A check that shows the visitor nothing and decides from signals alone, such as reCAPTCHA v3 or Turnstile's Invisible mode.

### JA4

A fingerprint of the TLS handshake a client sends when it opens a secure connection; JA3 is its older form. Different browsers and HTTP libraries produce different JA4 values, so a mismatch with the claimed browser is a signal ([Cloudflare docs](https://developers.cloudflare.com/bots/additional-configurations/ja3-ja4-fingerprint/), checked 2026-11-01).

### PACT

Private Access Control Tokens: an approach announced on 2026-06-22 by Cloudflare, Mozilla, Google, Microsoft and Shopify in which sites that know a visitor vouch for them anonymously and browsers carry the vouching elsewhere ([Mozilla Hacks](https://hacks.mozilla.org/2026/06/pact-anonymous-credentials-for-the-web/), checked 2026-11-01). Not yet deployed.

### Personhood credential

A credential proving the holder is one unique real person without revealing which ([Adler et al., 2024](https://arxiv.org/abs/2408.07892), checked 2026-11-01). World ID is a deployed example.

### Privacy Pass

The IETF standard for anonymous tokens: an issuer checks something about you once and gives you tokens that sites can verify but cannot link to you (RFC 9576, 9577, 9578, June 2024; [IETF](https://datatracker.ietf.org/wg/privacypass/documents/), checked 2026-11-01).

### Private Access Token

Apple's use of [Privacy Pass](#privacy-pass) with device [attestation](#attestation), available since iOS 16 and macOS 13: the device proves it is genuine so the site can skip a CAPTCHA ([Cloudflare blog](https://blog.cloudflare.com/eliminating-captchas-on-iphones-and-macs-using-new-standard), checked 2026-11-01).

### Proof of work

A check where the visitor's browser spends CPU time finding an answer that the server can verify in one step. It prices requests instead of testing for a human. Used by Anubis, ALTCHA, Cap and others; see [open-source CAPTCHAs](@/learn/open-source.md).

### Residential proxy

A proxy that sends traffic through home internet connections so it looks like ordinary users. Research found such networks are largely built from devices whose owners did not meaningfully agree ([Mi et al., IEEE S&P 2019](https://cse.buffalo.edu/faculty/xmi/files/resi_paper.pdf), checked 2026-11-01). Several vendors now detect them.

### Risk score

The number a vendor computes from the signals it collects, estimating how likely the visitor is a bot. Scales differ: reCAPTCHA v3 uses 0.0–1.0, Arkose 0–100, Cloudflare 1–99. See [What happens when you tick the box](@/learn/how-captchas-work.md).

### Signed agent

An AI agent whose requests carry a [Web Bot Auth](#web-bot-auth) signature, so a site can verify which operator sent them. Cloudflare's signed-agents programme started in 2025 ([blog](https://blog.cloudflare.com/signed-agents/), checked 2026-11-01).

### Site key and secret key

The two keys a CAPTCHA vendor gives a site. The site key is public and goes in the page; the secret key stays on the site's server and is sent with [siteverify](#siteverify) requests.

### Siteverify

The vendor's server endpoint that a site calls to check a [token](#token). It answers whether the token is valid for that site and, for score products, returns the score. Without this step a CAPTCHA protects nothing.

### Telltale

Arkose Labs' name for a named risk signal in its response, such as `g-reputation-vpn` ([docs](https://developer.arkoselabs.com/docs/verify-api-v4-response-fields), checked 2026-11-01).

### Token

The string a CAPTCHA widget gives the page once the visitor passes. The site's server sends it to [siteverify](#siteverify) to confirm it. Tokens are short-lived and meant to be used once.

### Token service

A paid service that returns a valid CAPTCHA token for a given site key and page address, solved by people, models or both. See [CAPTCHA farm](#captcha-farm).

### Turnstile

Cloudflare's free CAPTCHA, which usually runs only background checks and asks for a click "if a further check is necessary" ([docs](https://developers.cloudflare.com/turnstile/concepts/widget/), checked 2026-11-01).

### WCAG 2.2 SC 3.3.8

The accessibility rule (Accessible Authentication, Level AA) that forbids a login step from depending on a cognitive test such as a puzzle, maths or transcription unless an alternative exists. Object recognition is an allowed exception at AA ([W3C](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html), checked 2026-11-01). See [CAPTCHAs and accessibility](@/defend/accessibility.md).

### Web Bot Auth

A protocol, being standardised at the IETF, in which a bot or agent signs each HTTP request with a key and publishes its public keys, so sites can verify who sent it. It identifies the software, not the person using it ([working group](https://datatracker.ietf.org/wg/webbotauth/about/), checked 2026-11-01). See [What still works](@/learn/what-lasts.md#web-bot-auth-and-signed-agents).
