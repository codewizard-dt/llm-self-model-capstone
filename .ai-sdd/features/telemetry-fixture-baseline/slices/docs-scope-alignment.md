# Slice: docs-scope-alignment

| Field | Value |
|---|---|
| Feature | telemetry-fixture-baseline |
| Stack | coprocessor |
| Depends on | fixture-and-validation |

## What this slice delivers

Align the documentation and requirements notes with the agreed scope: JSONL fixtures unblock the MVP
self-modeling features now, while MCAP remains the later real-hardware replay and audit artifact.

## Scope

- Update relevant docs or requirements notes to state that downstream components consume
  `contracts.ContractLine` JSONL.
- Document that `telemetry-fixtures/` is fixture-backed and may be used by F8/F9/F10/F11/F12 and
  `make demo`.
- Document that real hardware runs later should produce MCAP plus the same semantic JSONL shape.
- Clarify that PR #43's telemetry pipeline is a useful JSONL baseline and partial MCAP capture, not
  proof that full hardware-capture requirements are complete.
- Preserve `MASTER_REQUIREMENTS.md` as authoritative and update only where the current milestone
  needs clarification.

## Acceptance

1. Documentation explicitly separates fixture-backed MVP evidence from later real hardware evidence.
2. Documentation says downstream self-modeling components depend on `ContractLine` JSONL, not ROS or
   MCAP directly.
3. Documentation does not imply the fixture is a real robot run.
4. Existing MCAP requirements for later hardware audit/replay remain visible.

## Out of Scope

- Do not rewrite the full milestone plan.
- Do not remove MCAP from the real hardware capture requirements.
- Do not document fake MCAP generation as an acceptable path.
