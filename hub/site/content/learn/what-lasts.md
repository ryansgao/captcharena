+++
title = "What still works: cost, scarcity, accountability"
description = "Once agents see as well as people, three levers remain: making abuse cost more, asking for scarce credentials, and making agents say who they are."
weight = 70
[extra]
checked = "2026-11-01"
+++

## The short version

If an agent can see, read and click as well as a person, no puzzle can tell them apart for long. Three things still work, because none of them depends on perception:

| Lever | The question it asks | Examples |
|---|---|---|
| **Cost** | Does this request cost more than abuse would earn? | Rate limits per account and action, proof of work, paid access (HTTP 402) |
| **Scarcity** | Does the visitor hold something that cannot be copied cheaply? | Private Access Tokens, Privacy Pass and ARC, PACT, personhood credentials |
| **Accountability** | Whose agent is this, and what may it do? | Web Bot Auth, signed agents, agent trust scores |

The industry has said this out loud. In Cloudflare's words: "There are wanted bots and there are unwanted humans" ([blog, 2026-04-21](https://blog.cloudflare.com/past-bots-and-humans), checked 2026-11-01). The question moves from "is this a human?" to "is this request allowed, and who answers for it?"

## Cost

A check only needs to make abuse unprofitable ([Motoyama et al., 2010](https://www.usenix.org/legacy/event/sec10/tech/full_papers/Motoyama.pdf), checked 2026-11-02). Puzzles set that price at a cent or less (see [the economics](@/learn/economics.md)). Better ways to set a price:

- **Rate limits on the action, not the visitor.** Limit sign-ups, posts, searches or checkouts per account, per device and per address, in proportion to what each is worth to an abuser.
- **Proof of work** for bulk traffic. It is cheap for one visitor and adds up for a crawler, though at common settings it adds up to very little ([Ormandy](https://lock.cmpxchg8b.com/anubis.html), checked 2026-11-01).
- **Paying for access.** Cloudflare's pay-per-crawl uses HTTP 402 with price headers, and identifies the crawler with Web Bot Auth ([blog, 2025-07-01](https://blog.cloudflare.com/introducing-pay-per-crawl/), checked 2026-11-01).
- **Reasoning gates.** A research proposal: puzzles that cost an agent 9.2 times the tokens they cost to make, slowing agents rather than blocking them ([arXiv 2509.01619](https://arxiv.org/abs/2509.01619), checked 2026-11-01).

## Scarcity: prove a property, not an identity

These schemes give the browser a token that says "this visitor has something scarce" without saying who the visitor is.

### Private Access Tokens

Apple devices (iOS 16 and macOS 13 onward) can prove they passed a device attestation check. The site receives a token, not a device ID. Apple's description: they "cryptographically sign the fact that a client was able to pass an attestation check" ([WWDC22](https://developer.apple.com/videos/play/wwdc2022/10077/); [Cloudflare blog](https://blog.cloudflare.com/eliminating-captchas-on-iphones-and-macs-using-new-standard), checked 2026-11-01). Turnstile uses them on Apple devices.

### Privacy Pass and ARC

Privacy Pass is the IETF standard behind these tokens: RFC 9576 (architecture), 9577 (HTTP authentication) and 9578 (issuance), published June 2024 ([IETF](https://datatracker.ietf.org/wg/privacypass/documents/), checked 2026-11-01). An issuer that has checked something about you gives you tokens; a site can verify a token but cannot link it to you. Cloudflare says Privacy Pass issues "billions of tokens daily", mostly for privacy relays ([blog](https://blog.cloudflare.com/past-bots-and-humans), checked 2026-11-01).

Newer drafts add rate limits. **ARC** (Anonymous Rate-Limited Credentials) lets one credential be shown a fixed number of times per site, unlinkably ([draft-ietf-privacypass-arc-crypto](https://datatracker.ietf.org/doc/html/draft-ietf-privacypass-arc-crypto-01), checked 2026-11-01). **ACT** (Anonymous Credit Tokens) is a stateful credit that a site can lower when a visitor misbehaves ([Cloudflare blog, 2025-10-30](https://blog.cloudflare.com/private-rate-limiting/), checked 2026-11-01). Apple's open-source crypto library already ships ARC code ([apple/swift-crypto](https://github.com/apple/swift-crypto), checked 2026-11-01).

### PACT

On 2026-06-22 Cloudflare, Mozilla, Google (Chrome), Microsoft (Edge) and Shopify announced **PACT** (Private Access Control Tokens): "anonymous tokens that show a visitor is either a person or an authorized bot", built on Privacy Pass ([The Next Web](https://thenextweb.com/news/cloudflare-pact-browser-privacy-bot-traffic-protocol), checked 2026-11-01). Mozilla's design post explains the idea: a site that knows you (because you have an account, a phone number or a subscription) vouches for you anonymously, and your browser carries that vouching to other sites. "If sites knew their visitors were restricted to a rate limit set by a site, that would be enough." An agent "can carry its user's Credentials, in which case the user remains accountable for how the agent behaves" ([Mozilla Hacks, 2026-06-23](https://hacks.mozilla.org/2026/06/pact-anonymous-credentials-for-the-web/), checked 2026-11-01).

Status: no deployment timeline has been announced, and Mozilla says "many of the details still need to be worked out". The protocol drafts underneath it list "Existing implementations: To be added" ([IETF MoLE drafts](https://datatracker.ietf.org/doc/draft-jms-mole-architecture/), checked 2026-11-01).

### Personhood credentials

A 2024 paper by 32 authors from OpenAI, MIT, Microsoft and others proposes credentials that prove you are one unique person without saying which. It argues that "existing countermeasures … such as CAPTCHAs — are inadequate against sophisticated AI" ([Adler et al.](https://arxiv.org/abs/2408.07892), checked 2026-11-01). World ID is the largest deployed example: about 18 million people verified by an iris-scanning device, by the company's own April 2026 figure ([Axios](https://axios.com/2026/04/17/worldcoin-zoom-shopify-retail-partnership), checked 2026-11-01).

## Accountability: agents that say who they are

### Web Bot Auth and signed agents

**Web Bot Auth** lets a bot or agent sign each HTTP request with a key (Ed25519, using HTTP Message Signatures, RFC 9421) and publish its public keys in a directory. A site can then verify which operator sent the request. Cloudflare proposed it in May 2025; an IETF working group now develops it, and its protocol draft reached -01 on 2026-10-29 ([working group](https://datatracker.ietf.org/wg/webbotauth/about/); [draft](https://datatracker.ietf.org/doc/draft-ietf-webbotauth-httpsig-protocol/), checked 2026-11-01).

Adoption is real. Cloudflare's **signed agents** programme covers agents "generally directed by an end user", with ChatGPT agent, Goose, Browserbase and Anchor Browser in its launch group ([blog, 2025-08-28](https://blog.cloudflare.com/signed-agents/)). Since 2026-07-01, Cloudflare lists signed agents as "Verified" ([docs](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/)). Google signs "a subset of requests made by the Google-Agent" ([Google docs](https://developers.google.com/crawling/docs/crawlers-fetchers/web-bot-auth)). Google Fraud Defense, HUMAN, Akamai, Fingerprint, Arkose and AWS WAF verify signatures (see [vendors](@/learn/vendors.md)). All checked 2026-11-01.

How to sign your own agent is covered in [Build: signing](@/build/signing.md).

### Identity is not permission

A signature says which software sent a request. It does not say which person authorised which action. The working group's charter leaves out "authenticating the end user of a participating client or agent" on purpose ([charter](https://datatracker.ietf.org/doc/charter-ietf-webbotauth/), checked 2026-11-01). Arkose Labs puts the gap plainly: Web Bot Auth "establishes an identity signal, rather than the user's permission for a particular transaction" ([interview, 2026-10-27](https://letsdatascience.com/news/arkose-labs-tells-lds-why-agent-identity-is-not-permission-39afe6cc), checked 2026-11-01). Payment networks have built delegation for shopping (Visa Trusted Agent Protocol, Mastercard Verifiable Intent, Google's AP2), but there is no open standard yet for ordinary web actions. The state of that work is on the [industry roadmap](@/research/industry-roadmap.md).

## The warning

Each of these levers has a cost, and someone pays it.

- **Attestation shuts people out.** Mozilla argues that device attestation means "access to the web would become tied to having bought expensive hardware" ([Mozilla Hacks](https://hacks.mozilla.org/2026/06/pact-anonymous-credentials-for-the-web/)). Google's earlier Web Environment Integrity proposal "is no longer pursued" ([repo](https://github.com/RupertBenWiser/Web-Environment-Integrity)).
- **Requirements creep.** Cloudflare's own warning: "infrastructure for proving properties can become infrastructure for requiring properties". It proposes a test: if anyone can no longer build their own device or browser and still reach the web, "we should stop" ([blog](https://blog.cloudflare.com/past-bots-and-humans)).
- **Personhood needs an issuer**, and whoever issues it holds power over access.
- **Behaviour signals are a privacy cost** paid to every site that collects them.

All checked 2026-11-01.

## What a site owner can do now

1. Treat a visible puzzle as a speed bump, not a wall.
2. Use the invisible score, and look at your own score distribution before choosing thresholds.
3. Price the action: rate limits per account and per action, scaled to what abuse earns.
4. Give wanted agents a door: accept signed agents and decide, agent by agent, what each may do.
5. Keep an accessible path, and remember it is also the bot's path. See [CAPTCHAs and accessibility](@/defend/accessibility.md).

The [Defend](@/defend/_index.md) section turns these into recipes per threat. The [Research](@/research/_index.md) section tracks the standards as they change.
