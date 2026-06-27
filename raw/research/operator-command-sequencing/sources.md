---
topic: "$research how to make sure that the operator executes all commands in sequence, waiting for each one to finish before the next"
slug: operator-command-sequencing
researched: 2026-06-26
---

# Primary Sources — Operator Command Sequencing

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode.__init__` | 2026-06-26 | Shows the node's subscriptions and timers, including `_tick_task_outline`, `_tick_controllers`, status publishing, and inbox polling. |
| S2 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode._run_task_outline` | 2026-06-26 | Shows that the task outline runner now starts a `TaskOutlineRun` instead of looping through every method immediately. |
| S3 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode._tick_task_outline` | 2026-06-26 | Shows current sequencing behavior: one current step, timeout check, invoke method, advance on success, stay on in-progress reasons, fail on terminal result. |
| S4 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/_core.py::Operator.pickup_ball` | 2026-06-26 | Shows pickup is a method-level state machine with opening, approaching, closing, retry, and success states. |
| S5 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/_core.py::Operator.move_to_tag` | 2026-06-26 | Shows move-to-tag is completion-aware and returns success only after distance/yaw/lateral tolerances are met. |
| S6 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/_core.py::Operator._timed_claw` | 2026-06-26 | Shows `grab`, `lift`, and `release` return success immediately after sending the primitive command. |
| S7 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/node.py::RosCommandSink.send_command` | 2026-06-26 | Shows primitive commands are published with incrementing sequence numbers. |
| S8 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode._on_ack` | 2026-06-26 | Shows `/vex/ack` updates bridge health with latest ack sequence and fault state. |
| S9 | codebase | `robot/ros2-runtime/tests/test_operator.py::OperatorNodeTests.test_task_outline_waits_for_pickup_ball_before_bin_steps` | 2026-06-26 | Shows regression coverage that later bin move/lift/release are not called while pickup returns in-progress. |
| S10 | codebase | `robot/ros2-runtime/tests/test_operator.py::OperatorNodeTests.test_task_outline_timeout_stops_before_bin_steps` | 2026-06-26 | Shows regression coverage that timeout stops the outline before later bin steps. |
| S11 | context7 | `/ros2/rclpy` — "How do rclpy timers and executors schedule callbacks?" | 2026-06-26 | Official rclpy docs state executors execute callbacks and callback groups enforce concurrency rules. |
| S12 | context7 | `/ros2/ros2_documentation` — "ROS 2 Python rclpy executors callback groups timers avoid blocking callbacks state machine pattern" | 2026-06-26 | Official ROS 2 docs describe callback deadlock when a timer waits for another callback in the same mutually exclusive group. |
| S13 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/_core.py::OperatorResult` | 2026-06-26 | Shows the current result type has `success` and `reason`, but no structured step status. |
| S14 | codebase | `CLAUDE.md` | 2026-06-26 | Defines raw/wiki conventions and says raw sources are immutable ground-truth after creation. |

## Excerpts

### S1 — OperatorNode timers and subscriptions
`robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode.__init__`
> The node creates subscriptions for TF, vision scene maps, object detections, object indications, VEX ack, VEX telemetry, bridge status, and operator commands; it creates timers for controllers, task outline ticks, status publication, and task inbox polling.

### S2 — Task outline start
`robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode._run_task_outline`
> `_run_task_outline` publishes a `run_start` event and stores `TaskOutlineRun(source_name, method_plan, step_index=0, step_started_s=time.monotonic())`.

### S3 — Task outline tick
`robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode._tick_task_outline`
> `_tick_task_outline` returns immediately when there is no run, checks the current step timeout, invokes the current method, advances on success, stays on in-progress reasons, and fails on terminal results.

### S4 — Pickup state machine
`robot/ros2-runtime/src/vexy_ros/operator/_core.py::Operator.pickup_ball`
> `pickup_ball` uses `pickup_phase` values including `idle`, `opening`, `approaching`, `closing`, and `done`; it returns `opening_claw`, `moving_to_ball`, `closing_claw`, `grab_not_confirmed`, or `ball_grabbed`.

### S5 — Move-to-tag completion
`robot/ros2-runtime/src/vexy_ros/operator/_core.py::Operator.move_to_tag`
> `move_to_tag` sends `stop` and returns `OperatorResult(True, "arrived", ...)` only when distance, yaw, and lateral errors are within configured tolerances.

### S6 — Timed claw commands
`robot/ros2-runtime/src/vexy_ros/operator/_core.py::Operator._timed_claw`
> `_timed_claw` builds and sends a primitive `grab`, `lift`, or `release` command, then returns `OperatorResult(True, f"{cmd}_sent", ...)`.

### S7 — Command sequence publication
`robot/ros2-runtime/src/vexy_ros/operator/node.py::RosCommandSink.send_command`
> `send_command` increments `self.seq`, builds a packet from the primitive command, publishes it to `/vex/cmd`, and returns the sequence number.

### S8 — Ack handling
`robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode._on_ack`
> `_on_ack` parses ack JSON, extracts `ack`, and stores `last_ack_seq` plus optional `fault` in `BridgeHealth`.

### S9 — Pickup sequencing regression
`robot/ros2-runtime/tests/test_operator.py::OperatorNodeTests.test_task_outline_waits_for_pickup_ball_before_bin_steps`
> The test ticks the outline while `pickup_ball` returns `opening_claw`, `moving_to_ball`, and `closing_claw`, asserting no later `move_to_tag:0`, `lift`, or `release` call occurs before pickup succeeds.

### S10 — Timeout regression
`robot/ros2-runtime/tests/test_operator.py::OperatorNodeTests.test_task_outline_timeout_stops_before_bin_steps`
> The test forces the current step past `task_step_timeout_s` and asserts the run ends with `task_file_execution_failed` reason `step_timeout`.

### S11 — rclpy execution and callbacks
`/ros2/rclpy`, source: https://github.com/ros2/rclpy/blob/rolling/rclpy/docs/source/api/execution_and_callbacks.md
> "Executors are responsible for the actual execution of callbacks. Callback groups are used to enforce concurrency rules for callbacks."

### S12 — ROS 2 callback deadlock guidance
`/ros2/ros2_documentation`, source: https://github.com/ros2/ros2_documentation/blob/rolling/source/How-To-Guides/Using-callback-groups.rst
> "When a timer and a service client are assigned to the same Mutually Exclusive Callback Group, a deadlock can occur."

### S13 — OperatorResult status shape
`robot/ros2-runtime/src/vexy_ros/operator/_core.py::OperatorResult`
> `OperatorResult` contains `success: bool` and `reason: str`, plus optional command, tag, pose, localization, drive health, and object state fields.

### S14 — Raw source immutability
`CLAUDE.md`
> "`raw/` is immutable — never create, modify, move, or delete files under `raw`" after ground-truth sources exist; the research skill explicitly allows creating new `raw/research/` files.
