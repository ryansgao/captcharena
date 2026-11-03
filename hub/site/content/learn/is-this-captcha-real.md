+++
title = "Is this CAPTCHA real? How to spot a fake one"
description = "Fake CAPTCHAs that tell you to press keys and paste a command are a common way to install malware. How the scam works, how to spot it, what to do."
weight = 90
[extra]
checked = "2026-11-03"
+++

## The one rule

**A real CAPTCHA never asks you to open anything, press a keyboard shortcut, paste text, or download a file.**

A real CAPTCHA asks you to tick a box, pick pictures, drag a slider, or wait a moment. That is all. If a "verify you are human" page tells you to press the Windows key and R, open Terminal, press Ctrl+V, or run something, it is not a CAPTCHA. It is an attack. Close the tab.

## What the fake looks like

The scam is called **ClickFix**. You visit a website, often a normal one that has been hacked. A page appears that looks like a familiar "I'm not a robot" check or a Cloudflare "Verify you are human" screen. Then it gives you "verification steps", for example:

1. Press the Windows key and R together (this opens the Run box).
2. Press Ctrl+V (this pastes something).
3. Press Enter.

Mac versions tell you to open Terminal and paste. What you paste is a command the page secretly copied to your clipboard. Running it downloads and starts malware on your computer, often an "infostealer": a program that steals saved passwords and other data.

New Zealand's National Cyber Security Centre described it in a 2 September 2026 alert: compromised websites show "a fake CAPTCHA or Cloudflare Turnstile verification page"; JavaScript on the page copies PowerShell, Terminal or shell commands to the visitor's clipboard; and running them can lead to "the installation of infostealers or other malware" ([NCSC NZ alert](https://www.ncsc.govt.nz/alerts/compromised-websites-serving-clickfix-pages/), checked 2026-11-03). It says these campaigns "commonly use compromised WordPress websites", and some target only Windows or Mac visitors.

## How common it is

- ESET reported a 108% rise in ClickFix detections in the first half of 2026 (as reported by [CybelAngel](https://cybelangel.com/blog/how-clickfix-uses-fake-captchas-to-compromise-users/), checked 2026-11-01).
- Brian Krebs traced a network of fake-CAPTCHA pages feeding a "dark adtech empire" ([Krebs on Security, June 2025](https://krebsonsecurity.com/2025/06/inside-a-dark-adtech-empire-fed-by-fake-captchas/), checked 2026-11-03).
- IT administrators trade warnings about it. One r/sysadmin post about a fake reCAPTCHA found on a local company's site drew over 1,000 upvotes in August 2026 ([thread](https://www.reddit.com/r/sysadmin/comments/1vxvmzv/)); others discuss turning off the Run box ([thread](https://www.reddit.com/r/sysadmin/comments/1u3aaas/)) and protecting users ([thread](https://www.reddit.com/r/sysadmin/comments/1wgc68k/)). Checked 2026-11-01.

## Why it works

- **It looks familiar.** People have clicked through CAPTCHAs for twenty years. The fake copies the look of the real thing.
- **It shows up on sites you trust.** The site itself is genuine; attackers have added the fake page to it.
- **It feels like a normal hurdle.** CAPTCHAs are annoying by design, so an odd extra step does not seem strange.
- **You run the code yourself.** The attack needs no software flaw, only your keystrokes. The NCSC notes that "ClickFix campaigns can evade traditional automated detection".
- **It hides from scanners.** The NCSC says the malicious page may appear only in real browsers, while scanners and search crawlers see a clean site.

## How to spot a fake

| Real CAPTCHA | Fake CAPTCHA |
|---|---|
| Tick a box, choose pictures, drag a slider, or wait | Asks you to press Windows+R, open Terminal or PowerShell, or press Ctrl+V |
| Stays inside a small box on the page | Often covers the whole screen shortly after the page loads |
| Never mentions your keyboard or your clipboard | Gives numbered "verification steps" |
| Never asks you to download or run anything | Asks you to "fix" an error, update your browser, or install something |
| Takes a few seconds | Insists, repeats, or counts down to pressure you |

If in doubt, close the tab. A real site will still work later, or from another device.

## If you already did it

Act quickly. These steps follow the NCSC's advice for people who interacted with the prompt.

1. **Disconnect the computer from the internet** (turn off Wi-Fi or unplug the cable).
2. **Do not run anything else** that was copied to your clipboard.
3. **Tell your IT department** right away if it is a work computer.
4. **Run a full scan** with up-to-date security software.
5. **From a different, clean device, change your passwords**, starting with email, banking and any password manager. Sign out of all sessions where the service lets you.
6. **Turn on two-factor authentication** where you can.
7. **Watch your accounts** for logins or payments you do not recognise.

## For IT teams and site owners

- **Teach the one rule.** "A real CAPTCHA never asks you to press Windows+R" fits on a poster.
- **Consider restricting the Run box and script hosts** for users who do not need them; administrators discuss this in the threads above.
- **If your site served the fake page:** the NCSC advises removing the prompt, then finding and fixing how the attacker got in and removing anything that could reinfect the site. If you are not sure how, "immediately take the site offline, reset your WordPress credentials" and get help. Update WordPress core, remove unused plugins and themes, turn on multi-factor sign-in, and tell visitors not to run anything copied to their clipboard ([NCSC NZ](https://www.ncsc.govt.nz/alerts/compromised-websites-serving-clickfix-pages/), checked 2026-11-03).
- **Watch Google's warnings.** Google Safe Browsing treats pages that "look and feel like a trusted entity" or "trick you into doing something you'd only do for a trusted entity" as social engineering, and shows visitors a "Deceptive site ahead" warning. Site owners see reports in Search Console's Security Issues report ([Google policy](https://developers.google.com/search/docs/monitor-debug/security/social-engineering), checked 2026-11-01). The policy does not name CAPTCHAs, but fake verification pages fit its description.

## How this site handles it

Our [practice puzzles](@/play/_index.md) will carry no vendor names or logos and will be labelled as practice. No page on CAPTCHArena will ever ask you to press a keyboard shortcut, paste anything, download a file, or open a terminal. If you see one that does, it is not us: please [tell us](@/about/_index.md).
