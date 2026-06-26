---
id: vision-stack-audit
title: Vision Stack Audit
aliases: [Robot Vision Stack Audit, Full Vision Stack Analysis]
updated: 2026-06-26
sources:
  - ../../raw/research/vision-stack-audit/index.md
  - ../../raw/research/vision-stack-audit/sources.md
  - ../../raw/research/vision-stack-audit/index-2.md
  - ../../raw/research/vision-stack-audit/sources-2.md
tags: [vision, ros2, calibration, pickup, audit]
---

# Vision Stack Audit

The audit traces the live pickup failure through the ROS 2 vision path: `camera_ros` publishes raw frames and CameraInfo, `image_proc` produces `/camera/image_rect`, `yellow_ball_detector` and optional `yolo_ncnn` publish object bboxes, `object_indication` projects those bboxes into camera-relative coordinates, and the operator consumes those coordinates for pickup. **The core finding is that the final pickup decision treats monocular bbox-derived object indications as a hard physical capture predicate, even though the bbox may only describe the visible fragment of an occluded ball.** derived_from::[[vexy-ros-runtime]] relates_to::[[object-indication-projection]]

The AprilTag path is not the same failure mode. AprilTag localization uses calibrated `/camera/image_rect` + `/camera/camera_info` through `apriltag_ros`, converts ROS optical-frame tag transforms into the project planar convention, and composes the configured camera offset into robot frame. The object path instead estimates depth from apparent bbox size (`known_diameter * focal_length / bbox_pixels`), which breaks near the claw when the motor or jaws hide part of the ball. relates_to::[[apriltag-workspace-layout]] relates_to::[[camera-module-3-setup]]

The follow-up audit adds lower-level correctness findings: image conversion currently assumes tightly packed image rows instead of honoring ROS `Image.step`; rectified object projection should use `CameraInfo.P` rather than raw-image `K`; `object_indication` publishes only positive sightings, so absence is not represented as a timestamped state; and the active Pi calibration source is `/home/vexy/calibration/imx708_wide_640x480.yaml`, not the starter YAML committed in the package. The tests cover ideal synthetic yellow circles and ideal bbox projection, but not partial occlusion, stale/no-detection behavior, padded rows, negative `forward_m`, or final physical delivery.

The recommended architecture is **coarse metric approach followed by image-space claw-mouth capture evidence and effector telemetry possession evidence**. Object indications remain useful for finding and approaching a fully visible ball, but final close should require a pickup-specific ROI detector with temporal stability and labeled calibration frames. relates_to::[[claw-mouth-pickup-vision]]
