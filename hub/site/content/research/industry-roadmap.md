+++
title = "What the industry says comes after CAPTCHAs, and what is built"
description = "PACT, Privacy Pass, ARC and ACT, Private Access Tokens, Web Bot Auth, delegation drafts, agent payments and personhood: who proposed each, and whether open code exists."
weight = 20
[extra]
checked = "2026-11-01"
+++

Vendors, browser makers and standards bodies broadly agree on what replaces the visible puzzle. Sites will stop asking "is this a human?" and ask three other questions: *whose agent is this*, *what may it do*, and *can this visitor prove a property (a rate limit, a good standing) without saying who they are?* This page lists each proposal, who made it, and whether an open implementation exists. Most of the user-side half does not exist as open code yet.

## The new questions in one table

| Old question | New question | Mechanisms |
|---|---|---|
| Is this a human? | Whose agent is this, and is it allowed? | Web Bot Auth and signed agents, permission manifests, agent payment schemes |
| Can it solve this puzzle? | What does each request cost it, and is the cost fair? | Proof of work, cost-based throttling, pay per crawl, rate-limited credentials |
| Prove you are human | Prove a property without revealing identity | Privacy Pass, ARC, ACT, PACT, personhood credentials |
| Is the puzzle answer correct? | Is the process human, and is the environment genuine? | Process detection, fingerprinting, device attestation |

Cloudflare's own framing: *"There are wanted bots and there are unwanted humans"*, and *"the human versus bots frame is misleading"* ([Cloudflare, 2026-04-21](https://blog.cloudflare.com/past-bots-and-humans/), checked 2026-11-01).

## PACT: anonymous tokens across browsers

**PACT (Private Access Control Tokens)** was announced on 2026-06-22 by Cloudflare, Mozilla, Google (Chrome), Microsoft (Edge) and Shopify. Sites that know a visitor vouch for them anonymously; the browser carries that vouching to other sites; an agent can carry its user's credential. Coverage: *"No deployment timeline has been announced"* ([TNW](https://thenextweb.com/news/cloudflare-pact-browser-privacy-bot-traffic-protocol), checked 2026-11-01). Cloudflare later wrote: *"Announced with Mozilla, Google, Microsoft, and Shopify, PACT lets sites vouch anonymously, so the agent can present the token elsewhere"* ([Cloudflare, 2026-08-06](https://blog.cloudflare.com/the-agentic-internet/), checked 2026-11-01).

Mozilla's design post ([Dennis Jackson, 2026-06-23](https://hacks.mozilla.org/2026/06/pact-anonymous-credentials-for-the-web/), checked 2026-11-01) sets out the roles and the open problems:

- **Thesis:** *"If sites knew their visitors were restricted to a rate limit set by a site, that would be enough."* Scarcity can come from anything an attacker cannot cheaply copy: an email account, a phone number, a paid subscription.
- **Roles:** an *Anchor* (a site that knows the user) issues Endorsements; a *Moderator* (one per site) exchanges an Endorsement for a stateful Credential and adjusts it by behaviour.
- **Agents:** *"An agent can carry its user's Credentials, in which case the user remains accountable for how the agent behaves."* Or the agent's operator runs its own Anchor.
- **Against device attestation:** Apple's tokens *"rely on device attestation … access to the web would become tied to having bought expensive hardware"*.
- **Unsolved:** *"sites at least need a way to calculate an aggregate score for each issuer they use"*, privately (Mozilla points to its Prio work).
- **Status:** *"many of the details still need to be worked out"*; crypto at the IETF, the browser API at the W3C.

PACT's protocol layer is **MoLE (Moderation of unLinkable Endorsements)**: three -00 drafts by Schlesinger (Google), Jackson (Mozilla) and Meunier (Cloudflare), 2026-07-06. Its IETF group is still at the BoF stage (updated 2026-10-23). The drafts' repository says *"Existing implementations: To be added"*; its proof-of-concept code covers the cryptography only, with no HTTP transport, browser or agent ([MoLE architecture](https://datatracker.ietf.org/doc/draft-jms-mole-architecture/), [group](https://datatracker.ietf.org/group/mole/about/), [repository](https://github.com/Moderation-of-unLinkable-Endorsements/internet-drafts), checked 2026-11-01). The W3C Anti-Fraud Community Group's `antifraudcg/pact` repository holds a 7-byte README ([repo](https://github.com/antifraudcg/pact), checked 2026-11-01).

## Status of every item

"Open implementation" means code anyone can run under an open-source licence. A "yes" for the cryptography does not mean the whole protocol runs end to end.

| Item | Who proposed | Spec | Open implementation? | Deployed? | Checked |
|---|---|---|---|---|---|
| **Web Bot Auth** (agents sign requests) | Cloudflare (2025-05); IETF working group | [draft-ietf-webbotauth-httpsig-protocol-01](https://datatracker.ietf.org/doc/draft-ietf-webbotauth-httpsig-protocol/) (2026-10-29) | **Yes**: [cloudflare/web-bot-auth](https://github.com/cloudflare/web-bot-auth), Apache-2.0 | Yes: verified by Cloudflare, Google, HUMAN, Akamai, Fingerprint, Arkose; used by ChatGPT agent, Google-Agent, Browserbase | 2026-11-01 |
| Signature Agent Card / registries | Meunier (Cloudflare) | individual draft -04 (2026-10-27), [Cloudflare post](https://blog.cloudflare.com/agent-registry/) | Not checked | — | 2026-11-01 |
| Web Bot Auth in open gates (Anubis) | Anubis issue #744 (2025-07-01) | — | **No**: maintainer reports a prototype (2026-09-28); no Web Bot Auth or Privacy Pass code in Anubis, Cap, ALTCHA or mCaptcha (source search) | No | 2026-11-01 |
| **Anonymous Bot Authentication** | Rescorla, Barnes | [draft-rescorla-anonymous-webbotauth-01](https://datatracker.ietf.org/doc/draft-rescorla-anonymous-webbotauth/) (2026-07-19); *"has not yet seen significant security analysis"* | **No** (draft only) | No | 2026-11-01 |
| **Privacy Pass** | IETF | RFC 9576–9578 (June 2024), [documents](https://datatracker.ietf.org/wg/privacypass/documents/) | **Yes**: e.g. [raphaelrobert/privacypass](https://github.com/raphaelrobert/privacypass) (MIT), [cloudflare/privacypass-ts](https://github.com/cloudflare/privacypass-ts) | Yes: Cloudflare (*"billions of tokens daily"*, mostly privacy relays), Apple | 2026-11-01 |
| **Private Access Tokens** (device attestation) | Apple (iOS 16 / macOS 13, 2022) | Privacy Pass with Apple's attester ([Cloudflare post](https://blog.cloudflare.com/eliminating-captchas-on-iphones-and-macs-using-new-standard)) | Partly: [cloudflare/pat-go](https://github.com/cloudflare/pat-go) (BSD-3); the attester is Apple's | Yes (closed issuer set) | 2026-11-01 |
| **ARC** (Anonymous Rate-Limited Credentials) | Yun, Wood (Apple), Faz-Hernandez (Cloudflare) | [arc-crypto-01](https://datatracker.ietf.org/doc/html/draft-ietf-privacypass-arc-crypto-01), [arc-protocol-01](https://datatracker.ietf.org/doc/html/draft-ietf-privacypass-arc-protocol-01) (working-group drafts) | **Yes, cryptography**: in [apple/swift-crypto](https://github.com/apple/swift-crypto) (Apache-2.0) | Not found deployed | 2026-11-01 |
| **ACT** (Anonymous Credit Tokens) | Schlesinger (Google) | draft-schlesinger-privacypass-act-01 (2026-08-17), CFRG crypto draft | **Yes, cryptography**: [SamuelSchlesinger/anonymous-credit-tokens](https://github.com/SamuelSchlesinger/anonymous-credit-tokens) (Apache-2.0, "Beta") | Cloudflare demo only | 2026-11-01 |
| ARC + ACT combined, per-site revocation | Cloudflare | Blog only ([2025-10-30](https://blog.cloudflare.com/private-rate-limiting/)) | **No**: *"We plan to open source the code once the specifications of ARC and ACT begin to stabilize"*; demo uses an earlier draft | No | 2026-11-01 |
| Post-quantum ARC / ACT | Open problem posed by Cloudflare | — ([Cloudflare](https://blog.cloudflare.com/pq-anonymous-credentials/)) | **No** | No | 2026-11-01 |
| **PACT** end to end | Cloudflare, Mozilla, Google (Chrome), Microsoft (Edge), Shopify | No spec; MoLE -00 drafts; [W3C CG proposal #22](https://github.com/antifraudcg/proposals/issues/22) | **No**: MoLE crypto proof of concept only | No | 2026-11-01 |
| Private reputation for Anchors (issuers) | Mozilla; W3C CG #22; Cloudflare | Named, no draft | **No** (Prio libraries exist: [divviup/libprio-rs](https://github.com/divviup/libprio-rs)) | No | 2026-11-01 |
| Private State Tokens | Google | Kept when most of Privacy Sandbox was retired, 2025-10-17 ([Google](https://privacysandbox.google.com/blog/update-on-plans-for-privacy-sandbox-technologies)) | Not checked | Chrome | 2026-11-01 |
| Web Environment Integrity | Google | *"This proposal is no longer pursued"* ([repo](https://github.com/RupertBenWiser/Web-Environment-Integrity)) | — | No | 2026-11-01 |
| Google Cloud Fraud Defense (QR-code human check, agent policy engine) | Google (2026-04-23) | Closed product ([Google Cloud](https://cloud.google.com/blog/products/identity-security/introducing-google-cloud-fraud-defense-the-next-evolution-of-recaptcha)) | **No** | Yes | 2026-11-01 |
| Verified-bot trust scores | Cloudflare (2026-10-16) | Closed ([post](https://blog.cloudflare.com/verified-bots-accountability/)); reputation is outside the Web Bot Auth charter | **No** | Yes (Cloudflare) | 2026-11-01 |
| **Delegation drafts** (a human authorises an agent's action) | About 30 individual IETF drafts, e.g. OAuth on-behalf-of, agent mandates, a "Delegation" HTTP scheme | [datatracker](https://datatracker.ietf.org/); Web Bot Auth defers delegation to a separate spec | **No** for general web actions; draft-mcgraw's own implementation is *"experimental … not … wire-compatible"* | No | 2026-11-01 |
| Human continuity across agents | draft-brezun-human-continuity-http-00 | One handle per unique human per scope, across accounts, devices and agents | **No**: *"no complete end-to-end implementation … is known"* | No | 2026-11-01 |
| Permission manifests | Lightweight Agent Standards WG | [arXiv 2601.02371](https://arxiv.org/abs/2601.02371), [las-wg.org](https://las-wg.org/) | Not checked | — | 2026-11-01 |
| Process signals turned into anonymous tokens | Proposed in passing by Cloudflare and Mozilla | — | **No** | Closed process detectors only | 2026-11-01 |
| Second-device human step-up | Google (closed); OpenID CIBA (standard) | — | Partly: [rotorstar/hitl-protocol](https://github.com/rotorstar/hitl-protocol) (generic, Apache-2.0) | Google only | 2026-11-01 |

## Payment-agent schemes

Payments are the one area where "a human authorised this agent to do this" is specified and partly built. Several schemes reuse Web Bot Auth for the agent's identity ([Cloudflare, 2025-10-24](https://blog.cloudflare.com/secure-agentic-commerce/), checked 2026-11-01).

| Scheme | Who | Open code | Licence | Checked |
|---|---|---|---|---|
| Trusted Agent Protocol | Visa (2025-10) | [visa/trusted-agent-protocol](https://github.com/visa/trusted-agent-protocol), last commit 2025-10-28 | **Visa Developer Center Terms of Use: a proprietary licence, not open source** | 2026-11-01 |
| Agent Pay and Verifiable Intent | Mastercard (2025-04-29; 2026-03-05) | [agent-intent/verifiable-intent](https://github.com/agent-intent/verifiable-intent), Draft v0.1, last commit 2026-04-20 | Apache-2.0 | 2026-11-01 |
| AP2 (Agent Payments Protocol), now at the FIDO Alliance | Google | [google-agentic-commerce/AP2](https://github.com/google-agentic-commerce/AP2) | Apache-2.0 | 2026-11-01 |
| Agentic Commerce Protocol | OpenAI and Stripe | [agentic-commerce-protocol](https://github.com/agentic-commerce-protocol/agentic-commerce-protocol) | Apache-2.0 | 2026-11-01 |
| x402 (HTTP 402 payments) | Coinbase, now the x402 Foundation; Cloudflare | [x402-foundation/x402](https://github.com/x402-foundation/x402) | Apache-2.0 | 2026-11-01 |
| KYAPay | Skyfire | [skyfire-xyz/kyapay](https://github.com/skyfire-xyz/kyapay) | MIT | 2026-11-01 |
| x401 (present a credential over HTTP) | Proof and Circle | [proof/x401](https://github.com/proof/x401) | Apache-2.0 | 2026-11-01 |

AP2's own text says its model *"could be applied more generally in the future"*, beyond payments. That has not happened in open code yet.

## Personhood

| Item | Status | Checked |
|---|---|---|
| Personhood credentials ([Adler, Hitzig, Jain et al., 2024-08](https://arxiv.org/abs/2408.07892)) | A 32-author proposal: credentials that prove a unique person without identity, with agents as verified delegates. Critiques focus on separating personhood from identity ([W3C CCG thread](https://lists.w3.org/Archives/Public/public-credentials/2024Aug/0036.html)) and on delegation ([BGIN](https://bgin.discourse.group/t/proof-of-personhood-biometrics-social-trust-and-dual-agent-systems/830)). | 2026-11-01 |
| World ID | About 18M Orb-verified people in 160 countries (company figure, April 2026) ([Axios](https://axios.com/2026/04/17/worldcoin-zoom-shopify-retail-partnership)). Open repositories: world-id-protocol (MIT). | 2026-11-01 |
| World AgentKit (agents backed by a verified human) | Beta 2026-03-17; its repository [worldcoin/agentkit](https://github.com/worldcoin/agentkit) is marked *"This repository is deprecated"*. Tied to one issuer. | 2026-11-01 |

Cloudflare's warning applies to all of these: *"Infrastructure for proving properties can become infrastructure for requiring properties"* ([2026-04-21](https://blog.cloudflare.com/past-bots-and-humans/)). Its proposed test: anyone must still be able to build their own device or browser and reach the web.

## What is missing

Every layer is specified or proposed somewhere. No open stack joins them.

- **Agent identity is built.** Web Bot Auth has open libraries and production verifiers.
- **Anonymous user standing is designed, not built.** PACT and MoLE have no end-to-end implementation; their cryptography exists in pieces.
- **Delegation is the most crowded paper space and the emptiest code space.** About 30 drafts; payments only in code, two schemes under a proprietary licence or stale since spring 2026.
- **Named open problems with no code:** private Anchor reputation, per-site revocation for ARC, post-quantum ARC and ACT, a browser and agent client API for PACT, anonymous bot authentication, and process signals turned into anonymous tokens.

For what this means for builders today, see [Sign your agent](@/build/signing.md). For the research questions, see [open questions](@/research/open-questions.md).

{% <coming> %}
A tracker that re-checks each row of the status table on a schedule (spec revisions, repository activity, new implementations) and records the date each status changed.
{% </coming> %}
