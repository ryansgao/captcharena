// Outbound fetches whose URL comes from a client (Signature-Agent) or from our probe list.
// SSRF guard per draft-ietf-webbotauth-httpsig-protocol-01 §6.7: https only, port 443, public addresses only
// (checked on the address the socket actually connects to, so DNS rebinding cannot slip past), no redirects,
// byte cap after decoding, wall-clock timeout. Node's https module; no dependency.
import https from "node:https";
import dns from "node:dns";
import net from "node:net";
import zlib from "node:zlib";

const BLOCKED_V4 = [
  ["0.0.0.0", 8], ["10.0.0.0", 8], ["100.64.0.0", 10], ["127.0.0.0", 8], ["169.254.0.0", 16],
  ["172.16.0.0", 12], ["192.0.0.0", 24], ["192.0.2.0", 24], ["192.168.0.0", 16], ["198.18.0.0", 15],
  ["198.51.100.0", 24], ["203.0.113.0", 24], ["224.0.0.0", 4], ["240.0.0.0", 4],
];

function v4ToInt(ip) {
  return ip.split(".").reduce((acc, part) => (acc << 8) + Number(part), 0) >>> 0;
}

export function isPublicAddress(ip) {
  if (net.isIPv4(ip)) {
    const n = v4ToInt(ip);
    return !BLOCKED_V4.some(([base, bits]) => {
      const mask = bits === 0 ? 0 : (~0 << (32 - bits)) >>> 0;
      return (n & mask) === (v4ToInt(base) & mask);
    });
  }
  if (net.isIPv6(ip)) {
    const lower = ip.toLowerCase();
    if (lower.startsWith("::ffff:")) return isPublicAddress(lower.slice(7));
    if (lower === "::" || lower === "::1") return false;
    // fc00::/7 unique local, fe80::/10 link local, ff00::/8 multicast, 2001:db8::/32 documentation, 64:ff9b::/96 NAT64
    if (/^f[cd]/.test(lower) || /^fe[89ab]/.test(lower) || lower.startsWith("ff")) return false;
    if (lower.startsWith("2001:db8") || lower.startsWith("64:ff9b:")) return false;
    return true;
  }
  return false;
}

function guardedLookup(hostname, options, callback) {
  dns.lookup(hostname, { ...options, all: true }, (err, addresses) => {
    if (err) return callback(err);
    const usable = addresses.filter((a) => isPublicAddress(a.address));
    if (usable.length === 0) {
      const e = new Error(`refused: ${hostname} resolves only to non-public addresses`);
      e.code = "ESSRF";
      return callback(e);
    }
    if (options.all) return callback(null, usable);
    callback(null, usable[0].address, usable[0].family);
  });
}

export class FetchError extends Error {
  constructor(kind, message) {
    super(message);
    this.kind = kind; // refused | dns | connect | timeout | too-large | status | decode
  }
}

/**
 * GET an https URL under the guard. Resolves {status, headers, body (Buffer), url}.
 * Rejects with FetchError. Non-200 statuses resolve (the caller decides); redirects are never followed.
 */
export function safeGet(rawUrl, { maxBytes = 65536, timeoutMs = 5000, accept = "*/*", userAgent } = {}) {
  return new Promise((resolve, reject) => {
    let url;
    try {
      url = new URL(rawUrl);
    } catch {
      return reject(new FetchError("refused", "not a URL"));
    }
    if (url.protocol !== "https:") return reject(new FetchError("refused", "https only"));
    if (url.port && url.port !== "443") return reject(new FetchError("refused", "port 443 only"));
    if (url.username || url.password) return reject(new FetchError("refused", "credentials in URL"));
    if (net.isIP(url.hostname.replace(/^\[|\]$/g, "")) && !isPublicAddress(url.hostname.replace(/^\[|\]$/g, ""))) {
      return reject(new FetchError("refused", "non-public address"));
    }
    const req = https.request(
      url,
      {
        method: "GET",
        lookup: guardedLookup,
        headers: {
          accept,
          "accept-encoding": "gzip, br",
          "user-agent": userAgent ?? "captcharena-observatory/1 (+https://observatory.captcharena.org/about)",
        },
        timeout: timeoutMs,
      },
      (res) => {
        const chunks = [];
        let size = 0;
        const enc = (res.headers["content-encoding"] || "").toLowerCase();
        let stream = res;
        if (enc === "gzip") stream = res.pipe(zlib.createGunzip());
        else if (enc === "br") stream = res.pipe(zlib.createBrotliDecompress());
        else if (enc && enc !== "identity") {
          res.destroy();
          return reject(new FetchError("decode", `unsupported content-encoding ${enc}`));
        }
        stream.on("data", (chunk) => {
          size += chunk.length;
          if (size > maxBytes) {
            req.destroy();
            reject(new FetchError("too-large", `response over ${maxBytes} bytes`));
          } else chunks.push(chunk);
        });
        stream.on("end", () =>
          resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks), url: url.href }),
        );
        stream.on("error", (e) => reject(new FetchError("decode", e.message)));
      },
    );
    const wall = setTimeout(() => {
      req.destroy();
      reject(new FetchError("timeout", `no full response in ${timeoutMs} ms`));
    }, timeoutMs);
    req.on("close", () => clearTimeout(wall));
    req.on("timeout", () => {
      req.destroy();
      reject(new FetchError("timeout", `idle over ${timeoutMs} ms`));
    });
    req.on("error", (e) => {
      if (e.code === "ESSRF") reject(new FetchError("refused", e.message));
      else if (e.code === "ENOTFOUND" || e.code === "EAI_AGAIN") reject(new FetchError("dns", e.message));
      else reject(new FetchError("connect", e.message));
    });
    req.end();
  });
}
