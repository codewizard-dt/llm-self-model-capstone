---
id: object-indication-projection
title: Object Indication Projection
aliases: [object indications, bbox projection, monocular object projection]
updated: 2026-06-26
sources:
  - ../sources/vision-stack-audit.md
tags: [concept, vision, ros2, calibration]
---

# Object Indication Projection

Object indication projection is the `vexy_ros` pattern that turns a 2D object detection bbox into a camera-relative metric hint. The current implementation combines a known class dimension, such as the yellow ball's 0.065 m diameter, with CameraInfo focal length and bbox pixel width/height to estimate `forward_m`; it then uses the bbox center and principal point to estimate `left_m`. derived_from::[[vision-stack-audit]] uses::[[vexy-ros-runtime]]

This is a useful coarse navigation estimate when the full object silhouette is visible. It is not a reliable final manipulation signal when the object is clipped, occluded by the claw/motor, partially thresholded, or represented by only a visible crescent. In those cases, the bbox describes visible pixels rather than the object's true diameter, so the depth estimate can jump, invert, or satisfy capture thresholds while the ball is still physically outside the claw.

The projection layer also has two implementation caveats from the audit: rectified `/camera/image_rect` consumers should use `CameraInfo.P` intrinsics, not only raw-image `K`, and downstream consumers need explicit empty/no-detection frames rather than only positive sightings. relates_to::[[camera-module-3-setup]] relates_to::[[claw-mouth-pickup-vision]]
