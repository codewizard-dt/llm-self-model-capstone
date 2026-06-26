---
id: camera-stack-startup
title: Research — Camera Stack Startup (vexy Pi)
updated: 2026-06-25
sources:
  - ../../raw/research/camera-stack-startup/sources.md
tags: [ros2, camera, apriltag, systemd, vexy, startup, operations]
---

# Research — Camera Stack Startup (vexy Pi)

Operational research from 2026-06-25 that verifies how the camera and AprilTag detection stack starts on the vexy Pi so that `/tf` publishes tag poses. Sources combine live Pi inspection (systemctl, unit file, drop-in, installed maps) and codebase cross-check (launch file, runbook docs).

derived_from::[[vexy-ros-runtime]]
relates_to::[[camera-module-3-setup]]
relates_to::[[pi-camera-module-3]]
relates_to::[[ros2-jazzy]]
relates_to::[[apriltag-workspace-layout]]

## Startup Pipeline

The three nodes that together produce `/tf` tag poses:

| Node | Package | Key output |
|---|---|---|
| `camera_node` | `camera_ros` (RPi libcamera fork) | `/camera/image_raw`, `/camera/camera_info` |
| `camera_rectify` | `image_proc` | `/camera/image_rect` |
| `apriltag` | `apriltag_ros` | `/apriltag/detections`, `/tf` |

All three nodes are started by the single launch command:

```bash
ros2 launch vexy_ros vexy.launch.py
```

## Managed Service: `vexy-ros-stack.service`

The vexy Pi runs the stack under a **systemd user service**. The base unit `ExecStart`:

```ini
[Service]
Type=simple
Environment=ROS_DOMAIN_ID=0
ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && source /home/vexy/ros2_ws/install/setup.bash && exec ros2 launch vexy_ros vexy.launch.py camera_fps:=30 serial_port:=auto'
Restart=on-failure
RestartSec=2
```

A **drop-in override** in `~/.config/systemd/user/vexy-ros-stack.service.d/` replaces `ExecStart` to add the calibration URL and set the active map:

```ini
[Service]
Environment=VEXY_MAP=gen0-grab-toss-v1
ExecStart=
ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && source /home/vexy/ros2_ws/install/setup.bash && exec ros2 launch vexy_ros vexy.launch.py camera_fps:=30 serial_port:=auto camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml'
```

The blank `ExecStart=` line is required by systemd to clear the base value before the override is applied.

**Calibration file**: `~/calibration/imx708_wide_640x480.yaml` (Camera Module 3 Wide, 640×480).

## Installed Maps

Two workspace maps installed at `~/ros2_ws/install/vexy_ros/share/vexy_ros/config/maps/`:

| File | Status |
|---|---|
| `gen0-grab-toss-v1.json` | Active (selected by drop-in) |
| `table-grab-toss-v1.json` | Alternate arena |

## Operations Quick Reference

| Task | Command |
|---|---|
| Restart managed stack | `systemctl --user restart vexy-ros-stack.service` |
| Check stack status | `systemctl --user status vexy-ros-stack.service` |
| List vexy units | `systemctl --user list-units vexy*` |
| Manual start | `source ~/ros2_ws/install/setup.bash && ros2 launch vexy_ros vexy.launch.py` |
| Camera health check | `ros2 topic hz /camera/image_raw` |
