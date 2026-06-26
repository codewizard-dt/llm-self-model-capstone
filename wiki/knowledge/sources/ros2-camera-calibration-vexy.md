---
id: ros2-camera-calibration-vexy
title: ROS 2 Camera Calibration for the VEXY Pi Camera Stack
aliases: [VEXY ROS 2 camera calibration, VEXY camera calibration workflow]
updated: 2026-06-26
sources:
  - ../../raw/research/ros2-camera-calibration-vexy/index.md
  - ../../raw/research/ros2-camera-calibration-vexy/sources.md
tags: [source, vision, ros2, calibration, camera]
---

# ROS 2 Camera Calibration for the VEXY Pi Camera Stack

This research covers how to calibrate the relates_to::[[pi-camera-module-3]] in the VEXY ROS 2 stack, where a Raspberry Pi 5 runs Ubuntu 24.04, relates_to::[[ros2-jazzy]], `camera_ros`, `image_proc`, and `apriltag_ros`. The standard ROS 2 path is checkerboard calibration over `/camera/image_raw`, then publishing calibrated `CameraInfo` through `camera_info_url` or a `set_camera_info` service so rectification and AprilTag pose estimation use measured intrinsics.

For VEXY, the practical primary workflow is the existing headless `vexy_calibrate_camera` utility in relates_to::[[vexy-ros-runtime]]. It already follows the OpenCV checkerboard calibration pattern and writes a ROS CameraInfo YAML, including the active runtime path `/home/vexy/calibration/imx708_wide_640x480.yaml`. The research recommends treating it with the same discipline as ROS `cameracalibrator`: exact board dimensions, varied board poses across the image, matching runtime resolution/focus/exposure, saved metadata, reprojection error thresholds, and post-load validation.

The key operational distinction is that loading a YAML does not itself prove the vision stack is correct. VEXY should verify nonzero `/camera/camera_info` intrinsics, a live `/camera/image_rect` stream, and plausible AprilTag `/tf` output after the managed stack restarts. This source strengthens relates_to::[[ros2-camera-calibration-workflow]] and the existing relates_to::[[camera-module-3-setup]] note that the active calibration is the measured Pi-side file, not the package starter YAML.

derived_from::[[ros2-camera-calibration-vexy]]
relates_to::[[vexy-ros-runtime]]
relates_to::[[camera-module-3-setup]]
relates_to::[[ros2-camera-calibration-workflow]]
relates_to::[[ros2-jazzy]]
relates_to::[[pi-camera-module-3]]
