# Vision Coordinate Map Proof

This is the interop layer between PiCam2/AprilTag vision and the self-model
loop. It follows the wiki references:

- `wiki/knowledge/concepts/apriltag-workspace-layout.md`
- `wiki/knowledge/sources/apriltag-larger-workspace-map.md`

The default map is `config/maps/table-grab-toss-v1.json`: a 150 cm x 200 cm
floor arena with 200 mm `tag36h11` tags.

| Tag | Role | Purpose |
|---|---|---|
| `0` | bin | final throw/score anchor |
| `1` | ball staging | approach/grab anchor |
| `2` | home | return/home re-fix anchor |

## Runtime Surface

`scene_map_node` subscribes to:

- `/apriltag/detections`
- `/tf`
- `/vision/object_indications`

It publishes:

- `/vision/scene_map`

The scene map JSON includes:

- `camera_pose`
- `robot_pose`
- `tags`
- `objects`
- `anchor_tag_ids`
- `observed_tag_ids`

Every pose includes both:

- ROS math fields: `x_m`, `y_m`, `yaw_rad`
- wiki map fields: `x_mm`, `y_mm`, `heading_deg`

## Current Device Status

As of 2026-06-24 on `vexy`:

- PiCam2 calibration captured 25 checkerboard samples and wrote
  `/home/vexy/calibration/imx708_wide_640x480.yaml`.
- `vexy-ros-stack.service` loads the measured calibration through
  `camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml`.
- `/camera/camera_info` now reports measured intrinsics (`fx` about 558.33,
  `fy` about 557.27), not the starter `430/320/240` matrix.
- `/camera/image_rect` publishes at camera rate and `/vex/ack` is green.
- `/apriltag/detections` is currently an empty array because no AprilTag is
  visible in the live camera frame. This is a scene-state blocker, not a
  calibration-load failure.

## Proof Gates

Run these in order. Do not call the stack healthy unless each gate is accounted
for separately.

1. PiCam2 calibration:

```bash
mkdir -p /home/vexy/calibration/imx708_wide_640x480_samples
ros2 run vexy_ros vexy_calibrate_camera \
  --cols 8 --rows 6 --square-m 0.025 \
  --samples 25 \
  --out /home/vexy/calibration/imx708_wide_640x480.yaml \
  --preview-dir /home/vexy/calibration/imx708_wide_640x480_samples
```

Move an 8x6 inner-corner checkerboard through the camera view until all samples
are captured. Relaunch with the measured calibration:

```bash
ros2 launch vexy_ros vexy.launch.py \
  camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml
```

For the persistent Pi service, use a user-systemd drop-in:

```ini
# /home/vexy/.config/systemd/user/vexy-ros-stack.service.d/20-measured-camera-info.conf
[Service]
ExecStart=
ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && source /home/vexy/ros2_ws/install/setup.bash && exec ros2 launch vexy_ros vexy.launch.py camera_fps:=30 serial_port:=auto camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml'
```

Then reload and restart:

```bash
systemctl --user daemon-reload
systemctl --user restart vexy-ros-stack.service
systemctl --user status vexy-ros-stack.service
```

2. Rectification:

```bash
ros2 topic hz /camera/image_rect
ros2 topic echo /camera/camera_info --once | grep -E 'k:|p:'
```

3. AprilTag pose:

```bash
ros2 topic echo /apriltag/detections --once
ros2 topic echo /tf --once
```

`/apriltag/detections` proves detector activity and tag IDs/corners; `/tf`
contains the camera-to-tag transform used by `scene_map_node`.

An empty `detections: []` message means the detector is alive but no configured
tag is visible enough to solve. Put a `tag36h11` tag from the active workspace
map back in the rectified camera view before running scene-map or motion proof.

4. Scene map:

```bash
ros2 topic echo /vision/scene_map --once
```

## Camera Mount Changes

The runtime is intended to be agnostic to camera placement at the task/planning
layer. Plans consume map-space `robot_pose`, tag poses, and object poses, not
hard-coded image positions. The geometry layer still needs truthful transforms:

- Do not re-run checkerboard intrinsics just because the camera mount moved.
- Do update `camera_in_robot_json` when the PiCam2 moves relative to the robot
  center.
- Do re-run checkerboard intrinsics if the camera module, lens/focus,
  resolution, or crop mode changes.
- Do update the workspace map only when the AprilTags themselves move.

Morning mount check:

```bash
ros2 launch vexy_ros vexy.launch.py \
  camera_in_robot_json:='{"x_m":0.12,"y_m":0.0,"yaw_rad":0.0}'
ros2 run vexy_ros vexy_scene_observation_proof
```

The proof is acceptable when the scene map reports stable `robot_pose`, the
visible tag IDs match the active workspace map, and `object:yellow_ball` plus
`survey:all` plans are produced with `dispatch:false`.

5. V5 Brain ack and telemetry:

```bash
ros2 topic echo /vex/ack --once
ros2 topic echo /vex/telemetry --once
ros2 topic echo /vex/bridge_status --once
```

6. MCAP capture:

```bash
ros2 bag record /camera/image_raw /camera/camera_info /camera/image_rect \
  /apriltag/detections /tf /vision/scene_map \
  /align_to_tag/feedback /align_to_tag/result \
  /vex/cmd /vex/ack /vex/telemetry /vex/bridge_status \
  -o proof/rosbags/align_to_tag_$(date +%Y%m%d_%H%M%S)
```

7. Contract JSONL export:

```bash
PYTHONPATH=/home/vexy/llm-self-model-capstone/contracts/src:$PYTHONPATH \
  ros2 run vexy_ros vexy_export_contract_jsonl \
  proof/align_to_tag_bundle.json \
  --out proof/contract/align_to_tag_$(date +%Y%m%d_%H%M%S).jsonl
```

The exporter writes existing `contracts.ContractLine` JSONL. It does not define
a second schema under `robot/ros2-runtime`.
