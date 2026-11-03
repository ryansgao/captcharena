# runner/ — the browser-score experiment's runner (build step 6; deep-2 §6.3)

Agent-facing. Loads the measurement page (`../measure/`, https://measure.captcharena.org) in one browser setup ("arm")
at a time, ticks what a person would tick, records the vendors' verdicts, and closes everything it opened. A user
systemd timer runs a batch every 30 minutes, all day. This is the warm-up stage of deep-2 §6.3 "Design" step 1: the
reCAPTCHA v3 key went real on 2026-11-03 06:04 UTC and Google warns its scores settle over ~7 days, so controls and
baseline run *now*, and the warm-up itself is data (does the score drift as the key and profiles age?).

| File | What |
|---|---|
| `run.py` | `batch` (what the timer runs), `one <arm> [--smoke]`, `arms`, `status`. uv script, Playwright 1.62 (Camoufox 0.5.9 pins Playwright < 1.63) |
| `analyze.py` | per-condition table with 95% intervals, from `/api/summary` plus the local log; `--since 2026-11-10` for post-warm-up only |
| `systemd/captcha-runner.{service,timer}` | the trigger; installed as symlinks in `~/.config/systemd/user/` |
| `state/` (git-ignored) | `runs.jsonl` (one line per load), `runner.log`, `queue.json` (block-randomised arm order), `profiles/` (aged profiles, each with a `.created` stamp), `bin/chrome-stable/` (Google's .deb extracted, no root), `runner-key` (600; same value as `MEASURE_RUNNER_KEY` on the box) |

## Arms (design x1; tag = `x1-` + one letter-digit per factor; levels in `../measure/app/main.py` FACTOR_LEVELS)

| Arm | Tag | Browser | Role |
|---|---|---|---|
| base | `x1-n0b0a2s2h0c0d0w1` | the shared automation browser (Debian Chromium 155, headed on display :1, aged profile signed in to the a project Google account), own tab via the tab broker on 9222, Playwright `connect_over_cdp` | baseline / drift control: every block of 7 contains it once |
| fresh | `x1-n0b0a2s0h0c0d0w0` | same binary and launch flags as the shared browser, brand-new profile per load, headed on the runner's own Xvfb `:37` | S0 |
| aged | `x1-n0b0a2s1h0c0d0w0` | same, persistent profile `state/profiles/aged-chromium` (created 2026-11-03; only ever visits this page; age in every log line) | S1, ageing in place |
| headless | `x1-n0b5a3s0h0c0d1w0` | stock `playwright.chromium.launch(headless=True)` (Playwright 1.62's headless shell 151), nothing changed | negative control |
| exit-syd | `x1-n1b0a2s1h0c0d0w0` | as aged (own profile `aged-chromium-syd`) through a commercial VPN's SOCKS5 exit (Sydney, M247), `TZ=Australia/Sydney`, WebRTC limited to the proxy | N1 vs aged |
| chrome | `x1-n0b1a2s1h0c0d0w0` | Google Chrome stable 156 (extracted .deb), own aged profile | B1 vs aged |
| camoufox | `x1-n0b2a3s1h0c0d0w0` | Camoufox 158 beta (Firefox), Playwright-launched, own aged profile, `os="linux"`, `geoip=True` | B2 (A3: Playwright launch) |

Every load, every arm: `?c=<tag>` → Cap box clicked at ~3 s → Turnstile box clicked only if it turned interactive →
v2 box ticked once Turnstile settled (≥ 5 s) → wait for every lane's `done_*` flag (≤ 90 s). A v2 picture challenge is
never solved by the runner: it is the outcome. In **base** the agents' CAPTCHA watcher sees the challenge and may solve
it by audio (`w1`); that is part of that arm, and `v2 tick-only pass` (no challenge shown) is the comparable number.
The runner's verify calls carry `X-Measure-Runner` (added by `page.route` on our own `/api/verify` only) so they count
against the runner pool and are logged `"source": "runner"`.

Schedule: timer at :05 and :35 (± 4 min), 2 loads per batch 150-240 s apart, arms in block-randomised order (each
block = all 7 arms once, shuffled), at most 100 loads per UTC day (the page's runner pool is 130 reCAPTCHA calls a
day). So each arm gets ~14 loads a day; 25 replicates per arm in under two days.

Kill switch: `touch runner/OFF` (or `$CAPTCHA_KILL_DIR/captcha-runner`). Logs:
`state/runner.log`, `journalctl --user -u captcha-runner`.

## Not done, and why (2026-11-03)

- **N2 home line, N3 cellular**: need the owner's yes and a device; plan.html recommends no for the home line. **N4 static
  ISP address**: paid (~$2-5/month). Only N1 (a second commercial VPN exit, already paid for) runs.
- **CloakBrowser (B3)**: not tried yet; Camoufox and Chrome stable cover the B factor for now.
- **A0 / A1** (no automation client during the load; raw CDP): need a launch-by-URL path and a header without
  `page.route`; stage 1 work.
- **H1** (dwell, scroll, curved pointer): stage 1 work; `<private v0 solver>` has the pointer primitives.
- **C1 / C2** (incoherent timezone, spoofed UA): stage 1 work.
- **Positive control** (the owner's MacBook Safari / iPhone loading `?c=human-mac` / `?c=human-iphone`): needs him, ~2 min
  now and then; those lines arrive as `source: public`.
- The negative control runs from the owner's own a commercial VPN exit, not "a cloud runner" (deep-2 §6.3 controls); a second
  negative control from the hosting box would need a browser there.
- Camoufox regenerates its fingerprint (screen, fonts, etc.) on every launch even with a persistent profile.
- Chromium arms run on Xvfb without a window manager (the shared browser runs maximised under openbox on Xvnc); both
  report "no webgl" and a 1440x900 screen.
