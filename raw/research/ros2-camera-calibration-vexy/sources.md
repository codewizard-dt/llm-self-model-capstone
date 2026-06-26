---
topic: "how people using this exact setup do camera calibration, even better if using ros2"
slug: ros2-camera-calibration-vexy
researched: 2026-06-26
---

# Primary Sources — ROS 2 Camera Calibration for the VEXY Pi Camera Stack

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/ros2-runtime/launch/vexy.launch.py::_launch_nodes`, `generate_launch_description` | 2026-06-26 | Launch file passes `camera_info_url` to `camera_ros`, rectifies with `image_proc`, and feeds AprilTag detection. |
| S2 | codebase | `robot/ros2-runtime/README.md` | 2026-06-26 | Runtime launch examples and argument table: `camera_info_url` must be a URL and starter config must be replaced with measured calibration. |
| S3 | codebase | `robot/ros2-runtime/src/vexy_ros/camera_calibration_capture.py::CheckerboardCalibrator` | 2026-06-26 | Existing headless ROS node for collecting checkerboard samples from `/camera/image_raw` and running `cv2.calibrateCamera`. |
| S4 | codebase | `robot/ros2-runtime/src/vexy_ros/camera_calibration_capture.py::camera_info_yaml`, `image_msg_to_gray`, `build_parser` | 2026-06-26 | YAML shape, stride-aware grayscale conversion, default board/sample/output settings. |
| S5 | codebase | `robot/ros2-runtime/docs/VISION_COORDINATE_MAP.md` | 2026-06-26 | Existing VEXY calibration proof workflow and exact command using `/home/vexy/calibration/imx708_wide_640x480.yaml`. |
| S6 | wiki | `wiki/knowledge/entities/components/vexy-ros-runtime.md`, `wiki/knowledge/concepts/camera-module-3-setup.md` | 2026-06-26 | Persistent service override path and warning that active runtime calibration is external to the starter package YAML. |
| S7 | web | https://raw.githubusercontent.com/ros-perception/image_pipeline/rolling/camera_calibration/doc/tutorial_mono.rst | 2026-06-26 | Official ROS image_pipeline monocular calibration workflow, checkerboard movement guidance, save/commit behavior, and rectification note. |
| S8 | web | https://github.com/christianrauch/camera_ros | 2026-06-26 | `camera_ros` calibration behavior: `CameraInfoManager`, `camera_info_url`, `~/set_camera_info`, zero intrinsics when missing calibration. |
| S9 | web | https://discourse.openrobotics.org/t/installation-and-configuration-of-the-raspberry-pi-camera-on-a-ros-2-jazzy-raspberry-pi-5/45177 | 2026-06-26 | Exact-stack community context: Raspberry Pi 5 + Ubuntu 24.04 + ROS 2 Jazzy + `camera_ros`, with Raspberry Pi libcamera fork caveat. |
| S10 | web | https://foxglove.dev/blog/calibrating-a-monocular-camera-for-the-lekiwi-robot-using-ros-2 | 2026-06-26 | Contemporary ROS 2 robot calibration practice: standard GUI workflow and headless modification when no display is available. |
| S11 | context7 | `/websites/opencv_4_13_0` — "camera calibration with chessboard..." | 2026-06-26 | OpenCV algorithm used by the repo's custom calibrator: chessboard corners, subpixel refinement, object/image points, `calibrateCamera`. |

## Excerpts

### S1 — VEXY launch path

`robot/ros2-runtime/launch/vexy.launch.py`

> The launch file validates `camera_info_url`, passes it as a parameter to `camera_ros`, starts `image_proc` rectification, and launches `apriltag_ros` over `/camera/image_rect` plus `/camera/camera_info`.

### S2 — README launch arguments

`robot/ros2-runtime/README.md`

> `camera_info_url` default is package config URL; it "must be a URL such as `file:///...`; replace the starter file with measured calibration before tag-pose proof."

> The README includes a measured calibration override example using `camera_info_url:=file:///home/vexy/calibration/imx708_wide_1280x720.yaml`.

### S3 — Headless calibrator

`robot/ros2-runtime/src/vexy_ros/camera_calibration_capture.py::CheckerboardCalibrator`

> The node subscribes to `args.image_topic`, detects chessboard corners with `cv2.findChessboardCorners`, refines them with `cv2.cornerSubPix`, appends object/image points, then writes calibration after `cv2.calibrateCamera`.

### S4 — YAML/output defaults

`robot/ros2-runtime/src/vexy_ros/camera_calibration_capture.py`

> `camera_info_yaml()` writes `camera_matrix`, `distortion_coefficients`, `rectification_matrix`, and `projection_matrix` in ROS CameraInfo YAML shape.

> Defaults are `--image-topic /camera/image_raw`, `--cols 8`, `--rows 6`, `--square-m 0.025`, `--samples 25`, and output `/home/vexy/calibration/imx708_wide_640x480.yaml`.

### S5 — Existing VEXY proof workflow

`robot/ros2-runtime/docs/VISION_COORDINATE_MAP.md`

> The documented proof gate runs `ros2 run vexy_ros vexy_calibrate_camera --cols 8 --rows 6 --square-m 0.025 --samples 25 --out /home/vexy/calibration/imx708_wide_640x480.yaml`.

> It then relaunches with `camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml` and verifies `/camera/image_rect`, `/camera/camera_info`, `/apriltag/detections`, and `/tf`.

### S6 — Wiki runtime calibration path

`wiki/knowledge/entities/components/vexy-ros-runtime.md`

> The systemd user-service drop-in starts `ros2 launch vexy_ros vexy.launch.py ... camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml`.

`wiki/knowledge/concepts/camera-module-3-setup.md`

> The package config YAML is a starter placeholder; patching it does not affect the managed robot unless the service override or measured file changes.

### S7 — ROS image_pipeline calibration tutorial

https://raw.githubusercontent.com/ros-perception/image_pipeline/rolling/camera_calibration/doc/tutorial_mono.rst

> "This tutorial cover using the `cameracalibrator` node to calibrate a monocular camera with a raw image over ROS 2."

> Example command: `ros2 run camera_calibration cameracalibrator --size 8x6 --square 0.108 image:=/camera/image_raw camera:=/camera`.

> Move the checkerboard around left/right/top/bottom, toward/away, filling the field, and tilted for skew; hold still until highlighted.

> "If you are satisfied with the calibration, click COMMIT to send the calibration parameters to the camera for permanent storage."

> "Simply loading a calibration file does not rectify the image. For rectification, use the `image_proc` package."

### S8 — camera_ros calibration docs

https://github.com/christianrauch/camera_ros

> `camera_ros` uses `CameraInfoManager` to manage intrinsics and distortion coefficients, load calibration files, publish `~/camera_info`, and set new parameters via `~/set_camera_info`.

> `camera_info_url` can be set manually, but the string must be URL format, for example `file:///home/nonroot/camera/calibration.yaml`.

> If the file is missing, the node warns and publishes zero-initialized intrinsic parameters.

> To calibrate and set parameters, use `cameracalibrator` from `camera_calibration` or any node that interfaces with `~/set_camera_info`.

### S9 — Pi 5 + Jazzy + camera_ros community context

https://discourse.openrobotics.org/t/installation-and-configuration-of-the-raspberry-pi-camera-on-a-ros-2-jazzy-raspberry-pi-5/45177

> The thread describes Raspberry Pi V1/V2/V3 cameras on Raspberry Pi 5 with Ubuntu 24.04 / ROS 2 Jazzy using `camera_ros`.

> The purpose was enabling `camera_ros` to publish `/camera/camera_info`, `/camera/image_raw`, `/camera/image_compressed`, `/parameter_events`, and `/rosout`.

> Christian Rauch notes some manual compile/install steps remain necessary because of the Raspberry Pi fork of libcamera.

### S10 — Foxglove ROS 2 headless calibration example

https://foxglove.dev/blog/calibrating-a-monocular-camera-for-the-lekiwi-robot-using-ros-2

> The article describes calibrating a ROS 2 mobile robot camera and notes the standard ROS 2 calibration package with a printed checkerboard as the official workflow.

> Because the robot ran Ubuntu Server without a desktop GUI, the author modified the calibration process to run remotely/headlessly and used Foxglove panels to validate.

### S11 — OpenCV calibration docs via Context7

Context7 library `/websites/opencv_4_13_0`.

> OpenCV calibration prepares object points and image points, uses `findChessboardCorners`, refines corners with `cornerSubPix`, and calls calibration routines with object points, image points, and image size.

> `calibrateCamera` estimates the camera matrix and distortion coefficients from corresponding 3D object points and 2D image points.
