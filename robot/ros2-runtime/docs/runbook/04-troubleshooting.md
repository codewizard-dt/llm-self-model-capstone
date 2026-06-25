# Troubleshooting

### Quick reference table

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `no cameras available` | User not in `video`/`render` groups | See §4.1 below |
| `bzip2` / package conflict on build | `noble-updates` missing from apt sources | See §4.2 below |
| `Permission denied /dev/media*` | `video` group not applied | See §4.3 below |
| Foxglove "Connection failed" | mDNS issue or bridge not running | See §4.4 below |
| Foxglove "Waiting for image messages" | Wrong topic name selected | See §4.5 below |
| `cannot open ... ttyACM...` | Brain not connected, permissions missing, or different port | See §4.6 below |
| Heartbeat timeout from Brain | `vex_bridge_node` crashed | See §4.7 below |

---

### 4.1 "no cameras available"

**Symptom:** `camera_node` exits immediately with `no cameras available` or similar libcamera error.

**Diagnosis:**

```bash
groups   # check output for 'video' and 'render'
ls -la /dev/video* /dev/media*
```

**Fix:**

```bash
sudo usermod -aG video,render vexy
# Log out and back in, OR reboot:
sudo reboot
```

Verify after reboot:

```bash
groups  # should include 'video' and 'render'
libcamera-hello --list-cameras  # should list the IMX708
```

---

### 4.2 bzip2 version conflict during build

**Symptom:** `colcon build` fails with a bzip2 version mismatch or `libbz2` conflict during libcamera compilation.

**Diagnosis:**

```bash
apt-cache policy libbz2-dev
# Check if noble-updates is in sources
grep -r "noble-updates" /etc/apt/sources.list /etc/apt/sources.list.d/
```

**Fix:**

```bash
# Add noble-updates if missing:
sudo add-apt-repository "deb http://ports.ubuntu.com/ubuntu-ports noble-updates main restricted universe multiverse"
sudo apt-get update
sudo apt-get install -y libbz2-dev
# Retry build — see [Workspace Rebuild](05-reboot-and-workspace.md#workspace-rebuild)
```

---

### 4.3 Permission denied on /dev/media*

**Symptom:** libcamera logs `Failed to open /dev/media0: Permission denied` or similar.

**Diagnosis:**

```bash
ls -la /dev/media*
# Should be: crw-rw---- 1 root video ...
stat /dev/media0 | grep Gid
```

**Fix:**

```bash
sudo usermod -aG video vexy
sudo reboot
# After reboot:
groups  # confirm 'video' is listed
```

If the group is correct but still denied, check udev rules:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

### 4.4 Foxglove "Connection failed"

**Symptom:** Foxglove Studio cannot connect to `ws://vexy.local:8765`.

**Step 1 — Verify bridge is running:**

```bash
ssh vexy@vexy.local "ros2 node list | grep foxglove"
# If empty, start the bridge:
ros2 launch vexy_ros vexy.launch.py  # foxglove_bridge starts automatically &
```

**Step 2 — Try IP address instead of hostname:**

**Browser WebSocket connections commonly fail with mDNS even when SSH to `vexy.local` works fine** — this was confirmed during initial setup. Always prefer the IP address for Foxglove. Find the Pi's current IP:

```bash
ssh vexy@vexy.local "hostname -I | awk '{print \$1}'"
```

Then connect Foxglove to `ws://<IP_ADDRESS>:8765`.

**Step 3 — Check firewall:**

```bash
ssh vexy@vexy.local "sudo ufw status"
# If active, allow port 8765:
sudo ufw allow 8765/tcp
```

---

### 4.5 Foxglove "Waiting for image messages"

**Symptom:** Foxglove is connected but the image panel shows "Waiting for image messages."

**Diagnosis:**

```bash
# Verify camera_node is running and publishing:
ros2 node list | grep camera
ros2 topic hz /camera/image_raw
```

**Fixes:**

1. **Wrong topic selected in Foxglove:** In the image panel settings, set topic to `/camera/image_raw` (not `/camera/image_compressed` or anything else).

2. **camera_node not running:** Restart it:
   ```bash
   ros2 run camera_ros camera_node \
     --ros-args \
     -p width:=640 -p height:=480 -p fps:=15 \
     --remap ~/image_raw:=/camera/image_raw \
     --remap ~/camera_info:=/camera/camera_info
   ```

3. **Message type mismatch:** The topic publishes `sensor_msgs/Image`. Confirm in Foxglove the panel is set to **Image** (not **3D**).

---

### 4.6 V5 serial port not found

**Symptom:** `vex_bridge_node` logs `cannot open ...` or the device file is absent.

**Step 1 — Check if Brain is connected:**

```bash
ls /dev/ttyACM*
# If nothing appears, the USB cable is not connected or the Brain is off
```

**Step 2 — Check which port:**

```bash
ls /dev/ttyACM*
# Common: /dev/ttyACM0 and /dev/ttyACM1, with the user/program port usually on if02
dmesg | tail -20 | grep tty
```

**Step 3 — Launch with the correct port:**

```bash
ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1
```

**Step 4 — Check dialout group:**

```bash
groups  # should include 'dialout'
sudo usermod -aG dialout vexy
sudo reboot
```

---

### 4.7 Heartbeat timeout from Brain

**Symptom:** `/vex/bridge_status` reports `missing_ack` or `serial_disconnect`; `/vex/ack` stops publishing.

**Diagnosis:**

```bash
ros2 topic hz /vex/ack
ros2 topic echo /vex/bridge_status --once
# If rate is 0 or node is absent:
ros2 node list | grep vex_bridge
```

**Fix — Restart the bridge node:**

If running via the launch file, `Ctrl+C` the launch and re-run:

```bash
ros2 launch vexy_ros vexy.launch.py
```

If running standalone:

```bash
pkill -f vex_bridge_node
ros2 run vexy_ros vex_bridge_node \
  --ros-args -p serial_port:=auto -p baud_rate:=115200
```

**If the Brain itself is at fault** (watchdog tripped, program not running):

1. On the V5 Brain, confirm the driver program is running (not paused at a print statement).
2. Power-cycle the Brain if needed.
3. Re-plug the USB cable.
