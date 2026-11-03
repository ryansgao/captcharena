// Live check of a running observatory: signs requests as our test agent (and with the published RFC 9421 test key
// against Cloudflare's research directory), sends positive and negative cases to /api/check, and asserts each
// verdict. Usage: node tools/live-check.mjs [base-url] (default https://observatory.captcharena.org).
// Reads the test agent's private key from OBSERVATORY_AGENT_JWK_B64 or ./.env; prints no key material.
import { readFileSync } from "node:fs";
import { generateKeyPairSync } from "node:crypto";
import { sign, generateNonce } from "web-bot-auth";
import { signerFromJWK } from "web-bot-auth/crypto";

const base = (process.argv[2] ?? "https://observatory.captcharena.org").replace(/\/$/, "");
const agentOrigin = process.argv[3] ?? "https://observatory.captcharena.org";
const b64 = process.env.OBSERVATORY_AGENT_JWK_B64 ?? readFileSync(new URL("../.env", import.meta.url), "utf8").match(/OBSERVATORY_AGENT_JWK_B64=(\S+)/)?.[1];
const OWN = JSON.parse(Buffer.from(b64, "base64").toString("utf8"));
const RFC_TEST = JSON.parse(readFileSync(new URL("../test/vectors/rfc9421-ed25519.json", import.meta.url)));
const STRANGER = generateKeyPairSync("ed25519").privateKey.export({ format: "jwk" });
const OWN_DIR = `${agentOrigin}/.well-known/http-message-signatures-directory`;
const CF_DIR = "https://http-message-signatures-example.research.cloudflare.com/.well-known/http-message-signatures-directory";
const authority = new URL(base).host;

async function headersFor({ jwk = OWN, signatureAgent = `sig1="${OWN_DIR}"`, signFor = authority, createdOffset = 0, life = 300, nonce = true } = {}) {
  const h = signatureAgent ? { "signature-agent": signatureAgent } : {};
  const created = new Date(Date.now() + createdOffset * 1000);
  const f = await sign(new Request(`https://${signFor}/api/check`, { headers: h }), {
    signer: await signerFromJWK(jwk), created, expires: new Date(created.getTime() + life * 1000), nonce: nonce ? generateNonce() : undefined,
  });
  return { ...h, signature: f.signature, "signature-input": f.signatureInput };
}

async function check(headers) {
  const res = await fetch(`${base}/api/check`, { headers: { "user-agent": "captcharena-selftest/1 (live-check)", ...headers } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()).verdict;
}

const cases = [
  ["unsigned request", async () => check({}), { outcome: "unsigned" }],
  ["own key, dictionary Signature-Agent with full directory URL", async () => check(await headersFor()), { outcome: "valid", attribution: "url" }],
  ["own key, legacy string Signature-Agent with bare origin", async () => check(await headersFor({ signatureAgent: `"${agentOrigin}"` })), { outcome: "valid" }],
  ["RFC 9421 test key, Cloudflare research directory (third-party host)", async () => check(await headersFor({ jwk: RFC_TEST, signatureAgent: `sig1="${CF_DIR}"` })), { outcome: "valid", testKey: true }],
  ["signature made for another site", async () => check(await headersFor({ signFor: "example.com" })), { outcome: "invalid", category: "bad-signature" }],
  ["expired signature", async () => check(await headersFor({ createdOffset: -7200, life: 60 })), { outcome: "invalid", category: "expired" }],
  ["stranger's key claiming our directory", async () => check(await headersFor({ jwk: STRANGER })), { outcome: "invalid", category: "key-not-in-directory" }],
  ["directory host does not exist", async () => check(await headersFor({ signatureAgent: 'sig1="https://no-such-agent.invalid/.well-known/http-message-signatures-directory"' })), { outcome: "unverified" }],
  ["SSRF: Signature-Agent pointing at loopback", async () => check(await headersFor({ signatureAgent: 'sig1="https://127.0.0.1/.well-known/http-message-signatures-directory"' })), { outcome: "unverified", category: "directory-refused" }],
  ["SSRF: Signature-Agent pointing at cloud metadata address", async () => check(await headersFor({ signatureAgent: 'sig1="https://169.254.169.254/latest"' })), { outcome: "unverified", category: "directory-refused" }],
  ["http (not https) Signature-Agent", async () => check(await headersFor({ signatureAgent: `sig1="http://${new URL(agentOrigin).host}/.well-known/http-message-signatures-directory"` })), { outcome: "invalid", category: "signature-agent-not-https" }],
  ["replay of the same signed headers", async () => { const h = await headersFor(); await check(h); return check(h); }, { outcome: "invalid", category: "replayed-nonce" }],
];

let failed = 0;
for (const [name, run, expect] of cases) {
  let v;
  try {
    v = await run();
  } catch (e) {
    v = { outcome: `error: ${e.message}` };
  }
  const ok = Object.entries(expect).every(([k, x]) => v[k] === x);
  if (!ok) failed += 1;
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}: ${v.outcome}${v.category ? ` (${v.category})` : ""}${v.reason && !ok ? ` - ${v.reason}` : ""}`);
}
console.log(`${cases.length - failed}/${cases.length} cases as expected against ${base}`);
process.exit(failed ? 1 : 0);
