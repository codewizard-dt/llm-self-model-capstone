---
topic: How to include vision into a VEX V5 architecture (Raspberry Pi + webcam)
slug: vision-vex-architecture
researched: 2026-06-16
sources: [./sources.md]
---

# Research: How to Include Vision into a VEX V5 Architecture

> Add a Raspberry Pi 5 as a vision/AI coprocessor connected to the V5 Brain via USB serial. The Pi runs OpenCV + YOLO11n for object detection (~8 FPS at 640×480, no extra hardware) and the `apriltag` library for pose localization. The V5 Brain stays in VEXcode V5 Python handling motors, encoders, and safety stops. JSON over USB serial is the communication bridge. This extends the capstone's Task Telemetry Contract with a visual observation layer and enriches the self-model's gap analysis with both motor and perceptual residuals.

---

## Research Questions

1. What is the recommended two-computer architecture for adding vision to a VEX V5 robot?
2. How do you physically mount a Raspberry Pi and camera on a VEX V5 robot?
3. What serial protocol connects Pi to V5 Brain, and how does it work in VEXcode V5 Python?
4. What vision stack runs on a Pi 5 at usable FPS — YOLO, AprilTags, OpenCV baseline?
5. How does vision integration change the capstone's Task Telemetry Contract and self-model loop?

---

## Current State (Codebase)

No Brain-side code exists yet. From the wiki and flowchart:

- **Architecture flowchart** (`capstone-experiment.flowchart.md`): LLM Generator → Critics → SimValidate → BOM → Builder → Robot → Task Execution → Telemetry → Gap Analysis → LLM Generator. No perception layer exists in the current flowchart.
- **Toolchain decision** (`raw/research/vex-v5-advanced-toolchains/index.md`): Stage 1 is VEXcode V5 Python on the Brain; USB serial user port is the LLM integration path.
- **Task Telemetry Contract** (`wiki/knowledge/concepts/task-telemetry-contract.md`): currently defined for motor telemetry only (torque, current, velocity, position) for grab/pull/throw primitives. No visual observation fields.
- **Self-model** (`wiki/knowledge/concepts/llm-authored-self-model.md`): structural, capability, predictive, gap layers — currently no vision capability or visual prediction layer.
- **VEX V5 tool page** (`wiki/knowledge/entities/tools/vex-v5.md`): notes native AI Vision Sensor but recommends Pi-based approach for AI workloads.

---

## Key Findings

### 1. The Two-Computer Architecture

The canonical architecture from the ChatGPT consultation [S1] and supported by community implementations [S2][S3]:

```
USB Webcam / Pi Camera Module 3
│
▼
Raspberry Pi 5
(OpenCV, YOLO11n, AprilTag detection, LLM inference, telemetry aggregation)
│
USB cable — microUSB on V5 Brain → USB-A on Pi
│
▼
VEX V5 Brain
(VEXcode V5 Python: motors, encoders, gyros, safety stops)
│
▼
Robot Chassis
```

**Pi handles**: object detection, localization, path planning, LLM reasoning, telemetry logging.  
**V5 handles**: motor control, encoder reads, gyro, basic sensor I/O, safety stops.

This split is strongly preferable to running vision on the Brain because [S1]:
- The V5 Brain (Xilinx ZYNQ running MicroPython) has no pip, no camera interface, and no spare compute for inference.
- The Pi offloads all non-deterministic AI work, letting the Brain run a tight deterministic motor control loop.

### 2. Physical Mounting Options

**Option A — VEX standoffs (recommended for speed)** [S1]:
- VEX metal plate + M2.5 standoffs + Pi mounting holes.
- Pi is bolted directly to a flat VEX plate; no 3D printing needed.
- The Pi 5 mounting hole pattern is standardized (56mm × 85mm, M2.5 holes at corners).

**Option B — 3D printed mount** [S1]:
- Print a Pi tray + webcam bracket + cable management, attach with VEX screws.
- Cleanest solution if a 3D printer is available; used by most advanced teams.

**Camera choice**:
- *USB webcam (cheapest, fastest to start)*: Logitech C270, C920, or any UVC webcam. Mount with VEX angle brackets, zip ties, or 3D printed bracket. Works out of the box with OpenCV `VideoCapture(0)`.
- *Pi Camera Module 3 (better)* [S15]: lower latency (~40ms vs ~100ms), lighter, flexible 200mm ribbon cable routing. 12MP Sony IMX708 sensor with Phase Detection Autofocus; 75° FOV standard or 120° FOV Wide variant; 1080p50 video; 25×24mm PCB; from $25; in production until Jan 2030. Uses Picamera2 Python library (pre-installed in Raspberry Pi OS). Connects to Pi CSI port — no USB bandwidth competition with the V5 serial link.

### 3. Pi-V5 Serial Communication

**Connection** [S2][S3]:
- Cable: microUSB on V5 Brain (user port) → USB-A on Pi.
- Pi sees two ACM devices: `/dev/ttyACM0` and `/dev/ttyACM1`. Use `/dev/ttyACM0`.
- May need udev rules for consistent naming: `SUBSYSTEM=="tty", ATTRS{idVendor}=="2888", MODE="0666", SYMLINK+="vex_brain"`.

**V5 Brain side (VEXcode V5 Python)** [S4]:
```python
from vex import *
brain = Brain()

# Print JSON to USB serial (user port)
brain.screen.print('{"x":0,"y":0}')  # or use sys.stdout for raw bytes
```
The `print()` call goes to the USB user serial port by default in VEXcode Python.

**Pi side (Python pyserial)**:
```python
import serial, json
port = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)

# Send command to V5
cmd = {"forward": 0.4, "turn": -0.1}
port.write((json.dumps(cmd) + '\n').encode())

# Read telemetry from V5
line = port.readline().decode().strip()
telemetry = json.loads(line)
```

**Alternative (PROS RS-485)**: PROS `pros::Serial` on a Smart Port gives a second high-speed channel (up to 921,600 baud), decoupling the USB debug port from the AI link. Relevant only if Stage 2 PROS migration proceeds (see `raw/research/vex-v5-advanced-toolchains/index.md`).

### 4. Vision Stack Performance on Pi 5

**Baseline — OpenCV (zero extra deps)**:
- Color detection, contour finding, blob detection: runs at 30+ FPS at 640×480.
- Useful for detecting colored game objects (cubes, rings, balls) — the capstone's grab/pull/throw primitives often involve specific-colored objects.

**YOLO11n with NCNN quantization** [S5][S6]:
- Pi 5 CPU only (no hardware accelerator): ~8–10 FPS at 640×480.
- At 240×240: 25+ FPS with INT8 quantization.
- YOLO26n (newest, hardware-aware): 7.79 FPS at 640×640 on Pi 5 [S7].
- For the capstone (robot manipulating slow-moving objects), 8 FPS is more than sufficient.
- **Install**: `pip install ultralytics`, then `yolo export model=yolo11n.pt format=ncnn`.

**Hailo AI Kit accelerator** (optional upgrade):
- Pi 5 + Hailo-8L M.2 HAT: 41 FPS at YOLOv8s 640×640 [S8].
- Adds ~$70 and HAT installation; not needed for the capstone demo.

**AprilTags for localization** [S9][S10][S11]:
- `pip install apriltag` (wraps the official C library).
- Single call: `detector.detect(gray_frame)` returns tag id + 3D pose (translation + rotation).
- Place printed tags around the workspace; Pi detects and returns `{tag_id, x, y, z, heading}` in real time.
- Enables the robot to know *where it is in the workspace* without odometry calibration.
- OpenCV ArUco (`cv2.aruco.detectMarkers`) is a built-in alternative: no extra pip install.

### 5. How Vision Changes the Capstone Architecture

**Extended Task Telemetry Contract**:

The current contract has only motor fields. Vision adds a visual observation block:

```json
{
  "task": "grab",
  "predicted": {
    "torque_Nm": 1.2,
    "object_detected": true,
    "object_bbox": [120, 80, 200, 160]
  },
  "observed": {
    "torque_Nm": 1.4,
    "object_detected": true,
    "object_bbox": [118, 83, 198, 162]
  },
  "gap": {
    "torque_residual": 0.2,
    "detection_match": true,
    "bbox_iou": 0.96
  }
}
```

The LLM self-model can now predict *visual* outcomes ("after the arm extends, the object should be in the lower-left quadrant of the camera frame") and compare against what the camera actually observes.

**Extended self-model capability layer**:

The LLM's structural self-model currently describes motor/mechanical configuration. Vision adds:
- `"camera_fov_deg": 78` — field of view based on webcam spec
- `"camera_mount_height_mm": 180` — derived from VEX plate geometry
- `"visual_range_mm": [100, 800]` — estimated detection range for given object size

**AprilTag localization → richer gap analysis**:

Currently the gap model feeds raw encoder counts. With AprilTags:
- Predicted spatial outcome: `{x: 500, y: 0, heading: 0}` (self-model predicts robot pose after action)
- Observed spatial outcome: `{x: 487, y: -12, heading: 2}` (camera reads pose from AprilTag landmarks)
- Gap: `{dx: -13, dy: -12, dtheta: 2}` (residual that feeds next-generation self-model revision)

This directly parallels the Hart / Scassellati visual self-observation lineage (`wiki/knowledge/entities/people/justin-hart.md`) — the robot observes its own outcome visually and uses that residual to correct its self-model.

---

## Constraints

1. **VEX competition rules forbid Raspberry Pi** — `<R16>a` prohibits external microcontrollers in competition. Not relevant here (capstone is not a competition).
2. **USB serial is single-channel** — the V5 USB user port and the programming/upload port share bandwidth. During demo, either monitor telemetry OR upload code, not both simultaneously. (PROS Smart Port RS-485 solves this.)
3. **Pi requires power supply** — the Pi 5 draws 5W–15W; VEX V5 battery cannot power it directly. A USB-C PD power bank or separate supply must be mounted on the robot.
4. **YOLO model loading time** — first inference on Pi 5 takes ~3 seconds to load the model into memory; subsequent frames are fast. Plan for a warm-up phase before the task begins.
5. **VEXcode V5 Python serial output** — `brain.screen.print()` goes to USB serial but also to the Brain's screen. Use explicit `sys.stdout.write()` for cleaner serial-only output. The baud rate is fixed by the V5 at 115200.

---

## Solution Comparison

| Criteria | USB Webcam + Pi 5 | Pi Camera Module 3 + Pi 5 | VEX AI Vision Sensor (native) |
|---|---|---|---|
| **Cost** | $25–80 | $25 (standard), $35 (Wide) [S15] | Included in some kits |
| **Resolution** | 720p–1080p | 12MP / 1080p50 [S15] | 640×480 |
| **FPS (YOLO)** | 8–10 FPS | 8–10 FPS | N/A (color+AprilTag only) |
| **FOV** | 60–90° (varies) | 75° (standard) or 120° (Wide) [S15] | ~60° |
| **Latency** | ~100ms | ~40ms | ~20ms |
| **AI capability** | Full (YOLO, LLM, any model) | Full | Limited (color signatures, AprilTags) |
| **Setup friction** | Low (plug in) | Medium (ribbon cable) | Very low (Smart Port) |
| **Demo timeline risk** | Low | Low–Medium | Low |
| **Fits capstone** | Yes (full perception layer) | Yes (best option) | Partial (no external ML) |

---

## Recommendation

**Start with a USB webcam + Raspberry Pi 5** for the Stage 1 demo (Jun 29 2026). Plug-and-play, zero hardware risk, and already sufficient for object detection and AprilTag localization at 8 FPS.

**Implementation outline**:

1. **Mount**: bolt Pi 5 to a VEX metal plate with M2.5 standoffs; attach USB webcam to a VEX angle bracket on the robot's front.
2. **Power**: add a USB-C PD power bank (20,000 mAh) zip-tied to the robot frame.
3. **Connect**: microUSB from V5 Brain user port to Pi USB-A.
4. **Brain-side (VEXcode V5 Python)**:
   - Main loop: read motor telemetry → emit JSON over `sys.stdout` → read JSON commands from `sys.stdin` → execute motor actions.
5. **Pi-side (Python)**:
   - `vision_loop.py`: capture frame → run YOLO11n NCNN → detect AprilTags → emit `{detections, pose}` JSON.
   - `serial_bridge.py`: receive telemetry from V5 → merge with vision observations → write to telemetry log → send next command to V5.
   - `llm_loop.py`: read telemetry log → build gap JSON → call Claude API → parse next motor command.
6. **Extend Task Telemetry Contract**: add `predicted.object_detected`, `observed.object_detected`, `observed.pose` fields.
7. **Print AprilTags**: generate tag36h11 family tags, print at 100mm × 100mm, tape to workspace walls.

**Risks and mitigations**:
- *Pi power draw on robot*: Pi 5 can draw up to 5A at 5V under load. Use a 65W USB-C PD power bank; do not power from V5 battery.
- *Serial timing*: if the V5 Python loop is too slow to emit telemetry at useful frequency, increase the V5 loop rate or buffer multiple readings per JSON emission.
- *YOLO latency*: 8 FPS means 125ms/frame. If the robot moves fast, detections lag position. For the capstone (slow manipulation tasks), this is acceptable.
- *USB cable tension*: the microUSB port on the V5 Brain is fragile. Use a right-angle microUSB cable and secure it with a zip tie to the frame.

---

## Next Steps

- `/task-add Add Raspberry Pi 5 + USB webcam to VEX V5 robot for vision integration`
- `/task-add Extend Task Telemetry Contract with visual observation fields`
- `/decision-create Choose camera type: USB webcam vs Pi Camera Module 3 for Stage 1 demo`
- **Ingest**: `/wiki-ingest raw/research/vision-vex-architecture/index.md`
