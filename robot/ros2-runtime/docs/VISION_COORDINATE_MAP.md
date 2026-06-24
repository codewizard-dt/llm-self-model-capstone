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

## Proof Gates

Run these in order. Do not call the stack healthy unless each gate is accounted
for separately.

1. PiCam2 calibration:

```bash
ros2 run camera_calibration cameracalibrator \
  --size 8x6 --square 0.025 \
  image:=/camera/image_raw camera:=/camera
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

4. Scene map:

```bash
ros2 topic echo /vision/scene_map --once
```

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
