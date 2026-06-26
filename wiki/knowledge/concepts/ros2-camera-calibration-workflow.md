---
id: ros2-camera-calibration-workflow
title: ROS 2 Camera Calibration Workflow
aliases: [ROS camera calibration workflow, cameracalibrator workflow, VEXY camera calibration]
updated: 2026-06-26
sources:
  - ../sources/ros2-camera-calibration-vexy.md
tags: [concept, ros2, camera, calibration, vision]
---

# ROS 2 Camera Calibration Workflow

ROS 2 camera calibration for VEXY starts with a known checkerboard on the raw camera stream. The canonical reference tool is `camera_calibration`'s `cameracalibrator`, run against `/camera/image_raw` with the correct inner-corner count and square size. It estimates intrinsics and distortion, then stores them as `sensor_msgs/CameraInfo` data that camera drivers can publish for downstream rectification and pose estimation.

For headless robot operation, VEXY can use its own `vexy_calibrate_camera` command instead of the GUI-oriented calibrator. The command subscribes to the raw image stream, detects checkerboard corners with OpenCV, collects samples, runs `cv2.calibrateCamera`, and writes a ROS CameraInfo YAML. This is not a semantic shortcut: it is the same calibration shape, adapted to the managed relates_to::[[vexy-ros-runtime]] environment.

Calibration is specific to resolution, lens mode, focus, and mounting. A valid run should record the image topic, resolution, board inner-corner dimensions, square size in meters, sample count, timestamp, output path, and reprojection error. Board poses should cover the full field of view, include near/far distances, and include tilt/skew, not only centered flat views.

After writing the YAML, the robot must restart or reload `camera_ros` with the measured file as `camera_info_url`, then verify the loaded stack:

- `/camera/camera_info` has nonzero `K`, `D`, and `P` values matching the expected YAML.
- `/camera/image_rect` is live from `image_proc`.
- AprilTag detections produce plausible `/tf` poses from the rectified image stream.
- Object-projection consumers use rectified-image intrinsics from `CameraInfo.P` when processing `/camera/image_rect`.

derived_from::[[ros2-camera-calibration-vexy]]
relates_to::[[camera-module-3-setup]]
relates_to::[[vexy-ros-runtime]]
relates_to::[[object-indication-projection]]
