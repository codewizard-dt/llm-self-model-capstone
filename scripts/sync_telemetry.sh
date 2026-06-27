#!/usr/bin/env bash
# Sync the newest operator telemetry runs from the RPi to a local directory.
#
# Usage:
#   ./scripts/sync_telemetry.sh [local_dest]
#
# Reads VEXY_HOST, VEXY_SSH_USER, VEXY_SSH_PW from .env at the repo root.
# Any of these can also be overridden as environment variables before calling.
#
# Example — override host at call time:
#   VEXY_HOST=10.10.3.5 ./scripts/sync_telemetry.sh ./telemetry
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  source "$REPO_ROOT/.env"
  set +a
fi

REMOTE_HOST="${VEXY_HOST:?VEXY_HOST must be set in .env or environment}"
REMOTE_USER="${VEXY_SSH_USER:?VEXY_SSH_USER must be set in .env or environment}"
REMOTE_PW="${VEXY_SSH_PW:?VEXY_SSH_PW must be set in .env or environment}"
REMOTE_DIR="/home/vexy/telemetry"
LOCAL_DIR="${1:-./telemetry}"
MAX_LOCAL_RUNS="${MAX_LOCAL_RUNS:-10}"
SYNC_MEDIA="${SYNC_MEDIA:-0}"

if ! command -v sshpass &>/dev/null; then
  echo "ERROR: sshpass is required. Install with: brew install sshpass" >&2
  exit 1
fi

mkdir -p "$LOCAL_DIR"

echo "Syncing newest ${MAX_LOCAL_RUNS} telemetry runs from ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/ -> ${LOCAL_DIR}/"

# Ensure the remote telemetry directory exists before syncing
SSHPASS="$REMOTE_PW" sshpass -e ssh -o StrictHostKeyChecking=no \
    "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR}"

REMOTE_RUNS=()
while IFS= read -r run; do
  [[ -n "$run" ]] && REMOTE_RUNS+=("$run")
done < <(
  SSHPASS="$REMOTE_PW" sshpass -e ssh -o StrictHostKeyChecking=no \
      "${REMOTE_USER}@${REMOTE_HOST}" \
      "REMOTE_DIR='$REMOTE_DIR' MAX_LOCAL_RUNS='$MAX_LOCAL_RUNS' python3 - <<'PY'
import os
from pathlib import Path

remote_dir = Path(os.environ['REMOTE_DIR'])
keep = int(os.environ['MAX_LOCAL_RUNS'])
runs = [
    path
    for path in remote_dir.iterdir()
    if path.is_dir() and not path.name.startswith('.pruning-')
]
runs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
for run in runs[:keep]:
    print(run.name)
PY"
)

if [[ "${#REMOTE_RUNS[@]}" -eq 0 ]]; then
  echo "No remote telemetry runs found."
  exit 0
fi

RSYNC_EXCLUDES=()
if [[ "$SYNC_MEDIA" != "1" ]]; then
  RSYNC_EXCLUDES+=(--exclude='bag/' --exclude='images/' --exclude='*.mcap')
  echo "Skipping bag/image media. Set SYNC_MEDIA=1 to include it."
fi

for run in "${REMOTE_RUNS[@]}"; do
  echo "Syncing ${run}/"
  SSHPASS="$REMOTE_PW" sshpass -e rsync -avz --progress \
    "${RSYNC_EXCLUDES[@]}" \
    -e "ssh -o StrictHostKeyChecking=no" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/${run}/" \
    "${LOCAL_DIR}/${run}/"
done

LOCAL_DIR="$LOCAL_DIR" MAX_LOCAL_RUNS="$MAX_LOCAL_RUNS" python3 - <<'PY'
import os
import shutil
from pathlib import Path

local_dir = Path(os.environ["LOCAL_DIR"])
keep = int(os.environ["MAX_LOCAL_RUNS"])
run_dirs = [
    path
    for path in local_dir.iterdir()
    if path.is_dir() and not path.name.startswith(".pruning-")
]
run_dirs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
for old_run in run_dirs[keep:]:
    prune_target = local_dir / f".pruning-{old_run.name}"
    try:
        old_run.rename(prune_target)
    except OSError:
        prune_target = old_run
    shutil.rmtree(prune_target, ignore_errors=True)
PY

echo "Done. Telemetry is in ${LOCAL_DIR}/"
