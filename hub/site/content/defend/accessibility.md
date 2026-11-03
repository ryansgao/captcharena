+++
title = "CAPTCHA accessibility: what WCAG 2.2 requires and how widgets compare"
description = "Which CAPTCHA types WCAG 2.2 allows at AA and AAA, the timing and flashing rules, how common widgets were graded, and a checklist you can run by hand."
weight = 40
[extra]
checked = "2026-11-01"
+++

A CAPTCHA is a test placed in front of every visitor, including people who are blind, have low vision, are deaf, have motor or cognitive disabilities, or use voice control or a switch. Many CAPTCHAs fail them. The W3C's accessibility group calls traditional CAPTCHA "largely inaccessible and insecure" ([W3C APA note](https://www.w3.org/TR/turingtest/), checked 2026-11-01).

This page sets out what the Web Content Accessibility Guidelines (WCAG) 2.2 require, how common widgets were graded, and where accessibility collides with resistance to AI agents.

{% <note> %}
This is not legal advice. Whether WCAG 2.2 AA applies to your site by law, for example under the European Accessibility Act, depends on what you sell, to whom and where. Ask whoever handles your compliance.
{% </note> %}

## What WCAG 2.2 requires

### Accessible authentication (SC 3.3.8, Level AA)

Success criterion 3.3.8 says a **cognitive function test** (remembering, transcribing, solving a puzzle or a sum) may not be required in any step of signing in, unless the site also offers one of these ([W3C Understanding SC 3.3.8](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html), checked 2026-11-01):

- an **alternative** method that is not a cognitive function test;
- a **mechanism** that helps the user complete it (for example, allowing paste or a password manager);
- an **object-recognition** test;
- a test of **personal content** the user supplied to the site.

What that means for CAPTCHA types:

| CAPTCHA type | Allowed at AA without an alternative? | Allowed at AAA (SC 3.3.9)? |
|---|---|---|
| Object recognition ("select all images with cars") | Yes, it is an exception | No |
| Distorted text to transcribe | No | No |
| Maths question | No | No |
| Logic or visual puzzle (rotate, count, order, match) | No | No |
| No visible test (proof of work, invisible score) | Yes, nothing to solve | Yes |

At AAA (SC 3.3.9, Accessible Authentication Enhanced), even object recognition is no longer an exception (same source, checked 2026-11-01).

### Timing (SC 2.2.1, Level A)

If a task has a time limit, users must be able to turn it off, adjust it or extend it, with some exceptions ([W3C Understanding SC 2.2.1](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html), checked 2026-11-01). CAPTCHA rounds that expire while a screen-reader user is still working, or tokens that expire before a slow typist submits the form, run into this rule.

### Flashing (SC 2.3.1, Level A)

Content must not flash "more than three times in any one second period", unless the flashes are below the general and red flash thresholds ([W3C Understanding SC 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html), checked 2026-11-03). Some 2025–2026 research designs that rely on motion or flicker to defeat AI agents publish no discussion of photosensitivity at all. For example, one motion-based design (MVCAP, ACM Multimedia 2026) has none ([arXiv 2609.27461](https://arxiv.org/abs/2609.27461), checked 2026-11-01). Check any motion-based CAPTCHA against this rule before you deploy it.

## What the W3C accessibility note recommends

The W3C Accessible Platform Architectures group's note "Inaccessibility of CAPTCHA" (Group Draft Note, 2021-12-16) prefers checks that ask nothing of the user ([W3C APA note](https://www.w3.org/TR/turingtest/), checked 2026-11-01):

- **Proof of work** "poses no direct accessibility problems, though it may slow older hardware".
- **WebAuthn** (passkeys and security keys) is "clearly advantageous to both security and accessibility".
- **Privacy Pass**-style anonymous tokens are rated acceptable.
- Where a visible test is used, "a variety of alternative challenges must be made available".

Audio CAPTCHAs, the usual alternative to a picture puzzle, are hard for blind users too. In a 2017 WebAIM survey, 90% of 1,792 visually impaired respondents found them difficult (as cited in [arXiv 2405.18547](https://arxiv.org/html/2405.18547v1), checked 2026-11-01).

## How common widgets were graded

The only published side-by-side grading we found is a 2025 manual audit by a11yboost, using VoiceOver, NVDA, keyboard-only use and macOS Voice Control ([a11yboost](https://a11yboost.com/articles/are-captcha-systems-failing-accessibility), published 2025-05-12, updated 2025-05-18, checked 2026-11-01).

| Widget | a11yboost grade (2025) |
|---|---|
| Cloudflare Turnstile | A+ |
| Honeypot field | A |
| reCAPTCHA v3 (invisible) | B |
| hCaptcha | C |
| reCAPTCHA v2 | E |
| Arkose Labs | E |
| Traditional text CAPTCHA | F+ |

{% <note> %}
**Limits of this grading, as its authors state or as we found.** It was done by hand and cannot be repeated exactly. The method is described as "not exhaustive". The author is not named. The number of testers is not stated, and it does not say whether disabled people tested. It covers one day in 2025; widgets change. Treat the grades as a starting point, not a certificate.
{% </note> %}

Some vendors make their own claims. Cloudflare's Turnstile plans page claims "WCAG 2.2 AAA compliance" ([Cloudflare](https://developers.cloudflare.com/turnstile/plans/), checked 2026-11-01). DataDome states its slider meets WCAG 2.2 AA, with audio in 58 languages ([DataDome docs](https://docs.datadome.co/docs/datadome-captcha.md), checked 2026-11-01). ALTCHA claims WCAG 2.2 AA and European Accessibility Act compliance ([GitHub](https://github.com/altcha-org/altcha), checked 2026-11-01). These are vendor claims; we have not tested them.

## The collision: what resists agents is what AA rules out

The puzzle types that AI models now solve easily, such as object recognition, are the ones WCAG 2.2 AA allows. The types that still give agents trouble in research (exact counting, maths, logic, spatial reasoning, ordered steps) are cognitive function tests, which AA does not allow in a sign-in step without an alternative. Recent attack papers list "exact counting, continuous geometry, and ordered execution" as the remaining failures ([CaptchaAgent, arXiv 2610.12866](https://arxiv.org/abs/2610.12866), checked 2026-11-01).

So an agent-hard puzzle in a sign-in step is not conformant unless a non-puzzle path exists. That path is then the easiest route for a bot. The designer of a viral 2026 motion CAPTCHA said it directly: "Any true accessible option… pretty much defeats the purpose" ([r/webdev](https://www.reddit.com/r/webdev/comments/1uxfzav/), checked 2026-11-01). The top reply to the post was "Neat concept but an accessibility nightmare".

What this means for a site owner:

- **Do not try to win with a harder puzzle.** It fails disabled users first and agents later.
- **Use checks that ask nothing of the user** (proof of work, an invisible score) as the first layer.
- **Make the fallback something a bot cannot cheaply repeat**, such as an email link with a rate limit per address, rather than an easier puzzle.
- **Remember that an agent can act for a disabled person.** An agent filling a form for its user is a legitimate visitor. See [signing agents](@/build/signing.md) for how an agent can identify itself.

## A checklist you can run by hand

Run each check on the page where your CAPTCHA appears, in at least one desktop and one phone browser.

1. **Keyboard only.** Unplug the mouse. Can you reach the CAPTCHA with Tab, operate it with Enter or Space, and submit the form?
2. **Screen reader.** With VoiceOver (macOS, iOS) or NVDA (Windows), does the widget announce what it is and what to do? Is every alternative (audio, a different challenge) announced and reachable?
3. **Type of test.** If a visible challenge appears, is it object recognition? If it is text, maths or a puzzle, is there a non-puzzle alternative on the same step?
4. **Time.** Start the challenge and wait. Does anything expire? If it does, can the user extend it, and does the form keep what they typed?
5. **Motion and flashing.** Does anything flash, flicker or move? Does it respect the operating system's reduced-motion setting?
6. **Zoom and contrast.** At 200% zoom, does the widget still fit and work? Is its text readable in high-contrast mode?
7. **Voice control.** With macOS Voice Control or Windows Voice Access, can you name and press the controls?
8. **Language.** Do the instructions and audio match the page language?
9. **Failure path.** Fail on purpose. Is the error message clear, announced to a screen reader, and does it offer another way through?
10. **With privacy settings on.** With third-party cookies blocked or a common privacy extension on, can a real person still get through?

{% <coming> %}
An automated accessibility checker for CAPTCHAs. It will drive the keyboard-only path, read the accessibility tree, time each step against SC 2.2.1 and classify the challenge type against SC 3.3.8. Screen-reader and voice-control runs cannot be fully automated, so those will be published as dated manual audits. Grades will sit next to each widget's measured agent resistance on the [Scoreboard](@/scoreboard/_index.md).
{% </coming> %}
