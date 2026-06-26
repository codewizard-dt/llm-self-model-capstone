---
topic: "This seems to be an issue with the vision processing. So, do a full audit of the entire vision stack and see if anything stands out."
slug: vision-stack-audit
researched: 2026-06-26
sources: [./sources.md]
---

# Research: Vision Stack Audit

> The delivery failure is very likely caused by using a monocular contour bounding box as a metric pickup signal after the claw/motor starts occluding the ball. The code estimates distance as `focal_length * known_ball_diameter / detected_bbox_pixels`; during pickup, the detected yellow blob may be only the visible slice of the ball, so the metric pose jumps or becomes physically impossible. Calibration still matters, but the bigger fix is to split coarse ball navigation from a pickup-specific claw-mouth visual classifier, then verify possession with effector telemetry.

## Research Questions

- What is the current camera-to-operator data flow for yellow ball pickup?
- Does the projection math match the image stream and calibration used at runtime?
- Why did static calibration produce contradictory "capturable" estimates?
- Which parts of the stack can create a false pickup or premature claw close?
- What implementation path best fits this robot and test setup?

## Current State (Codebase)

The launch stack starts `camera_ros`, rectifies `/camera/image_raw` into `/camera/image_rect`, runs AprilTag detection and a lightweight yellow-ball detector on the rectified stream, projects object detections into `/vision/object_indications`, and lets the operator consume those indications for pickup and delivery [S1].

The yellow-ball detector is a pure HSV/contour pipeline: it thresholds yellow pixels, performs morphology, finds external contours, filters by area and circularity, then publishes the largest bounding rectangle as a `yellow_ball` detection [S2]. It does not check whether the entire ball is visible.

The object indication layer converts each detection into metric `forward_m` and `left_m` using known object dimensions and camera intrinsics. For a yellow ball, the configured diameter is 0.065 m, so the estimate assumes the bounding-box width/height correspond to the full ball diameter [S3][S4].

The operator then transforms object indications from camera frame into robot frame using `DEFAULT_CAMERA_IN_ROBOT = {"x_m":-0.3302,"y_m":0.1143,"yaw_rad":0.0}`. That matches the user-supplied physical offset: the claw is 13 inches in front of the camera and 4.5 inches to the camera's right, expressed as the camera being 0.3302 m behind and 0.1143 m left of the claw/robot pickup frame [S7].

Pickup currently opens the claw, approaches the nearest fresh ball, closes once the projected robot-frame ball pose satisfies `forward_m <= 0.14` and `abs(left_m) <= 0.08`, then requires effector telemetry to confirm possession before reporting success [S5][S6]. The recent false-positive fix means the operator should now fail with `grab_failed` rather than continuing to the bin when the claw never actually captures the ball [S5][S6].

## Key Findings

1. **Metric ball pose is fragile near the claw.** `indication_from_detection()` computes distance from apparent pixel size: `fy * height_m / detection.height_px` and `fx * width_m / detection.width_px`, then uses the bbox center for lateral offset [S3]. This is only valid when the bbox is the full object silhouette. The yellow detector uses `cv2.boundingRect(contour)` over whatever yellow pixels survived thresholding [S2], and OpenCV defines that rectangle as enclosing the given point set/non-zero pixels, not as reconstructing hidden object extent [S11].

2. **The live calibration behavior matches partial-visibility failure.** Static tests produced contradictory estimates: a centered capturable ball was reported around 0.215-0.263 m forward and rejected, a centered ball about 1 inch out of reach was reported around 0.129-0.138 m and accepted, and a right-side in-claw ball became unstable or very far. That pattern is consistent with occlusion or partial masks changing bbox size/center rather than a simple constant camera offset error [S8]. This is an inference from the observed run data, not a standalone logged dataset.

3. **The detector is intentionally permissive for proof scenes, but too unconstrained for final pickup.** Defaults allow low saturation (`s_min=25`), low circularity (`0.25`), only `200 px` minimum area, and one largest detection [S1][S2]. That is fine for coarse "find the yellow thing" behavior, but at the claw mouth it can accept a partial ball, glare, or an occluded crescent as if it were the full ball.

4. **The runtime calibration is not the repo default.** The repo and installed package YAML contain placeholder-like values `fx=fy=430`, `cx=320`, `cy=240`, but the running Pi camera node uses `/home/vexy/calibration/imx708_wide_640x480.yaml` with `fx≈558`, `fy≈557`, `cx≈421.65`, `cy≈251.14` [S9]. This means changing only `robot/ros2-runtime/config/imx708_wide_640x480.yaml` will not affect the active robot unless the launch parameter or external calibration file is updated too.

5. **The rectified-image intrinsics path should be made explicit.** ROS documents `K` as the raw/distorted camera matrix and `P` as the rectified-image projection matrix [S10]. The code subscribes to `/camera/image_rect` but `intrinsics_from_camera_info()` reads only `CameraInfo.k` [S1][S3]. On the current Pi snapshot, `K` and `P` are numerically equal, so this is not the immediate source of the bad pickup behavior [S9]. Still, the object projection node should derive intrinsics from `P` when processing rectified images so the code stays correct if calibration changes.

6. **The live test still cannot prove physical delivery by itself.** `test_live_deliver.py` drives the operator from ROS indications and telemetry, but it does not independently verify that a yellow ball entered the bin after release [S12]. The effector telemetry fix closes the most damaging pickup false positive, but final delivery still needs either user observation, a bin-side visual check, or a post-release object-state check.

## Constraints

- The robot has a single forward camera and the claw/motor can physically block the ball from the camera near capture [S8].
- The pickup task needs real-time behavior on the Pi, so the final detector should stay lightweight unless a trained model is already available.
- AprilTag localization and coarse ball navigation already use the current camera/robot frame pipeline; replacing the whole stack would risk working parts [S1][S7].
- The current delivery test is operator-level, not a full physical-state oracle [S12].
- Runtime calibration lives outside the repo at `/home/vexy/calibration/imx708_wide_640x480.yaml` on the Pi [S9].

## Solution Comparison

| Criteria | Option A: Tune Existing Thresholds | Option B: Add Projection Plausibility Gates | Option C: Pickup-Specific Claw ROI |
|---|---|---|---|
| Approach | Adjust `camera_in_robot`, capture thresholds, HSV ranges, and min circularity. | Keep bbox projection but reject impossible depth jumps, negative/too-near forward values, edge/occlusion-like boxes, and unstable frames. | Use current projection for coarse approach, then switch to image-space calibrated claw-mouth zones for final close; verify possession with effector telemetry. |
| Pros | Fast, low code churn. | Reduces the worst false closes and wild estimates. | Directly matches the physical problem: "is the ball between the jaws?" |
| Cons | Cannot fix partial bbox geometry. | Still depends on a flawed metric signal near occlusion. | Requires calibration samples and new tests. |
| Complexity | Low | Medium | Medium |
| Dependencies | None | None | None if implemented with OpenCV; optional image logging/debug overlay. |
| Codebase fit | Poor as the main fix; useful for cleanup. | Good as a safety layer. | Best fit: keeps existing stack and narrows new logic to pickup. |
| Maintenance | Threshold drift likely. | Moderate, mostly parameter tuning. | Moderate, but easier to reason from physical labels. |

## Recommendation

Implement Option C with Option B as guardrails.

The stack should keep `/vision/object_indications` for coarse ball acquisition and approach while the ball is fully visible. Once the ball is near the claw, pickup should stop trusting metric distance from bbox size and instead use a calibrated image-space claw-mouth detector:

1. Capture and store labeled still frames from the static claw calibration: closed/open claw, centered capturable ball, left/right capturable extremes, out-of-reach centered, and occluded right-side cases.
2. Define a pickup ROI in image coordinates for the claw mouth, including left/right jaw limits and a "close now" band based on where capturable balls appear in the frame.
3. Publish a pickup-specific indication such as `ball_in_claw_roi` with image center, mask area, bbox, confidence, and temporal stability.
4. Change `pickup_ball()` final-close logic to require the pickup ROI signal for close. Use metric `forward_m/left_m` only before the final claw-mouth phase.
5. Add plausibility gates to the existing object projection: reject negative robot-frame forward values for ball pickup, reject extreme frame-to-frame depth jumps, and mark detections as `partial_or_unstable` when bbox aspect/fill/edge conditions look suspicious.
6. Keep the effector-based `has_object()` check as the final possession oracle after close.
7. Make runtime calibration explicit: either commit/update the calibrated YAML used on the Pi, or change launch/default docs so `camera_info_url=file:///home/vexy/calibration/imx708_wide_640x480.yaml` is the known source of truth. Update object projection to use `P` for rectified images.

The measuring-tape calibration idea is still useful, but it should tune `camera_in_robot.y_m` and `yaw_rad` after this split. Tape alignment can correct constant yaw/lateral bias; it cannot correct partial-ball bbox distance errors.

## Next Steps

- Create a task to add the pickup-specific claw-mouth ROI detector, projection plausibility gates, and replayable calibration-image fixtures.
- Create a smaller task to make calibration source-of-truth explicit and use `CameraInfo.p` for rectified object projection.
- Extend `test_live_deliver.py` or add a companion live test that requires post-release evidence that the ball reached the bin.
- Use the `wiki-ingest` skill on this report once accepted so the calibration and vision-stack findings become knowledge-base context.
