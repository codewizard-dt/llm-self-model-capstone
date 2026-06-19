#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src"
export VEXY_STATE_DIR="${VEXY_STATE_DIR:-/tmp/vexy-system2}"
export VEXY_BRIDGE_PORT="${VEXY_BRIDGE_PORT:-18765}"
mkdir -p "$VEXY_STATE_DIR"

python3 -m vexy_system2.bridge --mode sim --state-dir "$VEXY_STATE_DIR" --port "$VEXY_BRIDGE_PORT" >"$VEXY_STATE_DIR/bridge-smoke.log" 2>&1 &
bridge_pid=$!
trap 'kill "$bridge_pid" >/dev/null 2>&1 || true' EXIT

sleep 0.5
python3 -m vexy_system2.planner_demo --goal "smoke test simulated bridge" --port "$VEXY_BRIDGE_PORT"
test -s "$VEXY_STATE_DIR/bridge.json"
echo "smoke test ok"
