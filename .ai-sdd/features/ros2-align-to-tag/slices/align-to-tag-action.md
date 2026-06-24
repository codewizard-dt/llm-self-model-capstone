# Slice: align-to-tag-action

| Field | Value |
|---|---|
| Feature | ros2-align-to-tag |
| Stack | coprocessor |
| Depends on | bridge-demux-and-faults, camera-rectified-tags |

## What this slice delivers

Implement the first bounded ROS local-control skill: `AlignToTag`. Given a visible configured tag, the action reads tag pose/error, checks bridge health, sends short fixed-grammar VEX commands, and stops when alignment tolerance is reached or a typed failure occurs. Codex/LLM calls are not part of the control loop.

## Scope

- Add a minimal action/skill surface for `AlignToTag` in `robot/ros2-runtime`.
- A custom ROS interface package is allowed here if it makes the action contract clearer than untyped string topics; it remains a transport binding, not a durable schema source.
- Subscribe to the AprilTag pose/TF produced by `camera-rectified-tags`.
- Subscribe to bridge ack/status/fault topics from `bridge-demux-and-faults`.
- Publish action feedback with:
  - tag visibility/confidence where available
  - yaw error
  - lateral error
  - distance error or stand-off estimate where available
  - last command/ack state
  - safety/fault state
- Send only fixed-grammar bounded commands (`drive`, `turn`, `stop`, heartbeat as needed).
- Clamp all command magnitudes and durations on the Pi side before sending; Brain clamps/watchdog remain authoritative.
- Stop on success, timeout, cancel, bridge fault, stale tag pose, stale ack, or serial fault.
- Add fake tag/bridge tests that prove the controller converges, fails explicitly, and stops on fault.

## Suggested action shape

Goal fields should cover at least:

- `tag_id`
- `target_distance_m`
- `yaw_tolerance_rad`
- `lateral_tolerance_m`
- `timeout_s`
- `max_step_ms`

Result fields should cover at least:

- `success`
- `reason`
- `final_yaw_error_rad`
- `final_lateral_error_m`
- `final_distance_error_m`
- `fault`

Exact field names can be adjusted during implementation to match ROS interface conventions.

## Acceptance

1. `AlignToTag` refuses to start unless tag pose and bridge health are current.
2. With fake decreasing yaw/lateral error, the action reaches success and sends a final stop.
3. With stale tag pose, stale ack, serial fault, timeout, or cancellation, the action returns explicit failure/cancel and sends stop when possible.
4. Every outbound movement command is bounded by configured max magnitude and duration.
5. No LLM/API/Codex call occurs during action execution.
6. Unit tests cover success, timeout, stale pose, bridge fault, cancel, and command clamping.
7. The runbook includes the command to invoke the action on a visible printed tag.

## Out of scope

- Open-ended online-control harness.
- MCP tools.
- Object approach/acquisition/place behavior.
- Learning or updating the self-model during the action.
