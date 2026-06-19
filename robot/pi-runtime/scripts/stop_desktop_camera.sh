#!/usr/bin/env bash
set -euo pipefail

pkill -f "/home/vexy/Desktop/camera_feed.py" || true
sleep 0.5
fuser -v /dev/media0 /dev/media1 /dev/video0 2>&1 || true

