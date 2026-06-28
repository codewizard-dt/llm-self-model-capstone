# ROS Skill Executor Feature Requirements

Status: approved
Source brief: `PILOT_MASTER_REQUIREMENTS.md` (`P6 ros-skill-executor`)
Program: `pilot-online-task-loop`
Feature slug: `ros-skill-executor`
Owner: David
Vertical: `pilot`

## Goal

Build the pilot-side ROS skill executor that receives an accepted `pilot.safety.ValidationResult`,
maps the validated `contracts.PilotSkillCommand` through the skill registry to the existing ROS
operator command surface, publishes exactly one bounded skill request, waits for terminal feedback or
result, and returns a deterministic contract-compatible skill result for the loop, logger, replay, and
manual one-skill hardware proof.

The executor is the bridge between deterministic pilot validation and the live robot command surface.
It must not accept raw LLM output, bypass safety validation, redefine schemas, or become a second ROS
operator stack.

## In Scope

- Add a `pilot` executor module with a public API that executes only accepted safety validation
  results.
- Map every MVP `contracts.PilotSkillName` to a concrete executor behavior:
  `stop`, `survey_scene`, `face_target`, `approach_target`, `center_object_in_gripper`,
  `arm_to_angle`, `claw_open`, `claw_close`, `verify_grasp`, `go_to_destination`, and `verify_drop`.
- Publish movement and manipulator skills to the existing ROS operator command path using compact JSON
  payloads compatible with `robot/ros2-runtime` operator commands.
- Wait for matching terminal operator feedback/result with timeout handling based on the validated
  command parameters and registry max duration.
- Return a deterministic execution result that preserves command id, skill name, status, reason code,
  human-readable message, timing, and any raw ROS payload needed for diagnostics.
- Treat assertion-only skills such as `verify_grasp` and `verify_drop` as non-motion executor
  outcomes based on the current observation/assertion evidence until the dedicated assertion-engine
  feature owns richer fused judgments.
- Provide a ROS-free transport abstraction or fake transport so executor mapping, timeout, rejection,
  and result parsing tests run on a dev machine without ROS installed.
- Add a small supervised CLI entry point or command hook for the documented one-skill proof shape:
  `pilot skill --hardware --skill survey_scene --duration-s 3.0`.
- Add tests for accepted execution, rejected validation refusal, per-skill command mapping, timeout,
  terminal result parsing, stop behavior, assertion-only behavior, and ROS-free importability.

## Out Of Scope

- Safety validation, stale-state policy, hardware supervision policy, numeric clamping, or registry
  precondition enforcement beyond refusing non-accepted validation results.
- Defining or changing pydantic schemas in `pilot/`; `contracts/` remains the schema owner.
- Changing the closed MVP skill vocabulary or adding new skills beyond `contracts.PilotSkillName`.
- Rewriting `robot/ros2-runtime` operator nodes, PROS firmware, bridge packet formats, or low-level
  motor controllers.
- Implementing the full pilot loop, LLM decision adapter, observation builder, assertion engine, run
  logger, replay runner, delivery recipe, or skill baseline capture.
- Proving physical success for every skill. This feature must make one supervised skill execution
  possible; broad calibration belongs to `skill-baseline-capture`.

## Acceptance

- `pilot` exposes a public executor API that accepts a `ValidationResult` and refuses any result whose
  status is not `accepted`.
- Every MVP skill has an explicit executor mapping or explicit non-motion assertion-only behavior, and
  tests prove there are no unmapped contract skill names.
- Movement/manipulator skills publish to the approved operator command surface instead of publishing
  raw motor commands directly from LLM output.
- The executor waits for a matching terminal result/feedback and returns `ok`, `rejected`, `failed`, or
  `stale`/timeout status deterministically.
- Timeouts use the smaller applicable bound from the validated command parameters and registry
  metadata, with a small transport grace period where needed.
- `stop` publishes a stop/halt request when transport is available and returns a stopped result even
  when the preceding command failed or timed out.
- Assertion-only skills do not command motion and return deterministic results from supplied
  observation/assertion evidence.
- Executor tests run without ROS by using a fake transport; ROS imports are isolated to the hardware
  adapter path.
- Tests cover all skill mappings, successful terminal result parsing, command rejection, timeout,
  validation-refusal, stop behavior, assertion-only behavior, and JSON payload shape.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Constraints

- The executor may only execute commands that have already passed contract and safety validation.
- `contracts/` remains the only schema-owning vertical; `pilot/` may define plain dataclasses or typed
  helper objects for executor internals, but not new pydantic schema surfaces.
- Hardware execution requires the already-approved hardware CLI flag plus live supervision signal from
  the safety-validator path.
- The LLM may never publish to ROS directly; all ROS publication must flow through deterministic pilot
  validation and this executor.
- The implementation must reuse existing `pilot.skills` registry metadata and symbolic command paths
  rather than duplicating a separate skill routing table where possible.
- ROS dependencies must be optional for unit tests and replay-friendly imports.
- Tooling remains `uv` and `ruff`; do not introduce pip, poetry, black, isort, or flake8.

## Proposed Decisions

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| RSE-001 | closed | Implement the executor as `pilot.executor` with a ROS-free core plus a narrow ROS transport adapter. | Unit tests, replay, and mapping validation must run without ROS, while hardware mode still needs ROS publication. | Importing `rclpy` at module import time or making the executor hardware-only. |
| RSE-002 | closed | Accept only `pilot.safety.ValidationResult` objects with `status == accepted`, and derive the command from `ValidationResult.command`. | Keeps the executor behind the approved contract and safety gates. | Letting the executor parse raw LLM output or re-run partial validation itself. |
| RSE-003 | closed | Return a pilot-local immutable execution result type that mirrors `contracts.CommandStatus` and preserves command id, skill, reasons, timings, and raw transport payloads. | The run logger and replay features need inspectable deterministic outcomes, but `pilot/` should not define new schemas. | Adding a new pydantic result schema in `pilot/` or returning unstructured ROS payloads only. |
| RSE-004 | closed | Map skill commands to the existing `/operator/command` JSON surface first; use `/task_plan/request` only if a registered skill explicitly requires a task-plan route. | The source brief allows current operator actions to back MVP skills, and existing operator tests cover `/operator/command` and `/operator/results`. | Building a parallel operator node or publishing raw Brain command packets from the pilot. |
| RSE-005 | closed | Treat `verify_grasp` and `verify_drop` as observation/assertion-only executor paths for this feature. | These skills should not move hardware, and the dedicated assertion engine will later own fused confidence logic. | Publishing no-op ROS commands for verification or implementing the full assertion engine inside the executor. |
| RSE-006 | closed | Correlate terminal results by command id when available, falling back to ordered result matching for current operator payloads that lack pilot command ids. | Current ROS operator payloads may not yet carry pilot command ids; deterministic tests can still prove matching behavior and preserve a path to stronger correlation. | Assuming all existing operator results already include pilot command ids. |
| RSE-007 | closed | Use registry `max_duration_ms` and command timeout parameters as execution deadlines; classify missing terminal feedback as `stale`/timeout, not success. | The pilot loop must not hang or infer success without terminal evidence. | Waiting indefinitely or treating publish success as skill success. |
| RSE-008 | closed | Provide the one-skill hardware CLI as a thin wrapper around validation plus executor, not a separate command path. | The manual pm4 proof should exercise the same code path as the later pilot loop. | A separate hardware test script that bypasses validation or executor APIs. |

## Open Questions

None for this feature draft. Program-level open questions for raw drive/turn exposure, supervision,
and current operator action reuse were already closed in
`.ai-sdd/programs/pilot-online-task-loop/requirements.md`.

## Approval Gate

Approved by the human in-session. `.ai-sdd/features/ros-skill-executor/pipeline.yaml` and
`slices/*.md` files may be emitted.
