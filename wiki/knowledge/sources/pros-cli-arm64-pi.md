---
id: pros-cli-arm64-pi
title: Research: PROS CLI on ARM64 Linux (Raspberry Pi 5)
updated: 2026-06-25
sources:
  - ../../raw/research/pros-cli-arm64-pi/index.md
tags: [source, pros, vex, cli, raspberry-pi, arm64, upload, toolchain]
---

# Research: PROS CLI on ARM64 Linux (Raspberry Pi 5)

Research conducted 2026-06-25. Full report: `raw/research/pros-cli-arm64-pi/index.md`.

## Key Findings

**`pros-cli` is pure Python — ARM64 install has no obstacles.**
The PyPI distribution is `pros_cli-3.5.6-py3-none-any.whl` (no native extensions, any platform).
Install via `uv sync` from `robot/v5-brain/` on the Pi.

**`pros upload` is decoupled from the ARM cross-compiler.**
Upload reads a pre-built `bin/monolith.bin` and sends it to the Brain over USB serial.
`arm-none-eabi-gcc` is only needed for `pros build`.

**`pros upload` accepts a bare binary file or a project directory.**
```
pros upload [PATH] [PORT]

[PATH] may be a directory or file. If a file, --target must be specified.
--slot  INTEGER [1<=x<=8]   Program slot on the Brain GUI.
--after [run|screen|none]   Action after upload.
```

## Pi State (as of 2026-06-25)

| Item | Status |
|------|--------|
| Architecture | `aarch64` (ARM64) |
| OS | Ubuntu 24.04 LTS |
| Python | 3.12.3 |
| `uv` | Installed — `~/.local/bin/uv` v0.11.24 |
| `pros-cli` | Installed via `uv sync` — 3.5.6 |
| `arm-none-eabi-gcc` | NOT installed |
| `dialout` group | `vexy` user IS a member |
| V5 Brain connected | YES — `/dev/ttyACM0` + `/dev/ttyACM1` |
| Pre-built `monolith.bin` | EXISTS at `robot/v5-brain/pros_bridge/bin/` |

> **`pros --version` / `pros upload --help` bug (all Python versions):** `get_version()` in
> `pros/common/utils.py` looks for a `version` file at `site-packages/version` (only present in
> source checkouts, absent in uv/pip installs). The `pkg_resources` fallback also fails. Fix:
> `echo "3.5.6" > .venv/lib/python3.12/site-packages/version`. After this patch, `pros upload`
> works correctly. Applied on vexy 2026-06-25.

> `project.pros` template path is `/Users/kelly/Library/Application Support/PROS/...` (a macOS path). `pros build` / `pros conductor apply` will fail on the Pi. Build-only stays on the laptop.

## Install Procedure (one-time)

`uv` is already installed on vexy at `~/.local/bin/uv` (v0.11.24, confirmed 2026-06-25).

```bash
# On the Pi (via SSH) — uv is already present, just sync:
cd ~/llm-self-model-capstone/robot/v5-brain
~/.local/bin/uv sync

# Fix the version-file bug (one-time after first uv sync):
echo "3.5.6" > .venv/lib/python3.12/site-packages/version

# Verify:
.venv/bin/pros upload --help   # should print usage without errors
```

## Upload Workflow (from laptop)

```bash
# Build on laptop:
cd robot/v5-brain/pros_bridge && uv run pros build

# Push binary to Pi:
scp robot/v5-brain/pros_bridge/bin/monolith.bin \
    vexy@vexy.local:~/llm-self-model-capstone/robot/v5-brain/pros_bridge/bin/

# Stop bridge, upload (slot 7 or 8 — NEVER slot 1 during dev), restart:
ssh vexy@vexy.local "
  systemctl --user stop vexy-ros-bridge.service vexy-ros-stack.service
  cd ~/llm-self-model-capstone/robot/v5-brain/pros_bridge
  uv run pros upload --slot 7 --after none
  systemctl --user start vexy-ros-stack.service vexy-ros-bridge.service
"
```

See `robot/ros2-runtime/docs/RUNBOOK.md §8` for the full runbook including Python node
push (§8D) and port identification (§8E).

relates_to::[[pros]]
relates_to::[[vex-v5]]
relates_to::[[vex-coprocessor-pattern]]
relates_to::[[pros-cli-brain-bridge]]
relates_to::[[raspberry-pi-5]]
