# Slice: validator-api-and-policy

| Field | Value |
|---|---|
| Feature | safety-validator |
| Stack | pilot |
| Depends on | - |

## What this slice delivers

The public ROS-free safety validator API and policy/result types. This slice establishes the executor
and logger facing contract for validating a `contracts.PilotSkillCommand` against a
`contracts.PilotObservation`, mode, thresholds, and the static skill registry. It should implement the
core mode distinction, stop-command admissibility, and bridge/supervision health gates, but leave
skill-specific target and movement-envelope rules to the next slice.

## Files to create / change

```
pilot/
  src/pilot/safety.py          NEW - validator policy, result types, and core validation entry point
  src/pilot/__init__.py        CHANGE - additive exports for the safety validator API
  tests/test_safety.py         NEW - focused tests for API, mode, stop, and core health gates
```

## Requirements

- Define immutable dataclasses or typed helper objects for validation mode, policy thresholds,
  validation status/reason, and validation result.
- Expose a deterministic function for validating a `PilotSkillCommand` with a `PilotObservation`.
- Reuse `contracts` models and `pilot.skills` registry metadata; do not define pydantic schemas in
  `pilot/`.
- Implement explicit `replay` and `hardware` modes.
- In hardware mode, reject motion commands when human supervision is absent.
- Reject or stop unsafe non-stop commands when bridge state is `stale` or `fault`, estop is true, or
  heartbeat freshness exceeds the configured threshold.
- Keep `stop` admissible under unsafe conditions and surface the unsafe health state in the result.
- Use stable machine-readable reason codes plus concise messages.

## Acceptance

- The safety module can be imported without ROS dependencies.
- Valid replay-mode commands with healthy observation state are accepted.
- Hardware-mode commands require supervision.
- Non-stop commands reject stale/fault/estop bridge state with stable reason codes.
- `stop` returns an accepted or stopped outcome even when observation health is unsafe.
- Tests cover the public API, mode behavior, supervision gate, core bridge/estop gates, and stop
  behavior.

## Out Of Scope

- Skill-specific target/destination evidence checks.
- Numeric envelope enforcement beyond validating that command objects are already contract-valid.
- ROS publishing, executor feedback handling, LLM parsing, assertions computation, run logging, and
  replay loop orchestration.
