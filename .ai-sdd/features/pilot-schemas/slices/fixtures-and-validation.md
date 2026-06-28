# Slice: fixtures-and-validation

| Field | Value |
|---|---|
| Feature | pilot-schemas |
| Stack | contracts |
| Depends on | `models-and-schemas` |

## What this slice delivers

Canonical pilot fixtures and validation wiring for the schemas introduced by `models-and-schemas`.
This closes the automated `pm1-schemas-ready` prerequisite by proving observations, skills, decisions,
assertions, and run trace records validate through the repo's contract validation path.

## Files to create / change

```
contracts/
  fixtures/
    pilot_observation_example.json       NEW
    pilot_skill_command_examples.jsonl   NEW
    pilot_assertion_examples.jsonl       NEW
    pilot_decision_examples.jsonl        NEW
    pilot_trace_example.jsonl            NEW
  src/contracts/
    validate.py                          CHANGE - validate pilot fixture families
  tests/
    test_validate.py                     CHANGE - cover pilot fixture validation and rejection cases
```

## Requirements

- Add fixtures that cover at least one valid compact observation, skill command, pilot decision,
  assertion result, and pilot trace record.
- Include trace records for observation, decision, command, result, assertion, and stop events.
- Include examples carrying bridge freshness, telemetry freshness, estop/motion state, last command,
  last result, current assertions, and replay identifiers.
- Wire `contracts.validate` so the new fixture families are validated by their matching pydantic
  models or `TypeAdapter` instances.
- Add tests that prove the validation dispatch accepts the committed pilot fixtures.
- Add tests that prove invalid examples are rejected for unknown decisions, unknown skills, oversized
  numeric envelopes, stale or malformed hardware health where represented, and malformed trace records.
- Keep validation dispatch for existing fixture families unchanged except for any narrowly justified
  family glob additions required to avoid cross-parsing pilot fixtures as unrelated contracts.

## Acceptance

- `make validate` passes from the repo root.
- `make test` passes for `contracts/` and preserves existing fixture-validation behavior.
- Invalid pilot fixture mutations produce readable validation failures.
- The committed pilot fixtures are deterministic, small, and suitable for replay-mode tests in later
  features.
- `make lint` passes.

## Out Of Scope

- Implementing the pilot replay runner or run logger.
- Hardware execution or ROS topic integration.
- Adding live capture artifacts from a physical robot.
