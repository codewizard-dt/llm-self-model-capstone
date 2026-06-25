# Verification Checklist

Run these checks in order after starting the stack.

---

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
`scene_map_node` uses the `/tf` transform, not the detection array, for pose.

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

`/vex/ack` proves the Brain is receiving heartbeats/commands. `/vex/telemetry` should publish separately and include `motion_enabled`, `drive_ports_ok`, `motor_ports`, and `motor_samples` for the left/right drive motors when the guarded PROS bridge is loaded.

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

### 2.8 Guarded tag approach + scan proof

Only run this after 2.4 through 2.7 are green and the robot has clear floor space.
Record the proof first:

```bash
proof=~/proof/tag-approach-scan-$(date +%Y%m%d-%H%M%S)
mkdir -p "$proof"
ros2 bag record -s mcap -o "$proof/mcap" \
  /tf /apriltag/detections /vision/scene_map /vex/cmd /vex/ack /vex/telemetry /vex/bridge_status
```

Then run one bounded packaged proof from another sourced shell:

```bash
proof=~/proof/tag-approach-scan-<timestamp-from-recording-shell>
ros2 run vexy_ros vexy_tag_action_proof \
  --mode visual-one-foot-scan \
  --summary-out "$proof/summary.json"
```

Expected: the summary reports `approach_reached_target: true`, `/vex/ack`
reports `state:"ok"`, `/vex/telemetry` returns zero drive velocity after the
stop, and `/vision/scene_map`/`/tf` show the visible tag IDs observed during the
scan.

For scan-only tag visibility checks:

```bash
proof=~/proof/tag-approach-scan-<timestamp-from-recording-shell>
ros2 run vexy_ros vexy_tag_action_proof \
  --mode scan-only \
  --scan-duration-s 20 \
  --summary-out "$proof/scan-summary.json"
```

### 2.9 Foxglove bridge reachable

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

### 2.10 Scene map proof

The scene map turns the fixed AprilTag workspace layout into robot/object map
coordinates. The default map is `config/maps/table-grab-toss-v1.json`, matching
the wiki-backed 150 cm x 200 cm arena with 200 mm tag36h11 tags. For the Gen0
50 x 108 in arena from PR #20, launch with `VEXY_MAP=gen0-grab-toss-v1` or pass
the installed `workspace_map_path` explicitly.

- tag `0`: bin
- tag `1`: ball staging
- tag `2`: home

With a fixed anchor tag visible:

```bash
ros2 topic echo /tf --once
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
