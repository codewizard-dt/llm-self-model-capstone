# Slice: hardware-proof-transport

| Field | Value |
|---|---|
| Feature | pm4-one-skill-execution |
| Stack | pilot |
| Depends on | executor-core-and-trace |

## What this slice delivers

Add the PM4 hardware transport and CLI path for the approved supervised proof skill set:
`survey_scene`, `claw_open`, `claw_close`, `verify_grasp`, and `verify_drop`. ROS imports stay isolated
inside the hardware transport or CLI module. The CLI requires explicit hardware mode and the
`--human-supervised` proof flag before any motion-producing message is published.

## Files to create / change

```text
pilot/src/pilot/skill_cli.py          NEW/CHANGE - CLI parser for `pilot skill ...`
pilot/src/pilot/ros_execution.py      NEW - optional rclpy transport for PM4 proof topics
pilot/pyproject.toml                  CHANGE - route `pilot` command to subcommands if needed
pilot/tests/test_skill_cli.py         NEW - CLI parser and supervision gate tests
pilot/tests/test_ros_execution.py     NEW - mocked ROS-boundary transport tests without rclpy import
```

## Requirements

- Provide a command equivalent to
  `pilot skill --hardware --human-supervised --skill survey_scene --duration-s 3.0 --out <trace.jsonl>`.
- Support the approved PM4 skill names: `survey_scene`, `claw_open`, `claw_close`, `verify_grasp`, and
  `verify_drop`.
- Require `--hardware` and `--human-supervised` before constructing a hardware transport or publishing
  to ROS.
- Convert CLI convenience flags or command JSON into contract-valid `PilotSkillCommand` objects.
- Build or obtain the current `PilotObservation` needed by the safety validator before dispatch.
- Map `survey_scene` dispatch to `/survey/goal`, terminal wait to `/survey/result`, and cancel to
  `/survey/cancel`.
- Map ball-handling proof skills to the current safe ROS/Brain command surface available in this repo;
  if a specific live topic is not present, expose a clear unsupported-skill failure before dispatch
  and document the missing surface for follow-up.
- Convert terminal proof payloads into `PilotSkillResult` statuses: `ok`, `rejected`, `failed`, or
  `stale`.
- Keep `rclpy` optional at import time. Development-machine tests must be able to exercise parser and
  transport mapping with fakes.

## Acceptance

- CLI tests prove missing `--hardware`, missing `--human-supervised`, invalid skill, and missing output
  path fail before hardware dispatch.
- Tests cover command construction for `survey_scene`, `claw_open`, `claw_close`, `verify_grasp`, and
  `verify_drop`.
- Tests cover mocked `/survey/goal`, `/survey/result`, and `/survey/cancel` behavior for the canonical
  `survey_scene` proof.
- Tests cover unsupported or unavailable ROS surfaces for ball-handling skills without publishing an
  unsafe fallback command.
- Existing `pilot observe` behavior is preserved or migrated cleanly under the same console command.

## Out Of Scope

- Autonomous task loops, LLM-driven skill selection, skill baseline memory, destination navigation,
  approach/centering skill execution, firmware changes, and physical proof execution inside tests.
