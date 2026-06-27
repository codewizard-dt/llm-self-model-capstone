# Slice: validator-tests-and-exports

| Field | Value |
|---|---|
| Feature | safety-validator |
| Stack | pilot |
| Depends on | skill-safety-rules |

## What this slice delivers

The final coverage, package exports, and validation polish for the safety-validator feature. This
slice broadens the tests to the feature acceptance bar, ensures the public API is exported
consistently with the pilot package, and keeps root/pilot gates green.

## Files to create / change

```
pilot/
  src/pilot/__init__.py        CHANGE - final public exports if not already complete
  src/pilot/safety.py          CHANGE - small fixes from coverage/gate failures only
  tests/test_safety.py         CHANGE - acceptance-level coverage and edge cases
```

## Requirements

- Cover valid replay/dry-run commands and valid hardware-mode commands with supervision.
- Cover stale bridge/telemetry rejection, estop/fault stop, missing supervision rejection, oversized
  duration/speed/turn/arm/claw parameters, missing target/destination evidence, unknown registry
  lookup failures, and stable reason strings.
- Ensure safety-validator exports are discoverable from the `pilot` package without adding schemas.
- Keep tests deterministic and ROS-free.
- Run and fix pilot-local and root validation commands expected by the feature requirements.

## Acceptance

- `make -C pilot test` passes.
- `make -C pilot lint` passes.
- Root `make test`, `make validate`, and `make lint` pass or any pre-existing unrelated failure is
  clearly identified.
- The final API exports are additive and do not break observation builder or skill registry imports.
- The feature meets all acceptance items in `requirements.md`.

## Out Of Scope

- Adding executor, LLM adapter, assertion engine, run logger, replay runner, recipes, or hardware proof
  behavior.
