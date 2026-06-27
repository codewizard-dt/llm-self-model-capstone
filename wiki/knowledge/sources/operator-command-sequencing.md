---
id: operator-command-sequencing
title: Operator Command Sequencing
aliases: [Research: Operator Command Sequencing, task outline sequencing, operator outline sequencing]
updated: 2026-06-26
sources:
  - ../../../raw/research/operator-command-sequencing/index.md
tags: [operator, ros2, control, sequencing]
---

# Operator Command Sequencing

This research source narrowed the sequencing problem in rel::[[vexy-ros-runtime]]. The on-robot operator should treat a task outline as one active run with exactly one current step. The timer-driven wrapper is the right ROS 2 shape because it returns control to the executor between attempts, allowing telemetry, vision, acks, and other timers to advance while a command is still in progress.

The source distinguishes completion-aware operator methods from merely dispatched commands. **`move_to_tag` and `pickup_ball` already behave as stateful operations**, returning in-progress reasons until they reach `arrived` or `ball_grabbed`. The implementation now treats standalone `grab`, `lift`, and `release` as timed task-outline steps: they send once, remain pending until duration plus settle time has elapsed, and abort on bridge fault or rejected/fault ack. derived_from::[[operator-command-sequencing]]

The implemented fix is a runner-owned step-policy layer for timed primitives. It keeps the non-blocking ROS 2 state-machine architecture while making every outline method completion-aware enough for ordered task-file execution.
