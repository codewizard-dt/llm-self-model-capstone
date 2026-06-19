#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src"
set -a
source "$ROOT/config/defaults"
if [[ -f "$HOME/.config/vexy-system2/local" ]]; then
  source "$HOME/.config/vexy-system2/local"
fi
set +a

if [[ -z "${VEXY_SERIAL_PORT:-}" ]]; then
  echo "Set VEXY_SERIAL_PORT in ~/.config/vexy-system2/local first." >&2
  exit 2
fi

python3 -m vexy_system2.bridge --mode serial --serial-port "$VEXY_SERIAL_PORT" &
bridge_pid=$!
trap 'kill "$bridge_pid" >/dev/null 2>&1 || true' EXIT
sleep 0.8
python3 -m vexy_system2.planner_demo --goal "serial ping"
