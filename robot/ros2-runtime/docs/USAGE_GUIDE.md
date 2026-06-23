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
/parameter_events
/rosout
/vex/cmd
/vex/telemetry
```

### Check frame rate

```bash
ros2 topic hz /camera/image_raw
ros2 topic hz /vex/telemetry
```

### Inspect live messages

```bash
# Watch VEX telemetry (acks from Brain)
ros2 topic echo /vex/telemetry

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

The Brain will echo an ack on `/vex/telemetry`:

```json
{"v":1,"ack":2,"type":"ack","state":"ok","recv_ms":124,"battery_mv":12300,"heading_deg":45.2,"fault":null}
```

---

## 5. Recording a Session and Exporting for LLM Analysis

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
ros2 topic echo /vex/telemetry --no-arr > telemetry.txt
ros2 topic echo /vex/cmd --no-arr > commands.txt
```

Combine into a structured payload and pass to the Claude API for self-model revision. See the LLM feedback loop in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 6. Adding apriltag_ros for Workspace Localization

### Install

```bash
sudo apt install -y ros-jazzy-apriltag-ros
```

### Add to vexy.launch.py

Insert the following `Node` block into the `LaunchDescription` list in `launch/vexy.launch.py`:

```python
Node(
    package="apriltag_ros",
    executable="apriltag_node",
    name="apriltag",
    remappings=[
        ("image_rect", "/camera/image_raw"),
        ("camera_info", "/camera/camera_info"),
    ],
    parameters=[{
        "family": "36h11",
        "size": 0.200,  # tag physical size in metres (200 mm tags)
    }],
),
```

### Verify

```bash
ros2 topic list | grep detections
ros2 topic echo /detections
```

The node publishes `apriltag_msgs/AprilTagDetectionArray` on `/detections` with calibration-aware 6-DOF poses. Tag family `36h11` matches the printed tags in `raw/research/apriltag-prints/`.

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

### Raw Messages panel (VEX telemetry)

1. Click **+** → select **Raw Messages**.
2. Set **Topic** to `/vex/telemetry`.
3. Each ack from the Brain is displayed as formatted JSON.

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
| `camera_fps` | `15` | Camera frames per second |

**`vex_bridge_node` internal parameters** (set via `--ros-args -p` when running the node directly):

| Parameter | Default | Description |
|---|---|---|
| `serial_port` | `auto` | Passed through from launch arg |
| `baud_rate` | `115200` | Passed through from launch arg |
| `serial_timeout` | `0.4` | Serial read/write timeout in seconds |

**Velocity clamp constants** (code-level, not launch parameters):

| Constant | Value | Applies to |
|---|---|---|
| `MAX_LINEAR` | `0.35` m/s | `vx`, `vy` in `drive` commands |
| `MAX_OMEGA` | `0.60` rad/s | `omega` in `drive` and `turn` commands |
| `DEFAULT_TTL_MS` | `200` ms | Default `ttl_ms` if not specified |
| `HEARTBEAT_INTERVAL_S` | `0.15` s | Idle threshold before auto-heartbeat fires |
