---
topic: how to start the camera and AprilTag detection stack on the vexy Pi so that /tf publishes tag poses
slug: camera-stack-startup
researched: 2026-06-25
---

# Primary Sources — Camera Stack Startup

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/ros2-runtime/launch/vexy.launch.py` | 2026-06-25 | Full node list: camera_node→rectify→apriltag_node publishes `/tf`; launch command |
| S2 | live Pi | `systemctl --user list-units vexy*` on vexy@vexy.local | 2026-06-25 | `vexy-ros-stack.service` is active; exact unit file and drop-in contents |
| S3 | live Pi | `~/.config/systemd/user/vexy-ros-stack.service.d/*.conf` | 2026-06-25 | Drop-in sets `VEXY_MAP=gen0-grab-toss-v1` and overrides `ExecStart` with calibration URL |
| S4 | live Pi | `ls ~/ros2_ws/install/vexy_ros/share/vexy_ros/config/maps/` | 2026-06-25 | Installed maps: `gen0-grab-toss-v1.json`, `gen0-grab-toss-v1.json` |
| S5 | codebase | `robot/ros2-runtime/docs/runbook/01-daily-ops.md` | 2026-06-25 | `source ~/ros2_ws/install/setup.bash`; `ros2 launch vexy_ros vexy.launch.py` as the canonical start command |
| S6 | codebase | `robot/ros2-runtime/docs/RUNBOOK.md` | 2026-06-25 | Quick reference: `systemctl --user restart vexy-ros-stack.service`; workspace source path |

## Excerpts

### S1 — launch/vexy.launch.py node list header
```
camera_node   — Camera Module 3 via camera_ros (RPi libcamera fork)
                Publishes: /camera/image_raw, /camera/camera_info
camera_rectify — image_proc rectification
                Publishes: /camera/image_rect
apriltag      — AprilTag 36h11 detector over rectified camera stream
                Publishes: /apriltag/detections, /tf
```

### S2 — vexy-ros-stack.service unit file (live Pi)
```ini
[Service]
Type=simple
Environment=ROS_DOMAIN_ID=0
ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && source /home/vexy/ros2_ws/install/setup.bash && exec ros2 launch vexy_ros vexy.launch.py camera_fps:=30 serial_port:=auto'
Restart=on-failure
RestartSec=2
```

### S3 — Drop-in override (live Pi)
```ini
[Service]
Environment=VEXY_MAP=gen0-grab-toss-v1
ExecStart=
ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && source /home/vexy/ros2_ws/install/setup.bash && exec ros2 launch vexy_ros vexy.launch.py camera_fps:=30 serial_port:=auto camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml'
```

### S6 — RUNBOOK.md quick reference (relevant lines)
```
# Ensure managed stack is active
systemctl --user restart vexy-ros-stack.service

# Camera health
ros2 topic hz /camera/image_raw
```
