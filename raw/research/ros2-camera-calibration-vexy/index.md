---
topic: "how people using this exact setup do camera calibration, even better if using ros2"
slug: ros2-camera-calibration-vexy
researched: 2026-06-26
sources: [./sources.md]
---

# Research: ROS 2 Camera Calibration for the VEXY Pi Camera Stack

> For this exact class of setup — Raspberry Pi 5, Ubuntu 24.04/ROS 2 Jazzy, Pi Camera Module 3 through `camera_ros`, `image_proc`, and `apriltag_ros` — the standard calibration path is ROS `camera_calibration`'s `cameracalibrator` over `/camera/image_raw` with a printed checkerboard, saving/committing a CameraInfo YAML that `camera_ros` loads via `camera_info_url`. For VEXY specifically, the existing headless `vexy_calibrate_camera` tool is a good fit because the robot is often headless and already writes `/home/vexy/calibration/imx708_wide_640x480.yaml`; the main gap is that it should be made as disciplined as the ROS workflow: documented board motion, reprojection-quality thresholds, post-calibration `camera_info` verification, and `image_proc`/AprilTag validation.

## Research Questions

- What is the normal ROS 2 way to calibrate a monocular camera in this stack?
- How does `camera_ros` expect calibration to be loaded and stored?
- What does this repo already implement for Pi Camera Module 3 calibration?
- Which calibration workflow best fits VEXY's headless Raspberry Pi robot?
- What validation steps prove the calibration is good enough for AprilTag and object work?

## Current State (Codebase)

`robot/ros2-runtime` already models the intended runtime surface. The launch file requires `camera_info_url` to be a URL, passes it to `camera_ros`, uses `image_proc` to rectify `/camera/image_raw` into `/camera/image_rect`, and sends the rectified stream plus `/camera/camera_info` to `apriltag_ros` [S1]. The package includes `ros-jazzy-camera-calibration` as an install dependency in setup docs, and the launch README says the starter camera config must be replaced with measured calibration before tag-pose proof [S2].

VEXY already has a custom headless calibration command, `vexy_calibrate_camera`, implemented in `camera_calibration_capture.py`. It subscribes to `/camera/image_raw`, detects an inner-corner checkerboard using OpenCV, refines corners, collects object/image point pairs, runs `cv2.calibrateCamera`, and writes a ROS CameraInfo-style YAML with `camera_matrix`, `distortion_coefficients`, `rectification_matrix`, and `projection_matrix` [S3][S4].

The project docs already record the actual VEXY workflow: run `vexy_calibrate_camera --cols 8 --rows 6 --square-m 0.025 --samples 25 --out /home/vexy/calibration/imx708_wide_640x480.yaml`, then launch or restart the ROS stack with `camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml` [S5]. The active service path documented in the wiki is the same external calibration file, not the placeholder package YAML [S6].

The live Pi was unavailable during this research turn, so `/camera/set_camera_info`, installed `camera_calibration` executables, and current `camera_info_url` could not be re-verified live. Those checks are listed in Next Steps.

## Key Findings

1. **The canonical ROS 2 workflow is `camera_calibration cameracalibrator` with a checkerboard.** The ROS image_pipeline calibration docs say the monocular tutorial uses `cameracalibrator` over a raw image topic, with a large checkerboard of known dimensions, and the example command is `ros2 run camera_calibration cameracalibrator --size 8x6 --square 0.108 image:=/camera/image_raw camera:=/camera` [S7]. The docs emphasize moving the checkerboard around left/right/top/bottom, toward/away, filling the field of view, and tilted for skew coverage [S7].

2. **`camera_ros` is designed for exactly this calibration handoff.** Its docs say it uses `CameraInfoManager` to load camera intrinsics/distortion from a calibration file, publish them on `~/camera_info`, and accept new parameters through `~/set_camera_info`; `camera_info_url` must be a URL such as `file:///...`, not a bare path [S8]. It explicitly points users to `cameracalibrator` or any node that interfaces with `~/set_camera_info` [S8].

3. **The standard GUI calibrator is not always ergonomic on a headless robot.** A 2026 Foxglove write-up about calibrating a ROS 2 mobile robot describes the standard package as the official approach, but notes the GUI/display constraint and solves it by modifying the calibration node for remote/headless use; they validate with Foxglove panels [S10]. That matches VEXY's situation: the robot is a headless Pi attached to a physical robot, and the repo already created a headless calibrator.

4. **VEXY's custom calibrator follows the OpenCV algorithm used under ROS calibration.** OpenCV's calibration workflow is: prepare 3D object points, detect chessboard corners, refine with `cornerSubPix`, accumulate image/object points, and call `calibrateCamera` to estimate the intrinsic matrix and distortion coefficients [S11]. VEXY's `CheckerboardCalibrator` does that directly over ROS image messages and writes ROS-compatible YAML [S3][S4].

5. **The exact setup is a known ROS 2 Jazzy + Pi 5 pattern, but still depends on the Raspberry Pi libcamera fork.** A 2025 Open Robotics Discourse thread describes getting Raspberry Pi V1/V2/V3 cameras working on Pi 5 with Ubuntu 24.04/ROS 2 Jazzy using Christian Rauch's `camera_ros`, publishing `/camera/camera_info` and `/camera/image_raw`; Christian Rauch notes manual steps are still needed because of the Raspberry Pi libcamera fork [S9]. This supports the repo's existing choice to build/use the Raspberry Pi libcamera fork rather than a generic V4L2 webcam path.

6. **Calibration quality must be validated after loading, not just written.** ROS calibration docs say loading a calibration file does not itself rectify an image; rectification uses `image_proc` [S7]. For VEXY, the proof sequence should therefore check `/camera/camera_info` values, `/camera/image_rect` rate, and AprilTag `/tf` from a known tag after restarting with the measured YAML [S5]. This matters because the previous vision audit found the repo YAML and runtime YAML can diverge.

## Constraints

- VEXY runs a managed ROS 2 stack on a headless Raspberry Pi, so a GUI calibrator is less convenient than a terminal/headless workflow.
- The camera is Pi Camera Module 3 Wide through `camera_ros`, not a generic USB camera.
- The calibration is resolution-specific; the repo has separate examples for 640x480 and 1280x720 paths [S2][S5].
- The active runtime file is external to the package at `/home/vexy/calibration/imx708_wide_640x480.yaml`; editing the starter package YAML does not affect the managed robot unless launch parameters change [S5][S6].
- Live robot verification was unavailable in this turn.

## Solution Comparison

| Criteria | Option A: ROS GUI `cameracalibrator` | Option B: VEXY Headless OpenCV Calibrator | Option C: Offline Image/Bag Calibration |
|---|---|---|---|
| Approach | Run `ros2 run camera_calibration cameracalibrator ...`, move checkerboard until bars fill, calibrate, commit/save via camera service/YAML. | Run `ros2 run vexy_ros vexy_calibrate_camera ...`, collect samples from `/camera/image_raw`, write YAML directly. | Record images or rosbag, calibrate later with OpenCV/script or modified ROS calibration tool. |
| Pros | Canonical ROS path; can commit through `set_camera_info`; mature UI guidance. | Already in repo; works headless; writes exactly the active VEXY path; easy to script. | Reproducible and inspectable; can recalibrate without robot online. |
| Cons | Needs display/remote GUI; service commit path must work; less convenient on a robot bench. | Needs stronger quality gates and better operator guidance; bypasses `set_camera_info` service. | More moving parts; easy to mismatch resolution or camera settings. |
| Complexity | Medium | Low-Medium | Medium |
| Dependencies | `ros-jazzy-camera-calibration`, GUI/display or forwarding. | Existing `vexy_ros`, OpenCV, ROS image stream. | Storage plus calibration script/tooling. |
| Codebase fit | Good reference path | Best immediate fit | Good fallback/debug path |
| Maintenance | External package | Local code to maintain | Local data management |

## Recommendation

Use a two-tier workflow:

1. **Primary practical workflow for VEXY:** keep using and improving `vexy_calibrate_camera` because it is headless, already writes `/home/vexy/calibration/imx708_wide_640x480.yaml`, and matches the service override.
2. **Reference/validation workflow:** keep `camera_calibration cameracalibrator` documented as the canonical ROS method and use it when a display or remote GUI is available, especially to compare results against the custom tool.

Concrete recommended procedure for VEXY:

```bash
# 1. Start camera without trusting old calibration, at the exact resolution/fps to be used.
ros2 launch vexy_ros vexy.launch.py \
  camera_width:=640 camera_height:=480 camera_fps:=30 \
  camera_info_url:=file:///home/vexy/calibration/imx708_wide_640x480.yaml

# 2. Run headless calibration from another terminal.
mkdir -p /home/vexy/calibration/imx708_wide_640x480_samples
ros2 run vexy_ros vexy_calibrate_camera \
  --image-topic /camera/image_raw \
  --cols 8 --rows 6 --square-m 0.025 \
  --samples 25 \
  --out /home/vexy/calibration/imx708_wide_640x480.yaml \
  --preview-dir /home/vexy/calibration/imx708_wide_640x480_samples

# 3. Restart the managed stack so camera_ros loads the new YAML.
systemctl --user daemon-reload
systemctl --user restart vexy-ros-stack.service

# 4. Verify CameraInfo and rectification.
ros2 topic echo /camera/camera_info --once
ros2 topic hz /camera/image_rect

# 5. Verify an actual tag pose.
ros2 topic echo /apriltag/detections --once
ros2 topic echo /tf --once
```

Board guidance:

- Use an 8x6 inner-corner checkerboard if keeping current defaults; that means a printed board with 9x7 squares.
- Mount the checkerboard flat on a rigid backing.
- Use the exact square size in meters; if the print is 25 mm squares, `--square-m 0.025`.
- Capture coverage across the whole field: left/right/top/bottom, near/far, tilted/skewed, and filling much of the frame.
- Use the exact same camera resolution and focus/exposure behavior as runtime. If runtime changes to 1280x720, produce a separate YAML for 1280x720.

Implementation improvements to make `vexy_calibrate_camera` more ROS-grade:

- Print or save RMS reprojection error into a sidecar summary and fail above a configured threshold.
- Save the exact command, image topic, resolution, board geometry, sample count, and timestamp next to the YAML.
- Add a post-run check command that compares `/camera/camera_info` to the written YAML after restart.
- Optionally add a `--use-set-camera-info` mode that calls `/camera/set_camera_info` when available, while keeping direct YAML write as the robust headless path.
- Add a `cameracheck`/AprilTag validation step to the runbook.

## Next Steps

- Create a task: `/task-add Improve VEXY camera calibration workflow: document ROS cameracalibrator reference path, harden vexy_calibrate_camera quality gates, add post-load CameraInfo and AprilTag validation checks`
- When VEXY is back online, verify:
  - `ros2 service list | grep set_camera_info`
  - `ros2 pkg executables camera_calibration`
  - `ros2 param get /camera camera_info_url`
  - `/camera/camera_info` `K/D/P` after restart.
- If calibration still looks poor, run both workflows (`cameracalibrator` and `vexy_calibrate_camera`) at the same resolution and compare `K`, `D`, RMS, and AprilTag pose stability.
