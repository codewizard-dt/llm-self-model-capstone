---
topic: "This seems to be an issue with the vision processing. So, do a full audit of the entire vision stack and see if anything stands out."
slug: vision-stack-audit
researched: 2026-06-26
---

# Primary Sources — Vision Stack Audit

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/ros2-runtime/launch/vexy.launch.py::_launch_nodes` and `generate_launch_description` | 2026-06-26 | Launch data flow: camera, rectification, AprilTag, yellow-ball detector, object indication node, and detector/default parameters. |
| S2 | codebase | `robot/ros2-runtime/src/vexy_ros/yellow_ball_detector_node.py::detect_yellow_balls` | 2026-06-26 | HSV contour detector behavior, contour filtering, largest bounding-rectangle output, and confidence calculation. |
| S3 | codebase | `robot/ros2-runtime/src/vexy_ros/object_detection.py::indication_from_detection`, `intrinsics_from_camera_info` | 2026-06-26 | Projection formula from bbox pixels to `forward_m`/`left_m`, and use of `CameraInfo.k` for intrinsics. |
| S4 | codebase | `robot/ros2-runtime/src/vexy_ros/object_indication_node.py::ObjectIndicationNode`, `DEFAULT_OBJECT_DIMENSIONS_JSON` | 2026-06-26 | Object indication node consumes detections and CameraInfo; yellow-ball diameter is 0.065 m and min confidence defaults to 0.35. |
| S5 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/core.py::Operator.pickup_ball`, `fresh_ball` | 2026-06-26 | Pickup sequence, "nearest fresh ball" selection, capture thresholds, final close condition, and retry/fail behavior. |
| S6 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/core.py::Operator.has_object` | 2026-06-26 | Possession check uses manipulator telemetry position/velocity after the recent effector calibration work. |
| S7 | codebase | `robot/ros2-runtime/src/vexy_ros/vision_map.py::DEFAULT_CAMERA_IN_ROBOT`, `robot_from_camera_pose` | 2026-06-26 | Camera-to-robot transform default: camera is 0.3302 m behind and 0.1143 m left of the robot pickup frame; transforms are composed into robot frame. |
| S8 | session observation | Interactive live/static calibration runs of `operator/tests/test_static_claw_ball_calibration.py` and `operator/tests/test_live_deliver.py` | 2026-06-26 | Physical observations and telemetry samples: capturable/out-of-reach balls produced contradictory projected forward distances; live deliver failed with `grab_failed` after false-positive fix. |
| S9 | runtime | SSH snapshot from `vexy@vexy.local`: `ros2 node list`, `ros2 topic echo /camera/camera_info --once`, `ros2 param get /camera camera_info_url`, and `/home/vexy/calibration/imx708_wide_640x480.yaml` | 2026-06-26 | Runtime ROS nodes are active; camera node uses external calibration file with `fx≈558`, `fy≈557`, `cx≈421.65`, `cy≈251.14`, not the repo/install package default YAML. |
| S10 | web | https://docs.ros2.org/latest/api/sensor_msgs/msg/CameraInfo.html | 2026-06-26 | ROS CameraInfo semantics: `K` is raw image intrinsic matrix; `P` is rectified image projection matrix. |
| S11 | context7 | `/websites/opencv_4_13_0` — queries on `boundingRect`, `inRange`, `findContours`, and camera calibration | 2026-06-26 | OpenCV semantics for HSV threshold masks, contour bounding rectangles, camera calibration parameters, and camera matrix. |
| S12 | codebase | `operator/tests/test_live_deliver.py::DeliverTestNode` | 2026-06-26 | Live deliver test consumes `/vision/object_indications`, `/tf`, `/vex/telemetry`, and operator result reasons; it does not independently verify final ball-in-bin state. |

## Excerpts

### S1 — Launch data flow

`robot/ros2-runtime/launch/vexy.launch.py`

> `camera_ros` publishes `/camera/image_raw` and `/camera/camera_info`; `image_proc` remaps `image_rect` to `/camera/image_rect`; `yellow_ball_detector_node` is enabled by default; `object_indication_node` receives `object_dimensions_json`.

> Yellow-ball launch defaults include `yellow_ball_min_area_px=200.0`, `yellow_ball_min_circularity=0.25`, `yellow_ball_max_detections=1`, HSV `h_min=20`, `s_min=25`, `v_min=80`, `h_max=45`, and `object_min_confidence=0.35`.

### S2 — Yellow detector

`robot/ros2-runtime/src/vexy_ros/yellow_ball_detector_node.py::detect_yellow_balls`

> The detector converts BGR to HSV, thresholds with `cv2.inRange`, applies open/close morphology, runs `cv2.findContours(..., cv2.RETR_EXTERNAL, ...)`, and creates a detection from `cv2.boundingRect(contour)`.

> Confidence is calculated from circularity and fill ratio: `0.5 * circularity + 0.5 * fill_ratio`; detections are sorted by contour area and truncated to `max_detections`.

### S3 — Projection math and intrinsics

`robot/ros2-runtime/src/vexy_ros/object_detection.py::indication_from_detection`

> `distance_candidates.append(intrinsics.fy * height_m / detection.height_px)`

> `distance_candidates.append(intrinsics.fx * width_m / detection.width_px)`

> `forward_m = _median(distance_candidates)` and `left_m = -((center_x - intrinsics.cx) * forward_m / intrinsics.fx)`.

`robot/ros2-runtime/src/vexy_ros/object_detection.py::intrinsics_from_camera_info`

> `fx, fy = float(k[0]), float(k[4])` and `return CameraIntrinsics(fx=fx, fy=fy, cx=float(k[2]), cy=float(k[5]))`.

### S4 — Object dimensions and indication node

`robot/ros2-runtime/src/vexy_ros/object_indication_node.py`

> Default dimensions include `"yellow ball": {"diameter_m": 0.065}` and the launch override also includes `"yellow_ball":{"diameter_m":0.065}`.

> The node declares `camera_info_topic`, `object_dimensions_json`, `default_height_m`, and `min_confidence`, then calls `indications_from_detections(...)`.

### S5 — Pickup behavior

`robot/ros2-runtime/src/vexy_ros/operator/core.py::Operator.pickup_ball`

> Idle pickup sends a primitive command `release` with reason `open_claw_for_ball_pickup`, then enters `opening`.

> In `approaching`, if `forward_m <= ball_capture_forward_m` and `abs(left_m) <= ball_capture_lateral_m`, it sends `grab` with reason `close_claw_on_visual_ball`.

> If close is not confirmed, it emits `grab_retry`; after `pickup_max_attempts`, it returns reason `grab_failed`.

`robot/ros2-runtime/src/vexy_ros/operator/core.py::Operator.fresh_ball`

> Ball candidates are fresh yellow/object labels with `forward_m` and `left_m`; the chosen ball is the minimum `math.hypot(forward_m, left_m)`.

### S6 — Possession telemetry

`robot/ros2-runtime/src/vexy_ros/operator/core.py::Operator.has_object`

> If manipulator position is at or below the open threshold, return false; if position is at or below the object-closed threshold and velocity is low, return true; otherwise return false.

### S7 — Camera-to-robot transform

`robot/ros2-runtime/src/vexy_ros/vision_map.py`

> `DEFAULT_CAMERA_IN_ROBOT = '{"x_m":-0.3302,"y_m":0.1143,"yaw_rad":0.0}'`

> `robot_from_camera_pose(camera_from_pose, camera_in_robot)` returns `camera_in_robot.compose(camera_from_pose)`.

### S8 — Session observations

Current interactive session, static claw and live delivery tests.

> Centered capturable ball was estimated around `claw_forward≈0.215-0.263m` and rejected by capture threshold.

> Centered ball about 1 inch out of reach was estimated around `claw_forward≈0.129-0.138m` and accepted by capture threshold.

> Right-side in-claw placement produced unstable/far estimates, including values around `0.64-1.19m`.

> Live delivery after the possession fix failed as `grab_failed`; observed event included `ball_in_claw_zone` with `forward_m=-0.024...` and `left_m=0.077...`.

### S9 — Runtime Pi snapshot

SSH commands against `vexy@vexy.local`.

> Active ROS nodes included `/camera`, `/camera_rectify`, `/apriltag`, `/yellow_ball_detector`, `/object_indication`, `/scene_map`, and `/vex_bridge`.

> `/camera/camera_info` reported `k: [558.332927003, 0.0, 421.65145349, 0.0, 557.269171944, 251.144269554, 0.0, 0.0, 1.0]`.

> `/camera` parameter `camera_info_url` was `file:///home/vexy/calibration/imx708_wide_640x480.yaml`.

> `/home/vexy/calibration/imx708_wide_640x480.yaml` contains `camera_matrix` data `[558.332927003, 0, 421.65145349, 0, 557.269171944, 251.144269554, 0, 0, 1]`.

> Repo and installed package YAML still contain `[430.0, 0.0, 320.0, 0.0, 430.0, 240.0, 0.0, 0.0, 1.0]`.

### S10 — ROS CameraInfo documentation

https://docs.ros2.org/latest/api/sensor_msgs/msg/CameraInfo.html

> "The projection matrix P projects 3D points into the rectified image."

> "Intrinsic camera matrix for the raw (distorted) images."

> "By convention, this matrix specifies the intrinsic (camera) matrix of the processed (rectified) image."

### S11 — OpenCV documentation via Context7

Context7 library `/websites/opencv_4_13_0`.

> `cv::boundingRect` "calculates the up-right bounding rectangle of a point set or non-zero pixels of gray-scale image."

> `cv.inRange` checks whether input elements fall within lower and upper boundaries and produces a binary image.

> OpenCV camera calibration estimates the camera matrix and distortion coefficients from object points, image points, and image size.

> The camera matrix is `A=[fx 0 cx; 0 fy cy; 0 0 1]`, containing focal lengths and principal point.

### S12 — Live deliver test

`operator/tests/test_live_deliver.py::DeliverTestNode`

> The test subscribes to `/tf`, `/vision/object_indications`, and `/vex/telemetry`, then updates the operator and runs each delivery step until success, failure reason, or timeout.

> Object indications are transformed from camera frame to robot frame with `robot_from_camera_pose(camera_from_object, self.camera_in_robot)`.
