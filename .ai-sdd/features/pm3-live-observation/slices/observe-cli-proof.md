# Slice: observe-cli-proof

| Field | Value |
|---|---|
| Feature | pm3-live-observation |
| Stack | pilot |
| Depends on | live-payload-mapping |

## What this slice delivers

Add the observe-only live CLI path for PM3. The command subscribes to read-only ROS JSON topics,
builds `PilotObservation` snapshots through the mapping API, emits JSONL to stdout by default or to
`--out`, and exits after a bounded duration or snapshot count. The manual proof threshold is strict:
`/vision/agent_scene`, bridge telemetry, and object tracks must all be available.

## Files to create / change

```text
pilot/src/pilot/observe.py             NEW - optional ROS observe-only CLI implementation
pilot/pyproject.toml                   CHANGE - console script entrypoint if repo style supports it
pilot/tests/test_observe_cli.py        NEW - parser/behavior tests with mocked ROS boundary
docs or pilot docs/runbook             NEW/CHANGE - concise PM3 manual proof instructions
```

## Requirements

- Provide a CLI equivalent to `pilot observe --objective "<text>" --duration-s 30`.
- Require `--objective`; do not use an implicit delivery-task default.
- Emit one `PilotObservation` JSON object per line to stdout unless `--out` is provided.
- Support bounded termination by duration and, if implemented, optional snapshot count.
- Subscribe only to read-only evidence topics. Do not create publishers for `/operator/command`,
  `/task_plan/request`, `/vex/cmd`, or any motion-producing topic.
- Prefer `/vision/agent_scene` and also track bridge telemetry and object tracks for the strict manual
  proof threshold.
- Exit nonzero with a clear reason if ROS runtime dependencies are missing or if the strict topic
  readiness threshold is not reached before timeout.
- Keep `rclpy` imports optional and isolated so importing `pilot` and `pilot.observe` remains safe on
  development machines without ROS 2.
- Document the manual live command, expected required topics, expected stdout/file shape, and evidence
  that no motion was commanded.

## Acceptance

- Tests cover CLI parsing for required `--objective`, stdout default, `--out`, duration, and readiness
  threshold behavior.
- Tests verify the observe path refuses to run without ROS runtime dependencies using a clear error.
- Tests or code structure prove no motion command publishers are created.
- Manual proof documentation states that `/vision/agent_scene`, bridge telemetry, and object tracks are
  required for PM3 pass.
- The CLI emits contract-valid JSONL observations when given mocked live payloads.
- Existing pilot tests remain green.

## Out of scope

- Skill execution, LLM calls, safety validation, run logging beyond observe JSONL, task-plan requests,
  hardware motion, perception pipeline changes, or contract schema changes.
