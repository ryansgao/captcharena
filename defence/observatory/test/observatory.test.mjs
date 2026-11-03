// node --test test/  — verifier, identity schemes, store and HTTP app, with a fake network.
import { test } from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { generateKeyPairSync } from "node:crypto";
import { sign, generateNonce } from "web-bot-auth";
import { signerFromJWK } from "web-bot-auth/crypto";
import { createSignature, component } from "http-message-sig";
import { Verifier, discoveryUrl } from "../src/wba.mjs";
import { isPublicAddress, safeGet, FetchError } from "../src/net.mjs";
import { classify, parsePrefixes, inPrefixes, IpLists } from "../src/agents.mjs";
import { Store } from "../src/store.mjs";
import { createApp, directoryResponse } from "../src/server.mjs";

const vectors = (f) => JSON.parse(readFileSync(new URL(`./vectors/${f}`, import.meta.url)));
const TEST_ED25519 = vectors("rfc9421-ed25519.json");
const freshJwk = () => {
  const { privateKey } = generateKeyPairSync("ed25519");
  return privateKey.export({ format: "jwk" });
};
const AGENT_JWK = freshJwk();
const OTHER_JWK = freshJwk();
const AGENT_DIR = "https://agent.test/.well-known/http-message-signatures-directory";
const OBS = "obs.test";

/** Fake network: directories by URL; anything else is a DNS failure. */
function fakeFetcher(dirs) {
  return async (url) => {
    const d = dirs[url];
    if (!d) throw new FetchError("dns", `getaddrinfo ENOTFOUND ${new URL(url).host}`);
    if (typeof d === "function") return d(url);
    return d;
  };
}

async function signedDirectory(jwk, url) {
  const r = await directoryResponse(jwk, url, { host: new URL(url).host });
  return { status: 200, headers: r.headers, body: r.body, url };
}

async function signedHeaders({ jwk = AGENT_JWK, authority = OBS, signatureAgent = `sig1="${AGENT_DIR}"`, expiresIn = 300, created, nonce = generateNonce() } = {}) {
  const headers = signatureAgent ? { "signature-agent": signatureAgent } : {};
  const req = new Request(`https://${authority}/api/check`, { headers });
  const now = created ?? new Date();
  const fields = await sign(req, { signer: await signerFromJWK(jwk), created: now, expires: new Date(now.getTime() + expiresIn * 1000), nonce: nonce ?? undefined });
  return { ...headers, signature: fields.signature, "signature-input": fields.signatureInput };
}

async function verifierWithAgent() {
  return new Verifier({ fetcher: fakeFetcher({ [AGENT_DIR]: await signedDirectory(AGENT_JWK, AGENT_DIR) }) });
}

const check = (v, headers, authority = OBS) => v.verifyRequest({ method: "GET", url: `https://${authority}/api/check`, headers });

test("unsigned request", async () => {
  const v = await verifierWithAgent();
  const r = await check(v, { "user-agent": "curl/8" });
  assert.equal(r.outcome, "unsigned");
});

test("valid signature, dictionary Signature-Agent, signed directory", async () => {
  const v = await verifierWithAgent();
  const r = await check(v, await signedHeaders());
  assert.equal(r.outcome, "valid", r.reason);
  assert.equal(r.attribution, "url");
  assert.equal(r.signatureAgent.form, "dictionary");
  assert.equal(r.directory.resolution, "direct");
  assert.deepEqual(r.directory.proof, { signatures: 1, valid: 1, digestOk: true });
  assert.equal(r.directory.contentTypeOk, true);
  assert.equal(r.hasNonce, true);
});

test("legacy string Signature-Agent with a bare origin resolves origin + well-known", async () => {
  const v = await verifierWithAgent();
  const r = await check(v, await signedHeaders({ signatureAgent: '"https://agent.test"' }));
  assert.equal(r.outcome, "valid", r.reason);
  assert.equal(r.signatureAgent.form, "legacy-string");
  assert.equal(r.directory.resolution, "origin-plus-well-known");
});

test("signature made for another site is invalid", async () => {
  const v = await verifierWithAgent();
  const r = await check(v, await signedHeaders({ authority: "elsewhere.test" }));
  assert.equal(r.outcome, "invalid");
  assert.equal(r.category, "bad-signature");
});

test("expired signature is invalid", async () => {
  const v = await verifierWithAgent();
  const r = await check(v, await signedHeaders({ created: new Date(Date.now() - 3600_000), expiresIn: 60 }));
  assert.equal(r.outcome, "invalid");
  assert.equal(r.category, "expired");
});

test("signature dated in the future is invalid", async () => {
  const v = await verifierWithAgent();
  const r = await check(v, await signedHeaders({ created: new Date(Date.now() + 3600_000) }));
  assert.equal(r.outcome, "invalid");
  assert.equal(r.category, "created-in-future");
});

test("key not in the agent's directory is invalid", async () => {
  const v = await verifierWithAgent();
  const r = await check(v, await signedHeaders({ jwk: OTHER_JWK }));
  assert.equal(r.outcome, "invalid");
  assert.equal(r.category, "key-not-in-directory");
});

test("unreachable directory is unverified, not invalid (draft §6.10)", async () => {
  const v = await verifierWithAgent();
  const r = await check(v, await signedHeaders({ signatureAgent: 'sig1="https://nowhere.test/.well-known/http-message-signatures-directory"' }));
  assert.equal(r.outcome, "unverified");
  assert.equal(r.category, "directory-unreachable");
});

test("a failed refetch does not evict a good cached directory", async () => {
  let up = true;
  const good = await signedDirectory(AGENT_JWK, AGENT_DIR);
  let clock = Date.now();
  const v = new Verifier({
    now: () => clock,
    fetcher: async (url) => {
      if (!up) throw new FetchError("connect", "ECONNREFUSED");
      return { ...good, url };
    },
  });
  assert.equal((await v.directory(AGENT_DIR)).ok, true);
  up = false;
  clock += 11 * 60_000; // past the positive TTL
  const again = await v.directory(AGENT_DIR);
  assert.equal(again.ok, true);
  assert.equal(again.stale, true);
});

test("replayed nonce is invalid on the second use", async () => {
  const v = await verifierWithAgent();
  const h = await signedHeaders();
  assert.equal((await check(v, h)).outcome, "valid");
  const second = await check(v, h);
  assert.equal(second.outcome, "invalid");
  assert.equal(second.category, "replayed-nonce");
});

test("static signature without nonce verifies but is flagged as reused", async () => {
  const v = await verifierWithAgent();
  const h = await signedHeaders({ nonce: null });
  assert.equal((await check(v, h)).reused, false);
  const again = await check(v, h);
  assert.equal(again.outcome, "valid");
  assert.equal(again.reused, true);
});

test("wrong tag is invalid", async () => {
  const v = await verifierWithAgent();
  const headers = { "signature-agent": `sig1="${AGENT_DIR}"` };
  const signer = await signerFromJWK(AGENT_JWK);
  const created = Math.floor(Date.now() / 1000);
  const f = await createSignature(new Request(`https://${OBS}/api/check`, { headers }), {
    label: "sig1", signer, components: ["@authority", component("signature-agent", { key: "sig1" })],
    parameters: { created, expires: created + 300, keyid: signer.keyid, alg: "ed25519", tag: "not-web-bot-auth" },
  });
  const r = await check(v, { ...headers, signature: f.signature, "signature-input": f.signatureInput });
  assert.equal(r.outcome, "invalid");
  assert.equal(r.category, "wrong-tag");
});

test("Signature-Agent present but not covered is invalid", async () => {
  const v = await verifierWithAgent();
  const headers = { "signature-agent": `sig1="${AGENT_DIR}"` };
  const signer = await signerFromJWK(AGENT_JWK);
  const created = Math.floor(Date.now() / 1000);
  const f = await createSignature(new Request(`https://${OBS}/api/check`, { headers }), {
    label: "sig1", signer, components: ["@authority"],
    parameters: { created, expires: created + 300, keyid: signer.keyid, alg: "ed25519", tag: "web-bot-auth" },
  });
  const r = await check(v, { ...headers, signature: f.signature, "signature-input": f.signatureInput });
  assert.equal(r.outcome, "invalid");
  assert.equal(r.category, "signature-agent-not-covered");
});

test("no Signature-Agent and an unknown key is unverified", async () => {
  const v = await verifierWithAgent();
  const r = await check(v, await signedHeaders({ signatureAgent: null }));
  assert.equal(r.outcome, "unverified");
  assert.equal(r.category, "no-signature-agent");
});

test("garbage headers are malformed", async () => {
  const v = await verifierWithAgent();
  const r = await check(v, { signature: "nope", "signature-input": "((((" });
  assert.equal(r.outcome, "invalid");
  assert.equal(r.category, "malformed");
});

test("http Signature-Agent is refused before any fetch", async () => {
  let fetched = false;
  const v = new Verifier({ fetcher: async () => { fetched = true; throw new Error("x"); } });
  const r = await check(v, await signedHeaders({ signatureAgent: 'sig1="http://agent.test/keys"' }));
  assert.equal(r.outcome, "invalid");
  assert.equal(fetched, false);
});

test("Cloudflare's published request vectors verify (ed25519 and rsa-pss, with and without Signature-Agent)", async () => {
  for (const vec of vectors("web_bot_auth_architecture_v2.json")) {
    const { d, p, q, dp, dq, qi, ...pub } = vec.key;
    void d, p, q, dp, dq, qi;
    const dirUrl = "https://signature-agent.test/.well-known/http-message-signatures-directory";
    const v = new Verifier({
      now: () => vec.created_ms + 10_000,
      fetcher: fakeFetcher({ [dirUrl]: { status: 200, headers: { "content-type": "application/http-message-signatures-directory+json" }, body: Buffer.from(JSON.stringify({ keys: [pub] })), url: dirUrl } }),
    });
    const headers = { signature: vec.signature, "signature-input": vec.signature_input };
    if (vec.signature_agent) headers["signature-agent"] = vec.signature_agent;
    else await v.directory(dirUrl); // §4.3: without Signature-Agent we verify only with a key we already hold
    const r = await v.verifyRequest({ method: "GET", url: vec.target_url, headers });
    assert.equal(r.outcome, "valid", `${vec.label} ${vec.key.kty}: ${r.reason}`);
    assert.equal(r.attribution, vec.signature_agent ? "url" : "thumbprint");
    assert.equal(r.testKey, true);
  }
});

test("Cloudflare's published directory response vector passes the Appendix B proof check", async () => {
  const [vec] = vectors("web_bot_auth_directory_response_v1.json");
  const v = new Verifier({
    now: () => 1735689600_000 + 10_000,
    fetcher: async (url) => ({ status: 200, headers: Object.fromEntries(Object.entries(vec.response.headers).map(([k, x]) => [k.toLowerCase(), x])), body: Buffer.from(vec.response.body), url }),
  });
  const dir = await v.directory(vec.request.target_url);
  assert.equal(dir.ok, true);
  assert.equal(dir.proof.signatures, 1);
  assert.equal(dir.proof.valid, 1, JSON.stringify(dir.proof.errors));
  assert.equal(dir.proof.digestOk, true);
});

test("tampered directory body fails the digest", async () => {
  const good = await signedDirectory(AGENT_JWK, AGENT_DIR);
  const tampered = JSON.parse(good.body.toString());
  tampered.keys[0].use = "enc";
  const v = new Verifier({ fetcher: async (url) => ({ ...good, body: Buffer.from(JSON.stringify(tampered)), url }) });
  const dir = await v.directory(AGENT_DIR);
  assert.equal(dir.proof.digestOk, false);
  assert.equal(dir.proof.valid, 0);
});

test("discovery URL rules", () => {
  assert.equal(discoveryUrl({ uri: "https://a.test", type: "directory" }).url, "https://a.test/.well-known/http-message-signatures-directory");
  assert.equal(discoveryUrl({ uri: "https://a.test/keys.json?x=1", type: "directory" }).url, "https://a.test/keys.json");
});

test("SSRF guard", async () => {
  for (const ip of ["10.0.0.1", "127.0.0.1", "169.254.169.254", "172.20.1.1", "192.168.1.1", "100.64.0.1", "::1", "fd00::1", "fe80::1", "::ffff:127.0.0.1"]) assert.equal(isPublicAddress(ip), false, ip);
  for (const ip of ["1.1.1.1", "8.8.8.8", "2606:4700::1111"]) assert.equal(isPublicAddress(ip), true, ip);
  await assert.rejects(safeGet("http://example.com/"), /https only/);
  await assert.rejects(safeGet("https://127.0.0.1/"), /non-public/);
  await assert.rejects(safeGet("https://example.com:8443/"), /port 443/);
  await assert.rejects(safeGet("https://localhost/"), (e) => e.kind === "refused");
});

test("User-Agent classification", () => {
  assert.equal(classify("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot").family, "ChatGPT-User");
  assert.equal(classify("Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)").family, "ClaudeBot");
  assert.equal(classify("Mozilla/5.0 (Macintosh) Chrome/131").family, "Browser");
  assert.equal(classify("curl/8.5.0").family, "HTTP library / script");
  assert.equal(classify(undefined).family, "No User-Agent");
});

test("IP prefix matching (v4, v6, mapped)", () => {
  const p = parsePrefixes({ prefixes: [{ ipv4Prefix: "216.73.216.0/22" }, { ipv6Prefix: "2600:1f28:365:8000::/56" }] });
  assert.equal(inPrefixes("216.73.219.4", p), true);
  assert.equal(inPrefixes("216.73.220.1", p), false);
  assert.equal(inPrefixes("::ffff:216.73.216.9", p), true);
  assert.equal(inPrefixes("2600:1f28:365:80ff::1", p), true);
  assert.equal(inPrefixes("2600:1f28:365:8100::1", p), false);
});

// --- whole app over HTTP --------------------------------------------------------------------------------------

async function startApp(opts = {}) {
  const store = new Store(join(mkdtempSync(join(tmpdir(), "obs-")), "db.sqlite"));
  const verifier = opts.verifier ?? (await verifierWithAgent());
  const ipLists = new IpLists({ fetcher: async () => ({ status: 200, headers: {}, body: Buffer.from(JSON.stringify({ creationTime: "t", prefixes: [{ ipv4Prefix: "127.0.0.0/8" }] })) }) });
  await ipLists.refresh();
  let clock = Date.now();
  const app = createApp({ store, verifier, ipLists, agentJwk: AGENT_JWK, now: () => clock });
  const server = http.createServer((q, s) => app(q, s));
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const port = server.address().port;
  const get = (path, headers = {}) =>
    new Promise((resolve, reject) => {
      http.get({ host: "127.0.0.1", port, path, headers: { host: OBS, "x-forwarded-proto": "https", ...headers } }, (res) => {
        let body = "";
        res.on("data", (c) => (body += c));
        res.on("end", () => resolve({ status: res.statusCode, headers: res.headers, body }));
      }).on("error", reject);
    });
  return { store, get, close: () => server.close(), tick: (ms) => (clock += ms) };
}

test("app: verdicts recorded, page and exports render, no IP stored", async () => {
  const a = await startApp();
  try {
    assert.equal((await a.get("/health")).status, 200);
    const ok = JSON.parse((await a.get("/api/check", { ...(await signedHeaders()), "user-agent": "Mozilla/5.0 (compatible; ChatGPT-User/1.0)" })).body);
    assert.equal(ok.verdict.outcome, "valid");
    assert.equal(ok.ipList, "match"); // fake list covers 127.0.0.0/8
    const bad = JSON.parse((await a.get("/api/check", { ...(await signedHeaders({ jwk: OTHER_JWK })), "user-agent": "captcharena-selftest" })).body);
    assert.equal(bad.verdict.outcome, "invalid");
    assert.equal((await a.get("/robots.txt", { "user-agent": "GPTBot/1.1" })).body.includes("Disallow: /trap/"), true);
    await a.get("/trap/x", { "user-agent": "GPTBot/1.1" });
    const home = await a.get("/");
    assert.equal(home.status, 200);
    assert.match(home.headers["content-security-policy"], /default-src 'none'/);
    assert.match(home.headers["accept-signature"], /web-bot-auth/);
    assert.doesNotMatch(home.body, /<script/i);
    assert.match(home.body, /ChatGPT-User/);
    const data = JSON.parse((await a.get("/data.json")).body);
    const gpt = data.families.find((f) => f.family === "GPTBot");
    assert.equal(gpt.trap_hits, 1);
    assert.equal(gpt.robots_fetches, 1);
    assert.equal(data.signers.find((s) => s.signer === "agent.test" && s.self_test === 0).valid, 1);
    assert.match((await a.get("/data.csv")).body, /^month,family/);
    const cols = a.store.db.prepare("PRAGMA table_info(observations)").all().map((c) => c.name);
    assert.equal(cols.some((c) => /ip$|addr/.test(c) && c !== "ip_check"), false);
  } finally {
    a.close();
  }
});

test("app: 429 pace check counts early returns and waiting", async () => {
  const a = await startApp();
  try {
    const ua = { "user-agent": "PerplexityBot/1.0" };
    const first = await a.get("/pace/", ua);
    assert.equal(first.status, 429);
    assert.equal(first.headers["retry-after"], "20");
    assert.equal((await a.get("/pace/", ua)).status, 429); // early
    a.tick(21_000);
    assert.equal((await a.get("/pace/", ua)).status, 200); // respected
    const fam = JSON.parse((await a.get("/data.json")).body).families.find((f) => f.family === "PerplexityBot");
    assert.equal(fam.pace_early, 1);
    assert.equal(fam.pace_respected, 1);
  } finally {
    a.close();
  }
});

test("app: own test-agent directory is served signed and verifies", async () => {
  const a = await startApp();
  try {
    const res = await a.get("/.well-known/http-message-signatures-directory");
    assert.equal(res.status, 200);
    assert.equal(res.headers["content-type"], "application/http-message-signatures-directory+json");
    const v = new Verifier({ fetcher: async (url) => ({ status: res.status, headers: res.headers, body: Buffer.from(res.body), url }) });
    const dir = await v.directory(`https://${OBS}/.well-known/http-message-signatures-directory`);
    assert.equal(dir.ok, true);
    assert.equal(dir.proof.valid, 1, JSON.stringify(dir.proof.errors));
    assert.equal(JSON.parse(res.body).keys[0].d, undefined); // private part never published
  } finally {
    a.close();
  }
});

test("published RFC 9421 test key is flagged", async () => {
  const testDir = "https://signature-agent.test/.well-known/http-message-signatures-directory";
  const v = new Verifier({ fetcher: fakeFetcher({ [testDir]: await signedDirectory(TEST_ED25519, testDir) }) });
  const r = await check(v, await signedHeaders({ jwk: TEST_ED25519, signatureAgent: `sig1="${testDir}"` }));
  assert.equal(r.outcome, "valid", r.reason);
  assert.equal(r.testKey, true);
});
