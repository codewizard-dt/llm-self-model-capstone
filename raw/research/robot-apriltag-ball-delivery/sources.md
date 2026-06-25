---
topic: "proper workflow first... then write a new progam for the robot that does these things in order: 1) orients itself in the workspace using apriltags. 2) moves to the ball-loading area apriltag. 3) moves to the bin area apriltag, 4) drops the ball in the bin. Save this as a new program in the ros2-runtime folder."
slug: robot-apriltag-ball-delivery
researched: 2026-06-25
---

# Primary Sources - Robot AprilTag Ball Delivery

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/ros2-runtime/src/vexy_ros/tag_action_proof.py::{run_scan,approach_tag,TagActionProof.send,finalize_summary}` | 2026-06-25 | Existing bounded scan, tag approach, command publish, and summary helpers. |
| S2 | codebase | `robot/ros2-runtime/config/maps/{table-grab-toss-v1.json,gen0-grab-toss-v1.json}` | 2026-06-25 | Map roles: `bin` tag ID `0`, `ball_staging` tag ID `1`. |
| S3 | codebase | `robot/ros2-runtime/src/vexy_ros/bridge_protocol.py` | 2026-06-25 | Original command grammar had `stop`, `drive`, `turn`, and `set_goal`; release support had to be added. |
| S4 | codebase | `robot/v5-brain/pros_bridge/src/main.cpp::handle_line` | 2026-06-25 | Brain accepted drive/turn/stop and rejected `set_goal` as unsupported. |
| S5 | codebase | `robot/ros2-runtime/setup.py` | 2026-06-25 | Runtime programs are exposed as setuptools `console_scripts`. |
| S6 | context7 | `/ros2/rclpy` - "ROS 2 Python node publishers subscriptions timers spin_once API" | 2026-06-25 | rclpy is the canonical Python API for ROS 2 node interaction; callbacks are executor-driven. |

## Excerpts

### S1 - `tag_action_proof.py`
> `run_scan` sends repeated `turn` commands and spins; `approach_tag` uses `fresh_tag`, yaw correction, TTL-bounded `drive`, and a target distance stop condition.

### S2 - Runtime map configs
> Both map configs identify tag `0` with role `bin` and tag `1` with role `ball_staging`.

### S3 - `bridge_protocol.py`
> The command set was `{"stop", "drive", "turn", "set_goal"}` before this implementation.

### S4 - V5 brain bridge
> The V5 handler stops and rejects `set_goal` with `unsupported_goal`.

### S5 - `setup.py`
> Existing runtime commands such as `vexy_tag_action_proof` and `vexy_scene_observation_proof` are registered in `console_scripts`.

### S6 - rclpy docs
> "rclpy provides the canonical Python API for interacting with ROS 2."
