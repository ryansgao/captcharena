+++
title = "The browser-score experiment: method"
description = "How we will measure what moves a real reCAPTCHA v3 score and Turnstile's challenge rate, one signal at a time, and what we will publish."
weight = 30
[extra]
checked = "2026-11-01"
status = "coming"
+++

{% <coming> %}
The measurement page is live, but the experiment has not started. Our reCAPTCHA v3 key is in Google's 7-day warm-up until about 2026-11-10. Runs start after that, and results will be published here and on the [Scoreboard](@/scoreboard/_index.md) with the raw data.
{% </coming> %}

## The question

Vendors document which signals they use (see [what each vendor weighs](@/browser-score/what-vendors-weigh.md)). None publishes **how much each one moves the score**. Ordinary users, IT admins and agent builders are all left guessing. We want to answer, with numbers:

- For **reCAPTCHA v3**: how much does each signal change the chance of a score of 0.7 or above?
- For **Cloudflare Turnstile**: how much does each signal change the chance that the widget asks for a click instead of passing silently?
- Which signals **interact**, for example whether a good address matters more for a browser with no history?

## Why this has not been done

The last published test that changed one signal at a time against Google's risk engine is from 2016. It found that a Google cookie aged nine days earned the tick-box pass, that a mismatched user agent forced the fallback CAPTCHA, and that screen size and mouse behaviour made no difference ([Sivakorn et al., Black Hat Asia 2016](https://www.blackhat.com/docs/asia-16/materials/asia-16-Sivakorn-Im-Not-a-Human-Breaking-the-Google-reCAPTCHA-wp.pdf), checked 2026-11-01). The model has changed many times since. Newer work tests something nearby, not this:

| Work | What it varied | Vendor | Year |
|---|---|---|---|
| [Sivakorn et al.](https://www.blackhat.com/docs/asia-16/materials/asia-16-Sivakorn-Im-Not-a-Human-Breaking-the-Google-reCAPTCHA-wp.pdf) | Cookie age, browsing, network type, user agent, screen size, mouse | reCAPTCHA v2 tick box | 2016 |
| [Web Runner 2049](https://www.securitee.org/files/webrunner_dimva2020.pdf) | Campus versus cloud addresses, eight automation tools | 15 anti-bot services | 2020 |
| [Gundelach et al.](https://arxiv.org/abs/2606.14525) | Header changes in headless Chromium, 10,000 sites | Mixed live sites | 2026 |
| [Broken Gates](https://arxiv.org/abs/2607.18659) | Agent framework (the whole environment at once) | reCAPTCHA v3, Turnstile, hCaptcha | 2026 |
| [Fayolle et al.](https://arxiv.org/abs/2606.30119), [FP-Agent](https://arxiv.org/abs/2605.01247) | Which layer separates agents from people, on the authors' own sites | Own classifiers | 2026 |

All checked 2026-11-01. None varies one signal at a time against a current vendor score, with repeated runs, controls and the raw signals logged next to each score. We searched for one on 2026-11-01 and found none.

## The instrument

The [measurement page](https://measure.captcharena.org) on our own domain runs real widgets with our own keys: reCAPTCHA v3, the reCAPTCHA v2 tick box, Turnstile in managed mode, and two self-hosted proof-of-work CAPTCHAs (ALTCHA and Cap). Each run:

- gets its verdict from the **vendor's own server** (or the self-hosted software's server), never from our page;
- records, next to the verdict, the browser's own description of itself and an open-source automation check, so a score can be explained, not just reported;
- records the **egress class** of the run: home broadband, mobile, VPN, or data centre;
- stores no IP address. Runs from our own machines are tagged with their condition.

## The design: change one signal at a time

We start from two fixed setups (anchors) and change one signal per arm, keeping everything else the same.

| Signal | Settings compared |
|---|---|
| Network (egress class) | A hosting-network VPN server; a second VPN server; a home broadband line; a mobile connection; a fixed address from an internet provider. **No residential proxy pool**, for the consent reasons on [why am I getting so many CAPTCHAs](@/browser-score/why-am-i-getting-captchas.md#residential-proxy-pools) |
| Browser build | Open-source Chromium versus Google Chrome stable |
| Automation attached at scoring time | No automation connected while the page loads versus a standard automation connection |
| State | Fresh profile; profile aged nine days or more with no sign-in; aged profile signed in to a Google account |
| Behaviour before scoring | Immediate versus a short, human-paced visit (dwell, scroll, pointer movement) |
| Consistency | The browser's description as it is versus a deliberate contradiction (for example, a time zone from another continent) |

Then a second stage tests the binary versions of these six signals together in a fractional design of 16 cells, so main effects can be separated from two-way interactions.

### Repetitions and controls

- **About 25 runs per setting.** That is enough to tell a 20% pass rate from a 60% one with standard statistical confidence.
- **Positive control:** an ordinary phone and laptop on a home connection, loading the same page from time to time.
- **Negative control:** a stock headless browser from a cloud machine.
- **Drift check:** the anchor setting is repeated every ten runs, because the vendor's model learns from our own traffic.
- **Order and pacing:** randomised order, spread over at least three days and different times of day, at most one load every one to three minutes per address.

### Analysis

- reCAPTCHA v3 returns only four values without billing (0.1, 0.3, 0.7, 0.9), so we treat it as an ordered outcome and report the chance of 0.7 or above per setting, with confidence intervals.
- Turnstile: the share of runs that asked for a click, per setting.
- The logged signals are compared with the outcomes to explain each effect.

## Limits we already know

- **Results hold for our keys and our site.** reCAPTCHA "learns by seeing real traffic on your site" ([Google docs](https://developers.google.com/recaptcha/docs/v3), checked 2026-11-01). Your site's model may weigh things differently.
- **Vendors retrain often.** Cloudflare says its machine-learning engine is retrained frequently ([Cloudflare docs](https://developers.cloudflare.com/bots/concepts/bot-detection-engines/), checked 2026-11-01). Every result will carry its date.
- **Our own traffic shapes our key.** The drift check exists to catch this.
- **hCaptcha is excluded.** Its terms forbid passing its challenges with automated tools or AI ([hCaptcha terms](https://www.hcaptcha.com/terms), checked 2026-11-01). We will not test it without written permission.

## What will be published, and when

After the warm-up ends (about 2026-11-10) and the runs are complete:

1. **Effect sizes**: for each signal, how much it changed the chance of a good reCAPTCHA v3 score and of a Turnstile click, with confidence intervals.
2. **Score distributions** by egress class and setup, including the human controls.
3. **The raw data** (one line per run, no IP addresses) and the full method, so anyone can check the analysis.
4. **The measurement page's code**, so another site owner can run the same test on their own keys.

What we will **not** publish: a tuned setup for getting past any vendor's score, per-site recipes, or anything aimed at disguising automated traffic. The aim is to show users, admins and agent builders which honest choices (a stable profile, an ordinary connection, a declared identity) matter and by how much.
