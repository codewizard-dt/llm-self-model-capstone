# Slice: proof-docs-and-coverage

| Field | Value |
|---|---|
| Feature | pm4-one-skill-execution |
| Stack | pilot |
| Depends on | hardware-proof-transport |

## What this slice delivers

Finish the PM4 acceptance bar with supervised live-proof documentation, package exports, and
acceptance-level test/gate coverage. The docs should explain exactly what the `--human-supervised`
flag means for PM4: an operator is present for the proof, has prepared a safe workspace, and can
interrupt or estop if the bounded skill behaves unexpectedly; the human does not teleoperate the
skill.

## Files to create / change

```text
pilot/docs/pm4-one-skill-execution.md NEW - supervised PM4 proof runbook
pilot/src/pilot/__init__.py           CHANGE - final exports if needed
pilot/tests/                          CHANGE - acceptance-level coverage and regressions
```

## Requirements

- Document required ROS nodes/topics for `survey_scene` and any available ball-handling proof
  surfaces.
- Document setup, safe workspace expectations, command examples, expected JSONL trace events, expected
  terminal result behavior, and how to confirm the pilot stopped after exactly one skill.
- Explain the PM4 `--human-supervised` flag as a supervised proof gate, not teleoperation.
- Document unsupported ball-handling surfaces clearly if any approved proof skill cannot be dispatched
  safely with the current ROS runtime.
- Ensure exported APIs remain additive and import-safe on development machines without ROS.
- Run focused pilot tests and lint; run root validation if contract fixtures or schemas were touched.

## Acceptance

- PM4 runbook includes commands for `survey_scene`, `claw_open`, `claw_close`, `verify_grasp`, and
  `verify_drop`, or states the precise unsupported reason for any skill whose live surface is absent.
- Runbook includes expected command/result/stop JSONL record shapes and pass/fail criteria.
- Tests cover the feature-level acceptance cases from `requirements.md`.
- `make -C pilot test` and `make -C pilot lint` pass, or any unrelated pre-existing failure is clearly
  identified.
- Root `make validate` passes if this feature changes contract-facing artifacts.

## Out Of Scope

- Running the physical robot during automated tests, broad skill baseline capture, full delivery-task
  recipes, and changing the PM4-approved skill set.
