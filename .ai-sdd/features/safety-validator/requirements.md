# Safety Validator Feature Requirements

Status: approved
Source brief: `PILOT_MASTER_REQUIREMENTS.md` (`P5 safety-validator`)
Program: `pilot-online-task-loop`
Feature slug: `safety-validator`
Owner: David
Vertical: `pilot`

## Goal

Build the deterministic pilot safety validator that receives a contract-valid
`contracts.PilotSkillCommand`, the current `contracts.PilotObservation`, and static metadata from the
pilot skill registry, then returns either a safe validated command for execution or a structured
rejection/stop decision. The validator must enforce stale-state checks, hardware-mode supervision,
bridge/estop/fault stops, per-skill duration and movement limits, registry precondition failures that
can be decided from the current observation, and safe stop policy before any command reaches the ROS
skill executor.

## In Scope

- Add a ROS-free `pilot` safety validation module that validates command intent against observation
  state and registry metadata.
- Reuse contract-owned `PilotSkillCommand`, `PilotObservation`, `PilotSkillResult`, `PilotFailure`,
  and related models; do not define schemas in `pilot/`.
- Enforce hard stop/reject policy for stale bridge heartbeat, stale localization where required by the
  skill, estop, disabled or missing hardware supervision in hardware mode, bridge fault, degraded
  command state, command rejection/fault results, and missing required target/destination evidence.
- Clamp or reject numeric parameters according to the stricter of the contract model bounds and the
  registry metadata: max duration, max drive speed, max turn rate, arm limits, claw force, and skill
  envelopes.
- Distinguish replay/dry-run validation from hardware validation so replay can run without a live
  supervision signal while still preserving freshness and contract checks appropriate to replay inputs.
- Return structured validation outcomes that downstream executor/logger code can inspect, including
  accepted command, normalized command, rejection reason, stop reason, and recovery hint.
- Add tests for valid commands, stale telemetry/bridge rejection, estop/fault stop, missing hardware
  supervision, oversized numeric envelopes, missing targets/destinations, stop command behavior,
  replay-mode behavior, and deterministic rejection reasons.

## Out Of Scope

- Publishing ROS messages, invoking ROS actions, waiting for executor feedback, or changing
  `robot/ros2-runtime/`.
- Changing PROS firmware, Brain clamps, or low-level command packet definitions.
- Redesigning pilot contract schemas or adding new skill names beyond the closed MVP vocabulary.
- Implementing the LLM decision adapter, prompt rendering, assertion engine, run logger, replay loop,
  delivery recipe, or skill baseline capture.
- Proving physical robot safety through hardware runs; this feature supplies deterministic software
  gates and tests only.
- Implementing a general rule engine for every registry precondition string. Only preconditions that
  can be decided from current contract fields and registry metadata are enforced here.

## Acceptance

- `pilot` exposes a public safety validator API for validating a `PilotSkillCommand` with a
  `PilotObservation`, mode, policy thresholds, and the skill registry.
- Valid commands that satisfy observation freshness, bridge health, supervision, registry, and numeric
  envelope rules are accepted and returned in a normalized/contract-valid form.
- Commands are rejected or converted to stop outcomes when bridge heartbeat is stale, estop is true,
  bridge state is `fault` or `stale`, recent command result indicates rejection/fault where relevant,
  hardware supervision is missing in hardware mode, or required telemetry/evidence is too old.
- Movement commands are rejected or clamped to per-skill safe envelopes without allowing values outside
  the contract-owned schema bounds.
- Target-dependent skills reject missing or stale target/destination evidence when the current
  observation cannot support the registry preconditions.
- `stop` remains valid under unsafe conditions and produces a policy-compliant stopped outcome rather
  than being blocked by the same health gates that block motion.
- Tests cover accepted replay/dry-run commands, accepted hardware-mode commands with supervision,
  stale bridge/telemetry rejection, estop/fault stop, missing supervision rejection, oversized
  duration/speed/turn/arm/claw parameters, missing target/destination evidence, unknown registry
  lookup failures, and stable reason strings.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Constraints

- `contracts/` remains the only schema-owning vertical; `pilot/` may define plain dataclasses or typed
  helper objects for validation results but not new pydantic schema surfaces.
- The validator must be deterministic, ROS-free, and usable in replay mode and unit tests.
- The LLM output remains advisory until parsed as contract models and accepted by this validator.
- Hardware mode must stop or reject on stale bridge ack, stale telemetry/freshness evidence, estop,
  disabled motion, command rejection, bridge fault, or missing human supervision.
- Raw low-level drive/turn requests remain available only as internal implementations of named skills
  with short TTLs, strict clamps, and safety preconditions.
- Tooling remains `uv` and `ruff`; do not introduce pip/poetry/black/isort/flake8.

## Proposed Decisions

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| SV-001 | closed | Implement the validator as a ROS-free `pilot.safety` module with immutable dataclass result/policy types. | The executor and logger need inspectable outcomes, but schemas remain owned by `contracts/`. | Adding pydantic safety result schemas in `pilot/`. |
| SV-002 | closed | Validate in two explicit modes: `replay` and `hardware`. | Replay must work without live robot supervision, while hardware mode must enforce the human-supervision gate. | One global policy that either blocks replay or weakens hardware safety. |
| SV-003 | closed | Prefer rejection over silent clamping when LLM-provided numeric values exceed hard safety envelopes; use normalization only for omitted defaults and already contract-valid values. | Silent clamping can hide unsafe LLM intent and make run logs misleading. | Automatically reducing every oversized value and executing anyway. |
| SV-004 | closed | Treat `stop` as always admissible enough to request a halt, even when bridge state is stale/faulted; report the unsafe condition in the validation outcome. | Blocking stop during unsafe states creates the wrong failure mode. | Applying the same motion gates to stop commands. |
| SV-005 | closed | Enforce only concrete preconditions derivable from current contracts in this feature, and leave semantic/fused task assertions to `assertion-engine`. | The skill registry stores compact text metadata; a full policy language would exceed P5 scope. | Building a generic executable precondition engine now. |
| SV-006 | closed | Use stable machine-readable reason codes plus short human-readable messages for validation failures. | Later executor, run logger, and replay tests need deterministic behavior and readable traces. | Free-form exception text as the primary API. |
| SV-007 | closed | Keep contract model validation as the first gate, then apply registry and safety policy checks. | Invalid or unknown LLM output should fail before safety policy reasons are considered. | Attempting to repair malformed commands inside the safety validator. |

## Open Questions

None for this feature draft. Program-level safety and supervision questions are already closed in
`.ai-sdd/programs/pilot-online-task-loop/requirements.md`.

## Approval Gate

Approved by the human in-session. `.ai-sdd/features/safety-validator/pipeline.yaml` and
`slices/*.md` files may be emitted.
