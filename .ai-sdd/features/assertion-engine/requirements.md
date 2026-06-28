# Assertion Engine Feature Requirements

Status: approved
Source brief: `PILOT_MASTER_REQUIREMENTS.md` (`P7 assertion-engine`)
Program: `pilot-online-task-loop`
Feature slug: `assertion-engine`
Owner: David
Vertical: `pilot`
Depends on: `observation-builder`

## Goal

Build the pilot assertion engine: a deterministic, ROS-free Python component that evaluates compact
`contracts.PilotObservation` snapshots plus recipe/task context into contract-valid
`contracts.PilotAssertion` results for task progress. The engine must compute the first delivery task's
required assertions for target visibility, pose reliability, reachability, centering, grasp, carry,
arrival, drop, and final object-at-destination state using fused observation evidence and explicit
uncertainty rather than a single trusted sensor.

## In Scope

- Add a `pilot` assertion module that consumes `contracts.PilotObservation` and a small pilot-local
  task/assertion context, then returns deterministic `contracts.PilotAssertion` records.
- Cover the required delivery-task assertion ids from `PILOT_MASTER_REQUIREMENTS.md`:
  `target_ball_visible`, `robot_pose_reliable`, `ball_reachable`, `ball_centered_for_grasp`,
  `grasp_likely`, `carrying_ball`, `at_destination`, `drop_likely`, and `ball_at_destination`.
- Fuse available evidence from the existing observation contract: visible objects, visible tags,
  robot pose, localization confidence/age, manipulator state, last skill result, bridge health, task
  phase, recent failures, and current objective/context.
- Represent assertion outcomes as `true`, `false`, or `unknown` with bounded confidence, evidence
  entries, observed time or age metadata, and recovery hints when the next likely recovery step is
  clear.
- Keep destination and target selection in pilot-local context data, such as target label/id,
  destination tag/id/pose, reachability thresholds, image-center tolerances, localization age limits,
  and confidence thresholds.
- Add deterministic tests and fixtures for visible/missing target ball, reliable/stale pose, reachable
  and centered ball, likely/unknown/failed grasp, carrying state, arrival at destination, drop
  likelihood, and final ball-at-destination classification.
- Add focused test coverage proving the engine outputs contract-valid assertions and preserves stable
  ordering for downstream observations, replay mode, run logging, and LLM prompts.

## Out Of Scope

- Defining or changing contract schemas; all durable assertion shapes remain owned by `contracts/`.
- ROS subscription nodes, live topic wiring, camera/object tracker implementation, AprilTag mapping,
  motor-current drivers, or concrete provider adapters.
- LLM prompting, LLM judging, prompt construction, decision parsing, or retry orchestration.
- Safety-validator stop policy, command clamping, skill execution, ROS publishing, ack waiting, or
  hardware motion.
- Run logger, replay loop, skill baseline capture, delivery recipe orchestration, or full hardware
  proof runs.
- Training or adding a perception model for ball detection, grasp detection, or drop detection.

## Acceptance

- `pilot` exposes a public assertion-engine API that is pure Python, ROS-free, deterministic, and
  importable without ROS packages installed.
- The engine returns exactly one `contracts.PilotAssertion` for each required MVP assertion id in a
  stable order.
- Every returned assertion validates through `contracts.PilotAssertion` and carries at least one
  evidence entry explaining the sources used or missing.
- `target_ball_visible` becomes `true` only when a matching visible object satisfies configured label/id
  and confidence thresholds; it becomes `false` when observation evidence is fresh enough and no target
  is visible; it becomes `unknown` when object evidence is insufficient or unsafe to trust.
- `robot_pose_reliable` reflects localization pose presence, confidence threshold, localization age,
  bridge health, and fault/stale state without fabricating pose certainty.
- `ball_reachable` and `ball_centered_for_grasp` use configured reachability and image-center/grasp
  corridor thresholds when object pose or bbox evidence exists, and return `unknown` when required
  evidence is absent.
- `grasp_likely` and `carrying_ball` require fused manipulator/command-result/object evidence; a
  claw-close or verify-grasp success alone is not enough when object evidence conflicts.
- `at_destination`, `drop_likely`, and `ball_at_destination` use configured destination context,
  localization/tag evidence, manipulator state, last result, and visible object evidence; ambiguous or
  conflicting evidence produces `unknown` with a recovery hint.
- Tests cover true, false, and unknown outcomes for the high-risk grasp/drop assertions, including
  conflicting evidence cases.
- Tests prove assertion ordering, confidence bounds, evidence metadata, recovery hints, and contract
  validation are deterministic.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Constraints

- No schema may be defined in `pilot/`; output must use `contracts.PilotAssertion` and
  `contracts.AssertionEvidence`.
- Assertion logic must be deterministic and replay-friendly; no wall-clock reads inside core
  evaluation unless the caller supplies the timestamp.
- The engine must return uncertainty explicitly instead of optimistic defaults when evidence is stale,
  absent, or contradictory.
- The LLM may explain or label ambiguous outcomes later, but deterministic assertions decide what the
  pilot can treat as progress.
- Hardware safety remains owned by the safety validator and Brain boundary; the assertion engine may
  report bridge/fault evidence but must not execute stops or commands.
- Tooling remains `uv` and `ruff`; do not introduce pip/poetry/black/isort/flake8 workflow drift.

## Proposed Decisions

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| AE-001 | closed | Implement the assertion engine in `pilot/src/pilot/assertions.py` with focused tests in `pilot/tests/test_assertions.py`. | The feature belongs to the `pilot` vertical and should remain independent of ROS wiring, run logging, and replay orchestration. | Adding assertion computation to `pilot.observation`, `pilot.skills`, or a ROS package. |
| AE-002 | closed | Use `contracts.PilotObservation` as the primary input and `contracts.PilotAssertion` as the only output schema. | `contracts/` owns schemas; existing observation-builder output is the dependency for this feature. | Defining pilot-local pydantic assertion schemas or changing contract models. |
| AE-003 | closed | Add a pilot-local immutable `AssertionContext` or equivalent plain-data context for target/destination selectors and thresholds. | The current observation contract intentionally does not encode recipe-specific destination or grasp-corridor configuration. | Hard-coding the yellow-ball task into assertion functions or adding recipe fields to contracts in this feature. |
| AE-004 | closed | Emit the nine required MVP assertion ids exactly as named in the source brief. | Downstream run logging, replay mode, skill baselines, and the delivery recipe need stable assertion ids. | Using only skill-registry assertion ids such as `assert.object_held` or adding aliases. |
| AE-005 | closed | Return `unknown` when required evidence is missing, stale, unsafe, or contradictory, and attach a recovery hint when a bounded next skill is apparent. | The pilot brief explicitly requires fused assertions and uncertainty; false confidence would hide calibration and perception failures. | Treating missing data as success/failure by default. |
| AE-006 | closed | Require at least two evidence classes for `grasp_likely` and `carrying_ball`: manipulator/skill-result evidence plus either vision/object state or held-object state. | Program decision O1 says grasp cannot be trusted from one sensor or ack alone. | Trusting claw-close, verify-grasp, object disappearance, or motor/manipulator evidence alone. |
| AE-007 | closed | Keep assertion scoring as transparent heuristics with named thresholds, not a learned classifier. | The MVP needs deterministic replayable behavior and unit-testable confidence decisions before hardware baselines exist. | Training an ML classifier or asking the LLM to decide deterministic progress. |
| AE-008 | closed | Do not perform command execution, safety stops, or LLM escalation inside the assertion engine. | Safety-validator, executor, LLM adapter, run logger, and replay mode are separate features in the program graph. | Mixing assertion computation with loop control or hardware side effects. |
| AE-009 | closed | Use root `make sync` rather than literal root `uv sync` as the maintained dependency-sync gate for implementation slices. | This repo has per-vertical uv projects and no root `pyproject.toml`; existing accepted pilot slices use `make sync` to delegate `uv sync` into each vertical. | Requiring root `uv sync`, which currently exits non-zero because no root project exists. |

## Open Questions

None for this draft. The program-level open questions relevant to grasp evidence, destination choice,
raw drive/turn exposure, LLM runtime, human supervision, and skill-memory versioning are already closed
in `.ai-sdd/programs/pilot-online-task-loop/requirements.md`.

## Approval Gate

Approved by the human in-session. `.ai-sdd/features/assertion-engine/pipeline.yaml` and
`slices/*.md` files may be emitted.
