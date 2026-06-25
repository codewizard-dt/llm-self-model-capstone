---
id: robot-apriltag-ball-delivery
title: Research: Robot AprilTag Ball Delivery
aliases: [AprilTag ball delivery, vexy_deliver_ball research]
updated: 2026-06-25
sources:
  - ../../raw/research/robot-apriltag-ball-delivery/index.md
tags: [source, ros2, apriltag, vex-v5, bridge, delivery]
---

# Research: Robot AprilTag Ball Delivery

This source distills the implementation workflow for a robot routine that orients with AprilTags, approaches the ball-loading tag, approaches the bin tag, and drops the ball. **The recommended implementation is a ROS 2 console program that reuses existing bounded AprilTag proof helpers instead of introducing a new navigation controller.** derived_from::[[vexy_ros ROS 2 Runtime]] uses::[[AprilTag Workspace Layout for Manipulation Tasks]] uses::[[Robot Workspace Map (Multi-Arena JSON Format)]]

The source fixes the delivery routine to the current map roles: `ball_staging` is tag `1`, and `bin` is tag `0`. It also identifies a bridge-contract gap: the existing Brain command path accepted bounded drive/turn/stop packets but did not expose a real ball-drop action. **A bounded `release` command with `duration_ms` is required for the program to actually drop the ball rather than merely stop at the bin.** uses::[[VEX Coprocessor Pattern]]

The safety posture is fail-closed. Commands remain TTL-bounded and interruptible, the program stops in `finally`, and missing release hardware should produce a rejected ack rather than a fake success. This source therefore extends the ROS runtime component with `vexy_deliver_ball` and extends the V5 bridge contract with release-actuator support. relates_to::[[Task Telemetry Contract]]
