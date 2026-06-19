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
exec python3 -m vexy_system2.dashboard
