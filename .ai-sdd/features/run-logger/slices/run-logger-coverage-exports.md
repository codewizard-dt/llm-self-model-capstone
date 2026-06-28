# Slice: run-logger-coverage-exports

| Field | Value |
|---|---|
| Feature | run-logger |
| Stack | pilot |
| Depends on | `trace-readback-history` |

## What this slice delivers

Final public exports and acceptance-level coverage for the run logger. This slice closes integration
gaps with existing pilot components, proves trace records from observations, decisions, executor
results, and assertions round-trip through JSONL, and leaves the feature ready for replay mode, skill
baseline capture, and supervised hardware runs.

## Files to create / change

```
pilot/
  src/pilot/run_logger.py       CHANGE - final API polish if needed
  src/pilot/__init__.py         CHANGE - public exports if not completed earlier
  tests/test_run_logger.py      CHANGE - acceptance-level and integration coverage
```

## Requirements

- Ensure public exports are additive and do not disturb existing pilot imports.
- Prove logger append helpers work with representative `PilotObservation`, `PilotDecision`,
  `PilotSkillCommand`, `PilotSkillResult`, and `PilotAssertion` objects from existing pilot test
  builders or compact local fixtures.
- Prove stop records cover success, failure, operator interrupt, fault, and request-human reasons.
- Prove trace readback output can feed later replay-mode consumption without schema conversion.
- Prove recent-history output can feed `pilot.decision` as compact recent context without requiring
  ROS or a real LLM provider.
- Keep generated traces in temporary directories during tests and do not commit runtime JSONL output.
- Run and fix the feature's expected pilot-local and root verification gates.

## Acceptance

- Tests cover all requirements and acceptance bullets from `requirements.md`.
- Tests cover all trace event variants written and read back from JSONL.
- Tests prove `pilot.run_logger` exports are available from the intended package/module boundary.
- Tests prove no raw images, binary blobs, secrets, environment variables, or unbounded provider logs
  are added to trace records by the logger API.
- `make -C pilot test` passes.
- `make -C pilot lint` passes.
- Root `make test`, `make validate`, and `make lint` pass or any pre-existing unrelated failure is
  clearly identified.

## Out Of Scope

- Implementing replay-mode, skill-baseline capture, delivery recipe orchestration, supervised
  hardware loop control, ROS integrations, schema changes, or Brain firmware changes.
