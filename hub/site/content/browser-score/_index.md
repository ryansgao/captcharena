+++
title = "Browser score: the invisible check before any CAPTCHA"
description = "What the hidden risk score behind reCAPTCHA, Turnstile and other CAPTCHAs is, what it looks at, and a live page that shows your own result."
sort_by = "weight"
[extra]
checked = "2026-11-03"
+++

**Check your own browser now: [measure.captcharena.org](https://measure.captcharena.org)**

Before you see a puzzle, the site has usually already judged your browser. We call that judgement the **browser score**: the risk estimate a CAPTCHA or bot-defence vendor makes about your session, from signals such as your network address, your browser and its history, before deciding whether to let you through silently, show a tick box, show a puzzle, or block you.

Every major vendor works this way, and the puzzle is the fallback (all checked 2026-11-01):

- **reCAPTCHA v3** shows nothing at all. It returns a score from 0.0 ("very likely a bot") to 1.0 ("very likely a good interaction"), and the site decides what to do ([Google docs](https://developers.google.com/recaptcha/docs/v3)).
- **reCAPTCHA v2**'s picture grid is "only triggered when the risk score is high" ([Broken Gates, arXiv 2607.18659](https://arxiv.org/abs/2607.18659)).
- **Cloudflare Turnstile** in its managed mode asks for a click only "if a further check is necessary" ([Cloudflare docs](https://developers.cloudflare.com/turnstile/concepts/widget/)).
- **hCaptcha**'s paid "99.9% Passive" mode aims to challenge fewer than 0.1% of real people ([hCaptcha docs](https://docs.hcaptcha.com/pro)).
- **Arkose Labs** documents risk bands (low 0–40, medium 41–80, high 81–100) that steer which challenge you get ([Arkose docs](https://developer.arkoselabs.com/docs/risk-score.md)).
- **DataDome** runs a ladder: an invisible device check, then a slider, then a block ([DataDome docs](https://docs.datadome.co/docs/threat-detection.md)).

So whether you see a CAPTCHA at all, and how hard it is, is mostly decided by a score you never see.

## Who this section is for

- **Curious people** who want to know why one browser sails through and another gets a wall of puzzles.
- **IT admins** whose users sit behind one shared address, a VPN or virtual desktops, and get flagged all day.
- **Agent builders** who want their agents to be accountable and recognised, not to hide.

This section explains what vendors weigh and what published research has measured. It is not a guide to fooling a score. Disguising a browser tends to make things worse (see [why am I getting so many CAPTCHAs](@/browser-score/why-am-i-getting-captchas.md)), and the lasting route for agents is to identify themselves ([signing agents](@/build/signing.md)).

## What the live measurement page shows you

[measure.captcharena.org](https://measure.captcharena.org) runs real CAPTCHAs on our own domain, with our own keys, and shows you the verdict each one gave your browser. Every token is checked by the vendor's own server, or by the CAPTCHA software's own server for the self-hosted ones, never judged by our page alone. As of 2026-11-03 it runs five checks:

| Check | What it is | What you see |
|---|---|---|
| reCAPTCHA v3 | Google's invisible score | Your real score on our key |
| reCAPTCHA v2 | Google's "I'm not a robot" tick box | Whether the tick passed alone or you got a puzzle, and Google's verdict |
| Cloudflare Turnstile | Cloudflare's managed widget | Whether it passed silently or asked you to click, and Cloudflare's verdict |
| ALTCHA | Open-source proof of work, self-hosted | Whether your browser solved it and the server accepted it |
| Cap | Open-source proof of work, self-hosted | Whether it was solved and accepted, and how long it took |

**Proof of work** means your browser does a small calculation before the form is accepted; it asks nothing of you.

### Privacy on the measurement page

- **No IP address is stored.** The only location we keep is the country, which Cloudflare passes to us.
- **No cookie of ours.** The Google and Cloudflare widgets are third-party scripts and follow their own policies.
- **A daily cap** on checks protects the free tiers of the vendor keys, so the page may pause late in a busy day.

## Why there are no published score distributions yet

Google warns that reCAPTCHA scores "within 7 days of implementation might differ from the long-term production scores" ([Google docs](https://docs.cloud.google.com/recaptcha/docs/interpret-assessment-website), checked 2026-11-01). Our reCAPTCHA v3 key went live on 2026-11-03, so its warm-up runs until about **2026-11-10**. Your own result is real now, but we will not publish distributions (what scores phones, laptops, VPNs and agents typically get) until after the warm-up. The design of that study is on [the experiment page](@/browser-score/experiment.md).

{% <note> %}
Without a billing account, reCAPTCHA returns only four score values: 0.1, 0.3, 0.7 and 0.9 ([Google docs](https://docs.cloud.google.com/recaptcha/docs/interpret-assessment-website), checked 2026-11-01). Our key has no billing, so your score will be one of those four. A score on our site also says little about your score elsewhere: reCAPTCHA "learns by seeing real traffic on your site" ([Google docs](https://developers.google.com/recaptcha/docs/v3), checked 2026-11-01), so each site's model differs.
{% </note> %}

## In this section

- [What each vendor weighs in its score](@/browser-score/what-vendors-weigh.md): signals per vendor, documented or reverse-engineered, and what you see at each score band.
- [Why am I getting so many CAPTCHAs?](@/browser-score/why-am-i-getting-captchas.md): the usual causes, and what helps or backfires.
- [The browser-score experiment](@/browser-score/experiment.md): our planned one-signal-at-a-time measurement.

For the basics of how a CAPTCHA decides, see [how CAPTCHAs work](@/learn/how-captchas-work.md).
