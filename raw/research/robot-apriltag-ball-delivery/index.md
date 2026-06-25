---
topic: "proper workflow first... then write a new progam for the robot that does these things in order: 1) orients itself in the workspace using apriltags. 2) moves to the ball-loading area apriltag. 3) moves to the bin area apriltag, 4) drops the ball in the bin. Save this as a new program in the ros2-runtime folder."
slug: robot-apriltag-ball-delivery
researched: 2026-06-25
sources: [./sources.md]
---

# Research: Robot AprilTag Ball Delivery

> The right workflow is to build a ROS 2 console program that reuses the existing AprilTag proof helpers for bounded scan and tag approach, then add a small `release` command to the ROS-to-V5 bridge because the current command grammar did not expose a ball-drop action.

## Research Questions
- Which existing ROS 2 runtime code already performs bounded AprilTag orientation and approach?
- Which workspace tag IDs represent the ball-loading area and bin?
- Can the current ROS/V5 command grammar drop the ball?
- What package entrypoint and test style should the new program follow?

## Current State (Codebase)
- `vexy_ros.tag_action_proof` already provides `run_scan`, `approach_tag`, `TagActionProof.send`, and JSON summary finalization for supervised tag-action proofs [S1].
- Runtime maps define `ball_staging` as tag `1` and `bin` as tag `0` in both grab/toss map variants [S2].
- `bridge_protocol.py` previously allowed only `stop`, `drive`, `turn`, and `set_goal`; `pros_bridge/src/main.cpp` rejected `set_goal`, so dropping the ball required a new bridge command [S3], [S4].
- `setup.py` exposes ROS runtime programs as `console_scripts`, so the new program should be installed the same way [S5].

## Key Findings
- The lowest-risk robot workflow is scan first, then use fresh AprilTag transforms to drive toward tag standoff distances with TTL-limited `drive`/`turn` commands [S1].
- A release action must be explicit in the bridge contract; otherwise the program could only stop at the bin, not drop the ball [S3], [S4].
- ROS 2 Python programs should use normal rclpy node publisher/subscription/spin patterns; the existing `TagActionProof` node already follows that shape [S6].

## Constraints
- Commands must stay bounded and interruptible through TTLs, watchdog behavior, and stop-in-finally behavior.
- Missing hardware must fail closed. The V5 release motor path should reject when the configured release motor port is absent.
- The new program must live in `robot/ros2-runtime` and match existing unit-test style with ROS module stubs.

## Recommendation
- Add `vexy_ros.deliver_ball` as a ROS 2 console program named `vexy_deliver_ball`.
- Reuse `run_scan` and `approach_tag` rather than introducing a new navigation controller.
- Add a bounded `release` command with `duration_ms` to ROS bridge protocol and V5 brain firmware.
- Verify with tests for default tag IDs, sequence ordering, failure when no tags are observed, release packet publishing, and bridge protocol duration clamping.

## Next Steps
- Use the `wiki-ingest` skill on this report if it should become durable wiki knowledge.
- After hardware wiring is confirmed, adjust `RELEASE_MOTOR_PORT` and `RELEASE_RPM` in the V5 bridge if port `3` or the direction is wrong.
