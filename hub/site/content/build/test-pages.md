+++
title = "Test pages for agent developers, and which ones still work"
description = "The public CAPTCHA demo pages and bot-detection test sites agent developers use as fixtures, their measured status, and a maintained alternative."
weight = 40
[extra]
checked = "2026-11-01"
+++

Agent frameworks need somewhere to test what happens when a CAPTCHA appears. In practice the industry uses the public demo pages that CAPTCHA vendors and solving companies publish. These pages were never meant as test fixtures, nobody promises to keep them working, and several have quietly broken. This page lists them with their measured status, adds the bot-detection test sites, and describes the measurement page we maintain.

## Be a good guest on other people's demo pages

- **Do not point load at them.** A demo page is a vendor's sales page, not your CI server. Run a test by hand or a few times a day at most; never in a loop or from many workers.
- **Expect your address to be judged.** Repeated solves from one address can earn a block. One open solver's own documentation warns that more than *"a couple of reCAPTCHA challenges a day"* may lead to one ([Buster listing on addons.mozilla.org](https://addons.mozilla.org/addon/1013715/), checked 2026-11-01).
- **Read the vendor's terms.** hCaptcha's terms forbid AI passing its challenges, including on its demo ([policy map](@/build/policy-map.md)).
- **Test keys test nothing.** reCAPTCHA's and hCaptcha's test keys always pass; Turnstile's dummy keys pass, fail or force an interactive widget on demand. They are useful for wiring and hand-off flows, not for measuring whether a real widget would accept your agent ([Google](https://developers.google.com/recaptcha/docs/faq), [hCaptcha](https://docs.hcaptcha.com/), [Cloudflare](https://developers.cloudflare.com/turnstile/troubleshooting/testing/), checked 2026-11-01).

## Public CAPTCHA demo pages and their status

Status measured with a plain HTTP request (desktop Chrome user agent) on 2026-11-01, and in a real browser in October 2026 where noted. "Loads" means the page answered; it does not mean every widget on it works.

| Page | What it shows | Status | Checked |
|---|---|---|---|
| [google.com/recaptcha/api2/demo](https://www.google.com/recaptcha/api2/demo) | Google's official reCAPTCHA v2 demo | Loads (HTTP 200). Used as the end-to-end CAPTCHA test in Stagehand ([PR #1752](https://github.com/browserbase/stagehand/pull/1752)). | 2026-11-01 |
| [recaptcha-demo.appspot.com](https://recaptcha-demo.appspot.com/) | Google's reCAPTCHA demos, including v3 with the score shown | Loads (200) | 2026-11-01 |
| [accounts.hcaptcha.com/demo](https://accounts.hcaptcha.com/demo) | hCaptcha's demo | Loads (200). Its terms forbid AI passing challenges. | 2026-11-01 |
| [2captcha.com/demo](https://2captcha.com/demo) | A solving company's demo hub, many CAPTCHA types | Loads (200). In a browser in October 2026: the MTCaptcha demo redirected away (removed), the KeyCAPTCHA demo showed a blank widget with console errors, the GeeTest v3 demo never loaded ("Loading GeeTest…", v3 servers retired), and the rotate demo gave no fresh verdict. Stagehand's Turnstile test on this site *"was later removed"*. | 2026-11-01; widgets 2026-10-19 |
| [nopecha.com/demo](https://nopecha.com/demo) | A solving company's demo hub | Loads (200). In October 2026 its AWS WAF demo returned 403, and its FunCaptcha demo only said it required the company's extension. | 2026-11-01; widgets 2026-10-19 |
| [demo.arkoselabs.com](https://demo.arkoselabs.com/) | Arkose Labs demo | Loads (200), but its only script has an empty path segment where a public key normally sits, so it probably renders no challenge. No other public Arkose demo was found. | 2026-11-01 |
| [seleniumbase.io/apps/turnstile](https://seleniumbase.io/apps/turnstile) | A Turnstile test page | Loads (200) | 2026-11-01 |
| [peet.ws/turnstile-test/](https://peet.ws/turnstile-test/) | A Turnstile test page | Loads (200) | 2026-11-01 |
| [halligan.pages.dev](https://halligan.pages.dev/) | Project page of the Halligan research solver | Loads (200) | 2026-11-01 |
| [neal.fun/not-a-robot/](https://neal.fun/not-a-robot/) | A 48-level comedy CAPTCHA game, not a security product | 403 to a plain request (a bot wall, not down) | 2026-11-01 |

The pattern: the top-level pages load, but individual widgets on them rot. Vendors with no self-serve keys (Arkose, DataDome, HUMAN) have no usable public demo at all, so a framework that tests only on demo pages never meets them.

## Bot-detection and fingerprint test sites

These do not show CAPTCHAs. They show what a site's bot detection can see about your browser, which often decides whether a CAPTCHA appears at all. All answered HTTP 200 on 2026-11-01.

| Site | What it reports |
|---|---|
| [bot.sannysoft.com](https://bot.sannysoft.com/) | Common automation tells in the browser |
| [CreepJS](https://abrahamjuliot.github.io/creepjs/) | Fingerprint and lie detection; open source (MIT) |
| [browserscan.net/bot-detection](https://www.browserscan.net/bot-detection) | Bot-detection checks |
| [nowsecure.nl](https://nowsecure.nl/) | A Cloudflare-protected test page |
| [pixelscan.net](https://pixelscan.net/) | Fingerprint consistency |
| [deviceandbrowserinfo.com/are_you_a_bot](https://deviceandbrowserinfo.com/are_you_a_bot) | Bot checks, plus notes on headless detection |
| [bot-detector.rebrowser.net](https://bot-detector.rebrowser.net/) | Automation-library leaks |
| [demo.fingerprint.com](https://demo.fingerprint.com/) | A commercial fingerprinting vendor's demo |
| [iphey.com](https://iphey.com/) | Fingerprint and address checks |
| [amiunique.org](https://amiunique.org/) | Fingerprint uniqueness (research project) |

{% <note> %}
Several of these sites are run by companies that sell stealth or scraping tools, and some are tuned so that tools can "pass the test". A clean result there does not mean a real vendor would let your agent through. Our [browser score](@/browser-score/_index.md) section explains what the real scores are made of.
{% </note> %}

## A maintained fixture: measure.captcharena.org

[measure.captcharena.org](https://measure.captcharena.org) serves **real CAPTCHA widgets on our own domain, with our own keys**, and shows the verdict the vendor's own server returned for each attempt (for reCAPTCHA v3, the score). Unlike a clone or a test key, it answers the question that matters: *would a real site have accepted this?* Unlike a vendor's demo page, it exists to be tested against, and we maintain it.

What it serves, as of 2026-11-03:

| Widget | Kind | Verdict from |
|---|---|---|
| reCAPTCHA v3 | Invisible score | Google's server |
| reCAPTCHA v2 tick box | Tick box, with a picture or audio challenge when Google asks for one | Google's server |
| Cloudflare Turnstile (managed) | Mostly invisible; a click when Cloudflare asks for one | Cloudflare's server |
| ALTCHA | Open-source proof of work, self-hosted | Our server |
| Cap | Open-source proof of work, self-hosted | Our server |

How it differs from the demo pages above:

| | Vendor and solver demo pages | measure.captcharena.org |
|---|---|---|
| Real widget, real key | Yes | Yes |
| Server verdict shown | Sometimes | Always |
| Built and kept working as a test fixture | No | Yes |
| Covers open-source CAPTCHAs | No | Yes, self-hosted ones |
| hCaptcha | Yes (its terms apply) | No; only ever with hCaptcha's written permission |
| Stores your IP address or sets its own cookie | Varies | No (country only) |

Each widget has a daily limit on public checks, so heavy use from one visitor uses up the day for everyone. Please use it the same way as any other shared page: a person's pace, not a load test. If you need to run an agent against it repeatedly, [contact us](@/contact/_index.md) first.

The [scoreboard](@/scoreboard/_index.md) shows what we measure there, and its [method page](@/scoreboard/method.md) explains how.

## Playbook per CAPTCHA kind

{% <coming> %}
A per-kind playbook for agent developers, built from our own measurements: for each CAPTCHA kind, what usually decides the outcome (the invisible score, a time limit, pointer behaviour, or the puzzle itself) and what a well-behaved agent should do there. Published after review.
{% </coming> %}
