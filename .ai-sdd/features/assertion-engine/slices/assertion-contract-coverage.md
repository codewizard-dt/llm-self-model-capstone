# Slice: assertion-contract-coverage

| Field | Value |
|---|---|
| Feature | assertion-engine |
| Stack | pilot |
| Depends on | `assertion-evaluators` |

## What this slice delivers

Final assertion-engine contract and integration coverage: deterministic ordering, public exports,
snapshot round-trip behavior with `pilot.observation`, no-ROS import checks, and focused regression
tests that make the assertion output ready for run logger, replay mode, skill baselines, and delivery
recipe features.

## Files to create / change

```
pilot/
  src/pilot/assertions.py       CHANGE - final ordering/export polish if needed
  src/pilot/__init__.py         CHANGE - public exports if not completed in foundation slice
  tests/test_assertions.py      CHANGE - contract/order/export/no-ROS integration coverage
```

## Requirements

- Prove the engine returns exactly one assertion per required id in stable source-brief order.
- Prove outputs can be embedded into `ObservationCache.current_assertions` and compacted by
  `build_observation_snapshot` without violating `contracts.PilotObservation`.
- Prove no object, tag, failure, or assertion ordering behavior becomes nondeterministic.
- Ensure public exports from `pilot` are additive and do not disturb existing observation or skill
  registry exports.
- Keep tests fixture-sized and replay-friendly; do not add hardware captures.

## Acceptance

- Tests prove assertion output round-trips through `contracts.PilotAssertion` and
  `contracts.PilotObservation`.
- Tests prove stable ordering and exact id coverage across repeated calls.
- Tests prove package-level exports expose the intended assertion API while preserving existing pilot
  exports.
- Tests prove importing and evaluating `pilot.assertions` succeeds while ROS imports are rejected.
- Tests include representative full delivery-progress snapshots that feed current assertions into the
  observation builder for later replay/run-logger features.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- Adding replay runner, run logger, LLM adapter, safety validator, ROS executor, hardware proof runs,
  or recipe-level loop control.
- Editing contracts schemas, ROS runtime code, or Brain firmware.
