---
id: driver-telemetry-while-using-the-controller
title: Driver Telemetry While Using the Controller
aliases: [Driver telemetry labeling, Manual controller telemetry, Human-labeled driver telemetry]
updated: 2026-06-26
sources:
  - ../../raw/research/driver-telemetry-labeling/index.md
tags: [source, research, telemetry, vex-v5, pros, ros2, annotation]
---

# Driver Telemetry While Using the Controller

This source answers whether the [[vex-v5]] Brain can output telemetry while a human drives with the V5 controller. **Yes: PROS can poll the controller in `opcontrol()` while a separate FreeRTOS telemetry task samples motor, battery, and controller state and prints compact newline-delimited JSON over the Brain user serial port.** The decisive implementation rule is motor authority: in manual-driver mode, the controller loop must be the only writer to drivetrain motors, while telemetry remains read-only. uses::[[pros]] relates_to::[[vex-coprocessor-pattern]]

The repo already has most of the transport path: `pros_bridge` emits tagged `type:"telemetry"` records, `vexy_ros` demuxes Brain JSON into `/vex/telemetry`, and the ROS 2 runbook records bridge, camera, and scene-map topics into MCAP. The new work is therefore a capture mode, not a new telemetry pipeline. The first low-risk path is a small `driver_telemetry` PROS program or manual mode derived from `pros_bridge`, then folding the mode into the main bridge after one successful physical capture. uses::[[vexy_ros ROS 2 Runtime]]

The source also defines the label path. **Human state labels should be captured on the Pi as timestamped annotations, not typed into the Brain or used to interrupt driving.** A lightweight annotation script or ROS node can publish `/operator/annotation` JSON such as `{type:"annotation", label:"stuck_on_ball", wall_ms:...}`. Analysis then joins each annotation to nearby `/vex/telemetry`, camera, and scene-map samples in a small time window. extends::[[task-telemetry-contract]] relates_to::[[driver-telemetry-annotation]]

