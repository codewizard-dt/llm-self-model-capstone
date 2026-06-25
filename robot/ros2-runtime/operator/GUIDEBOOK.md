# Vexy Operator Guidebook

The operator is the RPi-side layer one level above the V5 Brain primitives. It
reads live camera, AprilTag, object, and telemetry streams, then emits only the
existing primitive commands to the Brain bridge. The Brain still runs one bridge
program; the Pi decides which primitive to send next.

An operator cannot be constructed without two pieces of context:

- an AprilTag map, loaded from `workspace_map_path` or `tag_anchors_json`
- a measured camera pose in the robot/action frame, loaded from `camera_in_robot_json`
- a frozen `ContractLine` JSON object loaded from `task_contract_json`
- a `task_outline_json` list of operator-method tuples

The loaded AprilTag map defines which tag indexes are available in the current
workspace. The operator ignores fresh detections for unmapped tags and rejects
direct `orient_to_tag(tag_index)` / `move_to_tag(tag_index)` calls when
`tag_index` is not in the map.
On startup it emits `apriltag_map_loaded` with the available tag IDs.

## Primitive Commands

Use these commands as the only direct Brain actions:

| Primitive | Use When | Notes |
| --- | --- | --- |
| `stop` | Motion should end, pause, or fail closed. | Also used for event-driven faults such as `stuck` and `spinout`. |
| `drive` | Move toward or away from a target while correcting heading. | `vx` and `omega` are physically meaningful; `vy` is accepted by the ROS protocol but the Brain drivetrain does not strafe. |
| `turn` | Search for or orient toward a target without forward motion. | Preferred when no fresh target is visible. |
| `grab` | Close/intake the end effector around an object. | The operator reports `grabbed` when manipulator telemetry suggests an object is loaded. |
| `lift` | Raise the end effector for bin entry. | Stops the drivetrain first on the Brain. |
| `release` | Drop the held object. | Stops the drivetrain first on the Brain. |

## Operator Abstractions

These methods are one level above primitives: they combine live sensing with one
primitive command decision, but they do not encode a full mission.

| Abstraction | Inputs Used | Primitive Emitted |
| --- | --- | --- |
| `locate_nearest_apriltag()` | Fresh AprilTag detections from `/tf` and `/vision/scene_map`. | No command if a tag is fresh; otherwise `turn`. |
| `orient_to_tag(tag_index)` | Fresh tag pose in the calibrated robot frame. | `turn` until yaw is within tolerance, then `stop`. |
| `move_to_tag(tag_index)` | Fresh tag pose plus drivetrain telemetry and the loaded map. | `drive` toward the map-derived stand-off pose, `turn` if target is missing, `stop` on arrival or fault. |
| `grab()` | Manipulator telemetry if available. | `grab`; emits `grabbed` when current/velocity indicate a held object. |
| `lift()` | Command timing and telemetry. | `lift`. |
| `release()` | Command timing and telemetry. | `release`. |

`tag_index` is zero-based and must be present in the loaded AprilTag map.
For `move_to_tag`, the user normally does not provide `target_distance_m`.
The operator derives the stand-off from the tag's map role:

- `bin`: `0.38 m`
- `ball_staging`, `ball_loading`, or `ball`: `0.45 m`
- `home`: `0.45 m`
- any other role: operator default `0.45 m`

The stand-off target pose is calculated from the tag anchor pose in the map:
`target_pose = tag_pose + standoff along the tag's facing direction`.
An explicit `target_distance_m` remains available only as a calibration override.

## Task Outline

The task outline contains operator class methods only. Primitive command names
such as `drive`, `turn`, or `stop` are not valid task outline entries.

Each entry is a tuple/list:

```json
["method_name", [required_args], {"optional_kwarg": "value"}]
```

Example:

```json
[
  ["locate_nearest_apriltag", []],
  ["move_to_tag", [1]],
  ["grab", [], {"duration_ms": 700}],
  ["move_to_tag", [0]],
  ["lift", []],
  ["release", []]
]
```

Supported method names are `locate_nearest_apriltag`, `orient_to_tag`,
`move_to_tag`, `grab`, `lift`, and `release`. Ad-hoc SSH commands are accepted
only when their `action` appears in the loaded task outline.

## Vision Input

The operator considers both target pose and object category:

- AprilTags arrive from `/tf` as tag-frame transforms. The node applies the
  configured `camera_in_robot_json` offset so tag poses are in the robot action
  frame, not the camera center.
- Object detections arrive from `/vision/object_detections`; object indications
  arrive from `/vision/object_indications` with estimated forward/left meters.
- `/vision/scene_map` is retained as raw context for tasks that need map-level
  reasoning.

## Localization

The operator tracks its own `map_pose` continuously:

- If any mapped AprilTags are currently visible, pose is recomputed from the
  loaded AprilTag map and the live tag poses. Status reports
  `localization_source:"apriltag"`.
- If no mapped AprilTags are visible but the operator has a previous map pose,
  pose is advanced from known commanded movement (`vx`, `omega`, and command
  TTL). Status reports `localization_source:"dead_reckoning"`.
- If no tag has ever localized the robot, pose remains `null` and status reports
  `localization_source:"unknown"`.

## Telemetry Events

The operator publishes structured JSON on `/operator/events`.

| Event | Meaning |
| --- | --- |
| `apriltag_searching` | The requested tag or nearest tag is not fresh, so the operator sent `turn`. |
| `apriltag_map_loaded` | The operator loaded its workspace map and detected the available tag IDs. |
| `apriltag_located` | A nearest fresh AprilTag was selected. |
| `oriented` | The requested tag is within yaw tolerance and the operator sent `stop`. |
| `arrived` | The requested tag is within distance, lateral, and yaw tolerances. |
| `stuck` | A drive command is active but wheel velocity is unexpectedly low. |
| `spinout` | Wheel velocity is high but visual progress toward the tag is too low. |
| `grabbed` | Manipulator current is elevated while manipulator velocity is low after `grab`. |
| `command_rejected` | An ad-hoc operator command was malformed or unsupported. |
| `pose_estimated` | The operator updated map pose from visible mapped AprilTags. |

The Brain telemetry includes `motor_samples` for left/right drivetrain motors
and, when port 3 is present, `release_motor` with `subsystem:"manipulator"`.
That manipulator sample is what makes `grabbed` and `has_object` possible.

## Contract Results

Every operator method run emits a `ContractLine`-compatible result on
`/operator/results`. The result includes:

- `motor_samples` normalized to the locked motor telemetry shape
- `vision` with `object_detected` and `apriltag_pose` when localized
- `outcome` with method name, success, reason, command, tag index,
  localization source, drive health, and `has_object`
- `source` with telemetry timing and sample count

Raw manipulator telemetry may use `subsystem:"manipulator"`, but contract
results map it to the locked motor contract subsystem `claw`.

## Ad-Hoc Commands From SSH

SSH into the Pi and publish JSON commands to `/operator/command`:

```bash
ros2 topic pub --once /operator/command std_msgs/msg/String \
  "{data: '{\"action\":\"locate_nearest_apriltag\"}'}"

ros2 topic pub --once /operator/command std_msgs/msg/String \
  "{data: '{\"action\":\"orient_to_tag\",\"tag_index\":0}'}"

ros2 topic pub --once /operator/command std_msgs/msg/String \
  "{data: '{\"action\":\"move_to_tag\",\"tag_index\":1}'}"

ros2 topic pub --once /operator/command std_msgs/msg/String \
  "{data: '{\"action\":\"grab\",\"duration_ms\":700}'}"
```

Supported actions are `locate_nearest_apriltag`, `orient_to_tag`,
`move_to_tag`, `grab`, `lift`, and `release`.

`vexy_operator_node` requires a task contract at startup:

```bash
ros2 run vexy_ros vexy_operator_node --ros-args \
  -p workspace_map_path:=/path/to/workspace-map.json \
  -p task_contract_json:='{"schema_version":"1.0","session_id":"deliver-ball","generation":0,"round":0,"task":"deliver_ball","motor_samples":[{"device":"left_drive"}],"predicted":{"success":true},"gap":{"distance_error_m":0.0}}' \
  -p task_outline_json:='[["locate_nearest_apriltag",[]],["move_to_tag",[1]],["grab",[],{"duration_ms":700}],["move_to_tag",[0]],["lift",[]],["release",[]]]'
```

## Composition Rule

Task programs should compose operator abstractions instead of sending raw
primitive packets directly. For example, ball delivery should run:

1. `locate_nearest_apriltag()`
2. `move_to_tag(ball_loading_tag_index)`
3. `grab()`
4. `move_to_tag(bin_tag_index)`
5. `lift()`
6. `release()`

If a step emits `stuck` or `spinout`, the task must stop, save its summary, and
wait for a human or an ad-hoc SSH command.
