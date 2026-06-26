# vexy Coprocessor — Operations Runbook

**System:** Raspberry Pi 5 · Ubuntu 24.04 LTS · ROS 2 Jazzy  
**Hostname:** vexy.local · **SSH user:** vexy  
**Workspace:** `~/ros2_ws` (libcamera fork + camera_ros + vexy_ros)  
**Last updated:** 2026-06-26

---

## Runbook Sections

| # | Topic | File |
|---|-------|------|
| 1 | Daily Operations — SSH, launch, start/stop nodes | [runbook/01-daily-ops.md](runbook/01-daily-ops.md) |
| 2 | Verification Checklist — post-launch health checks | [runbook/02-verification.md](runbook/02-verification.md) |
| 3 | Recording Sessions — bags, JSONL export, contract validation | [runbook/03-recording.md](runbook/03-recording.md) |
| 4 | Troubleshooting — camera, serial, Foxglove, Brain | [runbook/04-troubleshooting.md](runbook/04-troubleshooting.md) |
| 5 | Reboot Procedure & Workspace Rebuild | [runbook/05-reboot-and-workspace.md](runbook/05-reboot-and-workspace.md) |
| 6 | Log Locations — ROS 2, colcon, systemd, dmesg | [runbook/06-logs.md](runbook/06-logs.md) |
| 7 | PROS Brain Upload via SSH — build, push, upload | [runbook/07-pros-upload.md](runbook/07-pros-upload.md) |

---

## Quick Reference Card

```
# SSH
ssh vexy@vexy.local

# Source
source ~/ros2_ws/install/setup.bash

# Ensure managed stack is active
systemctl --user restart vexy-ros-stack.service
systemctl --user start vexy-ros-bridge.service

# Check nodes
ros2 node list

# Camera health
ros2 topic hz /camera/image_raw

# VEX serial ack proof
ros2 topic echo /vex/ack --once
ros2 topic echo /vex/bridge_status --once

# Foxglove bridge
ros2 launch vexy_ros vexy.launch.py  # foxglove_bridge starts automatically
# Connect: ws://vexy.local:8765

# Record session
ros2 bag record -a -o ~/bags/session_$(date +%Y%m%d_%H%M%S)

# Rebuild vexy_ros only
cd ~/ros2_ws && colcon build --packages-select vexy_ros && source install/setup.bash

# Logs
tail -f ~/.ros/log/latest/vex_bridge-1-stdout.log

# Upload PROS binary (stop stack → upload → restart):
# Slot ownership: David=7,8 | Jake=2-4 | Grace=5-6 | NEVER slot 1
SLOT=8
ssh vexy@vexy.local "
  systemctl --user stop vexy-ros-bridge.service vexy-ros-stack.service 2>/dev/null
  cd ~/llm-self-model-capstone/robot/v5-brain/pros_bridge
  uv run pros upload --slot $SLOT --after none
  systemctl --user start vexy-ros-stack.service vexy-ros-bridge.service
"
# Important: --after none uploads only. Start Slot 8 manually on the Brain before live tests.
```
