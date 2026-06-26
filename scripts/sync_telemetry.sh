#!/usr/bin/env bash
# Sync all operator telemetry runs from the RPi to a local directory.
#
# Usage:
#   ./scripts/sync_telemetry.sh [local_dest]
#
# Environment overrides:
#   VEXY_HOST   Pi hostname or IP  (default: vexy.local)
#   VEXY_USER   SSH user           (default: vexy)
#
# Example — use IP directly:
#   VEXY_HOST=10.10.3.5 ./scripts/sync_telemetry.sh ./telemetry
set -euo pipefail

REMOTE_HOST="${VEXY_HOST:-vexy.local}"
REMOTE_USER="${VEXY_USER:-vexy}"
REMOTE_DIR="/home/vexy/telemetry/"
LOCAL_DIR="${1:-./telemetry}"

mkdir -p "$LOCAL_DIR"

echo "Syncing telemetry from ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR} -> ${LOCAL_DIR}/"
rsync -avz --progress \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}" \
    "${LOCAL_DIR}/"

echo "Done. Telemetry is in ${LOCAL_DIR}/"
