# vexy_ros — ROS 2 Jazzy Runtime

ROS 2 Jazzy coprocessor stack for the Raspberry Pi 5 (`vexy`). Replaces `robot/pi-runtime` (Bookworm + picamera2).

**What it does:** Runs two nodes on the Pi — a camera pipeline publishing raw frames from the Camera Module 3, and a serial bridge forwarding JSON command packets to the VEX V5 Brain. The bridge publishes command acknowledgements, telemetry samples, and bridge fault/status separately so serial proof is not confused with motion proof. Foxglove Studio connects over WebSocket for real-time visualization, and `ros2 bag` captures sessions for the LLM feedback loop.

---

## Hardware Requirements

| Component | Detail |
|-----------|--------|
| SBC | Raspberry Pi 5 (hostname `vexy`, reachable as `vexy.local`) |
| Camera | Raspberry Pi Camera Module 3 Wide (IMX708 sensor, detected as `imx708_wide`) |
| Robot brain | VEX V5 Brain connected via USB (auto-detected, prefers the user serial interface `if02`) |
| OS | Ubuntu 24.04 LTS (not Raspberry Pi OS — ROS 2 Jazzy requires Ubuntu) |

---

## Prerequisites

### OS & ROS 2

Ubuntu 24.04 LTS with ROS 2 Jazzy installed:

```bash
# Add ROS 2 apt repo (one-time)
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list

sudo apt update
sudo apt install -y ros-jazzy-ros-base ros-dev-tools
```

### noble-updates repo (required — do not skip)

Without the `noble-updates` apt repo, `bzip2` has a version conflict that blocks `build-essential` from installing. This is a known Ubuntu 24.04 packaging issue on the Pi 5.

```bash
# Verify it is enabled (should already be present on fresh Ubuntu 24.04 images)
grep -r noble-updates /etc/apt/sources.list /etc/apt/sources.list.d/
# If missing, add it:
sudo add-apt-repository "deb http://ports.ubuntu.com/ubuntu-ports noble-updates main restricted universe multiverse"
sudo apt update
```

### User groups

The user running ROS nodes must be in the `video` and `render` groups for libcamera hardware access:

```bash
sudo usermod -aG video,render $USER
# Log out and back in (or reboot) for the groups to take effect
groups  # should include video and render
```

---

## Quick Start

### Option A — automated bootstrap (recommended)

Run the setup script once after Ubuntu 24.04 + ROS 2 Jazzy are installed. It clones dependencies, builds the workspace, and links `vexy_ros` from this repo:

```bash
# On the Pi, after cloning the capstone repo
bash robot/ros2-runtime/scripts/setup_pi.sh
```

Then launch the full stack:

```zsh
source /opt/ros/jazzy/setup.zsh
source ~/ros2_ws/install/setup.zsh
ros2 launch vexy_ros vexy.launch.py
```

Use `setup.bash` instead of `setup.zsh` when running the same commands from bash.

### Option B — one-liner verify after setup

```zsh
source /opt/ros/jazzy/setup.zsh
source ~/ros2_ws/install/setup.zsh
ros2 topic hz /camera/image_raw   # should show ~15 Hz (default) or ~30 Hz (configured)
ros2 topic hz /camera/image_rect  # rectified stream after calibration load
ros2 topic echo /apriltag/detections --once  # with tag36h11 id 0 visible
ros2 topic echo /vex/ack --once   # should show heartbeat/command acks from Brain
ros2 topic echo /vex/bridge_status --once  # bridge state/faults when present
```

### Multi-ball scene demo profile

Use the demo profile when the goal is perception/scene-model proof rather than
motor behavior. It enables the HSV yellow-ball detector, raises the detection
cap for multi-ball scenes, keeps YOLO disabled, and publishes the LLM-facing
scene contract:

```bash
ros2 launch vexy_ros vexy_demo_scene.launch.py
ros2 topic echo /vision/object_tracks --once
ros2 topic echo /vision/agent_scene --once
```

If a measured floor-projection setup is available, pass the calibrated mount
height/pitch explicitly:

```bash
ros2 launch vexy_ros vexy_demo_scene.launch.py \
  floor_projection_enabled:=true \
  camera_height_m:=0.35 \
  camera_pitch_rad:=0.45
```

Capture benchmark proof for a five-ball scene without commanding motion:

```bash
ros2 run vexy_ros vexy_scene_observation_proof \
  --target object:yellow_ball \
  --expected-count 5 \
  --proof-dir /home/vexy/proof/five-balls-001
```

Record the calibration and AprilTag residual surface used by that scene:

```bash
ros2 run vexy_ros vexy_localization_benchmark \
  --map gen0-grab-toss-v1 \
  --samples 30 \
  --camera-info-url file:///home/vexy/ros2_ws/src/vexy_ros/config/imx708_wide_640x360.yaml
```

---

## Manual Step-by-Step Setup

Use this when the script is not available or you need to rebuild selectively.

### 1. Install system dependencies

```bash
sudo apt-get install -y \
    meson ninja-build \
    libssl-dev libgnutls28-dev libboost-dev \
    libglib2.0-dev libpython3-dev pybind11-dev \
    python3-yaml python3-ply \
    libevent-dev libdrm-dev libjpeg-dev \
    libdw-dev libudev-dev \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    libcamera-dev libyaml-dev \
    python3-rosdep \
    ros-jazzy-apriltag-ros \
    ros-jazzy-camera-calibration \
    ros-jazzy-image-proc
```

### 2. Install colcon-meson

Required to build the libcamera meson project inside a colcon workspace:

```bash
pip install colcon-meson --break-system-packages
```

### 3. Create workspace and clone sources

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# RPi libcamera fork — upstream does NOT support IMX708 (Camera Module 3)
git clone --depth=1 https://github.com/raspberrypi/libcamera.git

# camera_ros — thin ROS 2 wrapper around libcamera
git clone --depth=1 https://github.com/christianrauch/camera_ros.git

# vexy_ros — symlink from this repo (avoids duplicating sources)
ln -s /path/to/capstone/robot/ros2-runtime vexy_ros
```

### 4. Run rosdep

```zsh
cd ~/ros2_ws
source /opt/ros/jazzy/setup.zsh

sudo rosdep init   # skip if already done
rosdep update --include-eol-distros -q
rosdep install --from-paths src --ignore-src -y --skip-keys=libcamera
```

### 5. Build

```bash
colcon build \
    --packages-select libcamera camera_ros vexy_ros \
    --cmake-args -DCMAKE_BUILD_TYPE=Release \
    --event-handlers console_direct+
```

Build time on Pi 5: ~8–12 min (libcamera dominates).

### 6. Source and verify

```zsh
source ~/ros2_ws/install/setup.zsh

# Smoke-test camera
ros2 run camera_ros camera_node &
ros2 topic hz /camera/image_raw
# expect: average rate: ~15.000 Hz
```

---

## Node Reference

### Launched by `vexy.launch.py`

| Node name | Package | Role |
|-----------|---------|------|
| `camera` | `camera_ros` | Camera Module 3 → /camera/image_raw + /camera/camera_info |
| `camera_rectify` | `image_proc` | /camera/image_raw + /camera/camera_info → /camera/image_rect |
| `apriltag` | `apriltag_ros` | /camera/image_rect + /camera/camera_info → /apriltag/detections + /tf |
| `scene_map` | `vexy_ros` | /tf tag poses + workspace map → /vision/scene_map |
| `yolo_ncnn` | `vexy_ros` | Optional YOLO NCNN inference over /camera/image_rect → /vision/object_detections |
| `yellow_ball_detector` | `vexy_ros` | Lightweight HSV yellow ball detector → /vision/object_detections |
| `object_overlay` | `vexy_ros` | /camera/image_rect + /vision/object_detections → /vision/object_overlay for Foxglove |
| `object_indication` | `vexy_ros` | Object boxes + /camera/camera_info → /vision/object_indications |
| `object_track` | `vexy_ros` | /vision/object_indications → stable /vision/object_tracks |
| `agent_scene` | `vexy_ros` | Scene map + tracks + bridge/telemetry → compact /vision/agent_scene for the LLM harness |
| `task_plan` | `vexy_ros` | /vision/scene_map + target request → /task_plan/current |
| `vexy_operator` | `vexy_ros` | Sole runtime command authority: /operator/command + live state → /vex/cmd |
| `vex_bridge` | `vexy_ros` | USB serial ↔ /vex/cmd + /vex/ack + /vex/telemetry + /vex/bridge_status |
| `foxglove_bridge` | `foxglove_bridge` | WebSocket bridge at port 8765 for Foxglove Studio |

### Topics

| Topic | Type | Direction | Description |
|-------|------|-----------|-------------|
| `/camera/image_raw` | `sensor_msgs/Image` | pub (camera) | Raw frames at configured FPS |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | pub (camera) | Calibration/intrinsics loaded from `camera_info_url` |
| `/camera/image_rect` | `sensor_msgs/Image` | pub (camera_rectify) | Rectified frames from `image_proc` |
| `/apriltag/detections` | `apriltag_msgs/AprilTagDetectionArray` | pub (apriltag) | Tag IDs/corners from rectified frames |
| `/tf` | `tf2_msgs/TFMessage` | pub (apriltag), sub (scene_map) | Tag transforms when pose estimation succeeds |
| `/vision/object_detections` | `std_msgs/String` | pub (yolo_ncnn), sub (object_indication) | JSON YOLO NCNN boxes in image coordinates |
| `/vision/object_overlay` | `sensor_msgs/Image` | pub (object_overlay) | Rectified camera stream annotated with the latest object boxes |
| `/vision/object_indications` | `std_msgs/String` | pub (object_indication/operator), sub (scene_map) | JSON object hints in camera-relative coordinates |
| `/vision/object_tracks` | `std_msgs/String` | pub (object_track), sub (scene_map, agent_scene) | Stable tracked objects with candidate/confirmed/stale states, ages, uncertainty, and range source |
| `/vision/scene_map` | `std_msgs/String` | pub (scene_map) | JSON robot/tag/object coordinates in the active workspace map |
| `/vision/agent_scene` | `std_msgs/String` | pub (agent_scene) | Compact LLM-facing scene summary with robot pose confidence, tracked objects, and non-dispatching affordances |
| `/task_plan/request` | `std_msgs/String` | sub (task_plan) | JSON target request, e.g. `tag:0`, `object:yellow_ball`, or `survey:all` |
| `/task_plan/current` | `std_msgs/String` | pub (task_plan), sub (operator/user) | JSON bounded plan. Dispatchable steps are executed through `/operator/command`; object plans remain map targets until object motion is proven. |
| `/operator/command` | `std_msgs/String` | sub (operator) | JSON operator action such as `align_to_tag`, `survey_scan`, `run_routine`, `move_to_tag`, or manipulator commands |
| `/operator/status` | `std_msgs/String` | pub (operator) | JSON operator state, localization summary, known tags, object categories, and held-object state |
| `/operator/events` | `std_msgs/String` | pub (operator) | JSON operator event stream |
| `/operator/results` | `std_msgs/String` | pub (operator) | Contract-shaped result lines for operator actions |
| `/align_to_tag/feedback` | `std_msgs/String` | pub (operator) | JSON feedback with tag errors, ack state, and fault state |
| `/align_to_tag/result` | `std_msgs/String` | pub (operator) | JSON result with success/failure reason |
| `/survey/feedback` | `std_msgs/String` | pub (operator) | JSON feedback with elapsed time, observed tags, ack state, and fault state |
| `/survey/result` | `std_msgs/String` | pub (operator) | JSON result with success/failure reason and observed tag IDs |
| `/vex/cmd` | `std_msgs/String` | sub (vex_bridge) | JSON command packet to Brain |
| `/vex/ack` | `std_msgs/String` | pub (vex_bridge) | JSON ack from Brain, keyed by `ack` sequence |
| `/vex/telemetry` | `std_msgs/String` | pub (vex_bridge) | JSON telemetry/sample/event records from Brain |
| `/vex/bridge_status` | `std_msgs/String` | pub (vex_bridge) | JSON bridge status/fault records |

### Wire protocol (v1)

**Command** (`/vex/cmd`):
```json
{"v":1,"seq":1,"type":"cmd","cmd":"drive","sent_ms":123,"ttl_ms":200,"vx":0.1,"vy":0.0,"omega":0.0}
```

Supported `cmd` values: `stop`, `drive`, `turn`, `set_goal`, `routine`

Brain routine command:
```json
{"v":1,"seq":2,"type":"cmd","cmd":"routine","sent_ms":123,"ttl_ms":500,"slot":2}
```

Routine slots are fixed Brain-side routines inside the running `pros_bridge`
program, not separate VEXos user-program upload slots:

| Slot | Routine | Requires |
|------|---------|----------|
| 2 | `spin_720` — bounded 720 degree in-place spin | drive ports 1 and 10 |
| 3 | `arm_full_cycle` — arm up to the bounded top target and back down | arm port 8 |
| 4 | `one_foot_forward_back` — one foot forward, pause, one foot back | drive ports 1 and 10 |

**Ack** (`/vex/ack`):
```json
{"v":1,"ack":1,"type":"ack","state":"ok","recv_ms":124,"battery_mv":12300,"motion_enabled":true,"drive_ports_ok":true,"arm_port_ok":true,"routine_active":false,"routine_slot":null,"motor_ports":[1,3,8,10],"fault":null}
```

**Telemetry** (`/vex/telemetry`):
```json
{"v":1,"type":"telemetry","motion_enabled":true,"drive_ports_ok":true,"motor_samples":[{"device":"left_drive","subsystem":"drivetrain","sample_ms":1200,"values":{"position_deg":10.0,"velocity_rpm":0.0,"current_amp":0.0,"power_w":0.0,"torque_nm":0.0,"efficiency_pct":0.0,"temperature_c":23.0}}]}
```

The guarded V5 firmware accepts `drive`/`turn` only when the expected drive ports
are present. It stops on command TTL expiry, watchdog expiry, explicit `stop`, or
estop.

`routine` is accepted only for slots `2`, `3`, and `4`. The Brain rejects a
routine while another routine is active (`fault:"busy"`) and cancels any active
routine on `stop`, watchdog loss, or estop.

Ack records are command acknowledgements; use `/vex/telemetry` for streaming
health and motor-sample proof. Task-file outlines add a stricter sequencing
layer inside `vexy_operator`: `grab`, `lift`, and `release` send once, remain
the active outline step through their duration plus settle time, and only then
allow the next outline step to run.

**Bridge status** (`/vex/bridge_status`):
```json
{"v":1,"type":"bridge_status","state":"fault","reason":"missing_ack","seq":42,"message":"no ack received before the bridge timeout"}
```

**Heartbeat:** `vex_bridge_node` automatically sends a heartbeat every 150 ms when no command arrives. This keeps the V5 Brain's watchdog alive and prevents an automatic motor stop. You do not need to send heartbeats from your controller.

**Velocity limits (enforced in node):**
- Linear (`vx`, `vy`): ±0.35 m/s
- Angular (`omega`): ±0.6 rad/s
- `ttl_ms` clamped to [1, 5000]

---

## Launch File

```bash
# Default launch (640×480 @ 15 Hz, auto-detected V5 user serial @ 115200)
ros2 launch vexy_ros vexy.launch.py

# Override serial port (e.g. if Brain appears on ACM1)
ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1

# Higher resolution
ros2 launch vexy_ros vexy.launch.py camera_width:=1280 camera_height:=720

# Smooth streaming profile
ros2 launch vexy_ros vexy.launch.py camera_fps:=15

# Combined, with measured calibration override
ros2 launch vexy_ros vexy.launch.py \
    serial_port:=auto \
    baud_rate:=115200 \
    camera_width:=1280 camera_height:=720 camera_fps:=15 \
    camera_info_url:=file:///home/vexy/calibration/imx708_wide_1280x720.yaml

# Select the Gen0 50x108 in arena map by id
VEXY_MAP=gen0-grab-toss-v1 ros2 launch vexy_ros vexy.launch.py
```

### All launch arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `serial_port` | `auto` | Serial device for V5 Brain; prefers `/dev/serial/by-id/*VEX*if02` |
| `baud_rate` | `115200` | Serial baud rate |
| `camera_width` | `640` | Frame width in pixels |
| `camera_height` | `480` | Frame height in pixels |
| `camera_fps` | `15` | Target frame rate, converted to `FrameDurationLimits` because libcamera exposes frame timing as duration |
| `camera_frame_id` | `camera_optical_frame` | Frame ID stamped into camera messages |
| `camera_info_url` | package config URL | Must be a URL such as `file:///...`; replace the starter file with measured calibration before tag-pose proof |
| `apriltag_config` | package config path | YAML for tag family, ID, frame name, and physical size |
| `workspace_map_name` | `VEXY_MAP` or `gen0-grab-toss-v1` | Map id under package `config/maps`; use `gen0-grab-toss-v1` for the 50 x 108 in arena |
| `workspace_map_path` | derived from `workspace_map_name` | Explicit workspace map JSON path; overrides `workspace_map_name` |
| `camera_in_robot_json` | `{"x_m":0.0,"y_m":0.0,"yaw_rad":0.0}` | Measured camera pose in the robot body frame |
| `yolo_enabled` | `false` | Launch optional in-package YOLO NCNN detector |
| `yolo_model_path` | `VEXY_YOLO_MODEL` or empty | Ultralytics-compatible NCNN export directory |
| `yolo_confidence` | `0.35` | Minimum detector confidence |
| `yolo_nms_iou` | `0.45` | Non-max suppression IoU threshold |
| `yolo_max_hz` | `5.0` | Maximum YOLO inference rate |
| `yolo_classes_json` | `[]` | Optional class-label allowlist |
| `yolo_class_names_json` | `{}` | Optional class id to label mapping, e.g. `{"0":"bin"}` |
| `yolo_input_size` | `640` | Square NCNN input size used for letterbox preprocessing |
| `yolo_input_name` | auto | Override NCNN input blob name when auto-detection is wrong |
| `yolo_output_name` | auto | Override NCNN output blob name when auto-detection is wrong |
| `yellow_ball_detector_enabled` | `false` | Run the lightweight yellow-ball color detector |
| `yellow_ball_max_hz` | `8.0` | Maximum yellow-ball color detection rate |
| `yellow_ball_min_area_px` | `200.0` | Minimum yellow blob area accepted as a ball candidate |
| `yellow_ball_min_circularity` | `0.25` | Minimum contour circularity accepted as a ball candidate |
| `yellow_ball_max_detections` | `1` | Maximum color-detector ball candidates to publish per frame |
| `yellow_ball_h_min` / `yellow_ball_h_max` | `20` / `45` | OpenCV HSV hue range for the yellow ball |
| `yellow_ball_s_min` / `yellow_ball_s_max` | `25` / `255` | OpenCV HSV saturation range for the yellow ball |
| `yellow_ball_v_min` / `yellow_ball_v_max` | `80` / `255` | OpenCV HSV value range for the yellow ball |
| `object_dimensions_json` | built-in defaults | Per-class dimensions used to estimate object depth from boxes |
| `default_object_height_m` | `0.12` | Fallback height for unlisted object classes |
| `object_min_confidence` | `0.35` | Minimum confidence for object projection into the scene map |
| `object_overlay_enabled` | `true` | Publish `/vision/object_overlay` for Foxglove's Image panel |
| `object_overlay_max_detection_age_s` | `0.5` | Keep drawing the latest boxes for this many seconds after each detection message |

Enable NCNN object detection only after the `.param`/`.bin` export and Python
`ncnn` runtime are installed on the Pi:

```bash
ros2 launch vexy_ros vexy.launch.py \
  yolo_enabled:=true \
  yolo_model_path:=/home/vexy/models/yolo11n_ncnn_model \
  yolo_class_names_json:='{"0":"bin"}'
```

The node publishes 2D detections. `object_indication` uses calibrated
`/camera/camera_info` and class dimensions to estimate camera-relative object
positions, which `scene_map` then transforms into map coordinates. This is an
estimate; for precise object coordinates, tag the object or provide a measured
operator indication.

The yellow ball has a first-class label, `yellow_ball`, with a default diameter
of `0.065 m`. The lightweight `yellow_ball_detector` publishes that label even
when no NCNN model is installed. A future NCNN model can also emit
`yellow_ball` or `yellow ball`; both labels are mapped.

---

## Foxglove Studio Debugging

Foxglove provides a browser-based ROS 2 visualizer — useful for inspecting camera frames and telemetry without a desktop environment on the Pi.

```bash
# Install bridge on the Pi (one-time)
sudo apt install -y ros-jazzy-foxglove-bridge
```

Then open **https://app.foxglove.dev** in a browser and connect:

| mDNS available | URL |
|----------------|-----|
| Yes (default) | `ws://vexy.local:8765` |
| No (mDNS fails on some networks) | `ws://10.10.3.4:8765` |

Useful panels: **Image** (subscribe `/camera/image_rect` for clean camera frames or `/vision/object_overlay` for bounding boxes), **Raw Messages** (subscribe `/vision/object_detections`, `/apriltag/detections`, `/vision/scene_map`, `/vex/ack`, `/vex/telemetry`, and `/vex/bridge_status`), **3D** (show `/tf`), **Topic Graph**.

---

## Recording Sessions for the LLM Feedback Loop

For real hardware evidence, `ros2 bag` records all topics to a self-describing
MCAP file for offline replay and audit. The semantic handoff to the downstream
self-modeling components is still `contracts.ContractLine` JSONL exported from
that hardware evidence.

For fixture-backed MVP work, use the repo-level `telemetry-fixtures/` run data
instead. F8, F9, F10, F11, F12, and `make demo` should consume its
`contract.jsonl` directly; the fixture path is not a real robot run and does not
require ROS, hardware, or MCAP. PR #43 provides a useful JSONL baseline with
partial MCAP capture, not proof that the full hardware capture and replay/audit
requirements are complete.

```bash
# Record everything
ros2 bag record -a -o session_$(date +%Y%m%d_%H%M%S)

# Record only camera, vision, plan, and VEX bridge topics (smaller files)
ros2 bag record /camera/image_raw /camera/camera_info /camera/image_rect /apriltag/detections /tf /vision/object_detections /vision/object_indications /vision/scene_map /task_plan/current /align_to_tag/feedback /align_to_tag/result /survey/feedback /survey/result /vex/cmd /vex/ack /vex/telemetry /vex/bridge_status /operator/annotation \
    -o session_$(date +%Y%m%d_%H%M%S)

# Inspect a recorded bag
ros2 bag info session_20260623_143000/

# Replay a bag (useful for offline debugging)
ros2 bag play session_20260623_143000/
```

Bags are written to the current directory. Transfer them off the Pi via `scp` or mount a USB drive beforehand.

For the semantic handoff into the self-model loop, build a proof bundle JSON
from the bag extracts, then export one or more `ContractLine` records:

```bash
PYTHONPATH=/home/vexy/llm-self-model-capstone/contracts/src:$PYTHONPATH \
  ros2 run vexy_ros vexy_export_contract_jsonl \
  proof/align_to_tag_bundle.json \
  --out proof/contract/session_$(date +%Y%m%d_%H%M%S).jsonl
```

The exporter validates against `contracts.ContractLine` when the `contracts`
package is importable. Use `--no-validate` only for a raw diagnostic dump.

For the standard calibrated tag-action proof, use the single-command wrapper:

```bash
ros2 run vexy_ros vexy_run_calibrated_tag_proof
```

It records MCAP, runs `vexy_tag_action_proof`, writes `summary.json`, and exports
`contract.jsonl` in a timestamped `/home/vexy/proof/` directory.

Dynamic task-plan requests use tag, object, survey, or home targets:

```bash
ros2 topic echo /task_plan/current &
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"tag:0\",\"action\":\"approach\",\"target_distance_m\":0.8,\"dispatch\":true}"}'
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"object:bin\",\"action\":\"inspect\"}"}'
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"object:yellow_ball\",\"action\":\"inspect\"}"}'
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"survey:all\",\"action\":\"survey_all\"}"}'
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"survey:all\",\"action\":\"survey_all\",\"dispatch\":true,\"survey_duration_s\":3.0,\"survey_omega_rad_s\":0.22}"}'
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"routine:2\",\"action\":\"spin_720\",\"dispatch\":true}"}'
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"routine:3\",\"action\":\"arm_full_cycle\",\"dispatch\":true}"}'
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"routine:4\",\"action\":\"one_foot_forward_back\",\"dispatch\":true}"}'
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"home:tag\",\"action\":\"return_home\",\"target_distance_m\":0.45,\"dispatch\":true}"}'
```

Tag and home plans are executed by sending the dispatchable `align_to_tag` step
to `/operator/command`. Home
plans default to AprilTag `2`, the workspace home anchor. Object plans are mapped
but report `object_go_to_pose_controller_not_proven` until a bounded
object/go-to-pose motion skill is implemented and physically verified. Survey
plans execute through the Operator's `survey_scan` action; the controller refuses
to start unless `/vex/ack`, `/vex/telemetry`, and drive safety state are fresh.
Use short `survey_duration_s` / `survey_omega_rad_s` overrides for supervised
checks, then omit them for the default full scan.

Routine plans execute through `/operator/command` with `action:"run_routine"` and do not
require a scene map. Run them only with the same proof discipline as other
motion: fresh `/vex/ack`, fresh `/vex/telemetry`, operator supervision, and an
MCAP recording for the routine.

To capture the no-motion vision/planning proof before a motion check:

```bash
ros2 run vexy_ros vexy_scene_observation_proof
```

This writes `scene_observation_proof.json` under `/home/vexy/proof/` with the
latest detections, object indications, scene map, and task plans for
`object:yellow_ball` plus `survey:all`. It always publishes task requests with
`dispatch:false`.

---

## Common Gotchas

### noble-updates must be enabled

The `bzip2` package in the base `noble` apt repo has a version that conflicts with `build-essential` on the Pi 5. Without `noble-updates`, the entire C/C++ build toolchain fails to install. Always verify this repo is active before troubleshooting build failures.

### User must be in `video` and `render` groups

libcamera opens DRM/V4L2 devices that require group membership. The symptom of missing groups is `camera_node` failing at startup with a permission error on `/dev/video*` or `/dev/dri/*`. Adding groups requires a logout/login or reboot — `newgrp` works for a single shell but is not inherited by the ROS launch process.

### RPi libcamera fork, not upstream

The **upstream** `libcamera` package (`apt install libcamera-dev`) does **not** include the IMX708 IPA (Image Processing Algorithm) needed by Camera Module 3. Using upstream libcamera will result in `camera_node` failing to enumerate any cameras or producing a black stream. The setup script and workspace explicitly clone `https://github.com/raspberrypi/libcamera.git` (the RPi fork) to the workspace so colcon builds it with IMX708 support. Do not `apt install libcamera-dev` and expect it to work with Camera Module 3.

### mDNS vs IP address

`vexy.local` resolves via mDNS for SSH, but **browser-based WebSocket connections (Foxglove) commonly fail with mDNS even when SSH works fine**. If Foxglove shows "Connection failed" with `ws://vexy.local:8765`, switch to the IP address — this was the observed behavior during setup. Check the Pi's current IP with `ip addr show wlan0` and use `ws://<IP>:8765` directly (e.g. `ws://10.10.3.4:8765`).

### Serial port enumeration

The V5 Brain exposes multiple USB CDC interfaces. The program/user serial interface is usually the `if02` by-id symlink, and may map to `/dev/ttyACM1`. Check with:

```bash
ls /dev/ttyACM*
# or
dmesg | grep tty | tail -20
```

The launch file auto-detects the user interface by default. Pass an explicit port such as `serial_port:=/dev/ttyACM1` only when debugging.

### colcon build artifacts are stale after vexy_ros edits

`vexy_ros` is symlinked into the workspace. Colcon does not always detect changes to Python source files via the symlink. If node changes are not taking effect, force a rebuild:

```bash
colcon build --packages-select vexy_ros --event-handlers console_direct+
```

---

## Fallback: picam_ros2

If the RPi libcamera fork fails to build (e.g., meson version incompatibility, missing kernel headers), `picam_ros2` is an alternative camera node that uses the Pi's V4L2 interface directly:

```bash
sudo apt install -y ros-jazzy-v4l2-camera
ros2 run v4l2_camera v4l2_camera_node --ros-args \
    -p video_device:=/dev/video0 \
    -p image_size:=[640,480]
```

Limitations: no hardware ISP, no auto-exposure tuning, lower image quality than the libcamera pipeline. Use only as a debugging fallback.

---

## Repository Layout

```
robot/ros2-runtime/
├── package.xml              # ament_python package descriptor (vexy_ros v0.1.0)
├── setup.py                 # entry point: vex_bridge_node = vexy_ros.vex_bridge_node:main
├── setup.cfg
├── resource/vexy_ros        # ament package marker
├── src/vexy_ros/
│   ├── __init__.py
│   └── vex_bridge_node.py   # serial bridge ROS 2 node
├── launch/
│   └── vexy.launch.py       # launches camera_node + vex_bridge_node
└── scripts/
    └── setup_pi.sh          # one-shot bootstrap (build workspace + deps)
```

## Related

- `robot/pi-runtime/` — legacy Bookworm/picamera2 stack (superseded by this package)
- V5 Brain firmware protocol: see `robot/pi-runtime/` serial protocol documentation
