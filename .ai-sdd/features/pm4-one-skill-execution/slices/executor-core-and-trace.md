# Slice: executor-core-and-trace

| Field | Value |
|---|---|
| Feature | pm4-one-skill-execution |
| Stack | pilot |
| Depends on | none |

## What this slice delivers

Add the ROS-free one-skill executor core for PM4. The executor validates exactly one
`contracts.PilotSkillCommand` against a `contracts.PilotObservation` using the existing safety
validator, dispatches through a test transport protocol, waits for one terminal result, writes
contract-valid `PilotTraceRecord` JSONL records, and exits with a structured outcome. This slice does
not import ROS or implement the hardware CLI.

## Files to create / change

```text
pilot/src/pilot/execution.py          NEW - one-skill executor API, transport protocol, outcomes
pilot/src/pilot/trace.py              NEW/CHANGE - small JSONL trace writer helpers if useful
pilot/src/pilot/__init__.py           CHANGE - additive exports for executor API
pilot/tests/test_execution.py         NEW - ROS-free executor and trace tests
```

## Requirements

- Expose a public function or class that accepts a `PilotSkillCommand`, `PilotObservation`,
  validation mode, human-supervision flag, timeout, and trace sink.
- Validate with `pilot.safety.validate_skill_command` before calling the transport.
- Dispatch at most one skill command per executor invocation.
- Define a small transport protocol with operations for dispatching, waiting for a terminal result,
  and canceling/stopping after timeout or interrupt.
- Normalize terminal transport outcomes into `contracts.PilotSkillResult`.
- Write contract-valid command, result, and stop `PilotTraceRecord` JSONL events with stable sequence
  numbers and session id.
- Write validation-failure and timeout/interruption traces without publishing extra skill commands.
- Keep all code in this slice importable without `rclpy` or ROS 2 installed.

## Acceptance

- Tests cover accepted validation, validation rejection before dispatch, one dispatch only, success
  result mapping, failure/rejection result mapping, timeout cancellation, interrupt cancellation, and
  contract validation of emitted trace records.
- Tests prove the executor core imports without ROS packages installed.
- The executor surfaces stable success/failure status for the future CLI.

## Out Of Scope

- ROS publishers/subscribers, CLI parsing, manual proof docs, LLM decisions, replay loop orchestration,
  baseline capture, and full registry-to-ROS coverage.
