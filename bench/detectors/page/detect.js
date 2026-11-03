// Bench detector page: open bot detectors (BotD 2.0.0, fpscanner 1.0.8; CreepJS runs on its own page) plus the
// two behaviour features of Choudhary et al., arXiv 2607.26935 v1, recorded from page load:
//   mouse_event_rate     = |mousemove| / T_session, Hz (their App. B.3; T_session here = page load -> read time)
//   teleport_click_ratio = fraction of clicks preceded within 100 ms by a mousemove jump of >100 px in <50 ms
//                          (their footnote 3, the definition their results use)
// The paper publishes no thresholds; the human reference is its own text: "Human interaction produces dense event
// streams (10-50 Hz)", humans' teleport ratio "cluster around 0.05", and "all 1,025 Playwright-driven agent
// sessions are at exactly 0". The flag rule applied by detectors/run.py is stated there, not here.
import { load as loadBotd } from './vendor/botd-2.0.0.esm.js';
import FingerprintScanner from './vendor/fpscanner-1.0.8.es.js';

const t0 = performance.now();
const moves = [];            // [t, x, y, isTrusted, coalescedCount]
const clicks = [];           // [t, x, y, isTrusted]
let raw = 0, untrusted = 0, zeroMovement = 0;
addEventListener('mousemove', (e) => {
  const c = e.getCoalescedEvents ? e.getCoalescedEvents().length : 0;
  moves.push([performance.now(), e.clientX, e.clientY, e.isTrusted, c]);
  if (!e.isTrusted) untrusted++;
  if (e.movementX === 0 && e.movementY === 0) zeroMovement++;
}, true);
addEventListener('pointerrawupdate', () => { raw++; }, true);
addEventListener('click', (e) => { clicks.push([performance.now(), e.clientX, e.clientY, e.isTrusted]); if (!e.isTrusted) untrusted++; }, true);

// a working slider, so a drag means something on the page
const knob = document.getElementById('knob');
let drag = null;
knob.addEventListener('mousedown', (e) => { drag = { x: e.clientX, left: knob.offsetLeft }; });
addEventListener('mouseup', () => { drag = null; });
addEventListener('mousemove', (e) => { if (drag) knob.style.left = Math.max(0, Math.min(376, drag.left + e.clientX - drag.x)) + 'px'; });

function behaviour() {
  const T = (performance.now() - t0) / 1000;
  let teleports = 0;
  for (const [tc] of clicks) {
    for (let i = 1; i < moves.length; i++) {
      const [t, x, y] = moves[i], [tp, xp, yp] = moves[i - 1];
      if (t > tc) break;
      if (tc - t <= 100 && Math.hypot(x - xp, y - yp) > 100 && t - tp < 50) { teleports++; break; }
    }
  }
  // also: rate while the pointer is actually travelling (moves within 250 ms of each other)
  let activeT = 0;
  for (let i = 1; i < moves.length; i++) { const d = moves[i][0] - moves[i - 1][0]; if (d < 250) activeT += d; }
  return {
    session_s: +T.toFixed(2), mousemove: moves.length, clicks: clicks.length,
    mouse_event_rate_hz: +(moves.length / T).toFixed(2),
    active_rate_hz: activeT ? +(moves.length / (activeT / 1000)).toFixed(1) : 0,
    teleport_click_ratio: clicks.length ? +(teleports / clicks.length).toFixed(3) : null,
    pointerrawupdate: raw, untrusted_events: untrusted,
    zero_movement_ratio: moves.length ? +(zeroMovement / moves.length).toFixed(3) : null,
    coalesced_mean: moves.length ? +(moves.reduce((s, m) => s + m[4], 0) / moves.length).toFixed(2) : null,
  };
}

const result = { botd: null, fpscanner: null };
const within = (p, ms, what) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error(what + ' timed out')), ms))]);
(async () => {
  try {
    const botd = await within(loadBotd(), 15000, 'botd load');
    result.botd = botd.detect();
  } catch (e) { result.botd = { error: String(e) }; }
  try {
    const fp = await within(new FingerprintScanner().collectFingerprint({ encrypt: false }), 45000, 'fpscanner');
    result.fpscanner = { fastBotDetection: fp.fastBotDetection, fastBotDetectionDetails: fp.fastBotDetectionDetails };
  } catch (e) { result.fpscanner = { error: String(e) }; }
  window.__benchReady = true;
  document.getElementById('out').textContent = JSON.stringify(result, null, 1);
})();
window.__benchResult = () => ({ ...result, behaviour: behaviour(), ua: navigator.userAgent, webdriver: navigator.webdriver });
