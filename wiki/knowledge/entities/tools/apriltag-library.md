---
id: apriltag-library
title: AprilTag Library
aliases: [apriltag Python library, AprilTags, apriltag pip package]
updated: 2026-06-16
sources:
  - ../../../raw/research/apriltags/index.md
  - ../../../raw/research/vision-vex-architecture/index.md
tags: [tool, vision, fiducial, localization, python, raspberry-pi]
---

# AprilTag Library

The `apriltag` Python package (`pip install apriltag`) wraps the official C library from the APRIL Robotics Lab at the University of Michigan (Edwin Olson, ICRA 2011). It is the primary localization tool in the capstone's Raspberry Pi 5 vision stack.

**What it does**: given a grayscale camera frame, `detector.detect(gray_frame)` returns a list of detected AprilTag fiducial markers, each with: integer `tag_id`, center pixel coordinates, corner pixels, and a 3D pose estimate (rotation matrix + translation vector relative to the camera). From the pose and known tag placement geometry, the robot's workspace position `{x_mm, y_mm, heading_deg}` is computable without odometry calibration.

**Tag families**: `tag36h11` is the standard robotics family (36-bit payload, 11-bit minimum Hamming distance) and is what the capstone uses. Tags are generated and printed at 100 mm × 100 mm and taped to stable fixed points in the workspace. At that size the library detects reliably at 30–80 cm range.

**Alternatives**:
- `cv2.aruco.detectMarkers(gray, cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11))` — OpenCV ArUco module; no extra pip install; compatible with the same printed tags
- VEX V5 native AI Vision Sensor — hardware-accelerated AprilTag detection via Smart Port, ~20 ms latency; no external ML possible alongside it

**Capstone role**: runs in `vision_loop.py` on the relates_to::[[raspberry-pi-5]] alongside YOLO11n NCNN object detection. Outputs `{tag_id, x, y, heading}` JSON over the serial bridge. This JSON populates `observed.pose` in the relates_to::[[task-telemetry-contract]], and the gap fields `dx`, `dy`, `dtheta` feed the spatial residual loop in the relates_to::[[llm-authored-self-model]].

**Origin**: APRIL Robotics Laboratory, University of Michigan. "AprilTag: A robust and flexible visual fiducial system," ICRA 2011, Edwin Olson. Homepage: https://april.eecs.umich.edu/software/apriltag

used_in::[[vision-vex-architecture]]
feeds::[[task-telemetry-contract]]
enriches::[[llm-authored-self-model]]
runs_on::[[raspberry-pi-5]]
mitigates::[[reality-gap]]
