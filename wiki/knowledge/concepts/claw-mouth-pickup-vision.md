---
id: claw-mouth-pickup-vision
title: Claw-Mouth Pickup Vision
aliases: [claw ROI detector, pickup ROI, ball-in-claw vision]
updated: 2026-06-26
sources:
  - ../sources/vision-stack-audit.md
tags: [concept, vision, manipulation, pickup]
---

# Claw-Mouth Pickup Vision

Claw-mouth pickup vision is the recommended final-stage capture contract for VEXY's ball delivery behavior. Instead of closing the claw solely from a metric object indication, the robot should use a calibrated image-space region of interest around the claw mouth to answer a narrower question: **is the ball visually between the jaws and stable enough to close?** derived_from::[[vision-stack-audit]] relates_to::[[object-indication-projection]]

The concept keeps the existing object indication path for coarse approach while the ball is fully visible, then switches to pickup-specific evidence near capture. The ROI detector should be calibrated from real labeled frames: open and closed claw, centered capturable ball, left/right capturable extremes, out-of-reach centered ball, inside-claw ball, occluded-right ball, and no-ball cases. It should publish image center, mask area, bbox, confidence, and temporal stability rather than pretending every yellow contour is a complete metric object.

Effector telemetry remains the final possession oracle after the close. The claw-mouth visual signal decides when to attempt a close; manipulator position/velocity decides whether an object was actually captured. uses::[[vexy-ros-runtime]] relates_to::[[task-telemetry-contract]]
