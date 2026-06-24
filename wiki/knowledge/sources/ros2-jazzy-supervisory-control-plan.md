---
id: ros2-jazzy-supervisory-control-plan
title: ROS 2 Jazzy Supervisory Control Plan
aliases: [Vexy ROS 2 supervisory plan, AlignToTag vertical slice plan]
updated: 2026-06-24
sources:
  - ../../raw/research/ros2-jazzy-supervisory-control-plan/index.md
tags: [source, ros2, jazzy, vexy, coprocessor, safety, apriltag]
---

# ROS 2 Jazzy Supervisory Control Plan

This source reconciles a proposed PiCam2-on-Ubuntu-24.04 + [[ros2-jazzy]] supervisory-control architecture with the actual Vexy codebase. Its core conclusion is that the proposed split is correct: Codex should operate as a **slow supervisory planner**, ROS should own local perception and skill execution, and the [[vex-v5]] Brain should remain the actuator authority with watchdogs, TTLs, clamps, and stop behavior. The repo-shaped implementation is a staged evolution of `robot/ros2-runtime`, not a new greenfield ROS workspace.

The plan refines the migration path: keep `robot/pi-runtime` as the current Bookworm fallback until Jazzy reaches parity; use [[pi-camera-module-3]] through `camera_ros` and the Raspberry Pi libcamera fork; add calibration plus `image_proc` rectification before trusting `apriltag_ros`; and make `AlignToTag` the first closed-loop proof. It explicitly separates camera proof, serial proof, and motion proof so a healthy frame stream is not mistaken for a healthy robot-control stack.

The source also corrects the immediate VEX bridge priority. Instead of jumping straight to binary packets, the current newline-delimited JSON protocol should remain until the first ROS proof works. The urgent fix is to port the older `robot/pi-runtime` serial reader pattern into the ROS bridge so acknowledgements and streaming telemetry are separated before logging or control. Binary framing with CRC belongs in a future protocol-v2 contract after JSON-v1 parity.

Finally, the source clarifies the evidence pipeline: rosbag2/MCAP should be treated as the raw replayable episode store, while exported contract-valid JSONL remains the semantic input to the [[task-telemetry-contract]] and LLM self-model loop. In short: MCAP proves what happened; the contract tells the operator what the self-model should learn from it.

derived_from::[[rpi-os-options]]
extends::[[vex-coprocessor-pattern]]
relates_to::[[robot-workspace-map]]
relates_to::[[apriltag-workspace-layout]]
grounds::[[task-telemetry-contract]]
