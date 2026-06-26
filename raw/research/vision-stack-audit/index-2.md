---
topic: "Full follow-up analysis of the entire robot vision stack after live pickup/delivery failures"
slug: vision-stack-audit
researched: 2026-06-26
sources: [./sources-2.md]
builds_on: [./index.md]
---

# Research Addendum: Full Vision Stack Analysis

> This addendum expands the first audit. The stack is structurally coherent for AprilTag localization, but the object path has several compounding weaknesses: tight-packed image assumptions, bbox-only object geometry, no partial-visibility contract, sparse-only indication publishing, no temporal filter, and tests that validate ideal synthetic frames rather than claw-mouth reality. The highest-value fix remains a pickup-specific image-space claw-mouth detector, but the supporting fixes should include correct `Image.step` handling, `CameraInfo.P` usage for rectified images, calibration source-of-truth cleanup, and replay fixtures from real frames.

## Scope

This pass covers:

- Camera node, rectification, image message conversion, and calibration.
- Yellow-ball HSV detector and optional YOLO NCNN path.
- Detection payloads, object projection, and scene-map object handling.
- AprilTag localization and camera-to-robot transforms.
- Operator/test consumers of object indications.
- Test coverage and runtime/debugging gaps.

It does not repeat the first report's base explanation of why monocular bbox depth fails under claw occlusion; see [index.md](index.md).

## End-to-End Vision Map

The runtime vision stack is:

1. `camera_ros` publishes `/camera/image_raw` and `/camera/camera_info`.
2. `image_proc` rectifies `/camera/image_raw` to `/camera/image_rect`.
3. `apriltag_ros` consumes `/camera/image_rect` plus `/camera/camera_info`, publishing `/apriltag/detections` and `/tf`.
4. `yellow_ball_detector_node` consumes `/camera/image_rect`, converts image bytes to BGR, thresholds yellow HSV, and publishes `/vision/object_detections`.
5. Optional `yolo_ncnn_node` also consumes `/camera/image_rect` and publishes `/vision/object_detections`, but it is disabled by default.
6. `object_indication_node` consumes `/vision/object_detections` and `/camera/camera_info`, then publishes `/vision/object_indications`.
7. `scene_map_node` consumes AprilTag data plus object indications and publishes `/vision/scene_map`.
8. Operator/test code consumes `/tf`, `/vision/object_indications`, and telemetry to decide pickup and delivery actions [S2-1][S2-6][S2-9][S2-10].

## Detailed Findings

### 1. Image conversion assumes tightly packed rows

`image_to_bgr_array()` calculates `expected = height * width * channels`, takes `data[:expected]`, and reshapes it into `(height, width, channels)` [S2-2]. ROS `sensor_msgs/Image.step` is defined as full row length in bytes, and `data` size is `step * rows` [S2-16]. If the camera/rectifier publishes padded rows, the current conversion will silently read incorrect pixels after the first padded row.

This may not be the current Pi's observed failure if `/camera/image_rect.step == width * channels`, but it is a real correctness bug in the vision foundation. It should be fixed before trusting calibration images or replay fixtures.

### 2. Rectified image projection should read `CameraInfo.p`, not only `k`

The detector consumes `/camera/image_rect`, but `object_indication_node` converts `CameraInfo.k` into intrinsics [S2-3]. ROS defines `K` as the raw distorted-image intrinsic matrix and `P` as the processed/rectified projection matrix; `P` may differ from `K` [S2-17]. The current runtime sample showed `K` and `P` equal, so this is not proven to be today's failure. It is still the wrong coupling for a rectified-image consumer.

Recommended correction: add `intrinsics_from_rectified_camera_info(p, fallback_k)` or a frame parameter in `object_indication_node`, and use `P[0]`, `P[5]`, `P[2]`, `P[6]` for `/camera/image_rect`.

### 3. Runtime calibration is intentionally outside the repo, but the code/tests do not enforce that

The launch default points at the package config YAML, while the managed Pi service overrides `camera_info_url` to `/home/vexy/calibration/imx708_wide_640x480.yaml` [S2-1][S2-15]. The repo test explicitly asserts the package YAML is a starter placeholder containing `430/320/240` [S2-14]. The runtime snapshot from the first report showed the Pi using measured `558/557/421.65/251.14` values from `/home/vexy/calibration/...`.

That split is acceptable operationally only if every calibration-dependent test and runbook names the runtime file as the source of truth. Right now, it is easy to patch the repo YAML and believe the robot changed when the service override still points somewhere else.

### 4. Yellow detection has no concept of "full ball visible"

The HSV detector is intentionally simple: threshold HSV, morphology, external contours, area/circularity filter, bounding rectangle, area sort, `max_detections=1` [S2-4]. It publishes whatever visible yellow contour wins. It does not emit:

- mask area,
- aspect ratio,
- bbox touching frame or claw-occlusion regions,
- contour completeness,
- multiple candidates,
- temporal stability,
- raw image-space center history,
- "partial/occluded" status.

Those omissions are fine for proof-of-life detection, but not for a final pickup-close decision.

### 5. YOLO would not fix the final pickup contract by itself

`yolo_ncnn_node` is disabled by default and publishes the same `Detection` bbox structure into `/vision/object_detections` [S2-5]. Its NCNN path letterboxes, parses YOLO rows, clamps boxes to the original frame, runs NMS, then hands bboxes to the same object projection node [S2-5]. A better detector might classify the ball more robustly, but the close-range control still depends on bbox size and center unless the downstream contract changes.

### 6. Object indications publish only positive detections; absence is not a timestamped state

`object_indication_node` returns early when no indications exist, so downstream consumers only receive positive sightings [S2-6]. The operator has `object_stale_s=0.75`, but there is no explicit "no ball visible" message. During pickup, this means the operator works from the last positive estimate until it ages out. At 8 Hz detector max rate, that is several control iterations where a now-occluded or moved ball can still drive behavior.

Recommended correction: publish an envelope message with `objects: []`, source timestamp, and image/frame metadata, or make the operator subscribe to detections/indications with explicit freshness per source. The current bare list payload makes "no detections this frame" indistinguishable from "no message delivered."

### 7. Operator pickup treats projected object pose as a hard predicate

`fresh_ball()` chooses the nearest fresh ball by `hypot(forward_m,left_m)`, and `pickup_ball()` closes when `forward_m <= 0.14` and `abs(left_m) <= 0.08` [S2-10]. There are no guards for:

- negative robot-frame forward distance,
- sudden depth jumps,
- bbox near image border,
- implausible apparent-size change,
- source-specific quality,
- final close requiring image-space claw-mouth confirmation.

This explains the observed `ball_in_claw_zone` event with a negative `forward_m`: the projected pose satisfied the threshold even though the physical ball was still several inches away.

### 8. AprilTag transform path is not the same failure mode

AprilTag handling converts ROS optical frame translation into planar camera frame by `x=optical_z`, `y=-optical_x`, then composes with `camera_in_robot` [S2-8]. Operator and align-to-tag consumers use the same convention [S2-9][S2-10]. This path is geometrically coherent and uses AprilTag pose output rather than known-size object bbox projection.

So the observed issue should not be generalized as "all camera geometry is wrong." It is more specifically "object bbox projection is not a reliable final pickup sensor."

### 9. Scene map can inherit bad object positions, but pickup does not need scene map

`scene_map_node` stores object indications as camera-relative poses and maps them through the estimated camera pose when tags are available [S2-7]. If object indications are wrong, scene-map objects are wrong too. But `test_live_deliver.py` and `OperatorNode` use `/vision/object_indications` directly for pickup, so scene map is a downstream casualty, not the primary cause.

### 10. Existing tests validate idealized vision, not live failure modes

Current tests verify:

- synthetic full-circle yellow detection [S2-12],
- tiny noise rejection and largest-contour behavior,
- bbox-to-distance math for ideal dimensions [S2-11],
- simple image encoding conversion for `bgra8` and `rgba8` [S2-13],
- launch contract wiring and starter calibration file [S2-14].

They do not verify:

- padded `Image.step`,
- partial ball occlusion,
- clipped or crescent contours,
- ball behind/inside/at the claw mouth,
- false close on negative `forward_m`,
- temporal stability,
- stale/no-detection behavior,
- final delivery state.

This is why unit tests can pass while the live robot repeatedly closes five inches short of the ball.

## Ranked Failure Modes

| Rank | Failure Mode | Evidence | Probability | Impact |
|---|---|---|---|---|
| 1 | Partial/occluded ball contour produces invalid bbox depth near claw | Live static contradictions plus bbox projection code | Very high | Premature close, missed pickup |
| 2 | Final pickup uses metric indication as hard close predicate | `pickup_ball()` threshold logic | Very high | Closes while ball is outside claw |
| 3 | No explicit no-detection state; stale positive estimates persist | `object_indication_node` returns without publishing empty frames | High | Robot acts on old ball pose |
| 4 | Calibration source confusion between repo YAML and Pi override | runtime service/wiki and launch default split | Medium | Changes applied to wrong file |
| 5 | Rectified image uses `K` not `P` for projection | code vs ROS CameraInfo semantics | Medium | Projection bias after calibration changes |
| 6 | `Image.step` ignored | code vs ROS Image semantics | Medium unless runtime rows are padded | Corrupted detection pixels |
| 7 | HSV thresholds accept non-ball yellow or partial shapes | detector defaults and contour-only output | Medium | False/unstable detections |
| 8 | Camera yaw/lateral offset not calibrated with tape | no completed tape dataset yet | Medium | Approach bias, but not contradictory depth alone |

## Recommended Fix Program

### Phase 1: Make observation data trustworthy

- Fix `image_to_bgr_array()` to honor `msg.step` and add a padded-row unit test.
- Change object projection on rectified images to use `CameraInfo.p`; keep `k` only as fallback.
- Add debug fields to detections/indications: bbox size, center, mask area, contour area, fill ratio, circularity, source frame id, image dimensions, and projected distance candidates.
- Publish explicit empty indication frames with source timestamp so stale state is visible.

### Phase 2: Add a pickup-specific visual contract

- Add a claw-mouth ROI detector that operates in image space after the coarse approach phase.
- Calibrate ROI from real labeled frames: centered capturable, left capturable, right capturable, out-of-reach, inside-claw, occluded-right, no-ball.
- Require temporal stability across several frames before `grab`.
- Treat metric object projection as coarse navigation only, not final close permission.

### Phase 3: Harden operator behavior

- Reject negative or physically impossible ball `forward_m` for pickup.
- Add max frame-to-frame depth/lateral jump gates.
- Add a pickup phase state such as `visual_intake_confirmed` driven by the claw-mouth ROI signal.
- Keep effector telemetry as the final possession oracle.
- Make `grab_failed` include the last N vision debug samples so live failures can be diagnosed after the run.

### Phase 4: Close the test gap

- Add unit tests for padded image rows.
- Add synthetic occlusion tests showing the current bbox projection lies when only a slice of the ball is visible.
- Add replay tests from saved calibration frames.
- Extend live deliver testing with post-release evidence: user-gated observation, bin-side vision, or a task-specific final state check.

## What Stands Out Most

The codebase already contains the right warning in the wiki: object indication coordinates are estimates and precise localization needs a proven object controller [S2-15]. The live pickup path currently violates that warning. It uses an estimate produced from a contour bbox as a physical capture predicate. That is the core architectural mismatch.

The correct direction is not more global threshold tweaking. It is a richer final-pickup sensor contract: image-space claw-mouth capture evidence plus telemetry possession evidence.
