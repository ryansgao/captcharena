#!/usr/bin/env bash
# Daily step-4 measurement (captcha-solver-models.timer): bring the lab up, run `suite.sh models` once per UTC day
# (it spends most of OpenRouter's 50 free calls), take the lab down again. Kill switch: solver/OFF or
# $CAPTCHA_KILL_DIR/captcha-solver.
set -uo pipefail
cd "$(dirname "$0")"
[ -e OFF ] || { [ -n "${CAPTCHA_KILL_DIR:-}" ] && [ -e "$CAPTCHA_KILL_DIR/captcha-solver" ]; } && { echo "off (kill switch)"; exit 0; }
export PATH="$HOME/.local/bin:$PATH"
docker compose -f lab/compose.yml up -d >/dev/null 2>&1
uv run lab/server.py > runs/lab-server.log 2>&1 & LAB=$!
trap 'kill $LAB 2>/dev/null; docker compose -f lab/compose.yml down >/dev/null 2>&1' EXIT
for i in $(seq 1 30); do curl -fs -o /dev/null http://127.0.0.1:8411/ && break; sleep 2; done
./suite.sh models
echo "done $(date -u +%FT%TZ)" >> runs/daily-models.log
