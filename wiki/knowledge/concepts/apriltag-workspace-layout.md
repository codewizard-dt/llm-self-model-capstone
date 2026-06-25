---
id: apriltag-workspace-layout
title: AprilTag Workspace Layout for Manipulation Tasks
aliases: [AprilTag workspace layout, manipulation tag layout, ball staging tag layout]
updated: 2026-06-25
tags: [concept, apriltag, vision, localization, workspace, manipulation]
sources:
  - ../sources/apriltags.md
  - ../sources/vision-vex-architecture.md
  - ../sources/apriltag-larger-workspace-map.md
  - ../sources/robot-apriltag-ball-delivery.md
---

# AprilTag Workspace Layout for Manipulation Tasks

Practical layout guide for placing `tag36h11` AprilTags in a workspace where a VEX V5 Clawbot performs a grab-and-toss task. Derived from the capstone's AprilTag research and vision architecture decisions.

derived_from::[[apriltags]]
derived_from::[[vision-vex-architecture]]
uses::[[apriltag-library]]
extends::[[task-telemetry-contract]]

---

## What AprilTags do (and don't do) here

**AprilTags localize the robot, not the objects.** Fixed tags in the workspace let the Pi 5 camera compute the robot's `{x_mm, y_mm, heading_deg}` pose after each action. The ball itself is detected by YOLO — not tagged. AprilTags on fixed landmarks (bin, wall, staging area) give the robot a pose anchor so it can express "drive to bin" as a target pose rather than dead-reckoning.

---

## Workspace size

> **Contradiction:** This section originally recommended **80 cm × 80 cm** with **100 mm tags**. [Research: AprilTag Larger Workspace & Map Format](../sources/apriltag-larger-workspace-map.md) (2026-06-22) supersedes both figures: the Clawbot is 50 cm nose-to-tail, leaving only 30 cm of free space per axis in an 80 cm arena — insufficient to turn or align. See corrected values below.

Use a **150 cm × 200 cm** floor rectangle (≈5 ft × 6.5 ft). This gives 3× the robot body length in the short axis and 4× in the long axis. Mark corners with tape. An 8-foot folding table (76 cm wide) is too narrow — use the floor.

Print tags at **200 mm × 200 mm** (fits on A4/Letter paper with 5 mm margin). At 640×480 resolution, 200 mm tags detect reliably up to ~1.5 m, sufficient for the full arena. Detection range scales linearly with tag size: 100 mm → 30–80 cm; 200 mm → 60–160 cm (practical ~1.5 m).

---

## How many tags to print

**3 tags minimum**, with purpose-assigned IDs:

| Tag ID | Placement | Role |
|--------|-----------|------|
| `0` | Bin (fixed to front face or adjacent wall) | Gives exact pose to the throw target; approach vector for the toss |
| `1` | Ball staging area (taped to table near where ball starts) | Approach vector for the grab |
| `2` | Back wall or corner reference | Home-position anchor; triangulation fallback |

A 4th tag at the opposite corner helps disambiguate heading when two tags are co-visible, but 3 is sufficient for a demo-scale arena.

Print extras — tags are paper and can be lost or damaged. Print the full `tag36h11` set (sheets 0–4) and keep spares.

---

## Arrangement rules

1. **Fixed surfaces only.** Tags must be on surfaces that do not move during a run: bin walls, arena walls, table edges. The ball itself must not carry a tag.
2. **Face the camera.** Orient each tag roughly toward the center of the arena. Tags seen at >45° angle degrade pose quality significantly.
3. **Checkpoint coverage, not continuous coverage.** The robot does not need a tag visible at all times — it dead-reckons between fixes (~1–3 cm/m drift on smooth floor). Design the task flow so a tag enters frame just before each precision maneuver (ball approach, throw alignment). Avoid clustering all tags in one corner; spread them so the robot naturally re-acquires one during each leg of the task. See [[robot-workspace-map]] for the full checkpoint pattern.
4. **Matte paper.** Print on matte white paper. Glossy surfaces produce specular reflections that cause false negatives. Laminate if available (matte laminate, not glossy).
5. **Clear margins.** Leave a white border around each tag equal to ~2× the module size. The library requires a quiet zone to decode correctly.

---

## Task flow mapping

| Step | Tag seen | What the pose enables |
|------|----------|----------------------|
| Home → ball | Tag 1 | Corrects approach vector before grab |
| Grab | (motor telemetry only) | Gap block: torque/current/position residuals |
| Ball → bin | Tag 0 | Locks final throw pose; `dtheta` residual feeds heading correction |
| Return | Tag 2 | Home-position confirmation |

The `{dx, dy, dtheta}` residuals from each tag observation populate the gap block in the [[task-telemetry-contract]] and feed the LLM's self-model revision loop alongside motor telemetry.

## Delivery Routine Confirmation

[Research: Robot AprilTag Ball Delivery](../sources/robot-apriltag-ball-delivery.md) confirms that the current ROS 2 delivery program uses this tag assignment directly: first scan/orient, then approach `ball_staging` tag `1`, then approach `bin` tag `0`, then run a bounded release command. **The tag layout is now executable as a proof routine, not only a proposed workspace design.** uses::[[vexy_ros ROS 2 Runtime]] relates_to::[[robot-workspace-map]]
