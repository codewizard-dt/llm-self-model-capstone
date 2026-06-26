# Reboot Procedure & Workspace Rebuild

---

## Reboot Procedure

### What survives a reboot

| Component | Survives reboot? | Notes |
|-----------|-----------------|-------|
| Ubuntu OS | Yes | |
| ROS 2 Jazzy base install | Yes | In `/opt/ros/jazzy/` |
| `~/ros2_ws` build artifacts | Yes | In `~/ros2_ws/install/` |
| `source` in `~/.bashrc` | Yes | If added permanently |
| User systemd services | Yes | `vexy-ros-stack.service` and `vexy-ros-bridge.service` |
| Running ROS nodes | Yes, if services are enabled | Verify after every reboot |
| Foxglove bridge | Yes, if `vexy-ros-stack.service` is active | Runs from the stack launch file |

### After reboot — restart sequence

```bash
# 1. SSH in
ssh vexy@vexy.local

# 2. Source workspace (if not in .bashrc already)
source ~/ros2_ws/install/setup.bash

# 3. Verify device nodes are present
ls /dev/ttyACM*     # VEX V5 Brain
ls /dev/video*      # Camera

# 4. Verify managed stack
systemctl --user is-active vexy-ros-stack.service
systemctl --user is-active vexy-ros-bridge.service

# 5. Confirm the legacy duplicate service is not running
systemctl --user is-enabled vexy-ros.service 2>/dev/null || true
systemctl --user is-active vexy-ros.service 2>/dev/null || true

# 6. Confirm one clean graph
ros2 node list
```

Expected nodes: `/camera`, `/camera_rectify`, `/apriltag`, `/scene_map`,
`/align_to_tag`, `/vex_bridge`, `/foxglove_bridge`, and `/vexy_ros_bridge`.
If each node appears twice, stop and disable the legacy service:

```bash
systemctl --user stop vexy-ros.service
systemctl --user disable vexy-ros.service
systemctl --user restart vexy-ros-stack.service
```

### Auto-start on boot with user systemd

Use user services, not a system `/etc/systemd/system/vexy-ros.service`, so the
ROS graph has one owner. The current Pi uses:

- `vexy-ros-stack.service` — camera, rectification, AprilTag, scene map, align skill, V5 serial bridge, Foxglove
- `vexy-ros-bridge.service` — `/vexy/cmd_vel` to `/vex/cmd` adapter

Create `~/.config/systemd/user/vexy-ros-stack.service`:

```ini
[Unit]
Description=Vexy ROS 2 camera and V5 bridge stack
After=default.target

[Service]
Type=simple
Environment=ROS_DOMAIN_ID=0
ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && source /home/vexy/ros2_ws/install/setup.bash && exec ros2 launch vexy_ros vexy.launch.py camera_fps:=15 serial_port:=auto yellow_ball_detector_enabled:=false'
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable vexy-ros-stack.service
systemctl --user start vexy-ros-stack.service
systemctl --user status vexy-ros-stack.service
```

---

## Workspace Rebuild

### When to rebuild

Rebuild `~/ros2_ws` when:

- You pull changes to `robot/ros2-runtime/` (vexy_ros source)
- You update `camera_ros` or the libcamera fork
- A `colcon build` previously failed and you fixed the underlying issue
- You change `package.xml` or `setup.py`

You do **not** need to rebuild for:
- Python node changes that only edit `.py` files in `src/vexy_ros/` (they are symlinked in development mode — changes take effect immediately on node restart)

### Full workspace rebuild

```bash
cd ~/ros2_ws

# Clean previous build artifacts (optional but safe)
rm -rf build/ install/ log/

# Rebuild all three packages
colcon build \
  --packages-select libcamera camera_ros vexy_ros \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  --event-handlers console_direct+

# Re-source the overlay
source ~/ros2_ws/install/setup.bash
```

Expected time: 10–25 minutes for libcamera + camera_ros (C++). `vexy_ros` (Python) builds in seconds.

### Rebuild vexy_ros only (fastest)

```bash
cd ~/ros2_ws
colcon build --packages-select vexy_ros --event-handlers console_direct+
source ~/ros2_ws/install/setup.bash
```

### Incremental rebuild after libcamera changes

```bash
cd ~/ros2_ws
colcon build \
  --packages-select libcamera camera_ros \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  --event-handlers console_direct+
source ~/ros2_ws/install/setup.bash
```

### Verify build succeeded

```bash
ros2 pkg list | grep -E 'vexy_ros|camera_ros'
# Both packages should appear
```
