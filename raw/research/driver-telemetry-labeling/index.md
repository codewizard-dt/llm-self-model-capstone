---
topic: "$research Can you research if you can output telemetry while I'm driving it with the controller? That would be pretty baller. Figure out a way to get telemetry while I'm driving. And I'll tell you at certain intervals what state the robot's in."
slug: driver-telemetry-labeling
researched: 2026-06-26
sources: [./sources.md]
---

# Research: Driver Telemetry While Using the Controller

> Yes: the V5 Brain can keep emitting telemetry while a human drives with the V5 controller. The cleanest implementation is a new/manual mode in the PROS Brain firmware where the controller loop is the only writer to the drivetrain motors, while a separate telemetry task samples motor/battery/controller fields and prints compact newline-delimited JSON to the V5 user serial port. State labels should be captured on the Pi as timestamped annotation JSONL or a ROS topic, then aligned to the nearest Brain telemetry samples during export.

## Research Questions
- Can PROS read V5 controller input and drive motors while other tasks emit telemetry?
- What telemetry path already exists in this repo, and does it conflict with manual driving?
- How should human state labels be recorded so they align with telemetry and vision data?
- What risks exist around serial bandwidth, task scheduling, and motor command ownership?

## Current State (Codebase)

- `robot/v5-brain/pros_bridge/src/main.cpp` already implements a guarded Brain serial bridge with a `telemetry_task` emitting `type:"telemetry"` JSON records every 500 ms via `printf`/`fflush`, protected by `stdout_mutex` [S1].
- That firmware currently treats the Pi/ROS side as the motion-command owner: `receive_task` parses `cmd` packets, `watchdog_task` stops motors if heartbeats expire, and `opcontrol()` starts receive, routine, watchdog, and telemetry tasks [S1].
- `robot/v5-brain/pros_bridge/README.md` documents the intended split: ack and telemetry are separate record types, and telemetry includes `motor_samples` using the contract exporter field names [S2].
- `robot/pi-runtime/docs/BRAIN_INTERFACE.md` records the physical serial finding: the V5 Brain exposes a system port and a user/program-output port; telemetry is read from the `if02` user port, not the upload/system port [S3].
- `robot/ros2-runtime/src/vexy_ros/bridge_demux.py` already demuxes mixed JSON lines into `ack`, `telemetry`, and `status` events, so a telemetry stream interleaved with other Brain output is already an expected design [S4].
- `robot/ros2-runtime/src/vexy_ros/vex_bridge_node.py` publishes demuxed telemetry as `/vex/telemetry` string messages [S5].
- `robot/ros2-runtime/docs/runbook/03-recording.md` already records `/vex/telemetry` into MCAP alongside camera, AprilTag, scene map, ack, and status topics [S6].
- `robot/ros2-runtime/src/vexy_ros/evidence_export.py` can normalize `motor_samples` from telemetry records into contract-shaped motor samples [S7].

## Key Findings

- PROS supports V5 controller polling in `opcontrol()`: analog stick data is in the range `[-127,127]`, digital buttons are pressed/unpressed values, and examples drive motors directly from controller inputs [S8].
- PROS supports tasks for concurrent repeated work, but repeated task loops must include `delay()`/`task_delay_until()` and shared state needs a clear ownership model or synchronization [S9].
- PROS serial output can be consumed directly if COBS is disabled; this matches the repo's current `pros::c::serctl(SERCTL_DISABLE_COBS, nullptr)` plus newline-delimited JSON design [S10].
- The current repo has already solved the hardest transport problem: the Brain can print `type:"telemetry"` records and the ROS bridge can publish them separately from acks/status [S1, S4, S5].
- For manual driving, the main change is not transport; it is authority. The current bridge watchdog assumes Pi-issued heartbeats. A driver telemetry mode should avoid having the watchdog stop controller-owned motors just because no Pi command is being sent. Instead, the controller loop owns motor writes, and telemetry is read-only [S1, S9].

## Constraints

- Do not have both ROS commands and controller input write drivetrain motors at the same time. PROS warns about synchronization and task responsibility; the safe pattern is one writer for each motor subsystem [S9].
- Keep telemetry compact. The repo has a documented approximate user serial ceiling of 11,520 B/s and already uses 500 ms telemetry in `pros_bridge`; controller state can be added without jumping to high-rate raw logging [S3].
- Filter non-JSON startup output on the reader side. The existing docs note a PROS boot banner before COBS is disabled and recommend keeping only JSON object lines [S3].
- Preserve contract field names for motor telemetry where possible: `position_deg`, `velocity_rpm`, `current_amp`, `power_w`, `torque_nm`, `efficiency_pct`, `temperature_c` [S1, S7].
- Human labels must carry timestamps from the same capture session. A label like "stuck", "turning left", or "ball contacted" is useful only if it can be joined to nearby telemetry/vision samples.

## Solution Comparison

| Criteria | Option A: Telemetry-only manual firmware | Option B: Add manual mode to `pros_bridge` | Option C: External logger only |
|----------|------------------------------------------|-------------------------------------------|-------------------------------|
| **Approach** | Create a small PROS program: controller loop drives; telemetry task prints JSON; Pi records and labels. | Extend `pros_bridge` with a `manual_mode` where controller owns motors and bridge still emits telemetry/status. | Leave Brain program alone and try to infer state from camera/labels without motor/controller telemetry. |
| **Pros** | Lowest risk; no command watchdog conflict; easy physical test. | Reuses existing ROS bridge and schemas; one firmware path long-term. | No Brain firmware change. |
| **Cons** | Separate firmware slot/program to maintain. | More mode/state complexity; must carefully disable Pi motor authority in manual mode. | Misses controller inputs and motor loads; much weaker data for self-model gaps. |
| **Complexity** | Low | Medium | Low |
| **Dependencies** | Existing PROS + existing Pi serial/ROS tools. | Existing PROS + ROS bridge; likely a small mode contract. | Existing recording tools only. |
| **Codebase fit** | Strong for quick data capture; fits current serial JSON path. | Strong for final architecture; fits two-loop repo direction. | Weak; does not satisfy the telemetry goal. |
| **Maintenance** | One simple firmware program or slot. | One richer firmware program. | Low code maintenance, high analysis debt. |

## Recommendation

Build Option A first as `driver_telemetry` or a manual slot derived from `pros_bridge`, then fold it into Option B after one successful capture.

Implementation outline:

1. Add a PROS manual telemetry program or mode.
   - In `opcontrol()`, instantiate `pros::Controller master(E_CONTROLLER_MASTER)`.
   - Controller loop runs every 10-20 ms, reads analog sticks/buttons, and commands drivetrain/arm/claw motors.
   - The loop records the latest controller values into a small shared snapshot protected by a mutex or atomics.

2. Keep telemetry independent and read-only.
   - A `telemetry_task` runs every 100-500 ms.
   - It emits one newline-delimited JSON object with `type:"telemetry"`, `t_ms`, battery fields, motor samples, and a `controller` object such as `left_y`, `right_x`, `r1`, `r2`, `a`, `b`.
   - It uses the existing `emit_json()`/stdout mutex pattern.

3. Capture labels on the Pi, not by stopping the robot.
   - Run the normal ROS launch or a lean serial recorder.
   - Add a tiny annotation node/script that reads your typed labels or hotkeys and publishes `/operator/annotation` as JSON: `{"type":"annotation","label":"stuck_on_ball","wall_ms":...,"note":"..."}`.
   - Record `/vex/telemetry`, `/operator/annotation`, camera, scene map, and relevant vision topics into the same MCAP.

4. Export joined windows.
   - During analysis, join each annotation to telemetry samples in a window such as `[-2s,+2s]`.
   - Use labels as ground truth intervals for state classification and offline self-model gap analysis.

Risks and mitigations:

- **Motor authority conflict:** avoid by making controller/manual mode the only drivetrain writer. Disable ROS `drive`/`turn` handling or reject commands while manual mode is active.
- **Bandwidth pressure:** start at 5 Hz or 2 Hz telemetry; only add controller fields and contract motor samples. Increase rate only if logs show headroom.
- **Timestamp alignment:** include Brain `t_ms` and Pi receive/wall timestamp; use Pi-side annotation timestamps for cross-topic joins.
- **Safety:** preserve estop/stop behavior for any Pi command mode, but do not let a missing Pi heartbeat stop manual controller driving unless explicitly desired.

## Next Steps

- To create an implementation task: `/task-add Add a driver telemetry mode that lets V5 controller driving own motor commands while the Brain emits JSON telemetry and Pi-side annotations are recorded with the session`
- A decision is worth recording if this becomes architecture: choose whether manual capture is a separate PROS slot/program or a mode inside `pros_bridge`.
- Use the first physical test to answer two remaining empirical questions: practical JSON rate over the user serial port while driving, and whether ROS bridge heartbeat behavior should be disabled or bypassed in manual mode.
