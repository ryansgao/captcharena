#!/usr/bin/env bash
# weekly.sh — one tick of the half-life clock (M10). Fired by the user systemd timer captcha-halflife.timer.
#   1. the clone suites are up (containers restart by themselves; this starts any that are stopped)
#   2. every solver re-runs the frozen sample (halflife/frozen-sample-v1.json) -> results/runs/<date>-weekly.jsonl
#   3. the open bot detectors re-check the browser solver v0 drives -> results/halflife/detector-runs.jsonl
#   4. compute.py recomputes the half-life table -> results/halflife/halflife.{json,md}
#   5. the results are committed in the captcha repo (pathspec bench/results only)
# Heartbeat: results/halflife/last-tick.json (start, end, exit codes) — what a liveness check reads.
set -uo pipefail
BENCH="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BENCH"
export PATH="$HOME/.local/bin:${CAPTCHA_EXTRA_PATH:+$CAPTCHA_EXTRA_PATH:}/usr/local/bin:/usr/bin:/bin"
export BENCH_DISPLAY="${BENCH_DISPLAY:-:87}"
DATE="$(date -u +%Y%m%d)"
KIND="weekly"; [ -n "${BENCH_LIMIT:-}" ] && KIND="proof"   # a shortened tick (timer proof) never counts on the clock
START="$(date -u +%FT%TZ)"
mkdir -p results/halflife results/runs
LOG="results/halflife/tick-$DATE.log"
{
  echo "tick $START"
  docker compose -f suites/compose.yml up -d
  .venv/bin/python harness/bench.py selftest; S=$?
  .venv/bin/python harness/bench.py run --solver random,v0,tiered --sample halflife/frozen-sample-v1.json \
      --run-id "$DATE-$KIND" ${BENCH_LIMIT:+--limit "$BENCH_LIMIT"}; R=$?
  .venv/bin/python detectors/run.py; D=$?
  .venv/bin/python halflife/compute.py; C=$?
  printf '{"start":"%s","end":"%s","selftest":%s,"run":%s,"detectors":%s,"compute":%s}\n' \
      "$START" "$(date -u +%FT%TZ)" "$S" "$R" "$D" "$C" > results/halflife/last-tick.json
  git -C "$BENCH/.." add bench/results && git -C "$BENCH/.." commit -q -m "bench: half-life tick $DATE (selftest $S, run $R, detectors $D, compute $C)" -- bench/results || true
  echo "done: selftest $S run $R detectors $D compute $C"
} >> "$LOG" 2>&1
