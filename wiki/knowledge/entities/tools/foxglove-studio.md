---
id: foxglove-studio
title: Foxglove Studio
aliases: [Foxglove, foxglove_bridge]
updated: 2026-06-23
sources:
  - ../../../raw/research/rpi-os-options/index-2.md
tags: [tool, software, debugging, visualization, ros2]
---

# Foxglove Studio

A web-based (and desktop) robotics visualization and debugging tool that connects to a ROS 2 robot via a WebSocket bridge. For headless Raspberry Pi deployments, Foxglove eliminates the need for SSH + print statements — all topic data is visible in a browser from any machine on the same network.

relates_to::[[ros2-jazzy]]
relates_to::[[raspberry-pi-5]]
derived_from::[[rpi-os-options]]

## Setup on ROS 2 Jazzy (Pi 5)

```bash
# On the Pi
sudo apt install ros-jazzy-foxglove-bridge
ros2 launch foxglove_bridge foxglove_bridge_launch.xml

# On any laptop/browser
# Open https://app.foxglove.dev
# Connect → WebSocket → ws://mypi.local:8765
```

Note: the Docker image for `foxglove_bridge` is amd64-only; must build from source on Pi's arm64. The apt package (`ros-jazzy-foxglove-bridge`) installs natively.

## Capstone Value

- **Live YOLO bounding boxes**: visualize `DetectionArray` overlaid on camera feed
- **AprilTag pose plot**: see TF2 transforms for tag positions in world frame over time
- **VEX motor commands**: plot motor velocity commands vs. encoder feedback
- **Message timestamps**: diagnose synchronization issues between camera and serial topics
- **No GUI required on Pi**: everything renders in the browser on your Mac/laptop

A significant debugging upgrade over SSH-based workflows, especially for a showcase demo where you want real-time visibility without a monitor attached to the robot.
