+++
title = "Play: try real CAPTCHAs and see the server's verdict"
description = "Solve real reCAPTCHA, Turnstile, ALTCHA and Cap widgets on our own domain and see what each vendor's server decides. Practice puzzles are coming."
sort_by = "weight"
[extra]
checked = "2026-11-03"
+++

Most CAPTCHA demo pages show you a puzzle and a green tick. They rarely show what matters: the verdict the vendor's server gives the site, and the invisible score behind it. Here you can see both.

<p><a class="cta" href="https://measure.captcharena.org">Open the live measurement page</a></p>

## What you can play now

| What | What you see | Status (2026-11-03) |
|---|---|---|
| Google reCAPTCHA v3 | No puzzle. Your browser's score from 0.0 to 1.0, as Google's server returns it to the site | Live, real key |
| Google reCAPTCHA v2 tick box | The "I'm not a robot" box, sometimes a picture or audio challenge, then the server verdict | Live, real key |
| Cloudflare Turnstile | Usually no puzzle; whether Cloudflare's server accepts the token, and whether it asked you to click | Live, real key |
| ALTCHA | A proof-of-work check your browser computes; verified by our own server | Live, self-hosted |
| Cap | A proof-of-work check; verified by its own server, which we host | Live, self-hosted |

All five run on [measure.captcharena.org](https://measure.captcharena.org) with keys we own, on our own domain, and every token is checked by the vendor's own server (or, for the self-hosted ones, by the software's own verifier). The page stores no IP address and sets no cookie of ours. More about what the page measures: [Browser score](@/browser-score/_index.md).

{% <note> %}

The domain is new, so its first week (until about 2026-11-10) is a warm-up. Google warns that reCAPTCHA scores in a site's first days [may differ](https://docs.cloud.google.com/recaptcha/docs/interpret-assessment-website) from later ones. Your result is real; just don't read much into a single low score this week.

{% </note> %}

## Coming next

{% <coming> %}

**Practice puzzles, you versus the best agent.** Open-source research puzzles (unbranded, clearly labelled "practice puzzle, not a real CAPTCHA") where you see your time and accuracy next to the best AI agent's on the exact same puzzle. Sources and licences: [Practice puzzles](@/play/practice-puzzles.md).

{% </coming> %}

{% <coming> %}

**More open CAPTCHAs, running unmodified.** Anubis, mCaptcha, Procaptcha and go-captcha beside ALTCHA and Cap, each with its own verify result. See [Open-source CAPTCHAs](@/learn/open-source.md) for how each works.

{% </coming> %}

## Elsewhere on the web

- [neal.fun "I'm Not a Robot"](https://neal.fun/not-a-robot/), a comedy game of increasingly absurd CAPTCHA levels by Neal Agarwal (launched 2025-09-16). It "offers 0% security and 100% user annoyance", in its author's words on its [embed page](https://neal.fun/not-a-robot/embed/) (checked 2026-11-01). It is a game, not a security check.
- Detection test pages that show what your browser reveals, such as [EFF Cover Your Tracks](https://coveryourtracks.eff.org/) and [BrowserLeaks](https://browserleaks.com/) (checked 2026-11-01).

## Rules every page here follows

- No practice puzzle ever imitates a real vendor's look, name or logo. Fake CAPTCHAs are a common malware lure, and we will not train people to trust lookalikes.
- No page here ever asks you to press a key combination, open a terminal, paste anything or download a file. If a "CAPTCHA" asks for that anywhere, it is an attack: [how to spot a fake CAPTCHA](@/learn/is-this-captcha-real.md).
