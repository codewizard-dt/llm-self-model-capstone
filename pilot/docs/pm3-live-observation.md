# PM3 Live Observation Proof

Run the observe-only proof on the Pi after the ROS 2 environment is sourced and the read-only
vision/bridge topics are active:

```bash
pilot observe --objective "collect the red cube" --duration-s 30
```

By default the command writes one compact `contracts.PilotObservation` JSON object per line to
stdout. Use `--out proof.jsonl` to write the same JSONL stream to a file. Use `--count N` to stop
after a fixed number of complete snapshots.

## Required Readiness Topics

The strict PM3 threshold requires all of these topics before any successful proof:

- `/vision/agent_scene`
- `/vision/object_tracks`
- `/vex/telemetry`
- `/vex/bridge_status`

The command also subscribes to optional read-only context when available:

- `/vision/scene_map`
- `/task_plan/current`
- `/operator/status`

Missing or malformed required topic payloads cause a nonzero exit with the missing topic or malformed
payload reason on stderr. A missing ROS runtime dependency also exits nonzero before any node is
created.

## Pass Criteria

- The process exits `0` because `--duration-s`, `--count`, or `Ctrl-C` ended the observe window.
- The JSONL stream contains complete `PilotObservation` objects with the requested objective.
- Required readiness topics were observed before `--readiness-timeout-s`.
- No motion-producing topics were published.

## No-Motion Evidence

`pilot observe` creates subscriptions only. It does not create publishers for `/operator/command`,
`/task_plan/request`, `/vex/cmd`, or any other command topic. The proof output is observation JSONL
only; it does not dispatch task plans, call an LLM, run skills, or send control-grammar commands.
