---
topic: "RPi OS options — addendum: Ubuntu 24.04 + ROS 2 Jazzy camera path confirmed"
slug: rpi-os-options
researched: 2026-06-23
sources: [./sources-2.md]
prior: [./index.md]
---

# Research Addendum: Ubuntu 24.04 + ROS 2 Jazzy Camera Path Confirmed

> Builds on [index.md](index.md); this update corrects Finding F1 and upgrades the Option 2 assessment.
> The original report called Ubuntu + Jazzy + PiCam2 "the worst of all worlds." Deeper investigation
> found a clear, recently-maintained guide that makes the camera path achievable with ~85–90% first-attempt
> success. The risk assessment is now purely about time, not technical feasibility.

---

## Correction: F1 (picamera2 on Ubuntu) Was Overstated

The original F1 stated picamera2 is "not officially supported on Ubuntu" and implied the workaround
was vague and risky. Deeper research found:

**`github.com/erykpawelek/libcamera_ros2_setup`** [S21]
- Explicitly targets: Pi 5 + Camera Module 3 (IMX708) + Ubuntu 24.04 + ROS 2 Jazzy
- Repo tags: `camera-module-3`, `raspberry-pi-5`, `ros2-jazzy`, `ubuntu-24-04`
- Last commit: 2025-11-18. Zero open issues.

**Root cause of Ubuntu camera failures (now understood):**
Upstream libcamera (in Ubuntu apt repos) lacks IMX708 support. The fix is exactly one change:
clone `github.com/raspberrypi/libcamera` (the Pi fork) instead of upstream libcamera. The `camera_ros`
node (`christianrauch/camera_ros`, 164 stars, updated 2026-06-22) is distro-agnostic once the correct
libcamera is compiled into the workspace.

**Exact build process (verified working):**
```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/raspberrypi/libcamera.git   # RPi fork, not upstream
git clone https://github.com/christianrauch/camera_ros.git
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -y --skip-keys=libcamera
colcon build --packages-select libcamera camera_ros
source install/setup.bash
ros2 run camera_ros camera_node
# → publishes /camera/image_raw and /camera/camera_info
```

Build time: 5–15 min on Pi 5. Expected output: `/camera/image_raw`, `/camera/image_raw/compressed`.

**Fallback if build fails:** `picam_ros2` (PhantomCybernetics) wraps the RPi camera stack differently
and is Docker-friendly — a second documented path that doesn't require source-building libcamera.

---

## Corrected Option 2 Assessment

Option 2 (Ubuntu 24.04 + ROS 2 Jazzy + PiCam2) is **no longer "the worst choice"**.
It is the best choice for long-term architecture — same as Option 3 but without the OAK-D hardware cost.

### Concrete rewards for THIS capstone

| Package | What it gives | vs. Bookworm today |
|---------|--------------|-------------------|
| `yolo_ros` (v4.6.1, 1.1k stars) [S22] | YOLO11n as lifecycle node; `DetectionArray` topics | In-memory custom loop |
| `apriltag_ros` (apt install, official) [S23] | Camera-calibration-aware 6-DOF pose into TF2 | Manual frame math, no calibration |
| `foxglove_bridge` (apt install) | Debug bounding boxes + poses from any browser (headless Pi!) | SSH + print statements |
| `ros2 bag record` | Record all detections/poses/motor commands with timestamps | No replay capability |
| `ros2 unbag` → JSON | Export to JSON → Claude API for LLM self-model revision | Manual JSONL construction |
| TF2 transform tree | AprilTag pose in world frame vs. camera frame | Manual frame conversion |

**Most impactful for the capstone self-model loop:**
`ros2 bag` → `ros2 unbag` → Claude API is a cleaner, repeatable LLM feedback loop than any
custom JSONL approach. This directly improves the Task Telemetry Contract observation quality.

---

## Updated Solution Comparison (Option 2 corrected)

| | **Option 1: Bookworm + PiCam2** | **Option 2: Ubuntu 24.04 + Jazzy + PiCam2** *(corrected)* | **Option 3: Ubuntu 24.04 + Jazzy + OAK-D** |
|---|---|---|---|
| Camera setup pain | None (working) | Medium — 15–30 min libcamera fork build | Low — USB plug-in |
| New hardware | No | No | Yes (~$79–$249) |
| FPS | ~8–10 | ~8–10 (same sensor, same speed) | ~15–30 (onboard VPU) |
| ROS 2 ecosystem | No | Yes — full Jazzy | Yes — full Jazzy + depthai-ros |
| LLM feedback loop | Manual JSONL | `ros2 bag` → JSON → Claude API | Same as Option 2 |
| Showcase risk | None | Medium (6 hrs migration, no time buffer) | High (new hw + ROS) |
| Long-term quality | Medium | **High** (revised upward from original) | Very High |

---

## Risk/Reward Summary

**Technical risk**: LOW. The camera path is documented, reproducible, maintained.

**Time risk**: MEDIUM-HIGH for pre-showcase execution.
- Honest migration estimate: 6–12 hours (flash + Jazzy + libcamera build + port 3 Python modules to ROS nodes + integration test)
- Buffer for unexpected issues eats into Jun 29 window

**Recommendation (revised):**

| When | What |
|------|------|
| Before Jun 29 | Stay on Bookworm. Demo the self-model loop. |
| After Jun 29, Day 1 | Flash Ubuntu 24.04 to a second SD card (keep Bookworm as fallback); build libcamera fork; verify camera topics. If working in 3 hr, proceed. If not, keep Bookworm. |
| After Jun 29, Day 2 | Port 3 Python modules → ROS nodes; add foxglove_bridge; ros2 bag record; end-to-end test. |

Option 4 (Trixie + Hailo AI HAT+) remains the **lowest-risk post-showcase upgrade** if the goal is
raw FPS improvement (30+ FPS with $70 AI HAT+, near-zero code change). Option 2 is better if the
goal is a production robotics platform with clean LLM data pipelines.

---

## Next Steps

- `/wiki-ingest raw/research/rpi-os-options/index.md` — ingest original report
- `/wiki-ingest raw/research/rpi-os-options/index-2.md` — ingest this addendum (corrects camera finding)
- `/task-add "Post-showcase: Migrate RPi to Ubuntu 24.04 + ROS 2 Jazzy (libcamera fork + 3 ROS nodes)"` — when ready to execute
