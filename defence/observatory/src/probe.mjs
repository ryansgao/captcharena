// Daily probe, run by the service itself (no outside timer): which agent operators publish a Web Bot Auth key
// directory, whether it is well-formed and signed (Appendix B), and which operators publish IP range lists.
// Also probes every Signature-Agent host seen in traffic, so a new signer is followed from the day it appears.
import { DIRECTORY_PATH, summarizeDirectory } from "./wba.mjs";

export const KNOWN_DIRECTORIES = [
  ["OpenAI (ChatGPT agent)", "chatgpt.com"],
  ["OpenAI", "openai.com"],
  ["Google (Google-Agent)", "agent.bot.goog"],
  ["Browserbase", "www.browserbase.com"],
  ["Anthropic (claude.ai)", "claude.ai"],
  ["Anthropic (claude.com)", "claude.com"],
  ["Anthropic (anthropic.com)", "www.anthropic.com"],
  ["Perplexity", "www.perplexity.ai"],
  ["Amazon", "www.amazon.com"],
  ["Manus", "manus.im"],
  ["browser-use", "browser-use.com"],
  ["Anchor Browser", "anchorbrowser.io"],
  ["Cloudflare Research demo agent", "http-message-signatures-example.research.cloudflare.com"],
];

export async function runProbe({ verifier, ipLists, store, extraHosts = [], now = Date.now }) {
  const ts = Math.floor(now() / 1000);
  const targets = new Map(KNOWN_DIRECTORIES.map(([label, host]) => [`https://${host}${DIRECTORY_PATH}`, label]));
  for (const host of extraHosts) {
    const url = `https://${host}${DIRECTORY_PATH}`;
    if (!targets.has(url)) targets.set(url, `Seen in traffic: ${host}`);
  }
  const results = [];
  for (const [url, label] of targets) {
    const dir = summarizeDirectory(await verifier.directory(url, { force: true }), "probe");
    const row = {
      ts, kind: "directory", target: url, label, status: dir.status, ok: dir.ok, keys: dir.keys, keyids: dir.keyids,
      contentType: dir.contentType, contentTypeOk: dir.contentTypeOk, proofSigs: dir.proof?.signatures ?? null,
      proofValid: dir.proof?.valid ?? null, digestOk: dir.proof?.digestOk ?? null, error: dir.error,
    };
    store.recordProbe(row);
    results.push(row);
  }
  for (const r of await ipLists.refresh()) {
    const row = { ts, kind: "iplist", target: r.url, label: r.key, ok: r.ok, keys: r.prefixes ?? null, error: r.error ?? null, extra: { creationTime: r.creationTime ?? null, keptPrevious: r.keptPrevious ?? false } };
    store.recordProbe(row);
    results.push(row);
  }
  return results;
}
