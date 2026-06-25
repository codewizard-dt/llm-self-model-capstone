# Deliver Ball Run Summary

Generated from persisted Raspberry Pi run summaries pulled into this folder.

## Current Diagnosis

The delivery routine consistently fails before `grab`, `lift`, and `release`.
The early runs showed the robot could sometimes get near the ball-loading tag,
but later physical observation showed the robot was missing the ball, contacting
the wall, and spinning its wheels. Increasing the global camera lateral offset
from `y_m=0.06` to `y_m=0.10` did not solve the behavior.

The latest run ended far from tag 1 and laterally off line:

- `deliver_ball_20260625_163233_offset_y010_retry_summary.json`
- `post_distance_m`: `1.267m`
- `post_left_m`: `0.661m`
- `post_yaw_rad`: `0.549 rad`
- result: `failed`, `ball_tag_approach_failed`, approach `timeout`

This points to the direct tag-centering approach loop being too brittle for the
wall/ball geometry. It should not keep driving/searching when the ball tag is
lost or when the robot is mechanically blocked.

## Runs

| File | Offset | Result | Ball approach detail |
|---|---:|---|---|
| `deliver_ball_summary.json` | none | failed | timed out at `0.774m` |
| `deliver_ball_20260625_144226_summary.json` | none | failed | timed out near `0.485m` |
| `deliver_ball_20260625_144427_summary.json` | none | failed later | ball approach reached, then bin approach failed |
| `deliver_ball_20260625_145627_summary.json` | none | failed | tag 1 lost; no post distance |
| `deliver_ball_20260625_145744_summary.json` | none | failed | timed out near `0.480m` |
| `deliver_ball_20260625_162031_offset_y006_summary.json` | `y=0.06m` | failed | timed out at `1.164m`; slot/bridge likely not actually ready |
| `deliver_ball_20260625_162234_offset_y006_after_slot8_summary.json` | `y=0.06m` | failed | timed out near `0.492m` after slot 8 + telemetry verification |
| `deliver_ball_20260625_162519_offset_y010_summary.json` | `y=0.10m` | failed | timed out near `0.491m` |
| `deliver_ball_20260625_162918_offset_y010_stuck_summary.json` | `y=0.10m` | failed | tag 1 not fresh at end; stuck detector did not trigger |
| `deliver_ball_20260625_163233_offset_y010_retry_summary.json` | `y=0.10m` | failed | ended far from tag 1: `1.267m`, `left=0.661m` |

## Implementation State

- `vexy_deliver_ball` exists and runs from the ROS 2 runtime.
- Slot 8 contains the guarded Brain bridge with bounded `grab`, `lift`, and `release` commands.
- Direct tag observation now supports `camera_in_robot_json`.
- Approach summaries now include diagnostic lateral/yaw fields when available.
- Stuck detection was added for visible-tag/no-progress cases, but the latest failure was tag-loss/timeout rather than a visible stagnant tag.

## Recommended Next Fix

Stop treating tag 1 as the only approach target once the robot is close to the
wall. The next iteration should either:

1. approach the detected `yellow_ball` object after initial tag orientation, or
2. stop immediately when tag 1 is lost during forward approach and report
   `tag_lost_during_approach` instead of continuing to search until timeout.

The current evidence suggests more lateral offset tuning alone is not enough.
