#!/usr/bin/env bash
# Push robot/ros2-runtime to the RPi.
# Dev/build artifacts are excluded explicitly (see MASTER_REQUIREMENTS coprocessor
# ignore_folders) plus repo-root .gitignore for anything else.
#
# Usage:
#   ./scripts/sync_pi_runtime.sh
#
# Reads VEXY_HOST, VEXY_SSH_USER, VEXY_SSH_PW from .env at the repo root.
# Any of these can also be overridden as environment variables before calling.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ENV_VEXY_HOST="${VEXY_HOST-}"
ENV_VEXY_SSH_USER="${VEXY_SSH_USER-}"
ENV_VEXY_SSH_PW="${VEXY_SSH_PW-}"

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  source "$REPO_ROOT/.env"
  set +a
fi

if [[ -n "$ENV_VEXY_HOST" ]]; then
  VEXY_HOST="$ENV_VEXY_HOST"
fi
if [[ -n "$ENV_VEXY_SSH_USER" ]]; then
  VEXY_SSH_USER="$ENV_VEXY_SSH_USER"
fi
if [[ -n "$ENV_VEXY_SSH_PW" ]]; then
  VEXY_SSH_PW="$ENV_VEXY_SSH_PW"
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

RSYNC_EXCLUDES=(
  --exclude='.git/'
  # coprocessor vertical (robot/ros2-runtime) — MASTER_REQUIREMENTS ignore_folders
  --exclude='.venv/'
  --exclude='__pycache__/'
  --exclude='build/'
  --exclude='install/'
  --exclude='log/'
  --exclude='models/'
  --exclude='captures/'
  --exclude='proof/'
  # local dev / test caches (present on laptop, rebuilt on Pi)
  --exclude='.ruff_cache/'
  --exclude='.pytest_cache/'
  --exclude='*.egg-info/'
  --exclude='*.py[cod]'
)

SSHPASS="$REMOTE_PW" sshpass -e rsync -avz --progress \
    --filter=":- ${REPO_ROOT}/.gitignore" \
    "${RSYNC_EXCLUDES[@]}" \
    -e "ssh -o StrictHostKeyChecking=no" \
    "$LOCAL_DIR" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"

echo "Done."
