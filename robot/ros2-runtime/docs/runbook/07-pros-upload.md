# PROS Brain Program — Push and Upload via SSH

This section covers how to update and upload the V5 Brain C++ program (`monolith.bin`) from a
laptop to the Brain via the Pi, and how to push Pi-side Python node updates. The V5 Brain must be
powered on and USB-connected to the Pi.

**CRITICAL:** Always stop the ROS bridge before uploading to prevent unexpected motor behavior
from partial commands during the upload.

### Slot ownership

| Slot | Owner | Policy |
|------|-------|--------|
| 1 | — | **Never upload here.** Reserved as a dynamic/ad-hoc slot; treated as read-only by all team members. |
| 2–4 | Jake | Jake's exclusive slots. Do not upload here unless you are Jake. |
| 5–6 | Grace | Grace's exclusive slots. Do not upload here unless you are Grace. |
| 7–8 | David | David's exclusive slots for development and testing. |

These are VEX GUI program upload slots. They are separate from `cmd:"routine"`
IDs inside the running `pros_bridge` program, where routine ID `2` is a 720 spin,
routine ID `3` is an arm up/down cycle, and routine ID `4` is one foot forward
then one foot back.

---

### 8.0 One-time setup: install PROS CLI on the Pi

The `pros-cli` wheel is pure Python (`py3-none-any`) — it installs on ARM64 with no issues.
The project uses `uv` for package management; `uv sync` reads the pinned `pros-cli>=3.5.6`
from `robot/v5-brain/pyproject.toml`.

```bash
# SSH into the Pi:
ssh vexy@vexy.local

# uv is already installed at ~/.local/bin/uv (v0.11.24, confirmed 2026-06-25).
# Install pros-cli into the project venv:
cd ~/llm-self-model-capstone/robot/v5-brain
~/.local/bin/uv sync

# Fix the version-file bug (one-time, after first uv sync):
echo "3.5.6" > .venv/lib/python3.12/site-packages/version

# Verify:
.venv/bin/pros upload --help
# Expected: prints pros upload usage without errors
```

> **Note — version-file bug (all Python versions):** `pros --version` and `pros upload --help`
> crash with `RuntimeError: Could not determine version` on a clean uv/pip install because
> `get_version()` looks for a `version` file that only exists in source checkouts. The fix above
> (writing `3.5.6` to `site-packages/version`) resolves it. Applied on vexy 2026-06-25.

> **Note — ARM toolchain:** `arm-none-eabi-gcc` is NOT on the Pi. `pros upload` does not
> need it — the cross-compiler is only required for `pros build`. Building happens on
> the laptop; the Pi only uploads the pre-built `monolith.bin`.

---

### 8A — Preferred workflow: build on laptop → upload from Pi

Use this when `main.cpp` has changed and a new binary is needed.

**Step 1 — Build on the laptop:**

```bash
# On the laptop, from repo root:
cd robot/v5-brain/pros_bridge
uv run pros build           # produces bin/monolith.bin
```

Or if the venv is activated:

```bash
source ../.venv/bin/activate
pros build
```

**Step 2 — Push the binary to the Pi:**

```bash
# From the laptop:
scp robot/v5-brain/pros_bridge/bin/monolith.bin \
    vexy@vexy.local:~/llm-self-model-capstone/robot/v5-brain/pros_bridge/bin/
```

**Step 3 — Upload from Pi via SSH:**

```bash
# Stop the bridge first:
ssh vexy@vexy.local "systemctl --user stop vexy-ros-bridge.service vexy-ros-stack.service"

# Upload to slot 7 or 8 (David's slots — see slot ownership table above):
ssh vexy@vexy.local "cd ~/llm-self-model-capstone/robot/v5-brain/pros_bridge && uv run pros upload --slot 7 --after none"

# Restart the stack:
ssh vexy@vexy.local "systemctl --user start vexy-ros-stack.service vexy-ros-bridge.service"
```

`--after none` prevents the Brain from auto-running the uploaded program. Tap the slot
on the Brain touchscreen when you are ready to run.

---

### 8B — Upload a bare binary file (without entering the project directory)

When you want to upload from any directory, or want to be explicit about the binary path:

```bash
ssh vexy@vexy.local \
  "uv --project ~/llm-self-model-capstone/robot/v5-brain run pros upload \
     ~/llm-self-model-capstone/robot/v5-brain/pros_bridge/bin/monolith.bin \
     --target v5 --slot 7 --after none"   # slot 7 or 8 for David; see slot ownership table
```

`--target v5` is required when supplying a bare file path (not a project directory).

---

### 8C — Full one-liner from the laptop (stop → upload → start)

```bash
SLOT=7   # David: 7 or 8 | Jake: 2–4 | Grace: 5–6 | NEVER slot 1
ssh vexy@vexy.local "
  systemctl --user stop vexy-ros-bridge.service vexy-ros-stack.service 2>/dev/null
  cd ~/llm-self-model-capstone/robot/v5-brain/pros_bridge
  uv run pros upload --slot $SLOT --after none
  systemctl --user start vexy-ros-stack.service vexy-ros-bridge.service
"
```

---

### 8D — Python node push (no Brain upload, no colcon build)

Python source changes in `robot/ros2-runtime/src/vexy_ros/` take effect immediately
on node restart — no `colcon build` needed (the package is installed in development
mode and the `.py` files are symlinked).

```bash
# Push Python source from laptop to Pi:
rsync -av --delete \
  robot/ros2-runtime/src/vexy_ros/ \
  vexy@vexy.local:~/ros2_ws/src/vexy_ros/src/vexy_ros/

# Restart nodes (changes active immediately):
ssh vexy@vexy.local "systemctl --user restart vexy-ros-stack.service"

# Verify the updated node is running:
ssh vexy@vexy.local "ros2 node list"
```

---

### 8E — Identifying the Brain serial ports on the Pi

The Brain always assigns the user port (stdout) to USB CDC interface `00` and the
system port (for upload) to interface `01`. Check which `ttyACM*` maps to which:

```bash
ssh vexy@vexy.local "
  for dev in /dev/ttyACM*; do
    echo \"\$dev → interface \$(cat /sys/class/tty/\${dev##*/}/device/../bInterfaceNumber)\"
  done
"
```

Example output:
```
/dev/ttyACM0 → interface 00   ← user/stdout port (used by vex_bridge_node)
/dev/ttyACM1 → interface 01   ← system port (used by pros upload)
```

`pros upload` auto-detects the system port. If auto-detection fails, pass it explicitly:

```bash
uv run pros upload --slot 7 --after none /dev/ttyACM1
```

---

### 8F — Troubleshooting PROS upload

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `pros: command not found` | `uv sync` not run or `uv` not on PATH | Run §8.0 setup; ensure `~/.local/bin` is in PATH |
| `Could not determine version` | version-file missing from uv/pip install | Run: `echo "3.5.6" > .venv/lib/python3.12/site-packages/version` (see §8.0) |
| `No device found` | Brain off or USB not connected | Power on Brain, check USB cable, `ls /dev/ttyACM*` |
| Upload succeeds but program doesn't run | `--after none` was used (expected) | Tap the slot on the Brain touchscreen |
| `Port in use` or upload times out | `vex_bridge_node` holds the user port | Stop the stack first (§8C); note: upload uses system port (interface `01`), bridge uses user port (interface `00`) — they are different devices but stopping the stack before upload is safest |
| `project.pros template path not found` | Building on Pi: template path points to `/Users/kelly/...` | Build only on the laptop; never run `pros conductor apply` or `pros build` on the Pi with the current `project.pros` |
