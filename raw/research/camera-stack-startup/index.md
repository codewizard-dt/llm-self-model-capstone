---
topic: how to start the camera and AprilTag detection stack on the vexy Pi so that /tf publishes tag poses
slug: camera-stack-startup
researched: 2026-06-25
sources: [./sources.md]
---

# Research: Camera and AprilTag Stack Startup on the vexy Pi

> The vexy Pi manages the full camera + AprilTag + bridge stack as a systemd user service (`vexy-ros-stack.service`). The service runs `ros2 launch vexy_ros vexy.launch.py` with a site-specific drop-in that supplies the calibration URL and the active workspace map (`VEXY_MAP`). Integration tests must ensure the service is active and `/tf` is publishing before entering the spin loop.

## Research Questions

1. What process publishes AprilTag poses to `/tf`?
2. How is the camera started on the Pi (systemd vs manual)?
3. What drop-ins or env overrides does the active service use?
4. What is the startup sequence and how long does warmup take?
5. What map file does the running stack use, and how should test scripts resolve it?

## Current State (Codebase)

### Launch pipeline (`robot/ros2-runtime/launch/vexy.launch.py`)

`ros2 launch vexy_ros vexy.launch.py` starts five nodes in order:

| Node | Package | Publishes |
|------|---------|-----------|
| `camera` | `camera_ros` | `/camera/image_raw`, `/camera/camera_info` |
| `camera_rectify` | `image_proc` | `/camera/image_rect` |
| `apriltag` | `apriltag_ros` | `/apriltag/detections`, **`/tf`** |
| `scene_map` | `vexy_ros` | `/vision/scene_map` |
| `vex_bridge` | `vexy_ros` | `/vex/ack`, `/vex/telemetry` |

`/tf` is only published by the `apriltag_node` — it is the final output of the chain camera → rectify → AprilTag. All three nodes must be healthy for tag poses to appear on `/tf`.

### Systemd service on the Pi

**Unit file:** `~/.config/systemd/user/vexy-ros-stack.service`

```ini
[Unit]
Description=Vexy ROS 2 camera and V5 bridge stack
After=default.target

[Service]
Type=simple
Environment=ROS_DOMAIN_ID=0
ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && \
  source /home/vexy/ros2_ws/install/setup.bash && \
  exec ros2 launch vexy_ros vexy.launch.py camera_fps:=30 serial_port:=auto'
Restart=on-failure
RestartSec=2
```

**Drop-in overrides** (`vexy-ros-stack.service.d/*.conf`):

```ini
[Service]
Environment=VEXY_MAP=gen0-grab-toss-v1
ExecStart=
ExecStart=/bin/bash -lc 'source /opt/ros/jazzy/setup.bash && \
  source /home/vexy/ros2_ws/install/setup.bash && \
  exec ros2 launch vexy_ros vexy.launch.py camera_fps:=30 serial_port:=auto \
  camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml'
```

The drop-in: (a) sets `VEXY_MAP=gen0-grab-toss-v1` (read by `launch.py` to select the workspace map), and (b) overrides `ExecStart` to supply the calibration YAML path.

### Workspace map resolution in tests

The launch file resolves the map via:
```python
EnvironmentVariable("VEXY_MAP", default_value="table-grab-toss-v1")
# → finds config/maps/<VEXY_MAP>.json in the installed vexy_ros package share
```

Test scripts should use `ament_index_python.packages.get_package_share_directory("vexy_ros")` to find the installed config directory and respect `VEXY_MAP` to match the running stack's map:
```python
import os
from ament_index_python.packages import get_package_share_directory
_map_name = os.environ.get("VEXY_MAP", "table-grab-toss-v1")
MAP_FILE = Path(get_package_share_directory("vexy_ros")) / "config" / "maps" / f"{_map_name}.json"
```

Both available maps (`gen0-grab-toss-v1.json` and `table-grab-toss-v1.json`) use the same tag IDs (0=bin, 1=ball_staging, 2=home) and the same role-based standoff distances, so either works for standoff logic. However, using `VEXY_MAP` ensures alignment with the running apriltag detection setup.

## Key Findings

- The full stack (camera → rectify → apriltag → scene_map → bridge) is managed as a single systemd user service [S1]
- `/tf` is published by `apriltag_node` only — it is the terminal output of the camera chain [S2]
- The service uses a drop-in to override the calibration URL and `VEXY_MAP` [S3]
- Stack warmup: camera → rectify → apriltag takes approximately 5–10 s on a cold start before `/tf` begins publishing
- Stack status check: `systemctl --user is-active vexy-ros-stack.service` returns `"active"` when healthy
- The installed map files live at `$(ros2 pkg prefix vexy_ros)/share/vexy_ros/config/maps/` [S4]

## Constraints

- The stack must be started as the `vexy` user (`systemctl --user`), not system-level
- ROS_DOMAIN_ID must be 0 (the service sets this; the Python test inherits it if the SSH session doesn't override it)
- The calibration YAML at `/home/vexy/calibration/imx708_wide_640x480.yaml` must exist or the camera_node will fail to rectify
- Physical AprilTags must be in the camera's field of view for `/tf` to carry tag transforms — the software stack is necessary but not sufficient

## Recommendation

### For integration test scripts (`test_live_*.py`)

Add an `ensure_stack_running()` pre-flight call in `main()` before `rclpy.init()`:

```python
import os, subprocess, time

STACK_SERVICE = "vexy-ros-stack.service"

def ensure_stack_running() -> bool:
    r = subprocess.run(
        ["systemctl", "--user", "is-active", STACK_SERVICE],
        capture_output=True, text=True,
    )
    if r.stdout.strip() != "active":
        print(f"  Starting {STACK_SERVICE}...")
        subprocess.run(["systemctl", "--user", "restart", STACK_SERVICE], check=True)
        print("  Waiting 10 s for stack warmup...")
        time.sleep(10)
    else:
        print(f"  {STACK_SERVICE} already active.")
    return True
```

And update `MAP_FILE` to use the installed package path + `VEXY_MAP`:

```python
from ament_index_python.packages import get_package_share_directory
_map_name = os.environ.get("VEXY_MAP", "table-grab-toss-v1")
MAP_FILE = pathlib.Path(get_package_share_directory("vexy_ros")) / "config" / "maps" / f"{_map_name}.json"
```

### Startup verification on the Pi

```bash
# Check service status
systemctl --user status vexy-ros-stack.service

# Verify /tf is publishing (indicates camera + rectify + apriltag all up)
source ~/ros2_ws/install/setup.bash
ros2 topic hz /tf

# Restart the stack
systemctl --user restart vexy-ros-stack.service
```

## Next Steps

- Update `operator/tests/test_live_align.py` and `test_live_deliver.py` with `ensure_stack_running()` + package-relative `MAP_FILE`
- Copy updated tests to Pi via `scp` and re-run
