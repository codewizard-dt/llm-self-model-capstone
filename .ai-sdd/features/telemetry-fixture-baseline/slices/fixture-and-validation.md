# Slice: fixture-and-validation

| Field | Value |
|---|---|
| Feature | telemetry-fixture-baseline |
| Stack | contracts |
| Depends on | none |

## What this slice delivers

Add the deterministic fixture run that downstream self-modeling components can consume without any
robot, ROS, or MCAP dependency. The fixture must live under repo-level `telemetry-fixtures/`, include
a provenance manifest, and include a contract-valid `contract.jsonl` artifact.

## Scope

- Create `telemetry-fixtures/<run-id>/manifest.json`.
- Create `telemetry-fixtures/<run-id>/contract.jsonl` with at least one valid `contracts.ContractLine`
  record representative of the robot align/telemetry baseline.
- Keep fixture data deterministic, small, and reviewable.
- Label the manifest provenance clearly as fixture-backed, not real hardware.
- Add validation coverage that reads every non-empty line from fixture `contract.jsonl` and validates
  it through the runtime `contracts.ContractLine` model.
- Wire validation into an existing test path or `make validate`, using repo conventions.

## Acceptance

1. `telemetry-fixtures/<run-id>/manifest.json` exists and points to `contract.jsonl`.
2. Manifest metadata includes run id, task, provenance, fixture status, and canonical evidence path.
3. `contract.jsonl` contains at least one valid `contracts.ContractLine` line.
4. A local deterministic test or validation command fails if any fixture contract line is invalid.
5. No ROS, MCAP, hardware, camera, serial device, or network dependency is introduced.

## Out of Scope

- Do not add or fake MCAP.
- Do not implement F8/F9/F10/F11/F12.
- Do not change frozen contract schemas.
- Do not require a real robot run.
