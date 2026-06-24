# Slice: camera-rectified-tags

| Field | Value |
|---|---|
| Feature | ros2-align-to-tag |
| Stack | coprocessor |
| Depends on | - |

## What this slice delivers

Turn the current camera launch into a calibrated AprilTag pose pipeline: Camera Module 3 through `camera_ros`, nonzero calibrated `CameraInfo`, `image_proc` rectification, and `apriltag_ros` consuming the rectified image stream. This slice proves tag pose before any robot motion.

## Scope

- Keep `camera_ros` as the Camera Module 3 ROS boundary.
- Add launch/config arguments for calibration file/URL, camera frame ID, image dimensions, and tag configuration.
- Verify the installed `camera_ros` frame-rate control semantics on the Pi; update the launch file so the configured frame rate is actually honored or clearly documented as best-effort.
- Add `image_proc` wiring that publishes a rectified image topic.
- Add `apriltag_ros` wiring against the rectified image and camera info topics.
- Document how to calibrate/load Camera Module 3 calibration.
- Document how to print/configure the first proof tag: family, tag ID, physical tag size, and expected standstill pose sanity checks.
- Add static/local tests where feasible: launch syntax, parameter names, config file loading, and docs command consistency.

## Topic expectations

Use stable topic names unless implementation evidence shows a better ROS convention:

- `/camera/image_raw`
- `/camera/camera_info`
- `/camera/image_rect`
- AprilTag detection and/or TF topics as produced by the installed `apriltag_ros` package.

The exact AprilTag executable/node name must be verified against the installed Jazzy package during implementation and recorded in the runbook.

## Acceptance

1. Launch config includes a calibration URL/path and does not silently accept zero/empty calibration for tag-pose proof.
2. `/camera/image_raw` publishes live frames with stable timestamps and frame IDs.
3. `/camera/camera_info` publishes nonzero calibration values.
4. `/camera/image_rect` publishes rectified frames from `image_proc`.
5. `apriltag_ros` consumes rectified image plus camera info, not raw image alone.
6. A stationary printed tag produces a stable detection/pose or TF in the documented topic.
7. The runbook includes exact commands for camera proof, rectification proof, and tag proof.
8. Local checks that do not require hardware pass.

## Out of scope

- YOLO/object detection.
- Object pickup or scoring.
- OAK-D/depth camera work.
