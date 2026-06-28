# Slice: models-and-schemas

| Field | Value |
|---|---|
| Feature | pilot-schemas |
| Stack | contracts |
| Depends on | - |

## What this slice delivers

The contract runtime models and exported JSON Schemas for the pilot loop boundary: skill commands,
compact observation snapshots, assertion results, LLM pilot decisions, and pilot trace records. This
slice is schema/API only; fixture files and validation dispatch are handled by the next slice.

## Files to create / change

```
contracts/
  src/contracts/
    pilot.py          NEW - pydantic v2 models for pilot schemas
    schema.py         CHANGE - add pilot schema export entries
    __init__.py       CHANGE - additive re-exports for public pilot contract models
  schemas/
    pilot_skill_command.json   NEW - generated schema
    pilot_observation.json     NEW - generated schema
    pilot_assertion.json       NEW - generated schema
    pilot_decision.json        NEW - generated schema
    pilot_trace_record.json    NEW - generated schema
  tests/
    test_pilot_schemas.py      NEW - model validation and bounds coverage
```

## Requirements

- Implement models in `contracts.pilot` using pydantic v2 and the strict-model style already used in
  `contracts`.
- Define `PilotSkillName` as a closed enum with the MVP skills: `stop`, `survey_scene`, `face_target`,
  `approach_target`, `center_object_in_gripper`, `arm_to_angle`, `claw_open`, `claw_close`,
  `verify_grasp`, `go_to_destination`, and `verify_drop`.
- Define typed bounded skill command variants rather than an untyped parameter dictionary.
- Define observation snapshots with task phase/objective, robot pose, localization confidence/age,
  visible objects/tags, manipulator state, bridge health, last command/result, recent failures, and
  current assertions.
- Define assertion results with state `true` / `false` / `unknown`, confidence, evidence entries,
  timestamps or age metadata, and optional recovery hints.
- Define pilot decisions with decisions limited to `continue`, `retry`, `stop_success`,
  `stop_failure`, and `request_human`.
- Define trace records as a discriminated union for observation, decision, command, result, assertion,
  and stop events.
- Keep ROS message classes and topic-specific types out of the contract layer.
- Add schema registry entries so `make schema` emits the five pilot schema JSON files.
- Re-export the public pilot models from `contracts` only additively.

## Acceptance

- `make schema` in `contracts/` emits non-empty JSON Schema files for the five pilot contracts.
- Unit tests cover valid instances for each schema family.
- Unit tests reject unknown skill names, unknown pilot decisions, malformed observation health fields,
  out-of-range command parameters, and invalid trace discriminators.
- Existing contract schemas and tests continue to pass.
- `make lint` and `make test` pass for `contracts/`.

## Out Of Scope

- Fixture JSONL files and validation dispatch.
- Pilot runtime behavior, ROS execution, replay mode, or hardware commands.
- Calibration baselines or task recipes.
