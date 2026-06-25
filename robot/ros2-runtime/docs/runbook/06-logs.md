# Log Locations

---

### ROS 2 node logs

ROS 2 writes per-session logs to:

```
~/.ros/log/
  latest/           → symlink to most recent session
  <session-id>/
    launch.log      (launch file output)
    <node-name>-1-stdout.log
    <node-name>-1-stderr.log
```

```bash
# View latest session logs
ls ~/.ros/log/latest/

# Tail camera node output live
tail -f ~/.ros/log/latest/camera-1-stdout.log

# Tail VEX bridge live
tail -f ~/.ros/log/latest/vex_bridge-1-stdout.log

# All logs for the current session
cat ~/.ros/log/latest/*.log
```

### Colcon build logs

```bash
ls ~/ros2_ws/log/latest/
cat ~/ros2_ws/log/latest/logger_all.log
```

### systemd journal (if running as a service)

```bash
# Live log stream
journalctl --user -u vexy-ros-stack.service -f

# Last 100 lines
journalctl --user -u vexy-ros-stack.service -n 100

# Since last boot
journalctl --user -u vexy-ros-stack.service -b

# Adapter bridge logs
journalctl --user -u vexy-ros-bridge.service -n 100
```

### System-level dmesg (USB/camera device events)

```bash
# Recent USB events (e.g., Brain plug/unplug, camera probe)
sudo dmesg | grep -E 'ttyACM|usb|v4l|media|imx708' | tail -30

# Live monitoring
sudo dmesg -w | grep -E 'ttyACM|usb|media|imx708'
```

### Log rotation / cleanup

ROS 2 log directories accumulate over sessions. Clean old logs:

```bash
ros2 doctor --report  # lists log directory size
# Manual cleanup: keep last 10 sessions
ls -dt ~/.ros/log/*/  | tail -n +11 | xargs rm -rf
```
