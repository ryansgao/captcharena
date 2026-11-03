// Web Bot Auth verification for one incoming request, on top of Cloudflare's reference library (`web-bot-auth`,
// `http-message-sig`, Apache-2.0). What this file adds is what the library leaves to the caller and the observatory
// needs to record: key discovery from Signature-Agent with an SSRF guard and a cache that obeys §6.10 of
// draft-ietf-webbotauth-httpsig-protocol-01 (a failed fetch never evicts a good entry), the directory's own
// signature check (Appendix B), nonce replay and static-signature reuse, the four outcomes of Appendix C.1
// (unsigned / valid / invalid / unverified) and a short reason category per failure.
import { createHash } from "node:crypto";
import { verify, parseSignatureAgentHeader, parseSignatureAgentCard } from "web-bot-auth";
import { verifierFromJWK } from "web-bot-auth/crypto";
import { verifySignature, component, isSignatureError } from "http-message-sig";
import { parseDictionary } from "structured-headers";
import { safeGet, FetchError } from "./net.mjs";

export const DIRECTORY_PATH = "/.well-known/http-message-signatures-directory";
export const DIRECTORY_MEDIA_TYPE = "application/http-message-signatures-directory+json";
const MAX_KEYS = 50;
const POSITIVE_TTL_MS = 10 * 60_000;
const NEGATIVE_TTL_MS = 2 * 60_000;
const STALE_LIMIT_MS = 24 * 3600_000;
const FETCHES_PER_MINUTE = 60;

// Published test keys (RFC 9421 Appendix B.1.4 Ed25519, B.1.2 RSA-PSS): §6.8 says verifiers SHOULD reject them.
// We verify them anyway, because test agents use them, and label the verdict.
export const KNOWN_TEST_KEYIDS = new Set([
  "poqkLGiymh_W0uP6PZFw-dvez3QJT5SolqXBCW38r0U", // RFC 9421 test-key-ed25519
  "oD0HwocPBSfpNy5W3bpJeyFGY_IQ_YpqxSjQ3Yd-CLA", // RFC 9421 test-key-rsa-pss
]);

class ResolveError extends Error {
  constructor(outcome, category, message) {
    super(message);
    this.outcome = outcome; // "invalid" | "unverified"
    this.category = category;
  }
}

function headerValue(headers, name) {
  const v = headers[name];
  if (v === undefined) return undefined;
  return Array.isArray(v) ? v.join(", ") : String(v);
}

function fieldsOf(headers) {
  const out = [];
  for (const [name, value] of Object.entries(headers)) {
    if (Array.isArray(value)) for (const v of value) out.push({ name, value: String(v) });
    else if (value !== undefined) out.push({ name, value: String(value) });
  }
  return out;
}

function sha256(buf) {
  return createHash("sha256").update(buf).digest();
}

/** Where a Signature-Agent member says the keys are. -01 resolves the member URL directly; the -00 form
 * (bare origin, type=directory) resolves origin + well-known path. Both are seen in the wild. */
export function discoveryUrl(entry) {
  const url = new URL(entry.uri);
  if (entry.type === "jwks_uri" || entry.type === "cimd") return { url: url.href, resolution: entry.type };
  if (url.pathname === "/" || url.pathname === "") {
    return { url: `${url.origin}${DIRECTORY_PATH}`, resolution: "origin-plus-well-known" };
  }
  url.search = "";
  return { url: url.href, resolution: "direct" };
}

export class Verifier {
  constructor({ fetcher = safeGet, now = () => Date.now() } = {}) {
    this.fetcher = fetcher;
    this.now = now;
    this.cache = new Map(); // url -> entry
    this.nonces = new Map(); // nonce -> expires (s)
    this.signatures = new Map(); // sha256(signature header) -> expires (s)
    this.fetchWindow = [];
  }

  fetchBudgetOk() {
    const t = this.now();
    this.fetchWindow = this.fetchWindow.filter((x) => t - x < 60_000);
    if (this.fetchWindow.length >= FETCHES_PER_MINUTE) return false;
    this.fetchWindow.push(t);
    return true;
  }

  /** Fetch (or reuse) a key directory. Returns a directory record; never throws. */
  async directory(url, { force = false } = {}) {
    const t = this.now();
    const cached = this.cache.get(url);
    if (!force && cached && t < cached.freshUntil) return { ...cached, fromCache: true };
    if (!this.fetchBudgetOk()) {
      return cached && t - cached.fetchedAt < STALE_LIMIT_MS && cached.ok
        ? { ...cached, fromCache: true, stale: true }
        : { url, ok: false, error: "fetch budget exhausted", errorKind: "budget", keys: [], fetchedAt: t };
    }
    let entry;
    try {
      const res = await this.fetcher(url, { accept: `${DIRECTORY_MEDIA_TYPE}, application/jwk-set+json, application/json` });
      const contentType = String(res.headers["content-type"] || "").split(";")[0].trim().toLowerCase();
      let json;
      let parseError = null;
      if (res.status === 200) {
        try {
          json = JSON.parse(res.body.toString("utf8"));
        } catch {
          parseError = "body is not JSON";
        }
      }
      entry = await this.buildEntry(url, { status: res.status, contentType, json, parseError }, res);
    } catch (e) {
      const kind = e instanceof FetchError ? e.kind : "connect";
      entry = { url, ok: false, error: e.message, errorKind: kind, keys: [], fetchedAt: t };
    }
    entry.fetchedAt = t;
    if (entry.ok || entry.evidence) {
      // A directory that resolved is evidence and replaces what we held (§6.10), even if it lacks the key.
      entry.freshUntil = t + (entry.ok ? POSITIVE_TTL_MS : NEGATIVE_TTL_MS);
      this.cache.set(url, entry);
      return entry;
    }
    // A failure is not evidence: keep serving a good cached entry for up to a day.
    if (cached && cached.ok && t - cached.fetchedAt < STALE_LIMIT_MS) {
      cached.freshUntil = t + NEGATIVE_TTL_MS;
      return { ...cached, fromCache: true, stale: true, lastError: entry.error };
    }
    entry.freshUntil = t + NEGATIVE_TTL_MS;
    this.cache.set(url, entry);
    return entry;
  }

  async buildEntry(url, { status, contentType, json, parseError }, res) {
    const entry = { url, status, contentType, contentTypeOk: contentType === DIRECTORY_MEDIA_TYPE, keys: [], ok: false };
    if (status !== 200) {
      entry.error = `HTTP ${status}`;
      entry.errorKind = "status";
      return entry;
    }
    if (parseError || !json || !Array.isArray(json.keys)) {
      entry.error = parseError ?? "not a JWK Set (no keys array)";
      entry.errorKind = "format";
      entry.evidence = true;
      return entry;
    }
    if (json.keys.length > MAX_KEYS) {
      entry.error = `more than ${MAX_KEYS} keys`;
      entry.errorKind = "format";
      entry.evidence = true;
      return entry;
    }
    for (const jwk of json.keys) {
      try {
        const verifier = await verifierFromJWK(jwk);
        const keyid = verifier.keyid;
        entry.keys.push({
          keyid,
          algorithm: verifier.algorithm,
          verifier,
          kidMatches: jwk.kid === undefined ? null : jwk.kid === keyid,
          nbf: jwk.nbf ?? null,
          exp: jwk.exp ?? null,
          testKey: KNOWN_TEST_KEYIDS.has(keyid),
        });
      } catch (e) {
        entry.skipped = (entry.skipped ?? 0) + 1;
      }
    }
    entry.evidence = true;
    entry.ok = entry.keys.length > 0;
    if (!entry.ok) {
      entry.error = "no usable Ed25519 or RSA-PSS key";
      entry.errorKind = "format";
    }
    if (res) entry.proof = await this.directoryProof(url, res, entry.keys);
    else entry.proof = { signatures: 0, valid: 0, digestOk: null };
    return entry;
  }

  /** Appendix B: one signature per key over @authority;req and content-digest, tag http-message-signatures-directory. */
  async directoryProof(url, res, keys) {
    const proof = { signatures: 0, valid: 0, digestOk: null, errors: [] };
    const digestHeader = headerValue(res.headers, "content-digest");
    if (digestHeader) {
      try {
        const d = parseDictionary(digestHeader).get("sha-256");
        proof.digestOk = d ? Buffer.from(d[0]).equals(sha256(res.body)) : false;
      } catch {
        proof.digestOk = false;
      }
    }
    const input = headerValue(res.headers, "signature-input");
    if (!input || !headerValue(res.headers, "signature")) return proof;
    let labels = [];
    try {
      labels = [...parseDictionary(input).keys()];
    } catch {
      proof.errors.push("unparseable Signature-Input");
      return proof;
    }
    proof.signatures = labels.length;
    const requestDescriptor = { kind: "request", method: "GET", targetUri: url, fields: [{ name: "host", value: new URL(url).host }] };
    const responseDescriptor = { kind: "response", status: res.status, fields: fieldsOf(res.headers), request: requestDescriptor };
    for (const label of labels) {
      try {
        await verifySignature(responseDescriptor, {
          label,
          policy: {
            algorithms: ["ed25519", "rsa-pss-sha512"],
            requiredComponents: [component("@authority", { req: true }), "content-digest"],
            requiredParameters: ["created", "expires", "keyid", "tag"],
            clockSkew: 60,
            now: Math.floor(this.now() / 1000),
          },
          resolveVerifier: (candidate) => {
            if (candidate.parameters.tag !== "http-message-signatures-directory") throw new Error("wrong tag");
            const key = keys.find((k) => k.keyid === candidate.parameters.keyid);
            if (!key) throw new Error("keyid not in directory");
            return key.verifier;
          },
        });
        if (proof.digestOk) proof.valid += 1;
        else proof.errors.push(`${label}: content-digest missing or wrong`);
      } catch (e) {
        proof.errors.push(`${label}: ${e.cause?.message ?? e.message}`);
      }
    }
    return proof;
  }

  cleanReplayMaps(nowS) {
    for (const map of [this.nonces, this.signatures]) {
      if (map.size < 50_000) continue;
      for (const [k, exp] of map) if (exp < nowS) map.delete(k);
      if (map.size > 100_000) map.clear();
    }
  }

  /**
   * Verify the Web Bot Auth signature on one request.
   * @param {{method: string, url: string, headers: Record<string, string|string[]>}} req  url must be absolute
   */
  async verifyRequest({ method, url, headers }) {
    const signature = headerValue(headers, "signature");
    const signatureInput = headerValue(headers, "signature-input");
    const saHeader = headerValue(headers, "signature-agent");
    const verdict = {
      outcome: "unsigned",
      category: null,
      reason: null,
      label: null,
      keyid: null,
      alg: null,
      tag: null,
      created: null,
      expires: null,
      lifetime: null,
      hasNonce: false,
      components: [],
      signatureCount: 0,
      signatureAgent: { form: saHeader === undefined ? "absent" : null, uri: null, type: null, memberParams: false },
      directory: null,
      attribution: null,
      testKey: false,
      reused: false,
    };
    if (saHeader !== undefined) {
      try {
        verdict.signatureAgent.form = saHeader.trim().startsWith('"') ? "legacy-string" : "dictionary";
        parseSignatureAgentHeader(saHeader);
      } catch {
        verdict.signatureAgent.form = "unparseable";
      }
    }
    if (signature === undefined && signatureInput === undefined) return verdict;

    // Pick the Web Bot Auth signature among possibly several labels.
    let params = null;
    try {
      const inputs = parseDictionary(signatureInput ?? "");
      verdict.signatureCount = inputs.size;
      for (const [label, [items, p]] of inputs) {
        if (verdict.label === null || p.get("tag") === "web-bot-auth") {
          verdict.label = label;
          params = p;
          verdict.components = Array.isArray(items)
            ? items.map(([name, cp]) => (cp.size ? `${name};${[...cp].map(([k, v]) => `${k}=${v}`).join(";")}` : name))
            : [];
          if (p.get("tag") === "web-bot-auth") break;
        }
      }
    } catch {
      return { ...verdict, outcome: "invalid", category: "malformed", reason: "Signature-Input is not a valid structured dictionary" };
    }
    if (params) {
      verdict.keyid = params.get("keyid") ?? null;
      verdict.alg = params.get("alg") ?? null;
      verdict.tag = params.get("tag") ?? null;
      verdict.created = params.get("created") ?? null;
      verdict.expires = params.get("expires") ?? null;
      verdict.hasNonce = params.has("nonce");
      if (typeof verdict.created === "number" && typeof verdict.expires === "number") verdict.lifetime = verdict.expires - verdict.created;
      verdict.testKey = KNOWN_TEST_KEYIDS.has(verdict.keyid);
    }

    const nowS = Math.floor(this.now() / 1000);
    this.cleanReplayMaps(nowS);
    const sigHash = signature ? sha256(Buffer.from(signature)).toString("hex") : null;
    if (sigHash && this.signatures.has(sigHash)) verdict.reused = true;

    const self = this;
    let resolveFailure = null;
    const request = { kind: "request", method, targetUri: url, fields: fieldsOf(headers) };
    try {
      const verified = await verify(request, {
        label: verdict.label ?? undefined,
        clockSkew: 60,
        maxAge: 86_400,
        now: new Date(this.now()),
        async resolver(candidate) {
          try {
            return await self.resolve(candidate, verdict);
          } catch (e) {
            resolveFailure = e;
            throw e;
          }
        },
        validate: ({ nonce, expires }) => {
          if (nonce === undefined) return true;
          if (self.nonces.has(nonce)) throw new ResolveError("invalid", "replayed-nonce", "nonce already used");
          self.nonces.set(nonce, Math.floor(expires.getTime() / 1000));
          return true;
        },
      });
      verdict.outcome = "valid";
      verdict.attribution = verdict.attribution ?? (verified.signatureAgent ? "url" : "thumbprint");
      if (sigHash) this.signatures.set(sigHash, verdict.expires ?? nowS + 86_400);
    } catch (e) {
      const inner = resolveFailure ?? (e.cause instanceof ResolveError ? e.cause : null) ?? (e instanceof ResolveError ? e : null);
      if (inner instanceof ResolveError) {
        verdict.outcome = inner.outcome;
        verdict.category = inner.category;
        verdict.reason = inner.message;
      } else {
        verdict.outcome = "invalid";
        verdict.reason = e.code === "ResolverFailed" && e.cause?.message ? e.cause.message : e.message;
        verdict.category = categorize(e);
      }
    }
    return verdict;
  }

  async resolve(candidate, verdict) {
    const entry = candidate.signatureAgent;
    if (!entry) {
      // §4.3: no URL to attribute to. Verify only with a key we already hold, attributed to its thumbprint.
      for (const dir of this.cache.values()) {
        const key = dir.keys?.find((k) => k.keyid === candidate.keyid);
        if (key) {
          verdict.attribution = "thumbprint";
          return key.verifier;
        }
      }
      throw new ResolveError("unverified", "no-signature-agent", "no Signature-Agent and the key is not one we hold");
    }
    verdict.signatureAgent.uri = entry.uri;
    verdict.signatureAgent.type = entry.type;
    let parsedUrl;
    try {
      parsedUrl = new URL(entry.uri);
    } catch {
      throw new ResolveError("invalid", "signature-agent-not-url", "Signature-Agent member is not a URL");
    }
    if (parsedUrl.protocol !== "https:") throw new ResolveError("invalid", "signature-agent-not-https", "Signature-Agent must be https (-01 §5.2.1)");
    let jwksUrl;
    let resolution;
    if (entry.type === "cimd") {
      const card = await this.fetchCard(entry.uri);
      if (card.jwks) {
        // Inline keys in a card: usable, attributed to the card URL.
        const dir = await this.buildEntry(entry.uri, { status: 200, contentType: "application/json", json: card.jwks }, null);
        verdict.directory = summarizeDirectory(dir, "card-inline");
        return pickKey(dir, candidate.keyid);
      }
      jwksUrl = card.jwks_uri;
      resolution = "card";
    } else {
      ({ url: jwksUrl, resolution } = discoveryUrl(entry));
    }
    const dir = await this.directory(jwksUrl);
    verdict.directory = summarizeDirectory(dir, resolution);
    if (!dir.ok) {
      if (dir.evidence) throw new ResolveError("invalid", "directory-unusable", `directory resolved but unusable: ${dir.error}`);
      throw new ResolveError("unverified", { status: "directory-http-error", refused: "directory-refused" }[dir.errorKind] ?? "directory-unreachable", `directory fetch failed: ${dir.error}`);
    }
    return pickKey(dir, candidate.keyid);
  }

  async fetchCard(uri) {
    if (!this.fetchBudgetOk()) throw new ResolveError("unverified", "directory-unreachable", "fetch budget exhausted");
    try {
      const res = await this.fetcher(uri, { accept: "application/json" });
      if (res.status !== 200) throw new ResolveError("unverified", "directory-http-error", `card HTTP ${res.status}`);
      return parseSignatureAgentCard(JSON.parse(res.body.toString("utf8")), uri);
    } catch (e) {
      if (e instanceof ResolveError) throw e;
      throw new ResolveError("unverified", "directory-unreachable", `card fetch failed: ${e.message}`);
    }
  }
}

function pickKey(dir, keyid) {
  const key = dir.keys.find((k) => k.keyid === keyid);
  if (!key) throw new ResolveError("invalid", "key-not-in-directory", "keyid is not in the Signature-Agent's directory");
  return key.verifier;
}

export function summarizeDirectory(dir, resolution) {
  return {
    url: dir.url,
    resolution,
    status: dir.status ?? null,
    contentType: dir.contentType ?? null,
    contentTypeOk: dir.contentTypeOk ?? null,
    keys: dir.keys?.length ?? 0,
    keyids: (dir.keys ?? []).map((k) => k.keyid),
    proof: dir.proof ? { signatures: dir.proof.signatures, valid: dir.proof.valid, digestOk: dir.proof.digestOk } : null,
    ok: Boolean(dir.ok),
    error: dir.error ?? null,
    fromCache: Boolean(dir.fromCache),
    stale: Boolean(dir.stale),
  };
}

export function categorize(e) {
  const msg = e?.message ?? "";
  if (!isSignatureError(e)) return "other";
  if (e.code === "ResolverFailed" && isSignatureError(e.cause)) return categorize(e.cause);
  switch (e.code) {
    case "VerificationFailed":
      return "bad-signature";
    case "MissingField":
      return /signature-agent|dictionary member/i.test(msg) ? "signature-agent-not-covered" : "missing-field";
    case "MalformedField":
    case "LabelMismatch":
    case "LabelRequired":
    case "DuplicateLabel":
      return "malformed";
    case "AlgorithmMismatch":
      return "algorithm";
    case "UnsupportedFeature":
    case "InvalidComponent":
    case "DuplicateComponent":
      return "unsupported-component";
    case "PolicyViolation":
      if (/expired/i.test(msg)) return "expired";
      if (/future/i.test(msg)) return "created-in-future";
      if (/too old/i.test(msg)) return "too-old";
      if (/tag/i.test(msg)) return "wrong-tag";
      if (/@authority|@target-uri/i.test(msg)) return "authority-not-covered";
      if (/signature-agent/i.test(msg)) return "signature-agent-not-covered";
      if (/Required parameter/i.test(msg)) return "missing-parameter";
      if (/nonce/i.test(msg)) return "bad-nonce";
      if (/algorithm/i.test(msg)) return "algorithm";
      return "policy";
    default:
      return "other";
  }
}

