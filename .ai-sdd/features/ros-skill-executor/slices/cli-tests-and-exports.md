# Slice: cli-tests-and-exports

| Field | Value |
|---|---|
| Feature | ros-skill-executor |
| Stack | pilot |
| Depends on | transport-results-timeouts |

## What this slice delivers

The user-facing one-skill command hook, final exports, and acceptance-level test coverage. This slice
adds the supervised hardware CLI wrapper for the pm4 proof path and closes any coverage or packaging
gaps left by the executor slices.

## Files to create / change

```
pilot/
  pyproject.toml              CHANGE - add console script if needed
  src/pilot/__init__.py        CHANGE - final public executor exports
  src/pilot/cli.py             NEW/CHANGE - one-skill hardware wrapper if no CLI exists
  src/pilot/executor.py        CHANGE - small fixes from final coverage only
  tests/test_executor.py       CHANGE - acceptance-level coverage
  tests/test_cli.py            NEW/CHANGE - CLI argument and validation/executor wiring tests
```

## Requirements

- Provide a supervised command shape equivalent to
  `pilot skill --hardware --skill survey_scene --duration-s 3.0`.
- Route the CLI through contract command construction, safety validation, and the executor; do not add
  a separate hardware execution path.
- Require hardware mode/supervision inputs through the same safety-validator path used by the executor.
- Ensure executor APIs are exported consistently without breaking existing pilot imports.
- Add final tests for all feature acceptance items and keep them ROS-free unless explicitly testing
  the optional ROS adapter boundary with stubs.
- Run and fix pilot-local and root gates expected by the feature requirements.

## Acceptance

- The CLI wrapper constructs a contract-valid skill command, invokes safety validation, and passes only
  accepted validation results to the executor.
- CLI tests cover survey skill arguments, hardware flag handling, validation refusal, and executor
  invocation through a fake transport.
- `make -C pilot test` passes.
- `make -C pilot lint` passes.
- Root `make test`, `make validate`, and `make lint` pass or any pre-existing unrelated failure is
  clearly identified.
- The feature meets all acceptance items in `requirements.md`.

## Out Of Scope

- Running the full pilot loop.
- Capturing skill baselines beyond enabling the one-skill manual proof.
- Changing closed contract schemas, registry vocabulary, ROS operator internals, or PROS firmware.
