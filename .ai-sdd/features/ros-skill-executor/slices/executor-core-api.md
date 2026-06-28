# Slice: executor-core-api

| Field | Value |
|---|---|
| Feature | ros-skill-executor |
| Stack | pilot |
| Depends on | - |

## What this slice delivers

The ROS-free executor core API and typed result surface. This slice establishes `pilot.executor` as
the only pilot entry point for executing safety-accepted skill commands, defines immutable local
executor result and reason types, introduces a small transport protocol for later ROS/fake adapters,
and refuses any validation result that has not already been accepted by `pilot.safety`.

## Files to create / change

```
pilot/
  src/pilot/executor.py        NEW - executor API, result types, transport protocol, validation gate
  src/pilot/__init__.py        CHANGE - additive executor exports if appropriate
  tests/test_executor.py       NEW - ROS-free API and validation-refusal tests
```

## Requirements

- Define immutable dataclasses or typed helper objects for executor status/reason, execution result,
  transport payloads, and executor policy/deadline settings.
- Expose a deterministic function or class that accepts a `pilot.safety.ValidationResult`.
- Refuse any validation result whose status is not `accepted` or whose command is missing.
- Preserve command id, skill name, command status, reason code, message, issued/completed timing, and
  optional raw transport payloads in the result.
- Reuse `contracts.CommandStatus`, `contracts.PilotSkillCommand`, `contracts.PilotSkillName`,
  `pilot.safety`, and `pilot.skills`; do not define schemas in `pilot/`.
- Keep the module importable without ROS packages.

## Acceptance

- `pilot.executor` imports successfully in a ROS-free test process.
- Accepted validation results reach the executor's mapping boundary.
- Rejected/stopped/malformed validation results return deterministic refusal results and never publish
  transport payloads.
- Executor result values use contract-owned command statuses where applicable.
- Tests cover public API shape, validation refusal, missing command refusal, and no-ROS importability.

## Out Of Scope

- Concrete per-skill ROS JSON mapping.
- Waiting for operator results, timeout behavior, or ROS adapter implementation.
- CLI wiring and hardware proof commands.
