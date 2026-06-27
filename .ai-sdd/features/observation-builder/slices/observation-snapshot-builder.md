# Slice: observation-snapshot-builder

| Field | Value |
|---|---|
| Feature | observation-builder |
| Stack | pilot |
| Depends on | `pilot-scaffold-and-cache` |

## What this slice delivers

The observation builder function/class that compacts normalized live-like or replay-like cache inputs
into a contract-valid `contracts.PilotObservation` snapshot for downstream LLM decision, assertion,
replay, and logging features.

## Files to create / change

```
pilot/
  src/pilot/observation.py          CHANGE - builder implementation over the cache/input models
  tests/test_observation_builder.py NEW - snapshot behavior and schema validation tests
```

## Requirements

- Map normalized cache/input records into `contracts.PilotObservation`.
- Preserve task objective, phase, robot pose, localization confidence/age, visible objects/tags,
  manipulator state, bridge health, last command/result, recent failures, and current assertions.
- Deterministically sort and truncate objects/tags/assertions/recent failures within contract bounds.
- Represent stale or missing optional evidence explicitly without fabricating confident state.
- Validate emitted snapshots through `PilotObservation.model_validate` or equivalent.
- Keep builder code ROS-free and replay-friendly.

## Acceptance

- Tests cover a complete snapshot with all required evidence categories.
- Tests cover missing/stale optional evidence without crashes or optimistic defaults.
- Tests cover deterministic object/tag ordering and bounded list lengths.
- Tests prove emitted snapshots validate through `contracts.PilotObservation`.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- ROS node/subscription wiring.
- Computing assertions from raw evidence; this builder carries assertions already supplied by
  upstream or replay inputs.
- LLM prompting, skill execution, safety validation, run logging, or replay loop orchestration.
