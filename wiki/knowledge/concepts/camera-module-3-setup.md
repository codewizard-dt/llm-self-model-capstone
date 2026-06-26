---
id: camera-module-3-setup
title: Camera Module 3 — Setup, Packages, and Verification
aliases: [Pi Camera Module 3 setup, Camera Module 3 setup, VEXY camera setup]
updated: 2026-06-26
tags: [concept, hardware, raspberry-pi, camera, setup, vision]
sources:
  - ../../entities/tools/pi-camera-module-3.md
  - ../../sources/vision-vex-architecture.md
  - ../sources/vision-stack-audit.md
  - ../sources/ros2-camera-calibration-vexy.md
---

# Camera Module 3 — Setup, Packages, and Verification

Step-by-step setup procedure for the relates_to::[[pi-camera-module-3]] on a Raspberry Pi 5 running Bookworm. Covers cable connection, OS enablement, Python package installs, and a minimal verification script.

## 1. Physical Connection

The Pi 5 uses a **22-pin 0.5mm "mini" FPC** camera connector. Camera Module 3 ships with a 15-pin 1mm standard cable — the wrong size for Pi 5. **Since December 4, 2025, the module ships with both cables in the box** (150mm standard + 200mm Pi 5 adapter). Use the 200mm adapter; no separate purchase needed for new orders. Standalone adapter cables cost $1–$3 from Raspberry Pi if you have an older module.

Plug the adapter into the `CAM/DISP 0` (or `CAM/DISP 1`) port on the Pi 5 with the ribbon contacts facing away from the USB ports.

## 2. OS / Driver Enablement

On **Bookworm** (the recommended Raspberry Pi OS release per relates_to::[[rpi5-mac-connection]]):
- The `libcamera` stack and `picamera2` are **pre-installed** — no `apt install` needed.
- The camera interface is **enabled by default** on Bookworm. If disabled, run `sudo raspi-config` → Interface Options → Camera → Enable.
- Reboot after enabling.

Quick CLI smoke test (no Python required):
```bash
rpicam-hello --timeout 5000
```
This opens a 5-second preview window. If it shows a live image, the driver, ribbon cable, and sensor are all working.

## 3. Python Packages

| Package | Install command | Purpose |
|---|---|---|
| `picamera2` | pre-installed (Bookworm) | Camera capture → numpy array |
| `opencv-python` | pre-installed (Bookworm) | Frame processing, color detection, ArUco fallback |
| `ultralytics` | `uv pip install ultralytics` | YOLO11n object detection |
| `apriltag` | `uv pip install apriltag` | Workspace localization via printed fiducial tags |

After installing `ultralytics`, export the model to Pi-optimized NCNN format:
```bash
yolo export model=yolo11n.pt format=ncnn
```
This is required to reach the ~8–10 FPS throughput documented in relates_to::[[vision-vex-architecture]].

## 4. Minimal Verification Script

```python
from picamera2 import Picamera2

cam = Picamera2()
cam.configure(cam.create_preview_configuration({"size": (640, 480)}))
cam.start()
frame = cam.capture_array()
print(frame.shape)  # expected: (480, 640, 3)
cam.stop()
```

A `(480, 640, 3)` output confirms the camera is wired, recognized by the OS, and delivering BGR frames. Pass the `frame` directly to OpenCV or YOLO:

```python
from picamera2 import Picamera2
import cv2

cam = Picamera2()
cam.configure(cam.create_preview_configuration({"size": (640, 480)}))
cam.start()

while True:
    frame = cam.capture_array()
    cv2.imshow("Camera Module 3", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.stop()
cv2.destroyAllWindows()
```

## 5. YOLO Smoke Test

```python
from picamera2 import Picamera2
from ultralytics import YOLO

cam = Picamera2()
cam.configure(cam.create_preview_configuration({"size": (640, 480)}))
cam.start()

model = YOLO("yolo11n_ncnn_model")  # after export step above
frame = cam.capture_array()
results = model(frame)
print(results[0].boxes)  # detected bounding boxes
cam.stop()
```

First inference takes ~3 seconds to load the model; subsequent frames run at 8–10 FPS. Plan a warm-up phase before starting the task loop.

## 6. AprilTag Smoke Test

```python
import apriltag
import cv2
from picamera2 import Picamera2

cam = Picamera2()
cam.configure(cam.create_preview_configuration({"size": (640, 480)}))
cam.start()

detector = apriltag.Detector()
frame = cam.capture_array()
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
detections = detector.detect(gray)
for d in detections:
    print(d.tag_id, d.pose_t)  # tag ID + 3D translation
cam.stop()
```

Print tag36h11 family tags at 100mm × 100mm and tape them to workspace walls. The detector returns `{tag_id, pose_t, pose_R}` per tag.

## Key Constraints

- **USB bandwidth**: Camera Module 3 uses the CSI ribbon, not USB — the V5 Brain serial link on `/dev/ttyACM0` is unaffected.
- **Latency**: ~40ms end-to-end, vs ~100ms for a USB webcam. Relevant when the robot is moving quickly.
- **YOLO warm-up**: ~3s first-inference delay. Build a warm-up call into the startup sequence.
- **Pi 5 cable connector**: 22-pin 0.5mm only — do not force the 15-pin 1mm cable into the Pi 5 port.

## 7. ROS 2 Jazzy Managed Stack (vexy Pi)

On the vexy Pi (Ubuntu 24.04 + ROS 2 Jazzy), the camera is **not** driven by picamera2 directly. Instead, the full camera-to-AprilTag chain runs as a ROS 2 stack managed by `vexy-ros-stack.service`:

```
camera_ros (libcamera fork) → image_proc rectify → apriltag_ros → /tf
```

The service ExecStart passes `camera_fps:=30` and `camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml` to the launch file. To restart the managed stack:

```bash
systemctl --user restart vexy-ros-stack.service
ros2 topic hz /camera/image_raw   # health check
```

For full service unit details and the drop-in pattern, see relates_to::[[camera-stack-startup]] and relates_to::[[vexy-ros-runtime]].

## 8. Calibration and Rectified-Image Semantics

derived_from::[[vision-stack-audit]] clarifies that the active vexy Pi calibration source is the service override path:

```text
file:///home/vexy/calibration/imx708_wide_640x480.yaml
```

The package config `robot/ros2-runtime/config/imx708_wide_640x480.yaml` is a starter placeholder. Patching the repo YAML does not affect the managed robot unless the service override is changed or the measured file under `/home/vexy/calibration/` is updated.

Two ROS message details matter for downstream vision:

- `sensor_msgs/Image.step` is the full row length in bytes. Image conversion code must account for row stride instead of assuming `height * width * channels` tightly packed data.
- `sensor_msgs/CameraInfo.K` describes raw/distorted images, while `CameraInfo.P` is the projection matrix for processed/rectified images. Consumers of `/camera/image_rect` should use the rectified intrinsics from `P`, with `K` only as a fallback when appropriate.

derived_from::[[ros2-camera-calibration-vexy]] adds the calibration workflow expectation for this stack. The canonical ROS 2 reference path is `camera_calibration` / `cameracalibrator` on `/camera/image_raw`; the practical VEXY path is the headless `vexy_calibrate_camera` command, which writes the same kind of CameraInfo YAML without requiring a GUI on the Pi:

```bash
vexy_calibrate_camera --cols 8 --rows 6 --square-m 0.025 --samples 25 --out /home/vexy/calibration/imx708_wide_640x480.yaml
systemctl --user restart vexy-ros-stack.service
```

The checkerboard dimensions are inner-corner counts, so an `8x6` board has `9x7` printed squares. Capture samples across the full field of view, at near and far distances, with tilt/skew, and at the same camera resolution/focus/exposure used by runtime. After restart, verify `/camera/camera_info`, `/camera/image_rect`, and AprilTag `/tf`; loading a YAML alone is not proof that rectified vision is correct.

derived_from::[[pi-camera-module-3]]
derived_from::[[vision-vex-architecture]]
derived_from::[[vision-stack-audit]]
derived_from::[[ros2-camera-calibration-vexy]]
relates_to::[[raspberry-pi-5]]
relates_to::[[apriltag-library]]
relates_to::[[camera-stack-startup]]
relates_to::[[vexy-ros-runtime]]
relates_to::[[ros2-camera-calibration-workflow]]
