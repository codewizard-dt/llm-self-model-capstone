# Slice: transport-results-timeouts

| Field | Value |
|---|---|
| Feature | ros-skill-executor |
| Stack | pilot |
| Depends on | skill-command-mapping |

## What this slice delivers

Transport execution, terminal-result waiting, and timeout classification. This slice adds the fake
transport used by unit tests and the narrow ROS transport adapter boundary for hardware mode, then
parses terminal operator feedback/results into deterministic executor results.

## Files to create / change

```
pilot/
  src/pilot/executor.py        CHANGE - fake transport, result parsing, deadlines/timeouts
  src/pilot/ros_executor.py    NEW - optional ROS adapter if separation keeps imports clean
  tests/test_executor.py       CHANGE - fake transport result, rejection, and timeout coverage
```

## Requirements

- Provide a fake/in-memory transport for deterministic tests.
- Isolate any `rclpy` or ROS message imports so importing `pilot.executor` still works without ROS.
- Publish exactly one transport request for each motion/manipulator skill execution.
- Wait for a matching terminal result when transport is expected to produce one.
- Correlate by command id when present and fall back to ordered result matching for current operator
  result payloads that lack pilot command ids.
- Parse terminal success, rejection, failure, and stale/timeout cases into stable executor results.
- Use the smaller applicable timeout from command parameters and registry `max_duration_ms`, with any
  configured grace period applied deterministically.
- Never classify publish success alone as skill success.

## Acceptance

- Fake transport tests cover successful terminal result, rejected result, failed result, timeout, and
  ordered fallback matching.
- Timeout results use `contracts.CommandStatus.STALE` or the agreed stale/timeout status and include a
  stable reason code.
- ROS adapter code is optional at import time and has a narrow topic/publish/subscribe boundary.
- Stop behavior publishes a halt request when transport is available and returns a stopped/ok result
  according to terminal evidence or policy timeout.

## Out Of Scope

- Live robot proof runs or calibration baselines.
- Run logger integration beyond returning enough result detail for future logging.
- Modifying `robot/ros2-runtime` operator nodes unless a small compatibility fix is unavoidable and
  covered by tests.
