#!/usr/bin/env bash
# Sync all operator telemetry runs from the RPi to a local directory.
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
REMOTE_DIR="/home/vexy/telemetry/"
LOCAL_DIR="${1:-./telemetry}"

if ! command -v sshpass &>/dev/null; then
  echo "ERROR: sshpass is required. Install with: brew install sshpass" >&2
  exit 1
fi

mkdir -p "$LOCAL_DIR"

echo "Syncing telemetry from ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR} -> ${LOCAL_DIR}/"

# Ensure the remote telemetry directory exists before syncing
SSHPASS="$REMOTE_PW" sshpass -e ssh -o StrictHostKeyChecking=no \
    "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR}"

SSHPASS="$REMOTE_PW" sshpass -e rsync -avz --progress \
    -e "ssh -o StrictHostKeyChecking=no" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}" \
    "${LOCAL_DIR}/"

echo "Done. Telemetry is in ${LOCAL_DIR}/"
