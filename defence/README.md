# defence/ — blue team, path A (plan step 10)

What the industry is building for agent identity and anonymous tokens, as running code. Built 2026-11-03/04.
Every part stands on the reference implementation of its standard; each is written in that implementation's
language (TypeScript for Web Bot Auth, Go for Privacy Pass/Anubis, Python for MoLE and Prio).

| Part | Plan item | Runs | Status |
|---|---|---|---|
| `observatory/` | C4 signed-agent observatory | **https://observatory.captcharena.org** (the hosting server `captcha-observatory`, port 8320) | live, 27 unit tests + 12/12 live cases |
| `anubis-tokens/` | C5 tokens in Anubis | **https://anubis.captcharena.org** (the hosting server `captcha-anubis`, port 8330) | live, 9 Go tests + 12/12 browser e2e (public and local) |
| `pact-lab/` | C1 PACT-lab (first slice) | container only (`docker build -t captcha-pactlab:local pact-lab && docker run --rm --network none captcha-pactlab:local`) | 14 tests pass; C7 and C2 not started |

## C4 — signed-agent observatory

Every visit is checked for a Web Bot Auth signature (draft-ietf-webbotauth-httpsig-protocol-01) with Cloudflare's
reference library (`web-bot-auth` 0.2.0, `http-message-sig` 0.3.0), and the declared agent is checked against the IP
list its operator publishes (12 lists: OpenAI ×3, Anthropic, Google ×3, Perplexity ×2, Apple, Bing, Common Crawl).
Only verdicts are stored (no IP, no browser User-Agent). Public page `/`, data `/data.json`, `/data.csv`, a
self-test endpoint `/api/check`, robots.txt trap `/trap/`, 429 pace test `/pace/`, `Accept-Signature` on every
response, and the site's own signed test-agent key directory.

What we wrote ourselves (the library leaves it to the caller): key discovery from Signature-Agent with an SSRF guard
(https/443 only, public addresses checked at connect time, no redirects, 64 KB, 5 s, 60 fetches/min), a cache that
obeys §6.10 (a failed fetch never evicts a good key set), the Appendix B directory-signature check, nonce replay and
static-signature reuse, the four outcomes of Appendix C.1 (unsigned / valid / invalid / unverified), and a daily
in-process probe of 13 operator directories plus every Signature-Agent host seen (no outside timer needed).

Evidence:
- `node --test test/*.test.mjs` 27/27, including Cloudflare's published request vectors (Ed25519 and RSA-PSS, with
  and without Signature-Agent) and its directory-response vector.
- `node tools/live-check.mjs` against the public site, 2026-11-04: **12/12** — own key (dictionary and legacy header
  forms), RFC test key against Cloudflare's research directory (third-party host), and negatives: wrong site
  (bad-signature), expired, stranger's key, nonexistent directory (unverified), loopback and 169.254.169.254
  (refused), http Signature-Agent, nonce replay.
- First probe (2026-11-03): directories published by **chatgpt.com** (1 key, directory proof 1/1 valid),
  **agent.bot.goog** (5 keys), **www.browserbase.com** (2 keys), Cloudflare's research agent (1 key). None at
  claude.ai, claude.com, anthropic.com, perplexity.ai, amazon.com, manus.im, anchorbrowser.io (404) — matches deep-3.

Findings worth writing up:
- Only ChatGPT's directory passes the -01 Appendix B proof. Google's and Cloudflare's research directory sign
  without `content-digest` (required by -01), and Browserbase signs `@authority` on a response without the `req`
  flag. All three still verify request signatures; the domain-binding proof is what fails.
- The -01 draft's own example `kid` for the RFC 9421 Ed25519 test key (`NFcWBst6…`) is not that key's RFC 7638
  thumbprint (`poqkLGiymh…`, computed independently in Python and by Cloudflare's library and vectors). Errata candidate.
- The reference library still emits `;type=directory` on Signature-Agent members, which -01 §5.2.1 says verifiers
  MUST ignore; the observatory accepts and counts both forms.

## C5 — tokens in Anubis

Anubis v1.28.2 has no Privacy Pass or Web Bot Auth code (checked 2026-11-03), so it runs **unmodified** behind a small
gate (`ppgate`, Go, Cloudflare's `pat-go` for RFC 9578 type-2 blind RSA, `golang-jwt` as Anubis uses):
- A visitor who solved Anubis's proof of work (valid EdDSA pass cookie, IP binding checked like Anubis does) may buy
  up to 10 blind-signed tokens; the gate cannot link a later token to the pass.
- A request with `Authorization: PrivateToken token=…` (RFC 9577) from a trusted issuer, made for this site's
  challenge and unspent, goes straight to the backend. Spent tokens are logged to disk, so a restart cannot reopen them.
- A request with a valid Web Bot Auth signature goes straight to the backend; verification is delegated to the
  observatory image (one WBA implementation in the stack). Published test keys and invalid signatures get Anubis.
- Everyone else gets Anubis, plus a `WWW-Authenticate: PrivateToken` challenge per trusted issuer. External issuers
  (`GATE_TRUSTED_ISSUERS`) are accepted too — the slot for the C7 process-check issuer.

Evidence: `go test ./gate/` 9/9 (double spend, other-site token, untrusted issuer, tampered token, expired /
foreign-key / other-IP pass, 10-per-pass cap, external issuer, restart, WBA path, forged gate header).
`e2e/run.py` (real headless Chromium solves the PoW; `ppclient` fetches and spends tokens; Node signs WBA requests):
**12/12 on https://anubis.captcharena.org** and 12/12 locally (2026-11-04). Proof of work 1.1 s in Chromium at
difficulty 4 vs a token visit of 170 ms over the internet (4 ms locally); 10 tokens per solve = 10 visits without
work and without a cookie.

Upstream shape: the gate package is what an Anubis PR (issues #119, #326) would contain; not opened (needs a
discussion with the maintainer first; WBA in Anubis is the maintainer's own work, #744).

## C1 — PACT-lab, first slice

The MoLE protocol layer and HTTP transport (draft-jms-mole-protocols and draft-jms-mole-http-transport-01, MoLE repo
at 2789337, 2026-11-02), which had no implementation ("Existing implementations: To be added"), on the draft authors'
own EC-IHAT and EC-ACT reference crypto. The reference code is fetched at pinned commits inside the image and never
runs on the owner's machine.
- `wire.py`: GrantRequest / GrantCommitments / GrantChallenges / GrantResponses, RedemptionChallenge,
  IssuanceRequest/Response, EC-ACT Challenge, PresentationAndUpdate, Update; the `Mole` auth-param syntax with the
  transport's validation rules (duplicates, malformed typed names, type 0, canonical unpadded base64url).
- `anchor.py`: grant in two exchanges, random session id claimed atomically, per-subject budget, pluggable policy.
- `moderator.py`: configuration per the draft's CDDL, stateless redemption context (HMAC of origin, policy, time
  window; adjacent window accepted), Redeem & Issue in the draft's step order with atomic replay record, presentation
  steps 1-4 with atomic nullifier record, 409 for duplicates, recovery by handle, abusive request → NoUpdate (the
  chain and its balance end).
- `client.py`: wallet (JSON, exportable), grant, Redeem & Issue on 401, presentation with cached policy-scoped
  challenge, Update finalisation, greasing; the **agent lane** is the user's wallet handed to an agent.

Evidence: 14/14 tests — end-to-end metered access, abuse revokes the chain, balance exhaustion then re-redeem,
duplicate → 409 + recovery, copied credential accepted once (agent vs user), endorsement redeemed once, Anchor outside
the accepted set refused, second Anchor in the set works (issuer hiding), Anchor budget and session rules, both
challenges on 401, greased type treated as absent, wire rules. Measured: presentation header 1,981 bytes, prove
~108 ms, verify + refund + finalize ~145 ms (Python reference code, not constant-time).

Deviations: balance width fixed at 8 bits (the reference code fixes L=8); client pending-spend state is in memory
only (recovery works within one process); policy-scoped challenge profile only; one Moderator key.

## Next (not started)

- **C7 process-check Anchor**: a short drag task whose process features are scored and discarded, issuing EC-IHAT
  Endorsements and Privacy Pass tokens (the gate already accepts external issuers). Then point our solver at it.
- **C2 private Anchor scoring**: per-presentation Prio3Histogram report of the Anchor index (CFRG VDAF reference
  code), labelled by the Moderator's abuse decision, two aggregators; simulate one bad Anchor. Open problem to state:
  a client can lie about its Anchor in the report.
- PACT-lab: browser extension client, operator-run Anchor variant, request-bound challenges, public demo.
- C4: a monthly scripted run of agent products we can access (ChatGPT agent, Comet, Manus, Browserbase …) against
  the observatory; show directory-proof failure reasons on the page.
- Registry rows owed (private files, not edited here): `the private automation registry` (observatory daily probe,
  in-process), `the deploy tool's README` deployed-projects table and `projects` copy (captcha-observatory 8320,
  captcha-anubis 8330), Plan `prj-captcha` step 10 status.
