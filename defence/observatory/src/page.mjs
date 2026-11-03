// Public HTML page. No script at all (passes a strict CSP); one stylesheet.
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const n = (x) => Number(x ?? 0);
const pct = (a, b) => (n(b) === 0 ? "–" : `${Math.round((100 * n(a)) / n(b))}%`);
const when = (ts) => (ts ? new Date(ts * 1000).toISOString().replace("T", " ").slice(0, 16) + " UTC" : "–");

function table(head, rows, empty) {
  if (rows.length === 0) return `<p class="empty">${esc(empty)}</p>`;
  return `<div class="scroll"><table><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows
    .map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`)
    .join("")}</tbody></table></div>`;
}

const yes = (ok, label = ok ? "yes" : "no") => `<span class="${ok ? "good" : "bad"}">${esc(label)}</span>`;

export function renderPage({ origin, cssHref, directories, ipLists, families, signers, failures, totals, keySets, windowDays }) {
  const dirRows = directories.map((d) => [
    esc(d.label),
    `<code>${esc(new URL(d.target).host)}</code>`,
    d.ok ? yes(true, `published (${d.keys} key${d.keys === 1 ? "" : "s"})`) : `<span class="muted">${esc(d.error ?? "no")}</span>`,
    d.ok ? (d.proof_sigs ? yes(d.proof_valid === d.proof_sigs, `${d.proof_valid} of ${d.proof_sigs} valid`) : `<span class="muted">not signed</span>`) : "–",
    d.ok ? yes(Boolean(d.content_type_ok), d.content_type_ok ? "yes" : esc(d.content_type || "none")) : "–",
    d.ok ? esc(keySets[d.target] ?? 1) : "–",
    esc(when(d.ts)),
  ]);
  const famRows = families.map((f) => [
    `${esc(f.family)}${f.self_test ? ' <span class="tag">our test agent</span>' : ""}`,
    esc(f.operator ?? "–"),
    esc(f.requests),
    pct(f.signed, f.requests),
    n(f.signed) ? `${pct(f.valid, f.signed)} of signed` : "–",
    n(f.ip_match) + n(f.ip_mismatch) ? `${pct(f.ip_match, n(f.ip_match) + n(f.ip_mismatch))}` : "–",
    esc(f.robots_fetches),
    n(f.trap_hits) ? `<span class="bad">${esc(f.trap_hits)}</span>` : "0",
    n(f.pace_early) + n(f.pace_respected) ? `${esc(f.pace_respected)} waited, ${esc(f.pace_early)} came back early` : "–",
  ]);
  const signerRows = signers.map((s) => [
    `<code>${esc(s.signer)}</code>${s.self_test ? ' <span class="tag">our test agent</span>' : ""}`,
    esc(s.requests),
    esc(s.valid),
    esc(s.invalid),
    esc(s.unverified),
    esc(s.keys),
    n(s.test_key) ? `<span class="bad">${esc(s.test_key)}</span>` : "0",
    esc(s.with_nonce),
    s.max_lifetime === null ? "–" : `${Math.round(n(s.max_lifetime) / 60)} min`,
    esc((s.forms ?? "").replace(/,/g, ", ")),
  ]);
  const failRows = failures.map((f) => [esc(f.outcome === "unverified" ? "could not check" : "invalid"), esc(REASONS[f.category] ?? f.category), esc(f.n), f.self_test ? "our test agent" : "visitors"]);
  const ipRows = ipLists.map((l) => {
    const extra = l.extra ? JSON.parse(l.extra) : {};
    return [esc(LIST_NAMES[l.label] ?? l.label), `<code>${esc(new URL(l.target).host + new URL(l.target).pathname)}</code>`, l.ok ? esc(l.keys) : `<span class="bad">${esc(l.error)}</span>`, esc(extra.creationTime ?? "–"), esc(when(l.ts))];
  });

  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Signed-agent observatory: which AI agents prove who they are</title>
<meta name="description" content="Live public measurement of Web Bot Auth adoption: which AI agents sign their HTTP requests, whether the signatures verify, and whether agents follow robots.txt and 429.">
<link rel="stylesheet" href="${esc(cssHref)}"></head><body><main>
<h1>Signed-agent observatory</h1>
<p class="lede">Which AI agents prove who they are, and whether they respect what a site asks. Every visit to this site is checked for a Web Bot Auth signature (the IETF standard for agents signing their HTTP requests) and against the IP lists the agent's operator publishes. Only counts are kept and shown.</p>
<p class="stats">${esc(n(totals.requests))} visits in the last ${windowDays} days, ${esc(n(totals.signed))} signed, ${esc(n(totals.valid))} with a valid signature (our own test traffic excluded). First visit recorded ${esc(when(totals.first_ts))}.</p>

<section><h2>Agent operators' key directories (checked daily)</h2>
<p>Each operator would publish its public keys at <code>/.well-known/http-message-signatures-directory</code>. "Signed directory" is the optional proof that the key holder served the list itself (Appendix B of the draft). A change in "key sets seen" means keys were rotated.</p>
${table(["Operator", "Host", "Key directory", "Signed directory", "Right content type", "Key sets seen (30 days)", "Checked"], dirRows, "No probe has run yet.")}
</section>

<section><h2>Visiting agents, last ${windowDays} days</h2>
<p>Grouped by the name the agent declares in its User-Agent. "IP in operator's list" counts only agents whose operator publishes one. robots.txt here forbids <code>/trap/</code>; <code>/pace/</code> answers 429 with Retry-After: 20 and checks whether the agent waits.</p>
${table(["Agent", "Operator", "Visits", "Signed", "Signature valid", "IP in operator's list", "Read robots.txt", "Entered forbidden path", "After a 429"], famRows, "No visits yet.")}
</section>

<section><h2>Who signed, last ${windowDays} days</h2>
<p>Grouped by the Signature-Agent URL (the key directory the agent points to). "Couldn't check" means the directory could not be fetched; the draft says that is not the same as invalid.</p>
${table(["Signature-Agent", "Signed visits", "Valid", "Invalid", "Couldn't check", "Distinct keys", "Used a public test key", "With nonce", "Longest signature life", "Header form"], signerRows, "No signed visit yet.")}
</section>

<section><h2>Why signatures failed</h2>
${table(["Result", "Reason", "Visits", "From"], failRows, "No failed signature yet.")}
</section>

<section><h2>Operators' published IP lists (checked daily)</h2>
<p>The older way to prove identity: a list of address ranges. A visit claiming one of these agents is checked against its list.</p>
${table(["List", "Where", "Ranges", "List dated", "Checked"], ipRows, "No list fetched yet.")}
</section>

<section id="test"><h2>Test your own agent</h2>
<p>Send a signed request to <code>${esc(origin)}/api/check</code>. The reply is the full verdict as JSON: which signature was checked, the key directory we fetched, and the exact reason if it failed. Your visit is counted like any other.</p>
<pre>curl -s ${esc(origin)}/api/check -H 'Signature-Agent: sig1="https://your-agent.example/.well-known/http-message-signatures-directory"' \\
  -H 'Signature-Input: sig1=("@authority" "signature-agent";key="sig1");created=…;expires=…;keyid="…";tag="web-bot-auth"' \\
  -H 'Signature: sig1=:…:'</pre>
<p>This site also publishes a key directory for its own test agent at <a href="${DIR}"><code>${DIR}</code></a>; our test visits are labelled "our test agent" above.</p>
</section>

<section><h2>Method and data</h2>
<ul>
<li>Verification uses Cloudflare's reference library (<code>web-bot-auth</code>) against draft-ietf-webbotauth-httpsig-protocol-01. Both the old header form (a bare string) and the new dictionary form are accepted and counted.</li>
<li>Nothing that identifies a person is stored: no IP address (it is compared with the published lists and then dropped), no browser User-Agent string, no cookies.</li>
<li>Downloads: <a href="/data.json">data.json</a> (everything on this page) and <a href="/data.csv">data.csv</a> (monthly counts per agent).</li>
<li>Part of the captcharena project's blue-team work: measuring the agent-identity half of what the industry is building.</li>
</ul></section>
</main></body></html>`;
}

const DIR = "/.well-known/http-message-signatures-directory";

export const REASONS = {
  "bad-signature": "the signature does not match the request",
  "key-not-in-directory": "the key is not in the agent's own directory",
  "directory-unreachable": "the key directory could not be reached",
  "directory-http-error": "the key directory answered with an error",
  "directory-refused": "the key directory points at a private or non-https address (refused)",
  "directory-unusable": "the key directory is not a usable key list",
  "no-signature-agent": "no Signature-Agent header and an unknown key",
  expired: "the signature had expired",
  "created-in-future": "the signature is dated in the future",
  "too-old": "the signature is more than a day old",
  "wrong-tag": "the tag is not web-bot-auth",
  "authority-not-covered": "the signature does not cover the site's name",
  "signature-agent-not-covered": "the signature does not cover Signature-Agent",
  "signature-agent-not-https": "Signature-Agent is not an https URL",
  "signature-agent-not-url": "Signature-Agent is not a URL",
  "missing-parameter": "a required parameter (created, expires, keyid, alg, tag) is missing",
  "replayed-nonce": "the nonce was already used (a replay)",
  "bad-nonce": "the nonce is not 64 bytes of base64",
  malformed: "the signature headers cannot be parsed",
  "missing-field": "a covered header is missing",
  "unsupported-component": "the signature covers a component we cannot rebuild",
  algorithm: "the algorithm is not Ed25519 or RSA-PSS-SHA512",
  policy: "another policy rule",
  other: "other",
};

const LIST_NAMES = {
  "openai-chatgpt-user": "OpenAI ChatGPT-User",
  "openai-searchbot": "OpenAI OAI-SearchBot",
  "openai-gptbot": "OpenAI GPTBot",
  anthropic: "Anthropic (all Claude bots)",
  "google-user-agents": "Google user-triggered agents",
  "google-user-fetchers": "Google user-triggered fetchers",
  "google-common": "Google common crawlers",
  "perplexity-user": "Perplexity-User",
  "perplexity-bot": "PerplexityBot",
  applebot: "Applebot",
  bingbot: "Bingbot",
  ccbot: "Common Crawl CCBot",
};
