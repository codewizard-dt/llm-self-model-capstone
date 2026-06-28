# Slice: logger-core-api

| Field | Value |
|---|---|
| Feature | run-logger |
| Stack | pilot |
| Depends on | - |

## What this slice delivers

The ROS-free run-logger foundation: immutable logger configuration, session/sequence/timestamp
bookkeeping, trace-record construction helpers, and the public API skeleton for appending contract
events. This slice establishes `pilot.run_logger` without yet implementing durable JSONL file writes.

## Files to create / change

```
pilot/
  src/pilot/run_logger.py       NEW - logger config, clock/session metadata, record builders
  src/pilot/__init__.py         CHANGE - additive run logger exports if appropriate
  tests/test_run_logger.py      NEW - API, metadata, validation, no-ROS tests
```

## Requirements

- Define a small ROS-free run logger API in `pilot.run_logger`.
- Support injectable `session_id`, next-sequence state, and clock/timestamp behavior for deterministic
  tests.
- Provide typed record-building helpers for observation, decision, command, result, assertion, and
  stop events.
- Use contract-owned types such as `PilotObservation`, `PilotDecision`, `PilotSkillCommand`,
  `PilotSkillResult`, `PilotAssertion`, and `PilotTraceRecord`.
- Validate constructed records through the contract trace schema before exposing them to writer code.
- Keep all data structures pilot-local and non-schema-owning; do not define pydantic schemas in
  `pilot/`.
- Keep the module importable without ROS packages.

## Acceptance

- Tests prove session id is stable across a logger instance.
- Tests prove `seq` starts at zero by default and increments exactly once per built/appended record.
- Tests prove `monotonic_ms` can come from an injected deterministic clock.
- Tests prove all six event variants can be constructed as contract-valid trace records.
- Tests prove invalid payloads are rejected before writer handoff.
- Tests prove `pilot.run_logger` imports without `rclpy`, ROS message packages, or ROS topic classes.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- Durable file writes, JSONL flushing, default file naming, readback parsing, recent-history
  formatting, replay-mode integration, CLI wiring, hardware run orchestration, or ROS behavior.
