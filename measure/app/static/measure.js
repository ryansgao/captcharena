// Measurement page client. Loads each configured CAPTCHA, hands its token to /api/verify (which asks the vendor's
// own server), and shows the verdict that was recorded. No inline script anywhere, so the page runs under a
// strict Content-Security-Policy. Runner use: ?c=<condition> tags every line of a run with the condition.

const runId = Array.from(crypto.getRandomValues(new Uint8Array(6)), b => b.toString(16).padStart(2, "0")).join("");
const condition = (new URLSearchParams(location.search).get("c") || "").toLowerCase().replace(/[^a-z0-9_.-]/g, "").slice(0, 40);
const started = performance.now();
let signals = {};

const $ = id => document.getElementById(id);

function setVerdict(lane, text, cls) {
  const el = $("v-" + lane);
  el.textContent = text;
  el.className = "verdict" + (cls ? " " + cls : "");
}

function describe(r) {
  if (r.error) return [r.error, "fail"];
  const parts = [r.success ? "accepted by its server" : "rejected by its server"];
  if (typeof r.score === "number") parts.push("score " + r.score.toFixed(1));
  if (r.errors && r.errors.length) parts.push(r.errors.join(", "));
  if (r.key === "test") parts.push("(test key)");
  return [parts.join(" · "), r.success ? "pass" : "fail"];
}

async function verify(lane, token, extra = {}) {
  setVerdict(lane, "checking with its server…");
  try {
    const resp = await fetch("/api/verify", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ lane, token, run_id: runId, condition, client: { signals, ...extra } }),
    });
    const r = await resp.json();
    const [text, cls] = describe(r);
    setVerdict(lane, text + (extra.solve_ms ? ` · ${(extra.solve_ms / 1000).toFixed(1)} s` : ""), cls);
    document.body.dataset["done_" + lane] = r.success ? "pass" : "fail";   // for the runner
  } catch (e) {
    setVerdict(lane, "could not reach our server: " + e, "fail");
  }
}

function loadScript(src) {
  return new Promise((ok, bad) => {
    const s = document.createElement("script");
    s.src = src; s.async = true; s.onload = ok; s.onerror = () => bad(new Error("could not load " + src));
    document.head.appendChild(s);
  });
}

function off(lane, why) {
  $("lane-" + lane).classList.add("off");
  setVerdict(lane, why);
}

async function collectSignals() {
  const s = {
    webdriver: navigator.webdriver === true,
    languages: (navigator.languages || []).slice(0, 5).join(","),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    platform: navigator.userAgentData ? navigator.userAgentData.platform : navigator.platform,
    cores: navigator.hardwareConcurrency || null,
    memory_gb: navigator.deviceMemory || null,
    screen: `${screen.width}x${screen.height}@${devicePixelRatio}`,
    touch_points: navigator.maxTouchPoints || 0,
    plugins: navigator.plugins ? navigator.plugins.length : null,
    cookies_enabled: navigator.cookieEnabled,
  };
  try {
    const gl = document.createElement("canvas").getContext("webgl");
    const ext = gl && gl.getExtension("WEBGL_debug_renderer_info");
    s.webgl_renderer = ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : (gl ? "masked" : "no webgl");
  } catch (e) { s.webgl_renderer = "error"; }
  try {
    const botd = await (await import("/static/vendor/botd-2.0.0.esm.js")).load({ monitoring: false });
    const r = botd.detect();
    s.botd = r.bot ? "bot: " + (r.botKind || "unknown") : "not a bot";
  } catch (e) { s.botd = "error: " + e.message; }
  return s;
}

function showSignals() {
  const rows = Object.entries(signals).map(([k, v]) => `<tr><td>${k.replace(/_/g, " ")}</td><td></td></tr>`);
  $("signals").innerHTML = "<tbody>" + rows.join("") + "</tbody>";
  Object.values(signals).forEach((v, i) => { $("signals").rows[i].cells[1].textContent = String(v); });
}

function setupRecaptcha(cfg) {
  const v3 = cfg.recaptcha_v3, v2 = cfg.recaptcha_v2;
  if (!v3) off("recaptcha_v3", "not set up yet");
  if (!v2) off("recaptcha_v2", "not set up yet");
  if (!v3 && !v2) return;
  window.__onRecaptcha = () => {
    if (v2) {
      const t = performance.now();
      grecaptcha.render("w-recaptcha_v2", {
        sitekey: v2.site,
        callback: token => verify("recaptcha_v2", token, { solve_ms: Math.round(performance.now() - t) }),
        "expired-callback": () => setVerdict("recaptcha_v2", "token expired; tick again"),
      });
      setVerdict("recaptcha_v2", "tick the box");
    }
    if (v3) {
      $("w-recaptcha_v3").textContent = "runs by itself, nothing to click";
      grecaptcha.ready(() => {
        const t = performance.now();
        grecaptcha.execute(v3.site, { action: "measure" })
          .then(token => verify("recaptcha_v3", token, { solve_ms: Math.round(performance.now() - t) }));
      });
    }
  };
  const render = v3 ? encodeURIComponent(v3.site) : "explicit";
  loadScript(`https://www.google.com/recaptcha/api.js?render=${render}&onload=__onRecaptcha`)
    .catch(e => { if (v3) setVerdict("recaptcha_v3", e.message, "fail"); if (v2) setVerdict("recaptcha_v2", e.message, "fail"); });
}

function setupTurnstile(cfg) {
  const ts = cfg.turnstile;
  if (!ts) return off("turnstile", "not set up yet");
  let interactive = false;
  window.__onTurnstile = () => {
    const t = performance.now();
    turnstile.render("#w-turnstile", {
      sitekey: ts.site, action: "measure",
      "before-interactive-callback": () => { interactive = true; },
      callback: token => verify("turnstile", token, { solve_ms: Math.round(performance.now() - t), interactive }),
      "error-callback": code => { setVerdict("turnstile", "widget error " + code, "fail"); return true; },
    });
  };
  loadScript("https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=__onTurnstile")
    .catch(e => setVerdict("turnstile", e.message, "fail"));
}

async function setupAltcha(cfg) {
  if (!cfg.altcha) return off("altcha", "not set up yet");
  await import("/static/vendor/altcha-3.5.0.min.js");
  const w = document.createElement("altcha-widget");
  w.setAttribute("challenge", cfg.altcha.challenge);
  w.setAttribute("auto", "onload");
  const t = performance.now();
  let sent = false;
  const done = payload => {
    if (sent || !payload) return;
    sent = true;
    verify("altcha", payload, { solve_ms: Math.round(performance.now() - t) });
  };
  w.addEventListener("verified", e => done(e.detail && e.detail.payload));
  w.addEventListener("statechange", e => {
    if (e.detail && e.detail.state === "verified") done(e.detail.payload);
    if (e.detail && e.detail.state === "error") setVerdict("altcha", "widget error", "fail");
  });
  $("w-altcha").appendChild(w);
  setVerdict("altcha", "working…");
}

async function setupCap(cfg) {
  if (!cfg.cap) return off("cap", "not set up yet");
  // Our own copies of the proof-of-work WASM; the widget would otherwise fetch them from jsDelivr (CSP blocks it).
  window.CAP_CUSTOM_WASM_URL = "/static/vendor/cap-wasm-0.0.8.wasm";
  window.CAP_CUSTOM_HASHWX_URL = "/static/vendor/cap-hashwx-0.0.8.wasm";
  try { await loadScript("/static/vendor/cap-widget-0.1.58.min.js"); }
  catch (e) { return setVerdict("cap", e.message, "fail"); }
  const w = document.createElement("cap-widget");
  w.setAttribute("data-cap-api-endpoint", cfg.cap.endpoint);
  let t = performance.now();
  let sent = false;
  w.addEventListener("progress", () => { if (!sent) setVerdict("cap", "working…"); }, { once: true });
  w.addEventListener("solve", e => {
    if (sent || !e.detail || !e.detail.token) return;
    sent = true;
    verify("cap", e.detail.token, { solve_ms: Math.round(performance.now() - t) });
  });
  w.addEventListener("error", e => setVerdict("cap", "widget error " + ((e.detail && e.detail.message) || ""), "fail"));
  w.addEventListener("click", () => { t = performance.now(); }, { capture: true });
  $("w-cap").appendChild(w);
  setVerdict("cap", "click the box");
}

async function main() {
  $("ver").textContent = `run ${runId}${condition ? " · condition " + condition : ""}`;
  let cfg = {};
  try {
    const c = await (await fetch("/api/config")).json();
    cfg = c.lanes || {};
    $("ver").textContent += ` · page version ${c.version}`;
  } catch (e) { /* every lane shows "not set up" */ }
  if (Object.values(cfg).some(l => l.key === "test")) $("testmode").hidden = false;
  signals = await collectSignals();
  signals.page_load_ms = Math.round(performance.now() - started);
  showSignals();
  setupRecaptcha(cfg);
  setupTurnstile(cfg);
  setupAltcha(cfg).catch(e => setVerdict("altcha", "could not load: " + e.message, "fail"));
  setupCap(cfg);
}

main();
