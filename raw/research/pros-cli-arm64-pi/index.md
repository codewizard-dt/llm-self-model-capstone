---
topic: Does the PROS CLI (pip install pros-cli) work on ARM64 Linux (Ubuntu 24.04, Raspberry Pi 5)? Specifically install on aarch64, upload-only mode, binary file flag, native extension wheels.
slug: pros-cli-arm64-pi
researched: 2026-06-25
sources: [./sources.md]
---

# Research: PROS CLI on ARM64 Linux (Raspberry Pi 5 / Ubuntu 24.04)

> **Executive summary:** `pros-cli 3.5.6` is a pure-Python wheel (`py3-none-any`) with no native extensions — it installs on any platform including ARM64 Ubuntu 24.04. The Pi (`vexy`) is `aarch64`, has Python 3.12.3, and is in the `dialout` group. PROS CLI is **not yet installed** but the project's `pyproject.toml` already pins `pros-cli>=3.5.6`; installing `uv` and running `uv sync` from `robot/v5-brain/` is the correct install path. `pros upload` accepts a bare binary file (`pros upload bin/monolith.bin --target v5 --slot N`) or a project directory (`pros upload --slot N`) — the ARM cross-compiler is **not needed for upload**, only for build. A pre-built `monolith.bin` already exists on the Pi. The recommended workflow is: build on laptop → `scp` binary to Pi → `pros upload --slot 7` via SSH from Pi.

---

## Research Questions

1. Does `pip install pros-cli` / `uv add pros-cli` succeed on ARM64 Ubuntu 24.04?
2. Does `pros upload --slot N` work without `arm-none-eabi-gcc` (upload-only mode with pre-built binary)?
3. Is there a `--file` or `--bin` flag to upload a pre-built binary without a full PROS project tree?
4. Are there native extension wheels in `pros-cli` that would block ARM64 install?
5. What is the current install state on `vexy`, and what is the correct install procedure?

---

## Current State (Codebase / Pi)

**Pi identity:** `vexy` — Raspberry Pi 5, `aarch64`, Ubuntu 24.04 LTS, Python 3.12.3, pip 24.0.

**PROS CLI status:** NOT installed. `which pros` returns empty. `pip3 show pros-cli` returns empty. `uv tool list` returns empty.

**`uv` status:** NOT installed on the Pi. (`which uv` returns empty.)

**ARM cross-compiler:** NOT installed. `which arm-none-eabi-gcc` returns empty.

**USB device:** V5 Brain IS connected — `/dev/ttyACM0` and `/dev/ttyACM1` are present. The `vexy` user is in the `dialout` group — no permission issues.

**Pre-built binary:** `monolith.bin` EXISTS at `robot/v5-brain/pros_bridge/bin/monolith.bin` on the Pi. It was built on a dev laptop (`/Users/kelly/...` template path in `project.pros`) and committed/synced to the Pi.

**`project.pros` template path:** `"location": "/Users/kelly/Library/Application Support/PROS/templates/kernel@4.2.2"` — a macOS path from the original dev machine. `pros conductor apply` would fail on the Pi (trying to find templates at a Mac path), but **`pros upload` is unaffected** — it only reads `project.pros` for upload metadata, not for template paths.

**`pyproject.toml`** (`robot/v5-brain/pyproject.toml`) declares `dependencies = ["pros-cli>=3.5.6"]`. **`uv.lock`** confirms `pros-cli` is pinned. After installing `uv` on the Pi, `uv sync` from `robot/v5-brain/` will create `.venv/` and install `pros-cli` correctly.

**Python 3.13 version-detection bug:** `TOOLCHAIN.md` documents that `pros-cli 3.5.6` crashes on Python 3.13 (`RuntimeError: Could not determine version` from deprecated `pkg_resources`). The Pi has Python **3.12.3** — this bug does NOT apply.

---

## Key Findings

**[S1] Pure Python wheel — installs on ARM64 with no obstacles.**
The PyPI distribution for `pros-cli` is `pros_cli-3.5.6-py3-none-any.whl`. The `py3-none-any` tag means: any Python 3, no ABI requirement, any platform. There are zero compiled extensions — nothing that could block ARM64. [S1]

**[S2] `pros upload` is decoupled from the ARM cross-compiler.**
`pros upload` reads the project binary from `bin/monolith.bin` (or a path you supply) and sends it to the Brain over USB serial. It does not invoke `arm-none-eabi-gcc` at any point. The cross-compiler is only needed for `pros build` / `pros make`. [S2, local]

**[S3] `pros upload` accepts a bare binary file as `[PATH]`.**
From `pros upload --help` (run locally against the dev venv):
```
Usage: pros upload [OPTIONS] [PATH] [PORT]

[PATH] may be a directory or file. If a directory, finds a PROS project root
and uploads the binary for the correct target automatically. If a file, then
the file is uploaded. Note that --target must be specified in this case.
```
So `pros upload bin/monolith.bin --target v5 --slot 7` is valid from any working directory. [local]

**[S4] `--slot` flag is supported (range 1–8).**
```
--slot  INTEGER RANGE [1<=x<=8]  Program slot on the GUI.
```
[local]

**[S5] `--project PATH` flag allows pointing to a project directory from outside it.**
```
--project  PATH  PROS Project directory or file [default: .]
```
So from any SSH session: `pros upload --project ~/llm-self-model-capstone/robot/v5-brain/pros_bridge --slot 7`. [local]

**[S6] Port auto-detection works on Linux by target.**
`[PORT]` is optional; the CLI auto-detects the Brain's system port. On the Pi, the Brain always assigns user port to USB CDC interface `00` and system port to `01`. Auto-detection should find `/dev/ttyACM1` (the system port, interface `01`) automatically. [TOOLCHAIN.md]

---

## Constraints

1. **Build requires laptop.** `arm-none-eabi-gcc` is not on the Pi, and `project.pros` template paths point to `/Users/kelly/...` (a Mac). `pros build` / `pros make` will fail on the Pi unless the ARM toolchain and templates are installed there. This is out of scope for the immediate runbook.
2. **`uv` must be installed on the Pi first.** The project uses `uv` for all Python management. Never `pip install pros-cli` directly — use `uv sync` from `robot/v5-brain/`.
3. **Serial port conflict.** `pros upload` uses the system port (interface `01`) while `vex_bridge_node` uses the user port (interface `00`). They target different ports so they do NOT conflict — but see Note below.
4. **Brain must be powered on and connected.** `/dev/ttyACM0` and `/dev/ttyACM1` were confirmed present when Brain was on.
5. **Do not initiate programs on the Brain during research.** Upload-only is allowed (to slots 7 or 8 only). `pros upload --after none` prevents auto-run after upload.

> **Note on serial port conflict (clarification):** The upload (system port, interface `01`) and the Pi bridge (user port, interface `00`) use *different* `/dev/ttyACM*` device nodes. They can run simultaneously at the OS level. However, the Brain should not be receiving motion commands during upload — stop the bridge before uploading to prevent unexpected motor behavior from partially-received commands during the upload.

---

## Solution Comparison

| Workflow | Build where? | Upload command (from Pi) | Requires on Pi |
|----------|-------------|--------------------------|----------------|
| **8A — Recommended: laptop build → Pi upload** | Laptop (`pros build`) | `pros upload --slot 7` (from `pros_bridge/`) | `uv` + `pros-cli` (via `uv sync`) |
| **8B — Bare binary upload** | Laptop (`pros build`) → `scp bin/monolith.bin` | `pros upload bin/monolith.bin --target v5 --slot 7` | `uv` + `pros-cli` |
| **8C — Full Pi build (future)** | Pi (`pros build`) | `pros upload --slot 7` | `uv` + `pros-cli` + `arm-none-eabi-gcc` + PROS templates |

8A is preferred because `project.pros` already exists in `pros_bridge/` so no `--target` flag is needed.

---

## Recommendation

**Install `uv` on the Pi, then `uv sync` to get `pros-cli`.**

```bash
# Install uv on the Pi (one-time):
ssh vexy@vexy.local
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or open a new shell; uv installs to ~/.local/bin

# Install pros-cli into the project venv (one-time):
cd ~/llm-self-model-capstone/robot/v5-brain
uv sync
# Verify:
uv run pros --version   # expected: pros, version 3.5.6
```

**Brain program upload from Pi (via SSH from laptop):**

```bash
# Stop bridge before uploading (prevents motor commands during upload):
ssh vexy@vexy.local "systemctl --user stop vexy-ros-bridge.service vexy-ros-stack.service"

# Upload the pre-built monolith to slot 7 (NEVER slot 1 during test/research):
ssh vexy@vexy.local "cd ~/llm-self-model-capstone/robot/v5-brain/pros_bridge && uv run pros upload --slot 7 --after none"

# Restart the stack:
ssh vexy@vexy.local "systemctl --user start vexy-ros-stack.service vexy-ros-bridge.service"
```

**If the binary needs to be refreshed (built on laptop, pushed to Pi):**

```bash
# On laptop — build:
cd robot/v5-brain/pros_bridge
uv run pros build    # or: pros build (if venv is activated)

# Push to Pi:
scp robot/v5-brain/pros_bridge/bin/monolith.bin vexy@vexy.local:~/llm-self-model-capstone/robot/v5-brain/pros_bridge/bin/

# Upload from Pi (via SSH):
ssh vexy@vexy.local "cd ~/llm-self-model-capstone/robot/v5-brain/pros_bridge && uv run pros upload --slot 7 --after none"
```

**Python node update (no Brain upload needed):**

```bash
# Push Python source from laptop:
rsync -av robot/ros2-runtime/src/vexy_ros/ vexy@vexy.local:~/ros2_ws/src/vexy_ros/src/vexy_ros/

# Restart nodes (changes take effect immediately — no colcon build):
ssh vexy@vexy.local "systemctl --user restart vexy-ros-stack.service"
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `uv` install script not yet run → `pros` not found | Install `uv` once; add `~/.local/bin` to PATH in `~/.bashrc` |
| `project.pros` template path (`/Users/kelly/...`) breaks `pros conductor apply` on Pi | Don't run `conductor apply` on Pi — build is laptop-only; upload reads only the binary and upload options |
| `pros upload` auto-runs the program after upload | Always pass `--after none` to prevent auto-run |
| Brain not in a slot before `vex_bridge_node` connects | Tap the slot on the Brain screen, or use `--after run` on a deliberate test upload |
| Port confusion (ACM0 vs ACM1) | `pros upload` auto-detects the system port; explicit `--port /dev/ttyACM1` as fallback |

---

## Next Steps

- `/task-add Install uv on vexy Pi, run uv sync in robot/v5-brain, verify pros --version`
- Update `robot/ros2-runtime/docs/RUNBOOK.md` with §8 (PROS Brain Program — Push and Upload via SSH) — covers 8A, 8B, 8C, and Python node push workflow
- Amend `wiki/knowledge/entities/tools/pros.md` to note Pi-hosted upload path
- Run `/wiki-ingest raw/research/pros-cli-arm64-pi/index.md` to synthesize into the knowledge base
