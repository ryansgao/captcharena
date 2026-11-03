+++
title = "About CAPTCHArena: who runs it, how it stays neutral"
description = "Who runs CAPTCHArena, its funding and conflict-of-interest policy, what it will never do, privacy, and the licences of its text and data."
sort_by = "weight"
[extra]
checked = "2026-11-03"
+++

CAPTCHArena is an independent, unfunded project that measures and explains human checks on the web. It started in November 2026 from a simple observation: no neutral, current source explains CAPTCHAs from both sides. Every comparison page we found was written by a CAPTCHA vendor or by a company selling something adjacent, the encyclopedia article does not mention AI agents, and the benchmarks stop at publication.

## Who runs it

An independent student project. The source repository and the operator's details will be published here when the code goes public.

## Funding and conflicts of interest

- **No vendor money.** We take no payment, sponsorship or credits from CAPTCHA vendors, bot-defence companies, solving services, scraping companies or AI labs in exchange for coverage or placement.
- **No affiliate links and no ads.** Links to products are plain links.
- **Running costs** (hosting and the agents' model usage for the scoreboard) are paid by the project. If a lab or framework team pays for its own verified scoreboard run, that run is labelled as submitter-funded.
- If this policy ever changes, the change will be dated in the [changelog](@/about/changelog.md) before any money arrives.

## What we will never do

- Sell, broker or hand out CAPTCHA tokens or solving code, or run a solving service.
- Put a vendor's real widget in front of agents where the vendor's terms forbid it, without written permission.
- Show vendor logos or imitate a vendor's widget on practice puzzles.
- Ask a visitor to press a key combination, paste a command or download anything.

## How facts are checked

Every fact shows the date it was last checked and links to its primary source: the vendor's own documentation, the paper, the standard. Where sources conflict, we say so. Where a claim is our own reading of several sources, we say that too. Vendors change products and terms every few months; if you find an outdated or wrong fact, please tell us via the [contact page](@/contact/_index.md).

## Privacy

- **This site** sets no cookies, runs no analytics and loads nothing from any other domain. Its server logs record the time, the page requested and the response code, but no IP address.
- **The scoreboard box** asks our measurement service for its published summary from your browser, without cookies.
- **The [measurement page](https://measure.captcharena.org)** loads real Google reCAPTCHA and Cloudflare Turnstile widgets, because that is what it measures. Google and Cloudflare receive what their widgets normally collect. Our own server stores no IP address and sets no cookie of its own; it records the country Cloudflare reports.

## Licences

- **Text:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quote, translate or reuse it with a link back.
- **Data:** published scoreboard data will be released openly, with a dated snapshot each quarter.
- **Trademarks:** product names belong to their owners and are used only to identify the products.

## Site technology

Plain static pages built with [Zola](https://www.getzola.org/) and served by [nginx](https://nginx.org/) in a locked-down container, with a strict content security policy that allows scripts only from this domain. No framework, no tracking, no external fonts.
