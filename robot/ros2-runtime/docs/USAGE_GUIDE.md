# Usage Guide — vexy_ros Day-to-Day Operations

This guide covers the practical operations you will run repeatedly when working with the stack. For architecture and design rationale see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 1. Connecting to the Pi

### SSH

```bash
ssh vexy@vexy.local
# or by IP if mDNS is not resolving
ssh vexy@<pi-ip-address>
```

If the hostname `vexy.local` does not resolve, check that `avahi-daemon` is running on the Pi:

```bash
sudo systemctl status avahi-daemon
```

### Foxglove Browser UI

Foxglove runs headlessly on the Pi and is accessed from any browser on the same network. No local install required.

```bash
# On the Pi — install once
sudo apt install -y ros-jazzy-foxglove-bridge
```

`foxglove_bridge` is included in `vexy.launch.py` and starts automatically with the full stack. No separate launch command needed.

Open `https://app.foxglove.dev` in your browser, click **Open Connection**, select **Rosbridge / Foxglove WebSocket**, and enter:

```
ws://vexy.local:8765
```

### RPi Connect (remote access fallback)

RPi Connect provides browser-based remote desktop and shell access without needing the same local network. Enable it once on the Pi:

```bash
sudo snap install rpi-connect
rpi-connect on
```

Then sign in at `connect.raspberrypi.com` with your Raspberry Pi ID account. This is the fallback when SSH over LAN is unavailable (e.g., demo sites with isolated networks).

---

## 2. Launching the Stack

Always source the workspace first:

```bash
source ~/ros2_ws/install/setup.bash
```

### Full stack (camera + VEX bridge + Foxglove)

```bash
ros2 launch vexy_ros vexy.launch.py
```

### With parameter overrides

```bash
# Different serial port (e.g. second USB connection)
ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1

# Higher resolution camera
ros2 launch vexy_ros vexy.launch.py camera_width:=1280 camera_height:=720

# Faster frame rate
ros2 launch vexy_ros vexy.launch.py camera_fps:=30

# Multiple overrides at once
ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1 camera_width:=1280 camera_height:=720 camera_fps:=30
```

### Individual nodes (useful for debugging)

Camera only:

```bash
ros2 run camera_ros camera_node \
  --ros-args \
  -p width:=640 -p height:=480 -p fps:=15 \
  --remap ~/image_raw:=/camera/image_raw \
  --remap ~/camera_info:=/camera/camera_info
```

VEX bridge only (camera not needed):

```bash
ros2 run vexy_ros vex_bridge_node \
  --ros-args \
  -p serial_port:=auto \
  -p baud_rate:=115200
```

---

## 3. Monitoring Topics

### List active topics

```bash
ros2 topic list
```

Expected output when the full stack is running:

```
/camera/camera_info
/camera/image_raw
/camera/image_rect
/apriltag/detections
/align_to_tag/feedback
/align_to_tag/result
/parameter_events
/rosout
/vex/cmd
/vex/ack
/vex/telemetry
/vex/bridge_status
```

### Check frame rate

```bash
ros2 topic hz /camera/image_raw
ros2 topic hz /camera/image_rect
ros2 topic hz /vex/ack
```

### Inspect live messages

```bash
# Watch VEX acks from Brain
ros2 topic echo /vex/ack

# Watch bridge status/faults
ros2 topic echo /vex/bridge_status

# Watch commands being sent (useful when another node publishes them)
ros2 topic echo /vex/cmd
```

---

## 4. Sending Commands to the VEX Brain

Publish directly to `/vex/cmd` using `ros2 topic pub`. All packets require `v`, `seq`, `type`, and `sent_ms`.

### Stop

```bash
ros2 topic pub --once /vex/cmd std_msgs/String \
  '{"data": "{\"v\":1,\"seq\":1,\"type\":\"cmd\",\"cmd\":\"stop\",\"sent_ms\":0,\"ttl_ms\":200}"}'
```

### Drive forward (vx = 0.2 m/s)

```bash
ros2 topic pub --once /vex/cmd std_msgs/String \
  '{"data": "{\"v\":1,\"seq\":2,\"type\":\"cmd\",\"cmd\":\"drive\",\"sent_ms\":0,\"ttl_ms\":200,\"vx\":0.2,\"vy\":0.0,\"omega\":0.0}"}'
```

### Turn left (omega = 0.4 rad/s)

```bash
ros2 topic pub --once /vex/cmd std_msgs/String \
  '{"data": "{\"v\":1,\"seq\":3,\"type\":\"cmd\",\"cmd\":\"turn\",\"sent_ms\":0,\"ttl_ms\":200,\"omega\":0.4}"}'
```

### Set goal

```bash
ros2 topic pub --once /vex/cmd std_msgs/String \
  '{"data": "{\"v\":1,\"seq\":4,\"type\":\"cmd\",\"cmd\":\"set_goal\",\"sent_ms\":0,\"ttl_ms\":200,\"goal\":\"collect_cube\"}"}'
```

**Velocity limits enforced by `vex_bridge_node`:**
- `vx`, `vy`: clamped to ±0.35 m/s
- `omega`: clamped to ±0.60 rad/s
- `ttl_ms`: clamped to 1–5000 ms

The Brain will echo an ack on `/vex/ack`:

```json
{"v":1,"ack":2,"type":"ack","state":"ok","recv_ms":124,"battery_mv":12300,"heading_deg":45.2,"fault":null}
```

---

## 5. Recording a Session and Exporting for LLM Analysis

### Align to a visible tag

The `align_to_tag` node is a bounded local-control skill. It does not call an LLM. It refuses to start unless a current configured tag and current VEX ack are both present.

```bash
ros2 topic echo /align_to_tag/result --once &
ros2 topic pub --once /align_to_tag/goal std_msgs/String \
  '{"data":"{\"tag_id\":0,\"target_distance_m\":0.45,\"yaw_tolerance_rad\":0.05,\"lateral_tolerance_m\":0.03,\"timeout_s\":5.0,\"max_step_ms\":150}"}'
```

Cancel:

```bash
ros2 topic pub --once /align_to_tag/cancel std_msgs/String '{"data":"operator_cancel"}'
```

### Record all topics

```bash
ros2 bag record -a -o session_$(date +%Y%m%d_%H%M%S)
```

This creates a directory (e.g. `session_20260623_143000/`) containing the bag files and metadata.

### Stop recording

Press `Ctrl+C` in the recording terminal.

### Inspect a bag

```bash
ros2 bag info session_20260623_143000/
```

### Play back a bag (for offline testing)

```bash
ros2 bag play session_20260623_143000/
```

### Export topics to JSON for LLM analysis

Extract the telemetry and command topics to newline-delimited JSON:

```bash
# Install ros2_bag_exporter if not present, or use the built-in convert
ros2 bag convert \
  --input session_20260623_143000/ \
  --output-options '{"output_bags": [{"uri": "session_converted", "serialization_format": "cdr"}]}'
```

For a simpler one-liner extraction of string topics (works without plugins):

```bash
ros2 bag play session_20260623_143000/ &
ros2 topic echo /vex/ack --no-arr > ack.txt
ros2 topic echo /vex/bridge_status --no-arr > bridge_status.txt
ros2 topic echo /align_to_tag/result --no-arr > align_result.txt
ros2 topic echo /vex/cmd --no-arr > commands.txt
```

Combine into a structured payload and pass to the Claude API for self-model revision. See the LLM feedback loop in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 6. AprilTag Workspace Localization

The launch file starts `image_proc` rectification and `apriltag_ros` by default. The detector consumes `/camera/image_rect` plus `/camera/camera_info`, then publishes `/apriltag/detections` and `/tf`.

Before accepting tag pose as proof, replace `config/imx708_wide_640x480.yaml` with measured Camera Module 3 calibration.

### Calibrate/load Camera Module 3

Headless over SSH, using an 8x6 inner-corner checkerboard with 25 mm squares:

```bash
mkdir -p /home/vexy/calibration/imx708_wide_640x480_samples
ros2 run vexy_ros vexy_calibrate_camera \
  --cols 8 --rows 6 --square-m 0.025 \
  --samples 25 \
  --out /home/vexy/calibration/imx708_wide_640x480.yaml \
  --preview-dir /home/vexy/calibration/imx708_wide_640x480_samples
```

Move the checkerboard through the frame until the command writes the YAML, then
relaunch with a URL:

```bash
ros2 launch vexy_ros vexy.launch.py \
  camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml
```

For the persistent `vexy-ros-stack.service`, put the same launch argument in a
user-systemd drop-in and restart the service:

```ini
# /home/vexy/.config/systemd/user/vexy-ros-stack.service.d/20-measured-camera-info.conf
[Service]
ExecStart=
ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && source /home/vexy/ros2_ws/install/setup.bash && exec ros2 launch vexy_ros vexy.launch.py camera_fps:=30 serial_port:=auto camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml'
```

```bash
systemctl --user daemon-reload
systemctl --user restart vexy-ros-stack.service
```

### Verify

```bash
ros2 topic hz /camera/image_rect
ros2 topic echo /camera/camera_info --once | grep -E 'k:|p:'
ros2 topic echo /apriltag/detections --once
ros2 topic echo /tf --once
```

`detections: []` means the AprilTag detector is running but no configured tag is
visible enough in the rectified frame. Put the printed tag back in view before
debugging `scene_map_node` or motion behavior.

The default config expects tag family `36h11`, tag ID `0`, physical size `0.200` m, and frame name `tag36h11_0`.
`/apriltag/detections` carries tag IDs/corners; `scene_map_node` uses `/tf`
for the pose transform that anchors `/vision/scene_map`.

---

## 7. Adding yolo_ros for Object Detection

`yolo_ros` is not available via apt for Jazzy and must be built from source.

### Clone into the workspace

```bash
cd ~/ros2_ws/src
git clone --depth=1 https://github.com/mgonzs13/yolo_ros.git
```

### Install Python dependencies

```bash
cd ~/ros2_ws/src/yolo_ros
pip install -r requirements.txt --break-system-packages
```

### Build

```bash
cd ~/ros2_ws
colcon build --packages-select yolo_ros --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

### Add to vexy.launch.py

```python
Node(
    package="yolo_ros",
    executable="yolo_node",
    name="yolo",
    parameters=[{
        "model": "yolov8n.pt",
        "input_image_topic": "/camera/image_raw",
        "threshold": 0.5,
        "device": "cpu",  # change to "cuda:0" if GPU available
    }],
),
```

### Verify

```bash
ros2 topic echo /yolo/detections
```

---

## 8. Foxglove Panel Setup

After connecting to `ws://vexy.local:8765`:

### Image panel (camera feed)

1. Click **+** to add a panel → select **Image**.
2. Set **Topic** to `/camera/image_raw`.
3. The camera stream appears live at the configured FPS.

### Raw Messages panel (VEX bridge)

1. Click **+** → select **Raw Messages**.
2. Set **Topic** to `/vex/ack`, `/vex/telemetry`, or `/vex/bridge_status`.
3. Ack, telemetry, and bridge status records are displayed as formatted JSON.

### Raw Messages panel (commands)

1. Duplicate the Raw Messages panel.
2. Set **Topic** to `/vex/cmd`.
3. Useful for confirming that a publishing node (e.g. the LLM loop) is sending correct packets.

### Saving a layout

Click the layout name at the top → **Save layout** → give it a name (e.g. `vexy-default`). Layouts persist in your Foxglove account and are available from any browser.

---

## 9. Parameter Reference — vexy.launch.py

| Parameter | Default | Description |
|---|---|---|
| `serial_port` | `auto` | USB serial device for V5 Brain; prefers the user/program `if02` device |
| `baud_rate` | `115200` | Serial baud rate — must match PROS firmware |
| `camera_width` | `640` | Camera capture width in pixels |
| `camera_height` | `480` | Camera capture height in pixels |
| `camera_fps` | `15` | Camera frames per second; launch converts this to libcamera `FrameDurationLimits` |
| `camera_frame_id` | `camera_optical_frame` | Frame ID for camera messages |
| `camera_info_url` | package config URL | Calibration URL; must use `file:///...` format |
| `apriltag_config` | package config path | YAML with tag family/ID/size settings |

**`vex_bridge_node` internal parameters** (set via `--ros-args -p` when running the node directly):

| Parameter | Default | Description |
|---|---|---|
| `serial_port` | `auto` | Passed through from launch arg |
| `baud_rate` | `115200` | Passed through from launch arg |
| `serial_timeout` | `0.1` | Serial read/write timeout in seconds |
| `ack_timeout_s` | `0.4` | Pending command ack timeout |
| `telemetry_stale_s` | `2.0` | Bridge status threshold for missing/stale telemetry samples |

**Velocity clamp constants** (code-level, not launch parameters):

| Constant | Value | Applies to |
|---|---|---|
| `MAX_LINEAR` | `0.35` m/s | `vx`, `vy` in `drive` commands |
| `MAX_OMEGA` | `0.60` rad/s | `omega` in `drive` and `turn` commands |
| `DEFAULT_TTL_MS` | `200` ms | Default `ttl_ms` if not specified |
| `HEARTBEAT_INTERVAL_S` | `0.15` s | Idle threshold before auto-heartbeat fires |
