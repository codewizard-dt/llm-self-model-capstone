---
id: driver-telemetry-annotation
title: Driver Telemetry Annotation
aliases: [Manual driver telemetry, Human state labels, Operator annotation stream]
updated: 2026-06-26
sources:
  - ../../raw/research/driver-telemetry-labeling/index.md
tags: [concept, telemetry, annotation, ros2, vex-v5, human-in-the-loop]
---

# Driver Telemetry Annotation

Driver telemetry annotation is the capture pattern for collecting real robot data while a human drives with the V5 controller. The Brain program splits responsibility: the controller loop owns drivetrain motor commands, while a separate telemetry task samples motor, battery, and controller state and emits newline-delimited JSON. This avoids the unsafe two-writer case where ROS commands and controller input both try to command the same motors. derived_from::[[driver-telemetry-while-using-the-controller]] uses::[[pros]]

The annotation stream lives on the Pi. A small script or ROS node records human labels as timestamped JSON, preferably on `/operator/annotation`, while `/vex/telemetry`, camera frames, scene maps, and bridge status are recorded in the same MCAP session. Labels such as `stuck_on_ball`, `turning_left`, or `ball_contacted` become interval-level ground truth by joining each label to nearby telemetry windows.

This pattern extends the [[task-telemetry-contract]] before full autonomy is reliable: it captures what the robot was doing, what the motors felt, what the camera saw, and what the human believed the state was. Those labeled windows can train or evaluate state classifiers and can feed the offline self-model loop as observed evidence before the online controller owns every action. feeds::[[llm-authored-self-model]] uses::[[vexy_ros ROS 2 Runtime]]

