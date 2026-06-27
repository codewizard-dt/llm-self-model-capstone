#!/usr/bin/env bash
# Push robot/ros2-runtime to the RPi, honouring .gitignore exclusions.
#
# Usage:
#   ./scripts/sync_pi_runtime.sh
#
# Reads VEXY_HOST, VEXY_SSH_USER, VEXY_SSH_PW from .env at the repo root.
# Any of these can also be overridden as environment variables before calling.
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
REMOTE_DIR="/home/vexy/llm-self-model-capstone/robot/ros2-runtime/"
LOCAL_DIR="$REPO_ROOT/robot/ros2-runtime/"

if ! command -v sshpass &>/dev/null; then
  echo "ERROR: sshpass is required. Install with: brew install sshpass" >&2
  exit 1
fi

echo "Syncing ${LOCAL_DIR} -> ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"

SSHPASS="$REMOTE_PW" sshpass -e rsync -avz --progress \
    --filter=':- .gitignore' \
    --exclude='.git/' \
    -e "ssh -o StrictHostKeyChecking=no" \
    "$LOCAL_DIR" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"

echo "Done."
