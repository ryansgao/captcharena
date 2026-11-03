// Signed-agent observatory (C4). Every request is checked for a Web Bot Auth signature and against the declared
// agent's published IP list; the verdict (never the IP) is stored; the home page shows the aggregates.
import http from "node:http";
import { createHash, createHmac, randomBytes } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { signerFromJWK } from "web-bot-auth/crypto";
import { createSignature, component } from "http-message-sig";
import { Verifier, DIRECTORY_PATH, DIRECTORY_MEDIA_TYPE } from "./wba.mjs";
import { classify, IpLists } from "./agents.mjs";
import { Store } from "./store.mjs";
import { runProbe } from "./probe.mjs";
import { renderPage } from "./page.mjs";

const WINDOW_DAYS = 30;
const PACE_SECONDS = 20;
const SELF_TEST_UA = /captcharena-selftest/i;
const ACCEPT_SIGNATURE = 'sig1=("@authority" "signature-agent";key="sig1");tag="web-bot-auth"';
const CSP = "default-src 'none'; style-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";
const ROBOTS = `# captcharena signed-agent observatory.
# /trap/ is forbidden to every agent: a visit there is counted as "entered forbidden path".
User-agent: *
Disallow: /trap/
`;

const here = fileURLToPath(new URL(".", import.meta.url));
const CSS = readFileSync(`${here}../static/style.css`);
const CSS_HREF = `/static/style.css?v=${createHash("sha256").update(CSS).digest("hex").slice(0, 10)}`;

export function pathClass(path) {
  if (path === "/") return "home";
  if (path === "/robots.txt") return "robots";
  if (path.startsWith("/trap")) return "trap";
  if (path.startsWith("/pace")) return "pace";
  if (path.startsWith("/api/")) return "api";
  if (path === DIRECTORY_PATH) return "directory";
  if (path.startsWith("/data.")) return "data";
  return "other";
}

/** The agent's own public directory, signed per Appendix B (one signature per key, @authority;req + content-digest). */
export async function directoryResponse(agentJwk, reqUrl, reqHeaders) {
  const { d, ...pub } = agentJwk;
  void d;
  const signer = await signerFromJWK(agentJwk);
  const body = Buffer.from(JSON.stringify({ keys: [{ ...pub, kid: signer.keyid, use: "sig" }] }));
  const digest = `sha-256=:${createHash("sha256").update(body).digest("base64")}:`;
  const headers = { "content-type": DIRECTORY_MEDIA_TYPE, "cache-control": "max-age=3600", "content-digest": digest };
  const created = Math.floor(Date.now() / 1000);
  const fields = await createSignature(
    {
      kind: "response",
      status: 200,
      fields: Object.entries(headers).map(([name, value]) => ({ name, value })),
      request: { kind: "request", method: "GET", targetUri: reqUrl, fields: [{ name: "host", value: reqHeaders.host ?? "" }] },
    },
    {
      label: "binding0",
      signer,
      components: [component("@authority", { req: true }), "content-digest"],
      parameters: { created, expires: created + 3600, keyid: signer.keyid, alg: signer.algorithm, tag: "http-message-signatures-directory" },
    },
  );
  return { body, headers: { ...headers, signature: fields.signature, "signature-input": fields.signatureInput } };
}

export function createApp({ store, verifier = new Verifier(), ipLists = new IpLists(), agentJwk = null, publicOrigin = null, verifyApi = false, now = () => Date.now() }) {
  const pace = new Map(); // client hash -> { until, expiresAt }
  let salt = { day: null, key: null };
  const clientHash = (ip) => {
    const day = new Date(now()).toISOString().slice(0, 10);
    if (salt.day !== day) salt = { day, key: randomBytes(32) }; // rotates daily, never stored
    return createHmac("sha256", salt.key).update(ip ?? "").digest("hex").slice(0, 32);
  };

  function paceVerdict(ip) {
    const t = now();
    for (const [k, v] of pace) if (v.expiresAt < t) pace.delete(k);
    if (pace.size > 20_000) pace.clear();
    const key = clientHash(ip);
    const entry = pace.get(key);
    if (!entry) {
      pace.set(key, { until: t + PACE_SECONDS * 1000, expiresAt: t + 600_000 });
      return { status: 429, pace: "asked" };
    }
    if (t < entry.until) return { status: 429, pace: "early" };
    pace.delete(key);
    return { status: 200, pace: "respected" };
  }

  function aggregates() {
    const since = Math.floor(now() / 1000) - WINDOW_DAYS * 86400;
    const directories = store.latestProbes("directory");
    const keySets = Object.fromEntries(directories.map((d) => [d.target, store.keySets(d.target, since)]));
    return {
      generatedAt: new Date(now()).toISOString(),
      windowDays: WINDOW_DAYS,
      totals: store.totals(since),
      directories,
      keySets,
      ipLists: store.latestProbes("iplist"),
      families: store.families(since),
      signers: store.signers(since),
      failures: store.failures(since),
    };
  }

  async function observe(req, url, path) {
    const ip = req.headers["cf-connecting-ip"] ?? req.socket.remoteAddress;
    const ua = req.headers["user-agent"];
    const selfTest = SELF_TEST_UA.test(ua ?? "");
    const who = selfTest ? { family: "Observatory self-test", operator: "captcharena", kind: "self-test", ipList: null, token: "captcharena-selftest" } : classify(ua);
    const wba = await verifier.verifyRequest({ method: req.method, url, headers: req.headers });
    const ipCheck = ipLists.check(who.ipList, ip);
    let saHost = null;
    try {
      saHost = wba.signatureAgent.uri ? new URL(wba.signatureAgent.uri).host : null;
    } catch {
      saHost = null;
    }
    return { ip, who, wba, ipCheck, saHost, selfTest, pathClass: pathClass(path), ua };
  }

  function record(o, extra = {}) {
    store.record({
      ts: Math.floor(now() / 1000),
      pathClass: o.pathClass,
      method: o.method,
      family: o.who.family,
      operator: o.who.operator,
      kind: o.who.kind,
      uaToken: o.who.token,
      uaSample: o.who.kind === "browser" || !o.ua ? null : String(o.ua).slice(0, 160),
      ipCheck: o.ipCheck,
      wba: o.wba,
      saHost: o.saHost,
      selfTest: o.selfTest,
      ...extra,
    });
  }

  return async function handler(req, res) {
    const send = (status, body, headers = {}) => {
      res.writeHead(status, {
        "content-security-policy": CSP,
        "x-content-type-options": "nosniff",
        "referrer-policy": "no-referrer",
        "accept-signature": ACCEPT_SIGNATURE,
        ...headers,
      });
      res.end(req.method === "HEAD" ? undefined : body);
    };
    let path;
    try {
      path = new URL(req.url, "http://x").pathname;
    } catch {
      return send(400, "bad request");
    }
    if (path === "/health") return store.writable() ? send(200, "ok", { "content-type": "text/plain" }) : send(503, "store not writable", { "content-type": "text/plain" });
    if (path === "/static/style.css") return send(200, CSS, { "content-type": "text/css", "cache-control": "public, max-age=31536000, immutable" });
    if (path === "/favicon.ico") return send(204, undefined);

    const proto = req.headers["x-forwarded-proto"] === "https" ? "https" : "http";
    const url = `${proto}://${req.headers.host ?? "localhost"}${req.url}`;

    if (verifyApi && path === "/api/verify-request" && req.method === "POST") {
      // Internal only (enabled in the Anubis gate's compose, off in the public deploy): verify a request on someone's behalf.
      const chunks = [];
      for await (const c of req) {
        chunks.push(c);
        if (chunks.reduce((a, b) => a + b.length, 0) > 65536) return send(413, "too large");
      }
      try {
        const body = JSON.parse(Buffer.concat(chunks).toString("utf8"));
        const verdict = await verifier.verifyRequest({ method: String(body.method), url: String(body.url), headers: body.headers ?? {} });
        return send(200, JSON.stringify(verdict), { "content-type": "application/json" });
      } catch (e) {
        return send(400, JSON.stringify({ error: e.message }), { "content-type": "application/json" });
      }
    }

    if (!["GET", "HEAD"].includes(req.method)) return send(405, "method not allowed", { allow: "GET, HEAD" });

    const o = await observe(req, url, path);
    o.method = req.method;

    if (path === "/robots.txt") {
      record(o);
      return send(200, ROBOTS, { "content-type": "text/plain; charset=utf-8" });
    }
    if (path === DIRECTORY_PATH) {
      record(o);
      if (!agentJwk) return send(404, "no test agent key configured", { "content-type": "text/plain" });
      const dir = await directoryResponse(agentJwk, url, req.headers);
      return send(200, dir.body, dir.headers);
    }
    if (path === "/api/check") {
      record(o);
      const out = {
        verdict: o.wba,
        declaredAgent: { family: o.who.family, operator: o.who.operator, kind: o.who.kind },
        ipList: o.ipCheck,
        note: "Outcomes: unsigned, valid, invalid, unverified (directory could not be fetched). The IP is compared and dropped, never stored.",
      };
      return send(200, JSON.stringify(out, null, 2), { "content-type": "application/json", "cache-control": "no-store" });
    }
    if (path.startsWith("/pace")) {
      const p = paceVerdict(o.ip);
      record(o, { pace: p.pace });
      if (p.status === 429) return send(429, `Too many requests. Retry after ${PACE_SECONDS} seconds.\n`, { "retry-after": String(PACE_SECONDS), "content-type": "text/plain", "cache-control": "no-store" });
      return send(200, "Thank you for waiting.\n", { "content-type": "text/plain", "cache-control": "no-store" });
    }
    if (path.startsWith("/trap")) {
      record(o);
      return send(200, "This path is forbidden by robots.txt. Your visit has been counted (no IP is stored).\n", { "content-type": "text/plain", "cache-control": "no-store" });
    }
    if (path === "/data.json") {
      record(o);
      return send(200, JSON.stringify(aggregates(), null, 1), { "content-type": "application/json", "cache-control": "public, max-age=300" });
    }
    if (path === "/data.csv") {
      record(o);
      const rows = store.monthly();
      const cols = ["month", "family", "operator", "kind", "self_test", "requests", "signed", "valid", "invalid", "unverified", "ip_match", "ip_mismatch", "robots_fetches", "trap_hits", "pace_early", "pace_respected"];
      const csv = [cols.join(","), ...rows.map((r) => cols.map((c) => `"${String(r[c] ?? "").replace(/"/g, '""')}"`).join(","))].join("\n");
      return send(200, csv + "\n", { "content-type": "text/csv; charset=utf-8", "cache-control": "public, max-age=300" });
    }
    if (path === "/") {
      record(o);
      const html = renderPage({ origin: publicOrigin ?? `${proto}://${req.headers.host}`, cssHref: CSS_HREF, ...aggregates() });
      return send(200, html, { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=60" });
    }
    record(o);
    return send(404, "not found\n", { "content-type": "text/plain" });
  };
}

// --- entry point -------------------------------------------------------------------------------------------------
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const store = new Store(process.env.OBSERVATORY_DB ?? "/data/observatory.sqlite");
  const verifier = new Verifier();
  const ipLists = new IpLists();
  const agentJwk = process.env.OBSERVATORY_AGENT_JWK_B64 ? JSON.parse(Buffer.from(process.env.OBSERVATORY_AGENT_JWK_B64, "base64").toString("utf8")) : null;
  const app = createApp({
    store, verifier, ipLists, agentJwk,
    publicOrigin: process.env.PUBLIC_ORIGIN ?? null,
    verifyApi: process.env.OBSERVATORY_VERIFY_API === "1",
  });
  const port = Number(process.env.PORT ?? 8000);
  http.createServer((req, res) => app(req, res).catch((e) => {
    console.error("request failed", e);
    if (!res.headersSent) res.writeHead(500);
    res.end();
  })).listen(port, "0.0.0.0", () => console.log(`observatory on :${port}`));

  // Daily probe, inside the service so it fires without any outside timer. First run a minute after start.
  const probe = async () => {
    try {
      const since = Math.floor(Date.now() / 1000) - WINDOW_DAYS * 86400;
      const seen = store.signers(since).map((s) => s.signer).filter((h) => h && !h.startsWith("("));
      const results = await runProbe({ verifier, ipLists, store, extraHosts: seen });
      store.prune(Math.floor(Date.now() / 1000) - 400 * 86400);
      console.log(`probe: ${results.filter((r) => r.ok).length}/${results.length} targets ok`);
    } catch (e) {
      console.error("probe failed", e);
    }
  };
  if (process.env.OBSERVATORY_PROBE !== "0") {
    setTimeout(probe, 60_000).unref();
    setInterval(probe, 24 * 3600_000).unref();
  }
}
