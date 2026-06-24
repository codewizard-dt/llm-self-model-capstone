# Slice: planted-fault-critic-tests

| Field | Value |
|---|---|
| Feature | operator-llm-critic |
| Maps to | F9 critic-panel |
| Stack | operator |
| Depends on | `critic-review-aggregation` |
| Related blockers | F3 parts-catalog grammar, F10 gap-analyzer |

## Scope

Plan planted-fault fixtures with known bad self-model candidates that each
critic lane must flag. These fixtures provide deterministic evidence that the
critic panel is not merely summarizing the candidate, but actively testing
physics, torque, and CoM/geometry claims against the visible packet.

## Acceptance

1. At least one planted fault targets physics plausibility.
2. At least one planted fault targets torque, load, motor evidence, or force
   claims.
3. At least one planted fault targets CoM, reach, connection, buildability, or
   geometry claims.
4. Each planted fault has an expected critic lane and expected cited field or
   packet section.
5. Tests distinguish true critic flags from blocked F3/F10 dependencies.
6. Fixtures validate candidate shape through `contracts.SelfModel` rather than
   an operator-local schema.

## Out of Scope

- Writing the actual test suite in this planning slice.
- Implementing critic prompt calls.
- Encoding hidden oracle answer keys.
- Implementing F3/F10 blockers.

## Dependencies

- `critic-review-aggregation` report expectations.
- `critic-prompt-panel` critic lanes and review template.
- F2 `SelfModel` validation.
- F3 valid-config rules and F10 residual summaries for later full-fidelity
  planted faults.

## Test / Validation Notes

- Plan fixture tests that fail if a planted fault is not flagged by its intended
  critic lane.
- Include blocked-dependency fixtures to ensure `[BLOCKED: awaiting F3
  parts-catalog valid-config rules]` and `[BLOCKED: awaiting F10 gap analyzer
  residual summary]` do not become false approvals.
- Include a reviewer check that test fixtures avoid hidden oracle leakage and
  cite only packet-visible evidence.
