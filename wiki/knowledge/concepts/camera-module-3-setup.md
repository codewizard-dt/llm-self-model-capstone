---
id: camera-module-3-setup
title: Camera Module 3 — Setup, Packages, and Verification
updated: 2026-06-19
tags: [concept, hardware, raspberry-pi, camera, setup, vision]
sources:
  - ../../entities/tools/pi-camera-module-3.md
  - ../../sources/vision-vex-architecture.md
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
| `ultralytics` | `pip install ultralytics` | YOLO11n object detection |
| `apriltag` | `pip install apriltag` | Workspace localization via printed fiducial tags |

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

derived_from::[[pi-camera-module-3]]
derived_from::[[vision-vex-architecture]]
relates_to::[[raspberry-pi-5]]
relates_to::[[apriltag-library]]
