+++
title = "Open-source and self-hosted CAPTCHAs"
description = "ALTCHA, Cap, Anubis, mCaptcha, Procaptcha, go-captcha, PrivateCaptcha, honeypots and tarpits: how each works, its licence, and what it does not stop."
weight = 40
[extra]
checked = "2026-11-01"
+++

## The short version

Most open-source CAPTCHAs today are **proof of work**: the visitor's browser spends a fraction of a second to a few seconds computing hashes, and the server checks the answer cheaply. There are no third-party scripts, no tracking, and nothing for the visitor to click. The trade-off is that proof of work prices a request; it does not tell a human from a machine. A scraper with real CPUs pays the same small price a visitor does. A few projects still offer visible puzzles (go-captcha, Procaptcha's puzzle mode, classic text libraries), and honeypots and tarpits sit next to them as cheap extra layers.

## Comparison table

Stars, licence and last push are from GitHub on 2026-11-01; licences were cross-checked against each repository's licence file.

| Project | Mechanism | Licence | Stars | Last push | Self-host end to end? |
|---|---|---|---|---|---|
| [Anubis](https://github.com/TecharoHQ/anubis) | SHA-256 proof of work, as a reverse proxy in front of a whole site | MIT | 23,858 | 2026-10-29 | Yes |
| [Cap](https://github.com/tiagozip/cap) | Proof of work plus optional "instrumentation challenges" | Apache-2.0 | 8,219 | 2026-10-29 | Yes |
| [ALTCHA](https://github.com/altcha-org/altcha) | Proof of work widget; v3 adds memory-hard Argon2 and scrypt | MIT | 2,864 | 2026-10-22 | Yes |
| [mCaptcha](https://github.com/mCaptcha/mCaptcha) | SHA-256 proof of work, difficulty rises under load | AGPL-3.0 | 2,497 | 2025-10-07 | Yes |
| [go-captcha](https://github.com/wenlng/go-captcha) | Click, slide and rotate puzzles | Apache-2.0 | 2,466 | 2026-03-07 | Yes |
| [Procaptcha](https://github.com/prosopo/captcha) (Prosopo) | Modes `pow`, `puzzle` and `frictionless` | Apache-2.0 (the frictionless detection library is closed) | 303 | 2026-10-31 | Yes for pow and puzzle |
| [PrivateCaptcha](https://github.com/PrivateCaptcha/PrivateCaptcha) | Proof of work service in Go, adaptive difficulty | PolyForm Noncommercial (source-available, not an OSI licence) | 199 | 2026-10-31 | Yes, non-commercial use only |
| [Friendly Captcha widget](https://github.com/FriendlyCaptcha/friendly-challenge) | Proof of work widget | MIT (SDK MPL-2.0) | 452 | 2026-06-30 | No: verification is their hosted service |
| Classic text libraries ([dchest/captcha](https://github.com/dchest/captcha), [Gregwar/Captcha](https://github.com/Gregwar/Captcha), [lepture/captcha](https://github.com/lepture/captcha), [mewebstudio/captcha](https://github.com/mewebstudio/captcha)) | Distorted text and audio images | MIT / BSD | 1–2.6k | — | Yes |

## Proof of work, explained

The server sends a random challenge and a difficulty. The browser searches for a number that, hashed together with the challenge, gives a result below a target. Finding it takes many attempts; checking it takes one. This idea comes from anti-spam work on Hashcash. The W3C accessibility group rates it well: proof of work "poses no direct accessibility problems, though it may slow older hardware" ([W3C APA note](https://www.w3.org/TR/turingtest/), checked 2026-11-01).

What it costs an attacker is the key question, and the published answer is: very little. In an analysis of Anubis at its default settings (about 2^16 hashes per token, tokens valid seven days), Tavis Ormandy estimated that covering all ~11,500 Anubis deployments for a week takes about six minutes on a free cloud VM: "the cost of unrestricted crawler access to the internet for a week is approximately $0" ([analysis](https://lock.cmpxchg8b.com/anubis.html), checked 2026-11-01). In the field, Codeberg reported in August 2025 that AI scrapers had "learned how to solve the Anubis challenges" ([The Register](https://www.theregister.com/software/2025/08/16/codeberg-beset-by-ai-bots-that-now-bypass-anubis-defense/1023101), checked 2026-11-01).

Yet it still helps in practice, for three reasons:

- **It filters cheap clients.** Many scrapers do not run JavaScript or keep cookies. A 2026 honeysite study found Anubis "stopped every HTTP scraper and no browser tool" ([Fayolle et al.](https://arxiv.org/abs/2606.30119), checked 2026-11-01).
- **It forces re-work.** Tokens bound to an address make scrapers that rotate through many addresses solve again and again.
- **Memory-hard variants close part of the gap.** Argon2 and scrypt (ALTCHA v3) and Cap's "GPU-resistant" design aim to stop GPUs and native code from solving far faster than a browser.

Treat proof of work as **rate shaping**: it smooths load and raises the floor. It is not a human test. For the arithmetic of what a given difficulty buys, see [Attacker cost](@/defend/attacker-cost.md).

## Project notes

### Anubis

A reverse proxy by Xe Iaso, first released 2025-01-19. It puts a proof-of-work page in front of an entire site and by default challenges only browsers whose user agent contains "Mozilla". Known users include GNOME's GitLab, Linux kernel mailing lists, FFmpeg, Wine and UNESCO ([Wikipedia](https://en.wikipedia.org/wiki/Anubis_(software)); [known instances](https://anubis.techaro.lol/docs/user/known-instances), checked 2026-11-01). The mascot branding can be removed only with a paid licence. **Stops:** clients that do not run JavaScript; bursts from single addresses. **Does not stop:** real browsers or purpose-built solvers.

### Cap

A self-hosted proof-of-work CAPTCHA with optional "instrumentation challenges", which its README says "can also be configured to stop autonomous AI agents". Used by bunny.net and AdGuard according to its README, and holds an OpenSSF gold badge ([repo](https://github.com/tiagozip/cap), checked 2026-11-01). Our [measurement page](https://measure.captcharena.org) runs it.

### ALTCHA

A proof-of-work widget with server libraries in ten languages. It claims WCAG 2.2 AA and European Accessibility Act compliance and offers an image-code fallback with audio. Version 3 added Argon2 and scrypt ([repo](https://github.com/altcha-org/altcha), checked 2026-11-01). Its maker also sells a commercial product, which we did not review. Our [measurement page](https://measure.captcharena.org) runs ALTCHA too.

### mCaptcha

Proof of work whose difficulty rises when the site is under load, so normal visitors pay little and floods pay more. AGPL-3.0, so a modified version run as a service must offer its source. The README says "active development", but there was no push for about 13 months before our check ([repo](https://github.com/mCaptcha/mCaptcha), checked 2026-11-01).

### Procaptcha

Prosopo's open CAPTCHA, built as a drop-in replacement for reCAPTCHA, hCaptcha and Turnstile, with three modes. The pow and puzzle modes are fully open; the frictionless mode's detection library is closed ([repo](https://github.com/prosopo/captcha), checked 2026-11-01). A general research solver passed 85.9% of 652 live Prosopo tasks ([Halligan](https://www.usenix.org/conference/usenixsecurity25/presentation/teoh), checked 2026-11-01).

### go-captcha

Interactive click, slide and rotate puzzles in the style common on Chinese sites, with an Apache-2.0 asset pack ([repo](https://github.com/wenlng/go-captcha), checked 2026-11-01). Visible puzzles of this kind are exactly what modern vision models solve; see [How AI agents fare](@/learn/ai-agents.md).

### PrivateCaptcha

A proof-of-work service in Go from an EU company. Its licence forbids commercial use, so it is source-available rather than open source ([repo](https://github.com/PrivateCaptcha/PrivateCaptcha), checked 2026-11-01).

## Honeypots and tarpits

These are not CAPTCHAs, but they are often used beside them.

- **Form honeypots.** A form field hidden from people with CSS. People leave it empty; naive bots fill it in. It costs visitors nothing, and one accessibility review graded honeypots "A", against "E" for reCAPTCHA v2 ([a11yboost, 2025](https://a11yboost.com/articles/are-captcha-systems-failing-accessibility), checked 2026-11-01; method not exhaustive). It stops only bots that fill every field.
- **Tarpits and poison.** Tools such as [Nepenthes](https://zadzmo.org/code/nepenthes/) and [iocaine](https://iocaine.madhouse-project.org/) feed crawlers endless generated pages. iocaine's own description: it "does not make the bots go away" ([LWN, 2026-02-12](https://lwn.net/Articles/1056953/)). Nepenthes' author warns it removes a site from search results. Cloudflare runs a hosted version, AI Labyrinth ([blog](https://blog.cloudflare.com/ai-labyrinth/)). All checked 2026-11-01. They raise a crawler's cost; they do not guard a login or a form.

## What open CAPTCHAs do not stop

| Threat | Proof of work | Visible open puzzle | Honeypot field |
|---|---|---|---|
| Scripts that do not run JavaScript | Yes | Yes | Often |
| Headless or real browsers driven by code | No, only slows them | Rarely, against current vision models | No |
| AI agents acting in a real browser | No | Rarely | No |
| Paid human solving farms | No | No | No |
| Floods from one address | Partly (cost per request) | Partly | No |

For layered defences that combine these with rate limits and signed agents, see [Defend](@/defend/_index.md) and [What still works](@/learn/what-lasts.md).

{% <note> %}
Licence notes are a summary, not legal advice. Read each project's licence file before you ship it.
{% </note> %}
