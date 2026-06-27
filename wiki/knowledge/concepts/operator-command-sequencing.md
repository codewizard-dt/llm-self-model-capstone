---
id: operator-command-sequencing
title: Operator Command Sequencing
aliases: [task outline sequencing, step policy state machine, operator step policies]
updated: 2026-06-26
sources:
  - ../../../raw/research/operator-command-sequencing/index.md
tags: [operator, ros2, sequencing, state-machine]
---

# Operator Command Sequencing

Operator command sequencing is the runtime rule that a task outline may have **one active step at a time**, and the next step may not start until the current step reaches terminal success. Terminal failure or timeout aborts the run. In-progress work must return control to ROS between attempts so subscriptions and timers can update live state.

The pattern fits rel::[[vexy-ros-runtime]] because the operator depends on `/tf`, vision detections, object indications, `/vex/ack`, `/vex/telemetry`, and bridge status. Blocking inside a callback would prevent the very evidence needed to decide whether a step is done. The correct implementation is a timer-driven state machine, not a synchronous loop or sleep-wait.

The current distinction is important: stateful methods such as `move_to_tag` and `pickup_ball` can be polled until domain success, while timed primitives such as `grab`, `lift`, and `release` need explicit step policies. The implemented policy sends a one-shot primitive once, records its command sequence and deadline, then polls elapsed duration, settle time, bridge faults, and ack rejection/fault state before returning success. relates_to::[[task-telemetry-contract]] relates_to::[[vex-coprocessor-pattern]]

Implementation shape:
- `StepStatus.RUNNING`, `SUCCEEDED`, `FAILED`, and `TIMED_OUT`
- `TaskOutlineRun` state for source, method plan, current index, start time, attempt count, pending command sequence, and last result
- runner-owned policies for timed primitive start/poll/timeout/completion
- tests proving later outline steps are not invoked during pickup, grab, lift, release, bridge-fault, or timeout states
