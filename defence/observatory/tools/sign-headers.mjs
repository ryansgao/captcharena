// Print Web Bot Auth headers (JSON) for one request, signed with Cloudflare's reference library.
// Usage: node tools/sign-headers.mjs <url> <signature-agent-url> [own|rfc-test]
//   own       the observatory's test agent key (OBSERVATORY_AGENT_JWK_B64 or ./.env)  [default]
//   rfc-test  the published RFC 9421 Ed25519 test key
import { readFileSync } from "node:fs";
import { sign, generateNonce } from "web-bot-auth";
import { signerFromJWK } from "web-bot-auth/crypto";

const [url, agent, which = "own"] = process.argv.slice(2);
let jwk;
if (which === "rfc-test") {
  jwk = JSON.parse(readFileSync(new URL("../test/vectors/rfc9421-ed25519.json", import.meta.url)));
} else {
  const b64 = process.env.OBSERVATORY_AGENT_JWK_B64 ?? readFileSync(new URL("../.env", import.meta.url), "utf8").match(/OBSERVATORY_AGENT_JWK_B64=(\S+)/)?.[1];
  jwk = JSON.parse(Buffer.from(b64, "base64").toString("utf8"));
}
const headers = { "signature-agent": `sig1="${agent}"` };
const now = new Date();
const f = await sign(new Request(url, { headers }), { signer: await signerFromJWK(jwk), created: now, expires: new Date(now.getTime() + 300_000), nonce: generateNonce() });
process.stdout.write(JSON.stringify({ ...headers, signature: f.signature, "signature-input": f.signatureInput }));
