# bench/ — the clone benchmark harness (build step 7) and the half-life clock (build step 4, M10)

Agent-facing. Built 2026-11-03/04. Plan of record: `../research/plan.html` (test set 2; build steps 4 and 7; M10).

## Results, first measured run (frozen sample v1, run `20261103-baseline`)

Frozen sample v1: 289 tasks (3 per type, 97 types), every solver on the same tasks, scored by each suite's own
checker. Replica browser, offline. Cost $0 throughout (no model calls were made by v0 or random; the tiered solver
reported none). Rows: `results/runs/20261103-baseline.jsonl`.

| Suite | random baseline | v0 (captcha.py automatic ladder) | tiered (projects/captcha/solver) |
|---|---|---|---|
| Halligan | 4/75 (5.3%) | 0/75 | 2/75 (2.7%): both `botdetect` (distorted text) |
| HLL | 7/75 (9.3%), 6 of them the two any-click control types | 0/75 | 0/75 |
| NextGen | 0/79 (78 no submit: no submit control found) | 0/79 | 0/79 |
| OCW | 9/60 (15.0%) | 0/60 | 0/60 |

- **v0 = 0/289, every row `exit4:none`**: its ladder recognises CAPTCHAs only by the vendor's frame address
  (google/recaptcha, hcaptcha, challenges.cloudflare.com, arkose, geetest). A clone served from 127.0.0.1 is
  never recognised, so v0 never acts. Its real second rung is the calling agent looking (a Claude model), which
  the bench does not run. Expected, now measured.
- **random passes are chance level** on types with large click targets: OCW Hold_Button 2/3, Misleading_Click
  2/3, Object_Match 2/3, Image_Matching/Path_Finder/Pick_Area 1/3; Halligan multichoice counting, dice_pair,
  galaxies, orbit_match_game 1/3 each; HLL missing_piece_dynamic 1/3. HLL click_anywhere and click_trace pass
  3/3: the end-to-end path (browser → page → checker → tap → row) works.
- **tiered** became available mid-run (its README appeared) and ran all 289 in its own browser: it engaged on few
  pages (283 no-submit). Its rows carry version `9b8545a` (the captcha repo head, a stamping bug fixed after the
  run; the solver folder's own last commit is `dcd924a`).
- Half-life (`results/halflife/halflife.md`): nothing reaches "half broken" yet — any solver breaks 8 of 100
  defences (97 clone types + 3 detectors with a reading). One run cannot give a trend; the clock adds a point
  every Monday.

## What runs

| Suite | Pinned commit | Licence | Types run (excluded) | Tasks | How a task is picked |
|---|---|---|---|---|---|
| Open CaptchaWorld (`ocw`) | 66c0a3b (2026-02-19) | MIT by README only, no LICENSE file: local evaluation only | 20 | 463 | exact puzzle id (our 3-line patch) |
| NextGen-CAPTCHAs (`nextgen`) | 3961f1b (2026-10-23) | MIT | 27 | 540 | `?type&puzzle_index&seed=0` (suite's own) |
| Halligan benchmark (`halligan`) | 31cba3b (2026-09-07) | MIT | 25 (hCaptcha dropped) | 2,500 | route `/<type>/<id>` |
| HLL (`hll`) | cbd7717 (2026-05-19) | MIT | 25 (real-hCaptcha type dropped) | fresh instance per load | type only (no task ids) |

All four run on the owner's machine in Docker (`suites/compose.yml`, every port on 127.0.0.1, `cap_drop: ALL`, 2 GB cap each).
Not on the hosting server: the owner's machine has 12 CPU / 58 GB and the clones must never be public; the hosting server (2 CPU, Arm)
gains nothing. 97 types, 4,004 frozen tasks plus HLL's generators.

## How it works

- **`suites/build.py`** clones each suite at its pinned commit (`suites/_src/`, gitignored, never run on the host),
  fetches Git LFS puzzles over the LFS batch API with sha256 checks (`suites/lfs_fetch.py`; OCW and NextGen keep
  every puzzle in LFS), copies the server part into `suites/_build/`, then:
  - **debrand**: every vendor URL becomes `about:blank` (39 in Halligan: gstatic logos, "privacy/terms" links, a
    Baidu image), vendor names in visible text and alt/title/aria-label become "Puzzle", "powered by" is removed,
    links to vendors and anything classed logo/brand are hidden by an injected style. Checked in the browser, not
    assumed: `harness/bench.py debrand-check` loads every type and searches all visible text of all frames for 29
    vendor names — **97/97 types clean** (`results/debrand-check.json`), plus contact sheets viewed by eye. One
    residue: a GeeTest-slide challenge image has the word "GEETEST" drawn into the picture; images are left as
    shipped, which is why the Halligan lane stays local.
  - **patches** (asserted, fail the build if the anchor moves): OCW and NextGen `/api/get_ground_truth` (an open
    answer endpoint) closed; OCW honours `puzzle_id`; HLL started per type with its own demo script's configs,
    debug answers off; three.js r128 (NextGen 3D types) served locally, sha256-pinned.
  - **verdict tap**: each server records every final checker reply (verdict only, never the answer) at
    `/bench/verdicts`. Every solver is scored from this server-side record, whichever browser it uses.
- **`harness/bench.py`** — `list`, `selftest` (each checker says yes to a right answer and no to a wrong one; 13/13
  pass), `debrand-check`, `run`, `report`. One JSONL row per attempt in `results/runs/<run id>.jsonl`: suite,
  suite commit, type, task id, solver + version, rig, pass, verdict (`pass`/`fail`/`no-submit`/`skipped`), time,
  cost, step, note. Answer endpoints are also blocked in the browser. A watchdog closes a tab whose raw input call
  hangs (seen on HLL form posts). Re-running a run id resumes it.
- **`harness/browser.py`** — the bench's own browser, never the agents' one: the **replica** is `/usr/bin/chromium`
  headed on a private Xvfb screen with the exact flags of `ops/browser-cdp-launch.sh`, a throwaway profile, CDP on
  127.0.0.1, and every DNS name except localhost unresolvable (`--host-resolver-rules`). Not copied: the agent
  accounts' profile and the tab-groups extension.
- **Solver adapters (`harness/solvers.py`)**
  - `random` — clicks, drags and keys on whatever looks interactive, then a submit-like click; seeded by task key.
  - `v0` — `<private v0 solver>` unmodified, through `harness/v0_shim.py`, which only repoints its CDP
    address and its event log at the bench. Its automatic ladder only.
  - `tiered` — `projects/captcha/solver/solve.py solve --url <task>` in its own browser (its own profile is part
    of its trust step); scored from the verdict tap. Skipped (logged as `skipped`, never as a fail) until
    `solver/README.md` exists.

## Half-life clock (M10)

- **Frozen sample**: `halflife/frozen-sample-v1.json` — 3 tasks per type, seed 0, 289 tasks, never edited (a new
  sample is a new file). HLL rows are fresh instances from the pinned generator.
- **Weekly tick**: user systemd timer `captcha-halflife.timer` (Mondays 04:30 UTC, Persistent, ±10 min) →
  `captcha-halflife.service` → `halflife/weekly.sh`: suites up, selftest, every solver on the frozen sample
  (`results/runs/<date>-weekly.jsonl`), the detector run, `halflife/compute.py`, commit of `bench/results`
  (pathspec), heartbeat `results/halflife/last-tick.json`. Unit copies: `halflife/systemd/`.
- **Seen firing on its own**: a temporary drop-in set the calendar to 12:39:00 UTC 2026-11-03; the journal shows
  `Starting captcha-halflife.service` at 12:39:00 and `Finished` at 12:41:11 (shortened tick, `BENCH_LIMIT=2`,
  hll only, run id `-proof` so it never counts); every step exit 0; it committed `9b8545a` itself. Drop-ins
  removed; next tick Mon 2026-11-09.
- **Definitions** (`halflife/compute.py`): a defence is one clone type or one detector; *broken* = pass rate ≥ 0.5
  on the frozen sample (detectors: not flagged); *time since first broken* counts from the first such run;
  *survival* = first broken − the defence's public date (suite paper date, detector release date), right-censored
  while standing; *half-life* = Kaplan–Meier median survival over defences, per solver and for "any solver".
  Output: `results/halflife/halflife.{json,md}`.

## Data point 1: does a 2026 bot detector catch the browser our solver drives?

`detectors/run.py` serves `detectors/page/` (BotD 2.0.0 and fpscanner 1.0.8 vendored, MIT, with licences; CreepJS
built page at 10aa672) and the two features of Choudhary et al., arXiv 2607.26935, re-implemented from the paper's
definitions (its code is not released). The v0 rig clicks three buttons and drags a slider through captcha.py's
own `click`/`drag` commands, 3 s apart (the look-and-decide pause of the web-captcha skill). Controls: the same
Chromium launched by Playwright, headless and headed, with Playwright's own mouse.

| Detector (what it checks) | replica + v0 (our solver's browser) | Playwright headless | Playwright headed |
|---|---|---|---|
| BotD 2.0.0 | not flagged | **flagged** `headless_chrome` | **flagged** `headless_chrome` |
| fpscanner 1.0.8 fastBotDetection | no reading: `collectFingerprint` never resolved (45 s cap) | **flagged**: hasWebdriver, hasCDP | **flagged**: hasWebdriver, hasCDP |
| CreepJS (headless / stealth rating) | not flagged: 0% / 0% (like-headless 44%) | **flagged**: 100% (webDriverIsOn, hasHeadlessUA) | **flagged**: 33% (webDriverIsOn) |
| Behaviour, arXiv 2607.26935 | **flagged**: 3.2 Hz mouse-event rate over the session | **flagged**: 1.1 Hz | **flagged**: 1.1 Hz |

- **Answer: yes, caught, but only by behaviour.** The fingerprint detectors pass the replica (no webdriver flag,
  real headed Chromium), while they catch both Playwright launches. The 2026 behaviour feature catches it: while
  the pointer moves, v0's hand-like paths produce 40–45 Hz (human range 10–50 Hz per the paper), but the cursor
  sits still during the 3 s look-and-decide pauses, so the session rate is 3.2 Hz, under the paper's human range.
  Teleport-click ratio is 0 for every rig (v0 travels; Playwright emits no raw jumps, as the paper also found),
  so it does not separate them here.
- The flag rules are ours (the paper publishes no thresholds): behaviour flagged if rate < 10 Hz or teleport ratio
  > 0.2; CreepJS if headless or stealth rating > 0. Readings: `results/detectors/2026-11-04.json`; rows with
  dates: `results/halflife/detector-runs.jsonl` (two measurements so far: the first run and the proof tick).
- A home-grown copy of fpscanner's CDP check (the console stack-getter probe) fired on no rig, not even the
  controls fpscanner itself flags, so it was removed rather than reported.

## Could not run / gaps

- **hCaptcha clones** (Halligan `hcaptcha`, HLL `hcaptcha`): excluded by rule, never run.
- **fpscanner in the headed replica**: never returns; the rig's most interesting fingerprint reading is missing.
- **HLL task ids**: the suite generates a fresh instance per load; its "frozen" rows are frozen per type only.
- **NextGen with random**: no submit control matched, so random never submitted there (78/79); chance level
  there is unmeasured, not zero.
- **Not run**: MCA-Bench (predicts answers, no live interaction), CaptchaArena (data gated, non-commercial),
  Muse CAPTCHA Gym (not in the plan's four; next candidate), hosted detectors (rebrowser-bot-detector has no
  licence: visit only, not copied), the real-widget lane (test set 1 lives in `measure/`).
- **Images**: Halligan challenge images are replicas of vendor images (one shows a GEETEST wordmark); the lane is
  local only and must not be served by the hub as is.

## Next

1. Register the timer in the owner's private automation registry (`the private automation registry`): `captcha-halflife.timer`
   (user unit, Mondays 04:30 UTC) → `bench/halflife/weekly.sh`; heartbeat `bench/results/halflife/last-tick.json`.
   Plus a liveness check on that heartbeat (stale > 8 days = fail) in the nightly verifier.
2. A v0 with eyes: run the web-captcha second rung through the free vision chain (the tiered solver's step 4) and
   measure it here; v0's automatic ladder alone will stay at 0 on clones.
3. Behaviour lane: repeat the detector run with think time 0, 1, 3, 10 s and with an OS-level input driver
   (xdotool on the private screen), the gap arXiv 2607.26935 names as untested.
4. Muse CAPTCHA Gym as a fifth suite; fresh NextGen instances from its generator each cycle.
5. Tiered solver: emit `step` and `cost_usd` per challenge so the table can say which ladder step answered.
