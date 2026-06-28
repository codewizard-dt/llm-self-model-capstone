# Pilot Schemas Feature Requirements

Status: approved
Source brief: `PILOT_MASTER_REQUIREMENTS.md` (`P1 pilot-schemas`)
Program: `pilot-online-task-loop`
Feature slug: `pilot-schemas`
Owner: 215eight
Vertical: `contracts`

## Goal

Define the contract-owned schemas required by the online pilot loop: skill command, observation
snapshot, assertion result, LLM pilot decision, and pilot run trace. These schemas are the boundary
between the deterministic pilot harness, the LLM decision adapter, replay mode, run logging, and the
robot execution path.

## In Scope

- Add pydantic v2 runtime models under `contracts/src/contracts/` for pilot-facing schema types.
- Export canonical JSON Schema files under `contracts/schemas/` for each pilot contract.
- Add canonical fixtures under `contracts/fixtures/` that exercise valid observations, skills,
  decisions, assertions, and trace records.
- Add validation coverage proving the fixtures validate against the exported schemas.
- Expose the new pilot contract models through the `contracts` package without defining schemas in
  `pilot/` or robot runtime packages.
- Keep the schema vocabulary closed enough for the MVP pilot loop while preserving explicit extension
  points for later task recipes.

## Out Of Scope

- Implementing the pilot loop harness, observation builder, skill registry, safety validator, executor,
  assertion engine, replay runner, or run logger behavior.
- Publishing to ROS topics or changing `robot/ros2-runtime/` command execution.
- Changing PROS firmware or low-level Brain packet handling.
- Adding arbitrary raw motor command access for the LLM.
- Calibrating skill baselines or proving hardware task success.

## Acceptance

- `contracts` contains pydantic models for pilot skill commands, compact observations, assertion
  results, pilot decisions, and pilot trace records.
- Each model exports a JSON Schema file under `contracts/schemas/`.
- Fixtures exist for at least one valid observation snapshot, skill command, pilot decision, assertion
  result, and trace record.
- Fixture validation is covered by tests and by the repo validation path.
- The pilot decision schema accepts only bounded decisions: `continue`, `retry`, `stop_success`,
  `stop_failure`, and `request_human`.
- Skill command schemas encode the MVP skill vocabulary and per-skill parameter envelopes needed by
  the program brief.
- Observation and trace schemas include bridge freshness, telemetry freshness, estop/motion state, last
  command/result, current assertions, and enough identifiers for replay.
- Invalid examples for unknown decisions, unknown skill names, oversized numeric envelopes, stale
  hardware state where represented, and malformed trace records are rejected by tests.
- The implementation uses `uv` and `ruff` conventions already established for `contracts`.

## Constraints

- `contracts/` is the only vertical allowed to define schemas.
- Models use Python 3.12 and pydantic v2.
- JSONL trace records must remain append-friendly and replayable.
- The LLM output remains advisory until parsed and validated as a `PilotDecision`.
- The schema set must support replay mode without ROS hardware.
- Hardware safety fields must be explicit enough for downstream validation to stop on stale bridge ack,
  stale telemetry, estop, disabled motion, command rejection, or bridge fault.
- Do not introduce non-`uv` dependency management or non-`ruff` formatting/linting tools.

## Proposed Decisions

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| PS-001 | closed | Put all pilot schema runtime models in a dedicated `contracts.pilot` module and export them from `contracts.__init__` only where consistent with existing package style. | Keeps the pilot boundary discoverable without mixing online-pilot contracts into offline self-model modules. | Defining schema models inside `pilot/`. |
| PS-002 | closed | Model `PilotSkillName` as a closed enum for MVP skills: `stop`, `survey_scene`, `face_target`, `approach_target`, `center_object_in_gripper`, `arm_to_angle`, `claw_open`, `claw_close`, `verify_grasp`, `go_to_destination`, and `verify_drop`. | The program requires reusable bounded skills and forbids arbitrary LLM motor packets. | Free-form skill names in LLM output. |
| PS-003 | closed | Represent skill parameters as typed bounded fields per command family, not an untyped dictionary. | Bounds must be machine-checkable before a command can reach the robot. | Generic JSON blobs with validator-only semantics. |
| PS-004 | closed | Represent assertion states as `true`, `false`, or `unknown` with confidence, evidence list, and timestamp/age metadata. | The pilot brief explicitly allows uncertainty when fused evidence conflicts. | Boolean-only assertions. |
| PS-005 | closed | Make `PilotTraceRecord` a discriminated union for observation, decision, command, result, assertion, and stop records. | JSONL logging needs appendable typed events without requiring one oversized record per loop. | A single loosely typed log object. |
| PS-006 | closed | Keep ROS-specific topic names and message classes out of the schema; use source identifiers, ages, and normalized evidence fields instead. | Replay and non-ROS tests should validate the same contracts as live mode. | Binding contract schemas directly to ROS message names. |

## Open Questions

None for this feature draft. The program-level open questions are already closed in
`.ai-sdd/programs/pilot-online-task-loop/requirements.md`; this feature carries those decisions forward.

## Approval Gate

Approved by the human in-session. `.ai-sdd/features/pilot-schemas/pipeline.yaml` and `slices/*.md`
may be emitted.
