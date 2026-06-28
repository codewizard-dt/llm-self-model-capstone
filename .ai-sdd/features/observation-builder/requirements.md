# Observation Builder Feature Requirements

Status: approved
Source brief: `PILOT_MASTER_REQUIREMENTS.md` (`P2 observation-builder`)
Program: `pilot-online-task-loop`
Feature slug: `observation-builder`
Owner: 215eight
Vertical: `pilot`

## Goal

Build the pilot-loop observation builder: a Python component that turns the current live or replayed
robot state cache into a compact `contracts.PilotObservation` snapshot for the LLM decision adapter,
assertion engine, replay mode, and run logger. The snapshot must summarize task phase/objective,
robot pose, localization confidence and age, visible objects/tags, manipulator state, bridge health,
last command/result, recent failures, and current assertions without exposing ROS message classes or
raw unbounded logs.

## In Scope

- Create the initial `pilot/` Python vertical scaffold if it does not already exist.
- Add an observation-builder module that consumes normalized topic/cache records and emits
  `contracts.PilotObservation`.
- Define a small in-process cache/input shape for replayable state sources, including scene/object
  evidence, tags, robot pose, manipulator state, bridge health, last command/result, recent failures,
  and current assertions.
- Provide deterministic fixture or test builders for live-like and replay-like inputs.
- Add unit tests for complete snapshots, stale/missing evidence handling, object/tag truncation or
  ordering, last-command/result propagation, assertion propagation, and schema validation.
- Keep the output contract-owned by `contracts`; `pilot/` imports schemas and does not define new
  schemas.

## Out Of Scope

- ROS subscription nodes, live topic wiring, or direct dependence on ROS message classes.
- LLM prompt construction, LLM invocation, decision parsing, retry logic, or model selection.
- Skill registry, safety validation, skill execution, assertions computation, run logging, or replay
  loop orchestration beyond replayable observation-builder inputs.
- Robot firmware, ROS operator commands, or hardware motion.
- Redesigning pilot contract schemas created by `pilot-schemas`.

## Acceptance

- A `pilot` Python package exists with uv/ruff-compatible project files or Makefile wiring consistent
  with this repo's vertical pattern.
- The observation builder emits `contracts.PilotObservation` instances from normalized input/cache
  records.
- The builder output validates through the committed `PilotObservation` contract schema.
- Tests cover a complete snapshot with task objective, phase, robot pose, localization confidence/age,
  visible objects, visible tags, manipulator state, bridge health, last command, last result, recent
  failures, and current assertions.
- Tests cover missing or stale optional evidence without crashing, using explicit unknown/empty fields
  rather than fabricated confidence.
- Tests cover deterministic object/tag ordering and bounded list lengths so snapshots remain compact.
- Tests prove no ROS message classes are required to construct an observation.
- Existing repo gates remain green: `make test`, `make validate`, and `make lint`.

## Constraints

- No schema may be defined in `pilot/`; use `contracts.PilotObservation` and related contract models.
- Observation snapshots must be compact and deterministic for repeatable LLM prompts and replay.
- The builder must support both live-cache inputs and replayed input records.
- The LLM receives summarized state only, not raw unbounded logs.
- Hardware safety fields must preserve bridge ack freshness, telemetry freshness where available,
  estop, motion-enabled state, command rejection/fault state, and stale data indicators.
- Tooling remains `uv` and `ruff`; do not introduce pip/poetry/black/isort/flake8.

## Proposed Decisions

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| OB-001 | closed | Initialize the `pilot/` vertical as a small Python package in this feature if it is absent. | The program graph schedules `observation-builder` under the `pilot` stack, but the package does not exist yet. | Waiting for a separate scaffold-only feature, which would block the current run. |
| OB-002 | closed | Keep observation-builder inputs ROS-free by defining normalized cache dataclasses or pydantic models inside `pilot`, then mapping them to `contracts.PilotObservation`. | The pilot brief requires replay mode and non-ROS tests; ROS topic wiring belongs later. | Accepting ROS message objects directly in the builder API. |
| OB-003 | closed | Reuse `contracts.PilotObservation`, `PilotAssertion`, `PilotSkillCommand`, and `PilotSkillResult` for outputs and embedded fields. | `contracts/` owns all schemas and `pilot/` must import rather than redefine them. | Mirroring or subclassing contract schemas in `pilot/`. |
| OB-004 | closed | Make snapshot compaction deterministic by sorting evidence by confidence/age/id and applying contract list bounds. | LLM prompts and replay traces need stable, bounded snapshots. | Preserving source arrival order when it can vary across ROS/replay sources. |
| OB-005 | closed | Represent stale or missing inputs explicitly with `None`, empty lists, low confidence, or existing bridge/localization state fields rather than inventing inferred facts. | The LLM and downstream assertions must see uncertainty instead of fabricated state. | Filling missing data with optimistic defaults. |

## Open Questions

None for this feature draft. The program-level observation-builder dependency and constraints are
closed in `.ai-sdd/programs/pilot-online-task-loop/requirements.md`.

## Approval Gate

Approved by the human in-session. `.ai-sdd/features/observation-builder/pipeline.yaml` and
`slices/*.md` files may be emitted.
