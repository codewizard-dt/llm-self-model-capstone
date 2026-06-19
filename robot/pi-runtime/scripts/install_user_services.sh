#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"
cp "$ROOT"/services/*.service "$UNIT_DIR"/
systemctl --user daemon-reload
echo "Installed user services. Start with:"
echo "  systemctl --user start vexy-bridge.service"
echo "  systemctl --user start vexy-dashboard.service"
echo "  systemctl --user start vexy-camera.service"
echo
echo "Optional local overrides belong in:"
echo "  ~/.config/vexy-system2/local"
