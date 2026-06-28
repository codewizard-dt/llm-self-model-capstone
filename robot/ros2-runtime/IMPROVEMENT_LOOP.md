# Runtime Improvment Loop

## PROMPT 1

```
› === telemetry written under: /home/vexy/telemetry/live-align-20260627-135310 ===
  Use this telemetry to determine why the robot did not move in the direction of tag 1, even though we thought we implemented a bypass if the tag isn't seen, but then it just goes in the direction of that tag and then, based on
  the predicted pose, moves toward where the tag should be.
```

## RESPONSE 1

```
• The robot did not move toward predicted tag 1 because that fallback was not in the code path used by this test.

  Telemetry says:

  - Requested tag 1 was never seen.
  - align_to_tag_result.jsonl:
    success=false, reason=stale_tag, fault=tag_not_visible

  - survey_result.jsonl:
    success=true, observed_tag_ids=[0, 2]

  - Command log:
    147 sent commands total:
      - 146 were turn
      - 1 was stop
      - 0 were drive
      - 0 had reasons like orient_to_predicted_tag_1 or move_to_predicted_tag_1

  The fallback we thought existed is in Operator.move_to_tag() via _move_to_predicted_tag_pose(). But test_live_align.py runs this sequence:

  1. locate_nearest_apriltag
  2. align_to_tag(tag_id=1)
  3. if tag missing: survey_scan
  4. if survey does not find tag 1: fail/return

  It never calls move_to_tag(1) or orient_to_tag(1) after the survey misses tag 1. So the robot only did the generic survey spin at omega=0.45, found tags 0 and 2, then stopped. It never entered the predicted-pose navigation code.

  Recommended fix: after align_to_tag returns stale_tag/tag_not_visible, call move_to_tag(tag_id, target_distance_m=...) in a bounded loop when map pose is available, instead of only doing survey_scan.
```

## PROMPT 2

```
› implement the fix
```

## RESPONSE 2 

```
• Implemented the predicted-pose fallback in robot/ros2-runtime/tests/test_live_align.py.

  Behavior now:

  - If align_to_tag fails with stale_tag / tag_not_visible, it still runs survey_scan.
  - If survey does not find the requested tag, it no longer fails immediately.
  - It enters a bounded move_to_tag(tag_id, target_distance_m=0.4064) loop for up to 20s, which exercises the existing predicted-map-pose navigation path
    (orient_to_predicted_tag_* / move_to_predicted_tag_*).

  Verified:

  - uv run --with 'pydantic>=2,<3' python -m unittest robot/ros2-runtime/tests/test_operator.py passed.
  - uv run python -m py_compile robot/ros2-runtime/tests/test_live_align.py passed.
  - Synced to Pi with make sync-pi.
  - Rebuilt and restarted vexy-ros-stack.service on the Pi successfully.

  I did not rerun the live align test because it moves the robot.
```

## COMMAND SEQUENCE AFTER CODE CHANGES

### On host machine
```bash
make sync-pi
```

### On Raspberry Pi
```bash
make rebuild-pi

python [test_name].py
```

## TEST OUTPUT

Feeds back into PROMPT 1