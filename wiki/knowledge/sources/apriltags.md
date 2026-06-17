---
id: apriltags
title: "Research: AprilTags — What They Are and How They Fit the Capstone"
updated: 2026-06-16
sources:
  - ../../raw/research/apriltags/index.md
tags: [source, research, apriltag, fiducial, localization, vision, robotics]
---

# Research: AprilTags — What They Are and How They Fit the Capstone

A research report (2026-06-16) consolidating what AprilTags are and how they integrate into the capstone architecture. The architecture decision was already committed in relates_to::[[vision-vex-architecture]]; this report is the standalone explainer for anyone new to the concept.

**AprilTags are printable fiducial markers** developed at the University of Michigan APRIL Robotics Lab (Edwin Olson, ICRA 2011). They work like a QR code purpose-built for robotics: a single camera frame yields the tag's integer ID plus **full 6-DOF pose** (translation vector + rotation matrix) relative to the camera — position and orientation, not just "tag visible." The C library has no external dependencies and runs real-time on a Raspberry Pi. The `tag36h11` family (36-bit payload, 11-bit Hamming distance) is the standard robotics choice and is what the capstone uses.

**In this project, AprilTags serve as the workspace indoor GPS.** Print `tag36h11` tags at 100 mm × 100 mm, tape them to stable fixed points in the workspace. The relates_to::[[raspberry-pi-5]] camera detects them and computes the robot's `{x, y, heading}` after each action — no odometry calibration required. Implementation: `pip install apriltag`; single detection call is `detector.detect(gray_frame)` which returns a list of detections each carrying `tag_id`, center pixel, and pose. An OpenCV ArUco alternative (`cv2.aruco.detectMarkers`) is built into OpenCV and requires no extra install.

**Two detection paths exist**: the Pi 5 coprocessor path (recommended — runs YOLO + AprilTag + LLM inference in one pipeline) and the VEX V5 native AI Vision Sensor (built-in AprilTag support since VEXcode V5 4.0, late 2024 — lower latency but no external ML). **AprilTags close the spatial gap loop** in the relates_to::[[task-telemetry-contract]]: the LLM self-model predicts a robot pose after each action; the AprilTag camera observation is the ground truth; the residuals `{dx, dy, dtheta}` populate the gap block alongside motor telemetry, giving the LLM Generator a richer correction signal to revise the relates_to::[[llm-authored-self-model]]'s kinematic predictions. This directly parallels the Hart/Scassellati visual self-observation lineage the capstone traces its intellectual roots to.

derived_from::[[vision-vex-architecture]]
extends::[[task-telemetry-contract]]
extends::[[llm-authored-self-model]]
mitigates::[[reality-gap]]
uses::[[raspberry-pi-5]]
uses::[[apriltag-library]]
uses::[[vexcode]]
