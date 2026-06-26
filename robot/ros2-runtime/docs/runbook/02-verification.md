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

Expected: `vexy_ros` appears in output. If not, run `source ~/ros2_ws/install/setup.zsh`
from zsh or `source ~/ros2_ws/install/setup.bash` from bash.

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

If commands are acknowledged but the robot never moves, confirm the correct Brain
program is actually running. `pros upload --after none` only uploads the binary;
it does not start the program. For the current David development workflow, start
Slot 8 manually on the V5 Brain before live operator or delivery tests.

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

If nearest-tag search or reacquisition is too slow during live delivery, tune the
bounded scan/turn speed upward only after the stop-on-cancel, stop-on-timeout,
fresh `/vex/ack`, and fresh `/vex/telemetry` checks above are passing. Faster
search is acceptable; unbounded search is not.

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

### 2.9 Brain routine task-plan proof

Brain routine targets are fixed routine IDs inside the running `pros_bridge`
program. They are not VEX GUI upload slots.

Start with a no-motion planning check:

```bash
ros2 topic echo /task_plan/current &
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"routine:2\",\"action\":\"spin_720\",\"dispatch\":false}"}'
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"routine:3\",\"action\":\"arm_full_cycle\",\"dispatch\":false}"}'
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"routine:4\",\"action\":\"one_foot_forward_back\",\"dispatch\":false}"}'
```

Expected: each plan has `status:"ready"`, step type `brain_routine`, and a
`cmd` payload with `cmd:"routine"` plus the requested slot ID.

Only dispatch a routine with the robot on blocks or clear floor, an operator
present, fresh `/vex/ack`, fresh `/vex/telemetry`, `motion_enabled:true`, and an
MCAP recording that includes `/vex/cmd`, `/vex/ack`, `/vex/telemetry`, and
`/vex/bridge_status`.

### 2.10 Foxglove bridge reachable

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

### 2.11 Scene map proof

The scene map turns the fixed AprilTag workspace layout into robot/object map
coordinates. The default map is `config/maps/gen0-grab-toss-v1.json`, matching
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

Current measured VEXY default from static calibration: the claw capture center is
4.5 in to the robot's right of the camera and 13 in in front of the camera. In
robot-frame coordinates, record that as the default camera/profile offset before
using object indications as pickup approach hints.

To indicate an untagged object in camera-relative coordinates:

```bash
ros2 topic pub --once /vision/object_indications std_msgs/String \
  '{"data":"[{\"name\":\"red_block\",\"forward_m\":0.65,\"left_m\":-0.12,\"confidence\":0.8}]"}'
ros2 topic echo /vision/scene_map --once
```

Expected: `/vision/scene_map` includes an `objects[]` entry with the object pose
transformed into the active workspace map. This is an operator/prototype hint;
the canonical object detector can replace it later.

### 2.12 Static claw and pickup calibration

Use this before live delivery testing when claw semantics, camera offsets, or
pickup thresholds have changed. The robot should be standing still with drive
motion disabled or physically blocked.

1. Start the correct Brain program manually on Slot 8.
2. Start/restart the ROS stack and verify `/vex/ack`, `/vex/telemetry`,
   `/camera/image_rect`, and `/vision/object_detections`.
3. Begin with the claw physically closed. Do not skip the open step in the test;
   the calibration sequence is always closed → open → place ball → close/grab.
4. Command open/release and have the spotter confirm the claw is fully open.
5. Place the ball at the claw mouth in known positions: centered capturable,
   near left rubber band, near right rubber band, and just out of reach.
6. At each placement, capture the live vision/object indication state and
   effector telemetry at that exact moment.
7. Command close/grab only after the ball is in a declared capturable pose, then
   have the spotter confirm whether the claw actually trapped the ball.

Recorded physical findings from the 2026-06-26 calibration session:

- Command semantics must stay physical: close means `grab`; open means
  `release`/open. Do not hide reversed behavior behind wrappers.
- Claw motor telemetry should be named `effector_motor`.
- The claw may over-open into its mechanical stop; watch effector telemetry and
  avoid treating that as a normal successful motion envelope.
- Object-indication distance can be wrong near the claw when the claw or motor
  occludes part of the ball. Use object indications for coarse approach, not as
  final proof that the ball is inside the claw.

### 2.13 Live delivery physical-success check

Software pass/fail is not enough for `vexy_deliver_ball`. A live delivery run is
only physically successful if the spotter observes this sequence:

1. The claw opens before approach.
2. The robot approaches until the ball is inside the capture zone, not several
   inches short.
3. The claw closes/grabs around the ball.
4. The robot travels to the bin/dropoff with the ball still held.
5. The robot opens/releases only at the dropoff.

If the test reports success but the ball was never picked up or never reached the
bin, treat it as a vision/manipulation failure even if command acknowledgements,
tag approach, or summary JSON look successful.
