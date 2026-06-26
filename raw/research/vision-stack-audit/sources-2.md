---
topic: "Full follow-up analysis of the entire robot vision stack after live pickup/delivery failures"
slug: vision-stack-audit
researched: 2026-06-26
builds_on: [./sources.md]
---

# Primary Sources — Vision Stack Audit Addendum

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S2-1 | codebase | `robot/ros2-runtime/launch/vexy.launch.py::_launch_nodes`, `generate_launch_description` | 2026-06-26 | Full launched graph and default parameters for camera, rectification, AprilTag, yellow detector, object projection, scene map, and bridge. |
| S2-2 | codebase | `robot/ros2-runtime/src/vexy_ros/yolo_ncnn_node.py::image_to_bgr_array` | 2026-06-26 | Image conversion assumes tightly packed `height * width * channels` bytes and does not use `msg.step`. |
| S2-3 | codebase | `robot/ros2-runtime/src/vexy_ros/object_detection.py::intrinsics_from_camera_info`, `indication_from_detection` | 2026-06-26 | Object projection reads `CameraInfo.k` and computes depth from bbox pixel size and known dimensions. |
| S2-4 | codebase | `robot/ros2-runtime/src/vexy_ros/yellow_ball_detector_node.py::YellowBallDetectorNode`, `detect_yellow_balls` | 2026-06-26 | HSV detector parameters, contour extraction, bounding-rectangle output, and lack of full-object/partial-object state. |
| S2-5 | codebase | `robot/ros2-runtime/src/vexy_ros/yolo_ncnn_node.py::YoloNcnnNode`, `DirectNcnnYoloDetector`, `parse_yolo_row`, `non_max_suppression` | 2026-06-26 | Optional YOLO path is disabled by default and still publishes bbox detections into the same projection contract. |
| S2-6 | codebase | `robot/ros2-runtime/src/vexy_ros/object_indication_node.py::ObjectIndicationNode` | 2026-06-26 | Object indication node returns without publishing when no indications exist; positive indications are emitted as a bare JSON list. |
| S2-7 | codebase | `robot/ros2-runtime/src/vexy_ros/scene_map_node.py::SceneMapNode`; `vision_map.py::build_scene_map`, `parse_object_observations` | 2026-06-26 | Scene map ingests object indications and maps them through tag-derived camera pose. |
| S2-8 | codebase | `robot/ros2-runtime/src/vexy_ros/vision_map.py::Pose2D`, `camera_from_apriltag_translation`, `robot_from_camera_pose`, `estimate_camera_pose` | 2026-06-26 | Transform convention is +x forward, +y left; optical x is negated into planar left; tag and object transforms compose consistently. |
| S2-9 | codebase | `robot/ros2-runtime/src/vexy_ros/align_to_tag_node.py::AlignToTagNode` | 2026-06-26 | AprilTag alignment consumes `/tf`/detections and camera offset, not object bbox projection. |
| S2-10 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode`; `operator/core.py::Operator.fresh_ball`, `pickup_ball`, `_update_pose_from_vision` | 2026-06-26 | Operator consumes object indications directly; pickup uses nearest projected ball and hard capture thresholds. |
| S2-11 | codebase | `robot/ros2-runtime/tests/test_object_detection.py::ObjectDetectionTests` | 2026-06-26 | Tests verify ideal bbox-to-distance projection and yellow-ball diameter alias, but not partial/clipped detections. |
| S2-12 | codebase | `robot/ros2-runtime/tests/test_yellow_ball_detector.py::YellowBallDetectorTests` | 2026-06-26 | Tests cover synthetic full yellow circles, tiny noise rejection, largest contour, and HSV override. |
| S2-13 | codebase | `robot/ros2-runtime/tests/test_image_conversion.py::ImageConversionTests` | 2026-06-26 | Image conversion tests cover color channel handling, not padded row `step`. |
| S2-14 | codebase | `robot/ros2-runtime/tests/test_launch_contract.py::test_camera_info_config_is_nonzero_and_marked_as_starter` | 2026-06-26 | Repo calibration YAML is intentionally asserted as a starter placeholder containing `430/320/240`. |
| S2-15 | wiki/codebase | `wiki/knowledge/entities/components/vexy-ros-runtime.md`; `MASTER_REQUIREMENTS.md`; `robot/ros2-runtime/src/vexy_ros/camera_calibration_capture.py::camera_info_yaml`, `CheckerboardCalibrator.calibrate_and_write` | 2026-06-26 | Project docs require measured CameraInfo and state runtime service uses `/home/vexy/calibration/...`; calibration tooling writes measured camera info. |
| S2-16 | web | https://docs.ros2.org/foxy/api/sensor_msgs/msg/Image.html | 2026-06-26 | ROS `Image.step` is full row length in bytes; data size is `step * rows`. |
| S2-17 | web | https://docs.ros2.org/foxy/api/sensor_msgs/msg/CameraInfo.html | 2026-06-26 | ROS CameraInfo semantics: `K` is raw/distorted intrinsics, `P` is rectified projection matrix and may differ from `K`. |

## Excerpts

### S2-1 — Launch Graph

`robot/ros2-runtime/launch/vexy.launch.py`

> The launch description starts `camera_ros`, `image_proc` rectification, `apriltag_ros`, `scene_map_node`, optional `yolo_ncnn_node`, `yellow_ball_detector_node`, `object_indication_node`, `task_plan_node`, `align_to_tag_node`, `survey_scan_node`, `vex_bridge_node`, and `foxglove_bridge`.

> Yellow-ball launch defaults include `yellow_ball_detector_enabled=true`, `yellow_ball_max_hz=8.0`, `yellow_ball_min_area_px=200.0`, `yellow_ball_min_circularity=0.25`, and `yellow_ball_max_detections=1`.

### S2-2 — Image Conversion

`robot/ros2-runtime/src/vexy_ros/yolo_ncnn_node.py::image_to_bgr_array`

> The function computes `expected = height * width * channels`, reads `np.frombuffer(msg.data)`, then reshapes `data[:expected]` into `(height, width, channels)`.

> It handles encodings `bgr8`, `rgb8`, `bgra8`, `rgba8`, and `mono8`; it does not inspect `msg.step`.

### S2-3 — Projection

`robot/ros2-runtime/src/vexy_ros/object_detection.py`

> `intrinsics_from_camera_info(k)` reads `fx = k[0]`, `fy = k[4]`, `cx = k[2]`, and `cy = k[5]`.

> `indication_from_detection()` appends `fy * height_m / detection.height_px` and `fx * width_m / detection.width_px` as distance candidates.

### S2-4 — Yellow Detector

`robot/ros2-runtime/src/vexy_ros/yellow_ball_detector_node.py`

> The node subscribes to `/camera/image_rect`, publishes `/vision/object_detections`, and calls `detect_yellow_balls(...)`.

> `detect_yellow_balls()` thresholds HSV, applies morphology, uses `cv2.findContours`, computes contour area/perimeter/circularity, then creates a detection from `cv2.boundingRect(contour)`.

### S2-5 — YOLO Path

`robot/ros2-runtime/src/vexy_ros/yolo_ncnn_node.py`

> `YoloNcnnNode` subscribes to `/camera/image_rect` and publishes `/vision/object_detections`.

> The launch file sets `yolo_enabled` default to `false`.

> `parse_yolo_row()` converts YOLO `cx, cy, width, height` output into a clamped bbox in original image coordinates and returns a `Detection`.

### S2-6 — Object Indication Publishing

`robot/ros2-runtime/src/vexy_ros/object_indication_node.py::ObjectIndicationNode._on_detections`

> If intrinsics are unavailable, detections are ignored until CameraInfo arrives.

> After projection, `if not indications: return`; otherwise it publishes `json.dumps(payload["objects"])`.

### S2-7 — Scene Map Object Handling

`robot/ros2-runtime/src/vexy_ros/scene_map_node.py` and `vision_map.py`

> Scene map subscribes to `/vision/object_indications`, parses them as camera-relative object observations, and calls `build_scene_map`.

> `build_scene_map()` maps objects with `map_from_camera.compose(observation.camera_from_object)`.

### S2-8 — Transform Convention

`robot/ros2-runtime/src/vexy_ros/vision_map.py`

> `Pose2D` is documented as "Planar pose in meters using +x forward and +y left."

> `camera_from_apriltag_translation()` returns `Pose2D(x_m=optical_z_m, y_m=-optical_x_m)`.

> `robot_from_camera_pose()` returns `camera_in_robot.compose(camera_from_pose)`.

### S2-9 — AprilTag Alignment

`robot/ros2-runtime/src/vexy_ros/align_to_tag_node.py::AlignToTagNode`

> The node subscribes to `/apriltag/detections` and `/tf`, converts tag transforms through `camera_from_apriltag_translation`, then `robot_from_camera_pose`.

### S2-10 — Operator Consumer

`robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode`

> `_on_object_indications()` transforms `forward_m`/`left_m` from camera frame into robot frame and replaces `_objects` with that list.

`robot/ros2-runtime/src/vexy_ros/operator/core.py`

> `fresh_ball()` selects the nearest fresh yellow/ball object by `math.hypot(forward_m, left_m)`.

> `pickup_ball()` sends `grab` when `forward_m <= ball_capture_forward_m` and `abs(left_m) <= ball_capture_lateral_m`.

### S2-11 — Object Projection Tests

`robot/ros2-runtime/tests/test_object_detection.py`

> Tests construct ideal `Detection` bboxes and assert projected `forward_m`, including a yellow-ball alias with `diameter_m=0.065`.

### S2-12 — Yellow Detector Tests

`robot/ros2-runtime/tests/test_yellow_ball_detector.py`

> Tests draw synthetic yellow circles and assert detection count, label, confidence, and bbox bounds.

> Tests verify tiny yellow noise rejection, preference over warmer yellow graphics, HSV override, and largest valid contour selection.

### S2-13 — Image Conversion Tests

`robot/ros2-runtime/tests/test_image_conversion.py`

> Tests cover `bgra8` alpha dropping and `rgba8` conversion to BGR order.

### S2-14 — Starter Calibration Test

`robot/ros2-runtime/tests/test_launch_contract.py`

> The test asserts the package camera config contains "Replace this with a measured camera_calibration output".

> It also asserts the placeholder camera matrix includes `data: [430.0, 0.0, 320.0`.

### S2-15 — Runtime Calibration Documentation and Tooling

`wiki/knowledge/entities/components/vexy-ros-runtime.md`

> The service override ExecStart passes `camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml`.

> Object indication coordinates are estimates; precise object localization still needs a tag, measurement, or proven object controller.

`MASTER_REQUIREMENTS.md`

> The vision pipeline owns `camera_ros` with measured calibration YAML loaded through `camera_info_url`, rectification, AprilTags, scene map, and object indications.

`robot/ros2-runtime/src/vexy_ros/camera_calibration_capture.py`

> `calibrate_and_write()` calls `cv2.calibrateCamera(...)`, builds a CameraInfo YAML with camera matrix, distortion coefficients, rectification matrix, and projection matrix, and writes it to the configured output path.

### S2-16 — ROS Image Message

https://docs.ros2.org/foxy/api/sensor_msgs/msg/Image.html

> `uint32 step # Full row length in bytes`

> `uint8[] data # actual matrix data, size is (step * rows)`

### S2-17 — ROS CameraInfo Message

https://docs.ros2.org/foxy/api/sensor_msgs/msg/CameraInfo.html

> `image_rect - monochrome, rectified`

> `The projection matrix P projects 3D points into the rectified image.`

> `Intrinsic camera matrix for the raw (distorted) images.`

> `P ... specifies the intrinsic (camera) matrix of the processed (rectified) image ... these may differ from the values in K.`
