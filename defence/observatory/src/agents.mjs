// The non-cryptographic identity schemes the observatory checks beside Web Bot Auth: the User-Agent product token
// an agent declares, and whether the connecting IP is in the range list its operator publishes (the JSON
// "prefixes" format OpenAI, Anthropic, Google, Perplexity, Apple, Microsoft and Common Crawl all use). URLs checked
// live 2026-11-03.
import net from "node:net";
import { safeGet } from "./net.mjs";

// [family, operator, kind, UA regex, IP-list key or null]. Order matters: first match wins.
export const AGENTS = [
  ["ChatGPT-User", "OpenAI", "ai-user-fetcher", /ChatGPT-User/i, "openai-chatgpt-user"],
  ["OAI-SearchBot", "OpenAI", "ai-search", /OAI-SearchBot/i, "openai-searchbot"],
  ["GPTBot", "OpenAI", "ai-crawler", /GPTBot/i, "openai-gptbot"],
  ["ChatGPT agent", "OpenAI", "ai-browser-agent", /ChatGPT[- ]Agent|OpenAI-Operator/i, null],
  ["Claude-User", "Anthropic", "ai-user-fetcher", /Claude-User/i, "anthropic"],
  ["Claude-SearchBot", "Anthropic", "ai-search", /Claude-SearchBot/i, "anthropic"],
  ["ClaudeBot", "Anthropic", "ai-crawler", /ClaudeBot|anthropic-ai/i, "anthropic"],
  ["Claude Code / Claude agent", "Anthropic", "ai-tool", /claude-code|Claude-Agent|claude-cli/i, null],
  ["Google-Agent", "Google", "ai-browser-agent", /Google-Agent/i, "google-user-agents"],
  ["Google user-triggered fetcher", "Google", "ai-user-fetcher", /Google-Read-Aloud|FeedFetcher-Google|Google-Site-Verification|Google-Extended|GoogleAgent-|Google-NotebookLM|Google-CWS/i, "google-user-fetchers"],
  ["Googlebot / Google crawler", "Google", "search", /Googlebot|GoogleOther|Google-InspectionTool|Storebot-Google|Google-CloudVertexBot|AdsBot-Google/i, "google-common"],
  ["Perplexity-User", "Perplexity", "ai-user-fetcher", /Perplexity-User/i, "perplexity-user"],
  ["PerplexityBot", "Perplexity", "ai-search", /PerplexityBot/i, "perplexity-bot"],
  ["Comet", "Perplexity", "ai-browser-agent", /Comet\//, null],
  ["Applebot", "Apple", "search", /Applebot/i, "applebot"],
  ["Bingbot", "Microsoft", "search", /bingbot|BingPreview|msnbot/i, "bingbot"],
  ["CCBot", "Common Crawl", "ai-crawler", /CCBot/i, "ccbot"],
  ["Amazonbot", "Amazon", "ai-crawler", /Amazonbot|Amzn-SearchBot|Amzn-User|NovaAct/i, null],
  ["Bytespider", "ByteDance", "ai-crawler", /Bytespider|TikTokSpider/i, null],
  ["Meta crawler / fetcher", "Meta", "ai-crawler", /meta-externalagent|meta-externalfetcher|meta-webindexer|FacebookBot|facebookexternalhit/i, null],
  ["MistralAI-User", "Mistral", "ai-user-fetcher", /MistralAI-User/i, null],
  ["DuckAssistBot", "DuckDuckGo", "ai-user-fetcher", /DuckAssistBot|DuckDuckBot/i, null],
  ["Manus", "Manus", "ai-browser-agent", /Manus/i, null],
  ["Browserbase", "Browserbase", "ai-browser-agent", /Browserbase/i, null],
  ["browser-use", "browser-use", "ai-browser-agent", /browser-use/i, null],
  ["Cohere", "Cohere", "ai-crawler", /cohere-ai|cohere-training/i, null],
  ["YouBot", "You.com", "ai-search", /YouBot/i, null],
  ["Diffbot", "Diffbot", "ai-crawler", /Diffbot/i, null],
  ["Other declared bot", null, "bot-other", /bot\b|crawler|spider|slurp|fetcher/i, null],
  ["HTTP library / script", null, "tool", /^(curl|Wget|python-requests|python-httpx|aiohttp|Go-http-client|node-fetch|undici|axios|okhttp|Java\/|libwww|Scrapy|HTTPie|PostmanRuntime|Deno|Bun)/i, null],
  ["Headless browser", null, "headless", /HeadlessChrome|PhantomJS|Playwright|Puppeteer/i, null],
  ["Browser", null, "browser", /^Mozilla\//, null],
];

export const IP_LISTS = {
  "openai-chatgpt-user": "https://openai.com/chatgpt-user.json",
  "openai-searchbot": "https://openai.com/searchbot.json",
  "openai-gptbot": "https://openai.com/gptbot.json",
  anthropic: "https://claude.com/crawling/bots.json",
  "google-user-agents": "https://developers.google.com/static/search/apis/ipranges/user-triggered-agents.json",
  "google-user-fetchers": "https://developers.google.com/static/crawling/ipranges/user-triggered-fetchers-google.json",
  "google-common": "https://developers.google.com/static/crawling/ipranges/common-crawlers.json",
  "perplexity-user": "https://www.perplexity.ai/perplexity-user.json",
  "perplexity-bot": "https://www.perplexity.ai/perplexitybot.json",
  applebot: "https://search.developer.apple.com/applebot.json",
  bingbot: "https://www.bing.com/toolbox/bingbot.json",
  ccbot: "https://index.commoncrawl.org/ccbot.json",
};

export function classify(userAgent) {
  const ua = userAgent ?? "";
  if (!ua) return { family: "No User-Agent", operator: null, kind: "none", ipList: null, token: null };
  for (const [family, operator, kind, re, ipList] of AGENTS) {
    const m = ua.match(re);
    if (m) return { family, operator, kind, ipList, token: kind === "browser" ? null : m[0] };
  }
  return { family: "Unrecognised", operator: null, kind: "other", ipList: null, token: null };
}

// --- IP prefix matching ------------------------------------------------------------------------------------------

function toBigInt(ip) {
  if (net.isIPv4(ip)) return { v: 4, n: ip.split(".").reduce((a, p) => (a << 8n) + BigInt(Number(p)), 0n) };
  if (!net.isIPv6(ip)) return null;
  let [head, tail] = ip.toLowerCase().split("::");
  let parts = head ? head.split(":") : [];
  let tparts = tail !== undefined && tail !== "" ? tail.split(":") : [];
  const v4tail = (tparts.length ? tparts : parts).at(-1)?.includes(".");
  const expand = (arr) =>
    arr.flatMap((p) => {
      if (p.includes(".")) {
        const n = p.split(".").map(Number);
        return [((n[0] << 8) | n[1]).toString(16), ((n[2] << 8) | n[3]).toString(16)];
      }
      return [p];
    });
  parts = expand(parts);
  tparts = expand(tparts);
  const fill = tail === undefined ? [] : Array(8 - parts.length - tparts.length).fill("0");
  const all = [...parts, ...fill, ...tparts];
  if (all.length !== 8) return null;
  void v4tail;
  return { v: 6, n: all.reduce((a, p) => (a << 16n) + BigInt(parseInt(p || "0", 16)), 0n) };
}

export function parsePrefixes(json) {
  const out = [];
  for (const p of json?.prefixes ?? []) {
    const cidr = p.ipv4Prefix ?? p.ipv6Prefix;
    if (typeof cidr !== "string") continue;
    const [addr, bitsStr] = cidr.split("/");
    const a = toBigInt(addr);
    if (!a) continue;
    const width = a.v === 4 ? 32 : 128;
    const bits = Number(bitsStr ?? width);
    const shift = BigInt(width - bits);
    out.push({ v: a.v, base: a.n >> shift, shift });
  }
  return out;
}

export function inPrefixes(ip, prefixes) {
  let clean = ip?.startsWith("::ffff:") && net.isIPv4(ip.slice(7)) ? ip.slice(7) : ip;
  const a = toBigInt(clean ?? "");
  if (!a) return false;
  return prefixes.some((p) => p.v === a.v && a.n >> p.shift === p.base);
}

export class IpLists {
  constructor({ fetcher = safeGet } = {}) {
    this.fetcher = fetcher;
    this.lists = new Map(); // key -> { url, prefixes, creationTime, fetchedAt, ok, error }
  }

  async refresh() {
    const results = [];
    for (const [key, url] of Object.entries(IP_LISTS)) {
      try {
        const res = await this.fetcher(url, { maxBytes: 2_000_000, timeoutMs: 15_000, accept: "application/json" });
        if (res.status !== 200) throw new Error(`HTTP ${res.status}`);
        const json = JSON.parse(res.body.toString("utf8"));
        const prefixes = parsePrefixes(json);
        this.lists.set(key, { url, prefixes, creationTime: json.creationTime ?? null, fetchedAt: Date.now(), ok: true });
        results.push({ key, url, ok: true, prefixes: prefixes.length, creationTime: json.creationTime ?? null });
      } catch (e) {
        const old = this.lists.get(key);
        if (!old?.ok) this.lists.set(key, { url, prefixes: [], ok: false, error: e.message, fetchedAt: Date.now() });
        results.push({ key, url, ok: false, error: e.message, keptPrevious: Boolean(old?.ok) });
      }
    }
    return results;
  }

  /** "match" | "mismatch" | "list-unavailable" | null (the declared agent has no published list) */
  check(listKey, ip) {
    if (!listKey) return null;
    const list = this.lists.get(listKey);
    if (!list?.ok) return "list-unavailable";
    return inPrefixes(ip, list.prefixes) ? "match" : "mismatch";
  }
}
