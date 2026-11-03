+++
title = "Sign your agent: Web Bot Auth and verified bots"
description = "What Web Bot Auth is, who verifies signed agents, who signs today (and who does not), the identity-is-not-permission gap, and the steps to sign."
weight = 10
[extra]
checked = "2026-11-01"
+++

Web Bot Auth lets an agent prove which product sent a request, with a cryptographic signature instead of an IP list or a user-agent string. A site, or the bot-defence vendor in front of it, can then apply a policy to that agent rather than show it a puzzle. It is the main legitimate alternative to solving CAPTCHAs, and it is already in production.

## What Web Bot Auth is

| Part | What it is | Source (checked 2026-11-01) |
|---|---|---|
| Signatures | Each request is signed with HTTP Message Signatures (RFC 9421), typically with an Ed25519 key. A `Signature-Agent` header says where to find the signer's keys. | [Cloudflare signed agents](https://blog.cloudflare.com/signed-agents/), [Cloudflare docs](https://developers.cloudflare.com/bots/concepts/bot/signed-agents) |
| Key directory | The operator publishes its public keys at `/.well-known/http-message-signatures-directory` on its own domain. | [Cloudflare docs](https://developers.cloudflare.com/bots/concepts/bot/signed-agents) |
| Standard | An IETF working group, `webbotauth`, chaired by David Schinazi and Rifaat Shekh-Yusef. Its one working-group draft is draft-ietf-webbotauth-httpsig-protocol-01 (2026-10-29). Its milestones (to the IESG in April 2026, BCP in August 2026) have passed. | [IETF working group](https://datatracker.ietf.org/wg/webbotauth/about/), [draft](https://datatracker.ietf.org/doc/draft-ietf-webbotauth-httpsig-protocol/) |
| Registry format | An individual draft for a "Signature Agent Card" and registries anyone can host (Meunier, -04, 2026-10-27). | [Cloudflare, 2025-10-30](https://blog.cloudflare.com/agent-registry/), [IETF documents](https://datatracker.ietf.org/wg/webbotauth/documents/) |

Cloudflare proposed the scheme in May 2025 and opened **signed agents**, a version of its verified-bots programme for agents *"generally directed by an end user instead of a single company"*, on 2025-08-28 ([Cloudflare](https://blog.cloudflare.com/signed-agents/), checked 2026-11-01).

## Cloudflare's listing: signed agents are now "Verified"

Cloudflare's verified-bots page has a section headed *"Signed agents are now Verified"*. It says: *"As of July 1, 2026, the distinction between a Verified bot and a signed agent is expressed by a new metadata field."* To be listed, an operator submits the *"BotBase submission form"* in the Cloudflare dashboard. The bot must be verified by one of two methods: Web Bot Auth or IP validation ([Cloudflare verified bots](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/), checked 2026-11-03).

So signing is not the only way onto the list, but it is the one that does not depend on fixed IP ranges.

## Who verifies signatures

| Verifier | What it does with signatures | Date | Source (checked 2026-11-01) |
|---|---|---|---|
| Cloudflare | Signed agents and verified bots; on 2026-10-16 it added an *"explainable trust band"* from robots.txt and HTTP 429 compliance, and plans to publish scores on Radar. | 2025-08-28; 2026-10-16 | [signed agents](https://blog.cloudflare.com/signed-agents/), [trust bands](https://blog.cloudflare.com/verified-bots-accountability/) |
| Google Cloud Fraud Defense (reCAPTCHA's successor) | Agentic activity dashboard *"integrating with industry standards such as Web Bot Auth"*; policy engine by *"risk scores, automation types, and agent identity"*. | 2026-04-23 | [Google Cloud blog](https://cloud.google.com/blog/products/identity-security/introducing-google-cloud-fraud-defense-the-next-evolution-of-recaptcha) |
| HUMAN Security (AgenticTrust) | High trust = *"verified via cryptographic key on each request"*, which can drop on behaviour; per-agent permissions. Verifies Amazon Bedrock AgentCore Browser (2025-12). | 2025-12 | [HUMAN](https://www.humansecurity.com/learn/resources/human-agentictrust), [SiliconANGLE](https://siliconangle.com/2025/12/16/human-security-brings-cryptographic-verification-amazon-bedrock-agents/) |
| Akamai | Web Bot Auth *"is key to achieving strong and accurate identification of the so-called 'known bots'"*; adds its own "Know Your Agent" signal. | 2025-11-20 | [Akamai blog](https://www.akamai.com/blog/security/bot-management-agentic-era) |
| Fingerprint | Verifies agents via Web Bot Auth; offers a free validation tool. | 2026-02-03 | [press release](https://www.businesswire.com/news/home/20260203647429/en/Fingerprint-Launches-Authorized-AI-Agent-Detection-to-Identify-Agentic-AI-Traffic-with-100-CertaintyAccelerating-Enterprise-Automation-and-Agentic-Commerce), [docs](https://docs.fingerprint.com/docs/bot-detection/web-bot-auth-implementation.md) |
| Arkose Labs (Agent Trust Manager) | Sorts agent traffic into *"Self-Disclosing Good Agents"* (publish IPs, sign headers), *"Non-Disclosing Good Agents"* and *"Malicious Adversaries"*. | 2026-06-16 | [Arkose](https://www.arkoselabs.com/news/arkose-agent-trust-manager-helps-companies-accelerate-revenue-by-classifying-and-controlling-agentic-traffic-as-a-customer-an-authorized-agent-or-an-adversary) |

One X post claims hCaptcha now supports Web Bot Auth; hCaptcha's own February 2026 post does not mention it. Unverified (checked 2026-11-01).

## Who signs today

We probed each operator's key directory at `https://<host>/.well-known/http-message-signatures-directory` on 2026-11-01.

| Agent or operator | Signs? | Evidence | Date |
|---|---|---|---|
| ChatGPT agent (OpenAI) | Yes | Directory at chatgpt.com returns one Ed25519 key, `"purpose":"ai"`. In the signed-agents launch group. | Probed 2026-11-01; launch 2025-08-28 ([Cloudflare](https://blog.cloudflare.com/signed-agents/)) |
| Google-Agent | Partly | *"A subset of requests made by the Google-Agent are signed"*, as `https://agent.bot.goog`; *"We don't sign every request of a particular agent."* The directory serves five Ed25519 keys. | Doc updated 2026-10-13 ([Google](https://developers.google.com/crawling/docs/crawlers-fetchers/web-bot-auth)); probed 2026-11-01 |
| Browserbase | Yes | Directory at www.browserbase.com returns an Ed25519 key. In the launch group. | Probed 2026-11-01 |
| Goose (Block), Anchor Browser, Cloudflare Browser Rendering | Yes, per Cloudflare | Named in the signed-agents launch group. (The apex probe of anchorbrowser.io returned 404; the header can point to another host.) | 2025-08-28 ([Cloudflare](https://blog.cloudflare.com/signed-agents/)) |
| Amazon Bedrock AgentCore Browser | Yes, with a service key | Plans to move to customer-specific keys *"once the protocol matures"*. | 2025-10-30 ([Cloudflare](https://blog.cloudflare.com/agent-registry/)) |
| Visa, Mastercard (payment agents) | Yes | Both host their own key directories; American Express *"will also be leveraging Web Bot Auth"*. | 2025-10-24 ([Cloudflare](https://blog.cloudflare.com/secure-agentic-commerce/)) |
| OpenAI, Google, AWS (in general) | Yes, per Cloudflare | *"OpenAI, Google and AWS sign with Web Bot Auth."* | 2026-09-30 ([Cloudflare](https://blog.cloudflare.com/agentic-web/)) |
| Anthropic (Claude) | No signature found | Publishes an IP list only (`claude.com/crawling/bots.json`); its crawler page does not mention signatures. Key directory on claude.ai, claude.com and www.anthropic.com: 404. | Page 2026-04-07 ([Anthropic](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)); probed 2026-11-01 |
| Perplexity, Amazon, Manus, browser-use, openai.com apex | Not found at the apex | 404 at each apex domain. This does not prove they do not sign, because the `Signature-Agent` header can point to any host. | Probed 2026-11-01 |

{% <note> %}
Coverage is thin in practice. Arkose files "Claude computer use, ChatGPT agent mode and agentic browsers" under non-disclosing agents ([Arkose, 2026-06-16](https://www.arkoselabs.com/news/arkose-agent-trust-manager-helps-companies-accelerate-revenue-by-classifying-and-controlling-agentic-traffic-as-a-customer-an-authorized-agent-or-an-adversary)). A figure of "2.3% of legitimate agent sessions" signed is attributed to an Arkose report by secondary coverage only, and one tester on X reports that only one of 23 browser agents signed in October 2026. Both are unverified (checked 2026-11-01).
{% </note> %}

## The gap: identity is not permission

A signature says which product is calling. It does not say which person authorised it, or what they authorised it to do. This is deliberate in the standard:

- The working-group charter puts *"Authenticating the end user of a participating client or agent"* out of scope, along with reputation and *"distinguishing non-participating bots from non-bot clients"* ([charter](https://datatracker.ietf.org/doc/charter-ietf-webbotauth/), checked 2026-11-01).
- The draft says it *"does not authenticate human users, does not provide anonymous authentication, and does not define authorization or delegation"*, and that delegation is *"expected to be specified separately"* ([draft -01](https://datatracker.ietf.org/doc/draft-ietf-webbotauth-httpsig-protocol/), checked 2026-11-01).
- Gosschalk of Arkose Labs, in an interview: Web Bot Auth *"establishes an identity signal, rather than the user's permission for a particular transaction"* ([interview, 2026-10-27](https://letsdatascience.com/news/arkose-labs-tells-lds-why-agent-identity-is-not-permission-39afe6cc), checked 2026-11-01).

Payments have partly filled the gap for purchases (Visa Trusted Agent Protocol, Mastercard Verifiable Intent, Google's AP2). Nothing open does it yet for ordinary actions such as posting, signing up or downloading. The [industry roadmap](@/research/industry-roadmap.md) lists the drafts and what is built.

## How to sign: the steps

These are the conceptual steps. Follow the specification and your verifier's documentation for the details.

1. **Generate a key pair** for the agent product (the deployments listed above use Ed25519). Keep the private key in your signing service, never in the browser profile a user can export.
2. **Publish a key directory** at `/.well-known/http-message-signatures-directory` on a domain you control, served as `application/http-message-signatures-directory+json`. Plan for key rotation: publish the new key before you sign with it.
3. **Sign outgoing requests** with HTTP Message Signatures (RFC 9421), and send a `Signature-Agent` header that points at your directory. Sign every request from the agent, not a subset, or sites cannot rely on it.
4. **Register with verifiers.** Submit the agent to Cloudflare's verified-bots programme (BotBase submission form) and to the other vendors your users meet. Describe what the agent does and who directs it.
5. **Behave like a verified agent.** Cloudflare now scores verified bots on robots.txt and HTTP 429 compliance ([2026-10-16](https://blog.cloudflare.com/verified-bots-accountability/)). A signature makes the agent accountable, including for bad behaviour.
6. **Keep a hand-off path.** A signed agent will still meet CAPTCHAs on sites that do not verify signatures. See [hand-off patterns](@/build/hand-off.md).

### Specifications and open libraries

| Resource | What | Licence and status (checked 2026-11-01) |
|---|---|---|
| [draft-ietf-webbotauth-httpsig-protocol](https://datatracker.ietf.org/doc/draft-ietf-webbotauth-httpsig-protocol/) | The working-group protocol draft | -01, 2026-10-29 |
| [RFC 9421](https://www.rfc-editor.org/rfc/rfc9421) | HTTP Message Signatures | Standard |
| [cloudflare/web-bot-auth](https://github.com/cloudflare/web-bot-auth) | Sign and verify libraries; reference implementation of the draft | Apache-2.0; last commit 2026-10-27 |
| [OpenBotAuth/openbotauth](https://github.com/OpenBotAuth/openbotauth) | Another open implementation | Apache-2.0; last commit 2026-10-23 |
| [sitedex/web-bot-auth-lint](https://github.com/sitedex/web-bot-auth-lint) | Linter for key directories | Small project |
| [Fingerprint validator](https://docs.fingerprint.com/docs/bot-detection/web-bot-auth-implementation.md) | Free validation tool | Vendor-hosted |

To check how your own signed agent and your browser look from the site side, see our [browser score](@/browser-score/_index.md) section.
