# vexy Coprocessor — Operations Runbook

**System:** Raspberry Pi 5 · Ubuntu 24.04 LTS · ROS 2 Jazzy  
**Hostname:** vexy.local · **SSH user:** vexy  
**Workspace:** `~/ros2_ws` (libcamera fork + camera_ros + vexy_ros)  
**Last updated:** 2026-06-23

---

## Table of Contents

1. [Daily Operations](#1-daily-operations)
2. [Verification Checklist](#2-verification-checklist)
3. [Recording Sessions](#3-recording-sessions)
4. [Troubleshooting](#4-troubleshooting)
5. [Reboot Procedure](#5-reboot-procedure)
6. [Workspace Rebuild](#6-workspace-rebuild)
7. [Log Locations](#7-log-locations)

---

## 1. Daily Operations

### SSH into the Pi

```bash
ssh vexy@vexy.local
# If mDNS fails, use the IP address directly:
ssh vexy@<IP_ADDRESS>
```

### Source the workspace (required in every new shell)

ROS 2 Jazzy base is sourced in `~/.bashrc`; the overlay must be sourced manually unless you add it there too:

```bash
source ~/ros2_ws/install/setup.bash
```

To add it permanently:

```bash
echo 'source ~/ros2_ws/install/setup.bash' >> ~/.bashrc
```

### Start the full stack

Launches both `camera_node` (Camera Module 3, IMX708) and `vex_bridge_node` (VEX V5 USB serial bridge):

```bash
ros2 launch vexy_ros vexy.launch.py
```

Override defaults if needed:

```bash
# Different serial port
ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1

# Higher resolution
ros2 launch vexy_ros vexy.launch.py camera_width:=1280 camera_height:=720 camera_fps:=30

# Both overrides
ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1 camera_width:=1280 camera_height:=720 camera_fps:=30
```

Default launch parameters:

| Parameter | Default | Notes |
|-----------|---------|-------|
| `serial_port` | `auto` | VEX V5 Brain user/program serial; prefers the `if02` by-id device |
| `baud_rate` | `115200` | Do not change |
| `camera_width` | `640` | |
| `camera_height` | `480` | |
| `camera_fps` | `15` | Converted to libcamera `FrameDurationLimits` |
| `camera_frame_id` | `camera_optical_frame` | Camera optical frame stamped into messages |
| `camera_info_url` | package config URL | Must be `file:///...`; replace starter config with measured calibration |
| `apriltag_config` | package config path | Tag family/ID/size YAML |

### Start individual nodes

**Camera node only:**

```bash
ros2 run camera_ros camera_node \
  --ros-args \
  -p width:=640 -p height:=480 -p fps:=15 \
  --remap ~/image_raw:=/camera/image_raw \
  --remap ~/camera_info:=/camera/camera_info
```

**VEX bridge node only:**

```bash
ros2 run vexy_ros vex_bridge_node \
  --ros-args \
  -p serial_port:=auto -p baud_rate:=115200
```

**Foxglove bridge only:**

```bash
ros2 launch vexy_ros vexy.launch.py  # foxglove_bridge starts automatically
```

### Stop the stack

Press `Ctrl+C` in the terminal running `ros2 launch`. All child nodes stop cleanly.

To kill a specific node by name:

```bash
ros2 lifecycle set /camera shutdown   # if lifecycle-managed
kill $(ros2 node info /camera | grep PID | awk '{print $2}')
```

Or simply kill by process name:

```bash
pkill -f camera_node
pkill -f vex_bridge_node
```

### Check running nodes

```bash
ros2 node list
# Expected output when full stack is running:
#   /camera
#   /vex_bridge
#   /foxglove_bridge   (if started separately)
```

---

## 2. Verification Checklist

Run these checks in order after starting the stack.

### 2.1 SSH connection

```bash
ssh vexy@vexy.local "echo 'SSH OK'"
```

Expected: `SSH OK`

### 2.2 ROS 2 workspace sourced

```bash
ros2 pkg list | grep vexy_ros
```

Expected: `vexy_ros` appears in output. If not, run `source ~/ros2_ws/install/setup.bash`.

### 2.3 All nodes running

```bash
ros2 node list
```

Expected: `/camera`, `/camera_rectify`, `/apriltag`, `/align_to_tag`, `/vex_bridge`, and `/foxglove_bridge` are all listed.

### 2.4 Camera publishing

```bash
ros2 topic hz /camera/image_raw
```

Expected: ~15 Hz (or the configured `camera_fps`). Let it run for 5 seconds, then `Ctrl+C`.

Also verify camera info is publishing:

```bash
ros2 topic hz /camera/camera_info
ros2 topic echo /camera/camera_info --once | grep -E 'k:|d:|p:'
```

Expected: `/camera/camera_info` publishes nonzero `k` and `p` matrix values. If the matrices are zero, the calibration URL did not load and tag-pose proof is not valid.

### 2.5 Rectification and AprilTag proof

```bash
ros2 topic hz /camera/image_rect
ros2 topic echo /apriltag/detections --once
ros2 topic echo /tf --once
```

Expected: `/camera/image_rect` runs at the camera rate. With a printed tag36h11 ID `0` visible and the physical tag size matching `config/apriltag_36h11.yaml`, `/apriltag/detections` publishes an `AprilTagDetectionArray`; `/tf` includes a transform for `tag36h11_0` when pose estimation succeeds.

### 2.6 VEX bridge connected to Brain

```bash
ros2 topic echo /vex/ack --once
```

Expected: A JSON ack from the Brain, e.g.:
```json
{"v":1,"ack":1,"type":"ack","state":"ok","recv_ms":124,"battery_mv":12300,"heading_deg":0.0,"fault":null}
```

Check for heartbeat timeouts in the node log:

```bash
ros2 node info /vex_bridge
ros2 topic hz /vex/ack
ros2 topic echo /vex/bridge_status --once
```

Expected: ~6–7 Hz (heartbeat fires at 0.15 s interval).

`/vex/ack` proves the Brain is receiving heartbeats/commands. `/vex/telemetry` is reserved for streaming telemetry/sample/event records; if the current Brain firmware only emits ack records, `/vex/bridge_status` may report `no_telemetry` until telemetry streaming is added.

### 2.7 AlignToTag bounded local skill

Only run this with the robot on blocks or in a safe fixture after camera, tag, and `/vex/ack` proof are green.

```bash
ros2 topic echo /align_to_tag/feedback &
ros2 topic echo /align_to_tag/result --once &
ros2 topic pub --once /align_to_tag/goal std_msgs/String \
  '{"data":"{\"tag_id\":0,\"target_distance_m\":0.45,\"yaw_tolerance_rad\":0.05,\"lateral_tolerance_m\":0.03,\"timeout_s\":5.0,\"max_step_ms\":150}"}'
```

Expected: feedback reports tag visibility plus yaw/lateral/distance error; result is either `success` or an explicit bounded failure such as `stale_tag`, `stale_ack`, `bridge_fault`, `timeout`, or `cancelled`. The node sends a final `stop` command on every terminal result.

Cancel an active run:

```bash
ros2 topic pub --once /align_to_tag/cancel std_msgs/String '{"data":"operator_cancel"}'
```

### 2.8 Foxglove bridge reachable

```bash
# From the Pi:
curl -s --max-time 3 http://vexy.local:8765 | head -c 100
# Non-empty or "upgrade required" response = bridge is up

# From your laptop:
nc -zv vexy.local 8765
```

In Foxglove Studio (browser or desktop):

1. Open `https://app.foxglove.dev`
2. Click **Open connection** → **Foxglove WebSocket**
3. Enter `ws://vexy.local:8765` (or `ws://<IP>:8765` if mDNS fails)
4. Confirm topics `/camera/image_raw`, `/camera/image_rect`, `/apriltag/detections`, `/align_to_tag/feedback`, `/align_to_tag/result`, `/vex/ack`, `/vex/telemetry`, `/vex/bridge_status`, etc. appear in the topic list

### 2.9 Scene map proof

The scene map turns the fixed AprilTag workspace layout into robot/object map
coordinates. The default map is `config/maps/table-grab-toss-v1.json`, matching
the wiki-backed 150 cm x 200 cm arena with 200 mm tag36h11 tags:

- tag `0`: bin
- tag `1`: ball staging
- tag `2`: home

With a fixed anchor tag visible:

```bash
ros2 topic echo /vision/scene_map --once
```

Expected: JSON with `robot_pose`, `camera_pose`, `tags`, `anchor_tag_ids`, and
`observed_tag_ids`. Poses include both ROS-friendly meter/radian fields and the
wiki map fields `x_mm`, `y_mm`, `heading_deg`.

If the camera is mounted away from the robot center, relaunch with the measured
camera pose in the robot body frame:

```bash
ros2 launch vexy_ros vexy.launch.py \
  camera_in_robot_json:='{"x_m":0.12,"y_m":0.0,"yaw_rad":0.0}'
```

To indicate an untagged object in camera-relative coordinates:

```bash
ros2 topic pub --once /vision/object_indications std_msgs/String \
  '{"data":"[{\"name\":\"red_block\",\"forward_m\":0.65,\"left_m\":-0.12,\"confidence\":0.8}]"}'
ros2 topic echo /vision/scene_map --once
```

Expected: `/vision/scene_map` includes an `objects[]` entry with the object pose
transformed into the active workspace map. This is an operator/prototype hint;
the canonical object detector can replace it later.

---

## 3. Recording Sessions

### Start a bag recording

```bash
# Record all topics, named by date/time
ros2 bag record -a -o session_$(date +%Y%m%d_%H%M%S)
```

Record specific topics only (smaller files):

```bash
ros2 bag record /camera/image_raw /camera/camera_info /camera/image_rect /apriltag/detections /tf /vision/scene_map /align_to_tag/feedback /align_to_tag/result /vex/cmd /vex/ack /vex/telemetry /vex/bridge_status \
  -o session_$(date +%Y%m%d_%H%M%S)
```

Stop with `Ctrl+C`. The bag is written to the current directory as `session_YYYYMMDD_HHMMSS/`.

### Naming convention

```
session_YYYYMMDD_HHMMSS/
  metadata.yaml
  session_YYYYMMDD_HHMMSS_0.mcap
```

Example: `session_20260623_143012/`

Store bags in `~/bags/` on the Pi:

```bash
mkdir -p ~/bags
ros2 bag record -a -o ~/bags/session_$(date +%Y%m%d_%H%M%S)
```

### Copy bags to laptop

```bash
# From laptop:
scp -r vexy@vexy.local:~/bags/session_20260623_143012 .
```

### Export VEX bridge topics and scene map to JSON for LLM analysis

Extract `/vision/scene_map`, `/vex/ack`, `/vex/telemetry`, and
`/vex/bridge_status` messages to newline-delimited JSON:

```bash
ros2 bag convert \
  --input-bagfile session_20260623_143012 \
  --output-bagfile /tmp/telem_only \
  --output-storage sqlite3

# Then extract the string payloads:
ros2 bag play session_20260623_143012 --topics /vision/scene_map /vex/ack /vex/telemetry /vex/bridge_status &
ros2 topic echo /vex/ack | while IFS= read -r line; do
  echo "$line" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',''))"
done > ack_$(date +%Y%m%d_%H%M%S).jsonl
```

Simpler one-liner (plays bag and writes JSONL):

```bash
ros2 bag play session_20260623_143012 --topics /vision/scene_map /vex/ack /vex/telemetry /vex/bridge_status --rate 10 &
PLAY_PID=$!
ros2 topic echo --csv /vex/ack > ack_raw.csv
kill $PLAY_PID
# Column 2 of ack_raw.csv is the JSON string; strip it with:
awk -F',' 'NR>1 {gsub(/^"|"$/, "", $2); print $2}' ack_raw.csv > ack.jsonl
```

### Export contract-valid JSONL

Create a proof bundle JSON containing the final `/vision/scene_map` message,
the terminal `/align_to_tag/result`, at least one V5 motor sample, and the raw
bag path. Then export it:

```bash
PYTHONPATH=/home/vexy/llm-self-model-capstone/contracts/src:$PYTHONPATH \
  ros2 run vexy_ros vexy_export_contract_jsonl \
  proof/align_to_tag_bundle.json \
  --out proof/contract/session_$(date +%Y%m%d_%H%M%S).jsonl
```

Validate from the repo checkout:

```bash
cd /home/vexy/llm-self-model-capstone
uv run --project contracts python - <<'PY'
from pathlib import Path
from contracts import ContractLine
for line in Path("proof/contract").glob("*.jsonl"):
    for raw in line.read_text().splitlines():
        ContractLine.model_validate_json(raw)
print("OK contract JSONL")
PY
```

---

## 4. Troubleshooting

### Quick reference table

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `no cameras available` | User not in `video`/`render` groups | See §4.1 |
| `bzip2` / package conflict on build | `noble-updates` missing from apt sources | See §4.2 |
| `Permission denied /dev/media*` | `video` group not applied | See §4.3 |
| Foxglove "Connection failed" | mDNS issue or bridge not running | See §4.4 |
| Foxglove "Waiting for image messages" | Wrong topic name selected | See §4.5 |
| `cannot open ... ttyACM...` | Brain not connected, permissions missing, or different port | See §4.6 |
| Heartbeat timeout from Brain | `vex_bridge_node` crashed | See §4.7 |

---

### 4.1 "no cameras available"

**Symptom:** `camera_node` exits immediately with `no cameras available` or similar libcamera error.

**Diagnosis:**

```bash
groups   # check output for 'video' and 'render'
ls -la /dev/video* /dev/media*
```

**Fix:**

```bash
sudo usermod -aG video,render vexy
# Log out and back in, OR reboot:
sudo reboot
```

Verify after reboot:

```bash
groups  # should include 'video' and 'render'
libcamera-hello --list-cameras  # should list the IMX708
```

---

### 4.2 bzip2 version conflict during build

**Symptom:** `colcon build` fails with a bzip2 version mismatch or `libbz2` conflict during libcamera compilation.

**Diagnosis:**

```bash
apt-cache policy libbz2-dev
# Check if noble-updates is in sources
grep -r "noble-updates" /etc/apt/sources.list /etc/apt/sources.list.d/
```

**Fix:**

```bash
# Add noble-updates if missing:
sudo add-apt-repository "deb http://ports.ubuntu.com/ubuntu-ports noble-updates main restricted universe multiverse"
sudo apt-get update
sudo apt-get install -y libbz2-dev
# Retry build (see §6)
```

---

### 4.3 Permission denied on /dev/media*

**Symptom:** libcamera logs `Failed to open /dev/media0: Permission denied` or similar.

**Diagnosis:**

```bash
ls -la /dev/media*
# Should be: crw-rw---- 1 root video ...
stat /dev/media0 | grep Gid
```

**Fix:**

```bash
sudo usermod -aG video vexy
sudo reboot
# After reboot:
groups  # confirm 'video' is listed
```

If the group is correct but still denied, check udev rules:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

### 4.4 Foxglove "Connection failed"

**Symptom:** Foxglove Studio cannot connect to `ws://vexy.local:8765`.

**Step 1 — Verify bridge is running:**

```bash
ssh vexy@vexy.local "ros2 node list | grep foxglove"
# If empty, start the bridge:
ros2 launch vexy_ros vexy.launch.py  # foxglove_bridge starts automatically &
```

**Step 2 — Try IP address instead of hostname:**

**Browser WebSocket connections commonly fail with mDNS even when SSH to `vexy.local` works fine** — this was confirmed during initial setup. Always prefer the IP address for Foxglove. Find the Pi's current IP:

```bash
ssh vexy@vexy.local "hostname -I | awk '{print \$1}'"
```

Then connect Foxglove to `ws://<IP_ADDRESS>:8765`.

**Step 3 — Check firewall:**

```bash
ssh vexy@vexy.local "sudo ufw status"
# If active, allow port 8765:
sudo ufw allow 8765/tcp
```

---

### 4.5 Foxglove "Waiting for image messages"

**Symptom:** Foxglove is connected but the image panel shows "Waiting for image messages."

**Diagnosis:**

```bash
# Verify camera_node is running and publishing:
ros2 node list | grep camera
ros2 topic hz /camera/image_raw
```

**Fixes:**

1. **Wrong topic selected in Foxglove:** In the image panel settings, set topic to `/camera/image_raw` (not `/camera/image_compressed` or anything else).

2. **camera_node not running:** Restart it:
   ```bash
   ros2 run camera_ros camera_node \
     --ros-args \
     -p width:=640 -p height:=480 -p fps:=15 \
     --remap ~/image_raw:=/camera/image_raw \
     --remap ~/camera_info:=/camera/camera_info
   ```

3. **Message type mismatch:** The topic publishes `sensor_msgs/Image`. Confirm in Foxglove the panel is set to **Image** (not **3D**).

---

### 4.6 V5 serial port not found

**Symptom:** `vex_bridge_node` logs `cannot open ...` or the device file is absent.

**Step 1 — Check if Brain is connected:**

```bash
ls /dev/ttyACM*
# If nothing appears, the USB cable is not connected or the Brain is off
```

**Step 2 — Check which port:**

```bash
ls /dev/ttyACM*
# Common: /dev/ttyACM0 and /dev/ttyACM1, with the user/program port usually on if02
dmesg | tail -20 | grep tty
```

**Step 3 — Launch with the correct port:**

```bash
ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1
```

**Step 4 — Check dialout group:**

```bash
groups  # should include 'dialout'
sudo usermod -aG dialout vexy
sudo reboot
```

---

### 4.7 Heartbeat timeout from Brain

**Symptom:** `/vex/bridge_status` reports `missing_ack` or `serial_disconnect`; `/vex/ack` stops publishing.

**Diagnosis:**

```bash
ros2 topic hz /vex/ack
ros2 topic echo /vex/bridge_status --once
# If rate is 0 or node is absent:
ros2 node list | grep vex_bridge
```

**Fix — Restart the bridge node:**

If running via the launch file, `Ctrl+C` the launch and re-run:

```bash
ros2 launch vexy_ros vexy.launch.py
```

If running standalone:

```bash
pkill -f vex_bridge_node
ros2 run vexy_ros vex_bridge_node \
  --ros-args -p serial_port:=auto -p baud_rate:=115200
```

**If the Brain itself is at fault** (watchdog tripped, program not running):

1. On the V5 Brain, confirm the driver program is running (not paused at a print statement).
2. Power-cycle the Brain if needed.
3. Re-plug the USB cable.

---

## 5. Reboot Procedure

### What survives a reboot

| Component | Survives reboot? | Notes |
|-----------|-----------------|-------|
| Ubuntu OS | Yes | |
| ROS 2 Jazzy base install | Yes | In `/opt/ros/jazzy/` |
| `~/ros2_ws` build artifacts | Yes | In `~/ros2_ws/install/` |
| `source` in `~/.bashrc` | Yes | If added permanently |
| Running ROS nodes | **No** | Must be restarted |
| Foxglove bridge | **No** | Must be restarted |

### After reboot — restart sequence

```bash
# 1. SSH in
ssh vexy@vexy.local

# 2. Source workspace (if not in .bashrc already)
source ~/ros2_ws/install/setup.bash

# 3. Verify device nodes are present
ls /dev/ttyACM*     # VEX V5 Brain
ls /dev/video*      # Camera

# 4. Launch full stack
ros2 launch vexy_ros vexy.launch.py

# Foxglove bridge starts automatically with the launch file above
```

### Optional: auto-start on boot with systemd

Create `/etc/systemd/system/vexy-ros.service`:

```ini
[Unit]
Description=vexy ROS 2 Stack
After=network.target

[Service]
User=vexy
ExecStart=/bin/bash -c 'source /opt/ros/jazzy/setup.bash && source /home/vexy/ros2_ws/install/setup.bash && ros2 launch vexy_ros vexy.launch.py'
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable vexy-ros.service
sudo systemctl start vexy-ros.service
sudo systemctl status vexy-ros.service
```

---

## 6. Workspace Rebuild

### When to rebuild

Rebuild `~/ros2_ws` when:

- You pull changes to `robot/ros2-runtime/` (vexy_ros source)
- You update `camera_ros` or the libcamera fork
- A `colcon build` previously failed and you fixed the underlying issue
- You change `package.xml` or `setup.py`

You do **not** need to rebuild for:
- Python node changes that only edit `.py` files in `src/vexy_ros/` (they are symlinked in development mode — changes take effect immediately on node restart)

### Full workspace rebuild

```bash
cd ~/ros2_ws

# Clean previous build artifacts (optional but safe)
rm -rf build/ install/ log/

# Rebuild all three packages
colcon build \
  --packages-select libcamera camera_ros vexy_ros \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  --event-handlers console_direct+

# Re-source the overlay
source ~/ros2_ws/install/setup.bash
```

Expected time: 10–25 minutes for libcamera + camera_ros (C++). `vexy_ros` (Python) builds in seconds.

### Rebuild vexy_ros only (fastest)

```bash
cd ~/ros2_ws
colcon build --packages-select vexy_ros --event-handlers console_direct+
source ~/ros2_ws/install/setup.bash
```

### Incremental rebuild after libcamera changes

```bash
cd ~/ros2_ws
colcon build \
  --packages-select libcamera camera_ros \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  --event-handlers console_direct+
source ~/ros2_ws/install/setup.bash
```

### Verify build succeeded

```bash
ros2 pkg list | grep -E 'vexy_ros|camera_ros'
# Both packages should appear
```

---

## 7. Log Locations

### ROS 2 node logs

ROS 2 writes per-session logs to:

```
~/.ros/log/
  latest/           → symlink to most recent session
  <session-id>/
    launch.log      (launch file output)
    <node-name>-1-stdout.log
    <node-name>-1-stderr.log
```

```bash
# View latest session logs
ls ~/.ros/log/latest/

# Tail camera node output live
tail -f ~/.ros/log/latest/camera-1-stdout.log

# Tail VEX bridge live
tail -f ~/.ros/log/latest/vex_bridge-1-stdout.log

# All logs for the current session
cat ~/.ros/log/latest/*.log
```

### Colcon build logs

```bash
ls ~/ros2_ws/log/latest/
cat ~/ros2_ws/log/latest/logger_all.log
```

### systemd journal (if running as a service)

```bash
# Live log stream
journalctl -u vexy-ros.service -f

# Last 100 lines
journalctl -u vexy-ros.service -n 100

# Since last boot
journalctl -u vexy-ros.service -b
```

### System-level dmesg (USB/camera device events)

```bash
# Recent USB events (e.g., Brain plug/unplug, camera probe)
sudo dmesg | grep -E 'ttyACM|usb|v4l|media|imx708' | tail -30

# Live monitoring
sudo dmesg -w | grep -E 'ttyACM|usb|media|imx708'
```

### Log rotation / cleanup

ROS 2 log directories accumulate over sessions. Clean old logs:

```bash
ros2 doctor --report  # lists log directory size
# Manual cleanup: keep last 10 sessions
ls -dt ~/.ros/log/*/  | tail -n +11 | xargs rm -rf
```

---

## Quick Reference Card

```
# SSH
ssh vexy@vexy.local

# Source
source ~/ros2_ws/install/setup.bash

# Launch full stack
ros2 launch vexy_ros vexy.launch.py

# Check nodes
ros2 node list

# Camera health
ros2 topic hz /camera/image_raw

# VEX serial ack proof
ros2 topic echo /vex/ack --once
ros2 topic echo /vex/bridge_status --once

# Foxglove bridge
ros2 launch vexy_ros vexy.launch.py  # foxglove_bridge starts automatically
# Connect: ws://vexy.local:8765

# Record session
ros2 bag record -a -o ~/bags/session_$(date +%Y%m%d_%H%M%S)

# Rebuild vexy_ros only
cd ~/ros2_ws && colcon build --packages-select vexy_ros && source install/setup.bash

# Logs
tail -f ~/.ros/log/latest/vex_bridge-1-stdout.log
```
