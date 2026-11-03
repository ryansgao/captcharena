#!/usr/bin/env bash
# suite.sh — the solver's measurement runs, as run for the README. Needs the lab up (README "Run").
#   suite.sh local     steps 0-3 only, no model calls: learning curves on the lab + the measurement page ladder
#   suite.sh models    step 4 (and forced step 5) on every kind; spends ~30-40 free-API calls, which is most of
#                      OpenRouter's 50-a-day free allowance: run once per UTC day
set -euo pipefail
cd "$(dirname "$0")"
LAB=http://127.0.0.1:8411
case "${1:-local}" in
  local)
    for t in go-slide go-drag go-rotate; do
      uv run solve.py bench --url "$LAB/?t=$t" --n 10 --fresh --max-step 3 --series "curve-$t" --pause 0.5
    done
    uv run solve.py bench --url "$LAB/?t=text" --n 12 --fresh --max-step 3 --series curve-text-local --pause 0.5
    uv run solve.py bench --url "https://measure.captcharena.org/?c=solver-1" --n 5 --max-step 3 --series measure-ladder --pause 3
    ;;
  models)
    D=$(date -u +%Y%m%d)
    uv run solve.py bench --url "$LAB/?t=text" --n 6 --steps 4 --series "s4-text-$D"
    for t in go-click-en go-click-shape go-slide go-drag go-rotate; do
      uv run solve.py bench --url "$LAB/?t=$t" --n 2 --steps 4 --series "s4-$t-$D"
    done
    uv run solve.py bench --url "https://measure.captcharena.org/?c=solver-4" --n 2 --steps 4 --kinds recaptcha-v2 --series "s4-recaptcha-$D"
    uv run solve.py bench --url "$LAB/?t=go-click-shape" --n 1 --steps 5 --series "s5-click-$D"
    uv run solve.py bench --url "$LAB/?t=text" --n 8 --fresh --series "curve-text-full-$D"
    ;;
esac
