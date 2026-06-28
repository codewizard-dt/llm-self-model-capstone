# Skill Registry Feature Requirements

Status: approved
Source brief: `PILOT_MASTER_REQUIREMENTS.md` (`P3 skill-registry`)
Program: `pilot-online-task-loop`
Feature slug: `skill-registry`
Owner: 215eight
Vertical: `pilot`

## Goal

Define the reusable pilot skill registry: a ROS-free catalog of bounded skill definitions that maps
the closed `contracts.PilotSkillName` vocabulary to preconditions, parameter limits, command paths,
expected result/ack sources, success assertions, failure reasons, and recovery hints. The registry is
the action surface the LLM decision adapter may choose from and the safety/executor features will later
validate and execute.

## In Scope

- Add a `pilot` skill registry module that exposes deterministic skill definitions for all MVP skills.
- Cover the closed skill vocabulary: `stop`, `survey_scene`, `face_target`, `approach_target`,
  `center_object_in_gripper`, `arm_to_angle`, `claw_open`, `claw_close`, `verify_grasp`,
  `go_to_destination`, and `verify_drop`.
- Define per-skill metadata: inputs/defaults, preconditions, maximum duration, maximum movement
  envelope, command path, expected result source, success assertion, failure reasons, and recovery
  hints.
- Reuse contract-owned skill command models and bounds; do not define schema-bearing duplicates in
  `pilot/`.
- Add tests proving all contract skill names have registry entries, definitions are deterministic and
  bounded, command paths/result sources are declared, and invalid lookup fails clearly.

## Out Of Scope

- Executing skills, publishing ROS commands, waiting for ROS action results, or mapping to concrete
  ROS messages.
- Safety validation policy, stale-state rejection, numeric clamping at runtime, or stop policy
  enforcement beyond static registry metadata.
- LLM prompt construction, decision parsing, retry logic, assertion computation, run logging, replay
  mode, recipes, baselines, or hardware runs.
- Adding new skills beyond the MVP contract vocabulary.
- Changing `contracts` schemas or generated fixtures.

## Acceptance

- `pilot` exposes a public registry API for listing and retrieving skill definitions.
- Every `contracts.PilotSkillName` enum value has exactly one registry definition.
- Each definition includes inputs/defaults, preconditions, max duration, max movement envelope, command
  path, expected result source, success assertion id/name, failure reasons, and recovery hints.
- Registry definitions reuse contract skill names and parameter bounds rather than duplicating schema
  definitions.
- Registry ordering is deterministic for prompt generation and tests.
- Unknown skill lookup raises a clear error.
- Tests cover registry completeness, bounded metadata, deterministic ordering, command path/result
  source declarations, and no ROS dependency.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Constraints

- No schema may be defined in `pilot/`; `contracts/` owns skill command schemas.
- The registry must be pure Python and ROS-free so it works in replay and prompt-generation tests.
- The LLM may only choose named bounded skills from this registry, not arbitrary motor packets.
- Registry values must remain compact and serializable enough for prompt construction.
- Tooling remains `uv` and `ruff`.

## Proposed Decisions

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| SR-001 | closed | Implement the registry as immutable dataclasses in `pilot.skills`, not pydantic models. | The registry is static metadata, not a new schema surface; contracts own schemas. | Defining registry schemas in `pilot/`. |
| SR-002 | closed | Use `contracts.PilotSkillName` as the registry key type and require exact enum coverage. | Keeps the executable action surface aligned with the closed contract vocabulary. | Free-form string keys or partial registry coverage. |
| SR-003 | closed | Store command paths as symbolic route names such as `operator.command`, `task_plan.request`, or `internal.assertion`, not ROS topic classes. | The executor will later map routes to concrete ROS paths; the registry must stay ROS-free. | Importing ROS message/topic types into the registry. |
| SR-004 | closed | Represent preconditions, failure reasons, and recovery hints as compact strings/lists for prompt and validator use. | This is enough for the LLM prompt and later validator without inventing a policy engine in this slice. | Implementing executable precondition predicates now. |
| SR-005 | closed | Keep runtime clamping/enforcement out of this feature; include static max duration/envelope metadata only. | Safety-validator owns enforcement and depends on this registry. | Performing safety validation inside the registry. |

## Open Questions

None for this feature draft. Program-level decisions already close that skills are the execution unit
and LLM output is advisory until validated.

## Approval Gate

Approved by the human in-session. `.ai-sdd/features/skill-registry/pipeline.yaml` and `slices/*.md`
files may be emitted.
