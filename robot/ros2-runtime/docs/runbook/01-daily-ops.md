# Daily Operations

**System:** Raspberry Pi 5 · Ubuntu 24.04 LTS · ROS 2 Jazzy
**Hostname:** vexy.local · **SSH user:** vexy

---

### SSH into the Pi

```bash
ssh vexy@vexy.local
# If mDNS fails, use the IP address directly:
ssh vexy@<IP_ADDRESS>
```

### Source the workspace (required in every new shell)

ROS 2 Jazzy base is sourced in `~/.bashrc`; the overlay must be sourced manually unless you add it there too:

```bash
source ~/ros2_ws/install/setup.bash
```

To add it permanently:

```bash
echo 'source ~/ros2_ws/install/setup.bash' >> ~/.bashrc
```

### Start the full stack

Launches both `camera_node` (Camera Module 3, IMX708) and `vex_bridge_node` (VEX V5 USB serial bridge):

```bash
ros2 launch vexy_ros vexy.launch.py
```

Override defaults if needed:

```bash
# Different serial port
ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1

# Higher resolution
ros2 launch vexy_ros vexy.launch.py camera_width:=1280 camera_height:=720 camera_fps:=30

# Both overrides
ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1 camera_width:=1280 camera_height:=720 camera_fps:=30
```

Default launch parameters:

| Parameter | Default | Notes |
|-----------|---------|-------|
| `serial_port` | `auto` | VEX V5 Brain user/program serial; prefers the `if02` by-id device |
| `baud_rate` | `115200` | Do not change |
| `camera_width` | `640` | |
| `camera_height` | `480` | |
| `camera_fps` | `15` | Converted to libcamera `FrameDurationLimits` |
| `camera_frame_id` | `camera_optical_frame` | Camera optical frame stamped into messages |
| `camera_info_url` | package config URL | Must be `file:///...`; replace starter config with measured calibration |
| `apriltag_config` | package config path | Tag family/ID/size YAML |

### Start individual nodes

**Camera node only:**

```bash
ros2 run camera_ros camera_node \
  --ros-args \
  -p width:=640 -p height:=480 -p fps:=15 \
  --remap ~/image_raw:=/camera/image_raw \
  --remap ~/camera_info:=/camera/camera_info
```

**VEX bridge node only:**

```bash
ros2 run vexy_ros vex_bridge_node \
  --ros-args \
  -p serial_port:=auto -p baud_rate:=115200
```

**Foxglove bridge only:**

```bash
ros2 launch vexy_ros vexy.launch.py  # foxglove_bridge starts automatically
```

### Stop the stack

Press `Ctrl+C` in the terminal running `ros2 launch`. All child nodes stop cleanly.

To kill a specific node by name:

```bash
ros2 lifecycle set /camera shutdown   # if lifecycle-managed
kill $(ros2 node info /camera | grep PID | awk '{print $2}')
```

Or simply kill by process name:

```bash
pkill -f camera_node
pkill -f vex_bridge_node
```

### Check running nodes

```bash
ros2 node list
# Expected output when full stack is running:
#   /camera
#   /vex_bridge
#   /foxglove_bridge   (if started separately)
```
