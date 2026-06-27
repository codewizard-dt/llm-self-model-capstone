# Pilot Online Task Loop Program Requirements

Status: approved
Source brief: `PILOT_MASTER_REQUIREMENTS.md`
Program slug: `pilot-online-task-loop`
Mode: create

## Goal

Build an online pilot loop that can complete the first physical VEX-V5 robot task without recompiling
controller code during the run: find a yellow ball at source location A, approach and grab it,
navigate to destination B, release it, and verify that the ball is at B. The program delivers a
bounded, replayable observe-judge-act harness over reusable skills, with deterministic validation,
hardware safety stops, structured assertions, and JSONL trace logging.

## Sub-Features

| ID | Source | Goal | Vertical | Depends On | MVP | Owner |
|---|---|---|---|---|---|---|
| `pilot-schemas` | P1 | Define skill command, observation, assertion, decision, and trace schemas. | `contracts` | - | yes | 215eight |
| `observation-builder` | P2 | Build compact snapshots from live ROS topic cache. | `pilot` | `pilot-schemas` | yes | 215eight |
| `skill-registry` | P3 | Define reusable skills with preconditions, parameter limits, and result mapping. | `pilot` | `pilot-schemas` | yes | 215eight |
| `llm-decision-adapter` | P4 | Provide structured prompt, JSON response parsing, and retry on invalid output. | `pilot` | `pilot-schemas`, `observation-builder`, `skill-registry` | yes | 215eight |
| `safety-validator` | P5 | Enforce stale-state checks, numeric clamps, max step/time limits, and stop policy. | `pilot` | `pilot-schemas`, `skill-registry` | yes | David |
| `ros-skill-executor` | P6 | Publish validated skills and wait for terminal feedback/result. | `pilot` | `skill-registry`, `safety-validator` | yes | David |
| `assertion-engine` | P7 | Compute fused task assertions for visibility, pose, grasp, carry, and drop. | `pilot` | `observation-builder` | yes | David |
| `run-logger` | P8 | Write JSONL traces for every loop iteration and command outcome. | `pilot` | `observation-builder`, `llm-decision-adapter`, `ros-skill-executor`, `assertion-engine` | yes | David |
| `replay-mode` | P9 | Run the loop against recorded snapshots/results without moving hardware. | `pilot` | `observation-builder`, `llm-decision-adapter`, `assertion-engine`, `run-logger` | yes | David |
| `skill-baseline-capture` | P10 | Capture supervised proof runs for each small skill. | `pilot`, `coprocessor` | `ros-skill-executor`, `assertion-engine`, `run-logger` | yes | David |
| `delivery-recipe` | P11 | Define the ball A to destination B task plan over reusable skills. | `pilot` | `skill-registry`, `assertion-engine`, `skill-baseline-capture` | yes | David |
| `supervised-hardware-run` | P12 | Run the full loop with human interrupt and hard stop policy. | `pilot`, `coprocessor`, `brain` | `safety-validator`, `ros-skill-executor`, `run-logger`, `delivery-recipe` | yes | David |
| `generalized-recipes` | P13 | Add non-ball tasks using the same skill registry. | `pilot` | `supervised-hardware-run` | stretch | David |

## Milestones

| ID | Mode | Owner | Validates | Depends On | Unblocks |
|---|---|---|---|---|---|
| `pm1-schemas-ready` | automated | 215eight | Pilot schema examples validate for observations, skills, decisions, assertions, and run traces. | `pilot-schemas` | `observation-builder`, `skill-registry` |
| `pm2-replay-loop` | automated | David | The pilot can run a full observe-decide-act trace in replay mode without ROS hardware and stop for success/failure. | `replay-mode` | none in source sequencing |
| `pm3-live-observation` | manual | 215eight | The pilot builds live snapshots from ROS topics without commanding motion. | `observation-builder` | none in source sequencing |
| `pm4-one-skill-execution` | manual | David | The pilot executes one validated skill, waits for terminal result, logs outcome, and stops safely. | `ros-skill-executor` | `skill-baseline-capture` |
| `pm5-skill-baselines` | manual | David | Search, face, approach, center, grasp, verify, navigate, release, and verify-drop have supervised proof runs and baseline memory. | `skill-baseline-capture` | `delivery-recipe` |
| `pm6-delivery-loop-replay` | automated | David | The full ball-delivery recipe succeeds in replay using recorded observations and mocked decisions. | `delivery-recipe` | `supervised-hardware-run` |
| `pm7-supervised-delivery-run` | manual | David | The full pilot loop attempts the physical delivery task with human interrupt, hard limits, and complete trace logging. | `supervised-hardware-run` | `generalized-recipes` |
| `pm8-expansion-proof` | automated | David | One new task recipe uses the same skill registry without changing the loop harness. | `generalized-recipes` | none; terminal program milestone |

## Sequencing

The master graph follows the source brief sequencing:

- `pilot-schemas` -> `pm1-schemas-ready`
- `pm1-schemas-ready` -> `observation-builder`
- `pm1-schemas-ready` -> `skill-registry`
- `observation-builder` -> `llm-decision-adapter`
- `skill-registry` -> `llm-decision-adapter`
- `skill-registry` -> `safety-validator`
- `safety-validator` -> `ros-skill-executor`
- `observation-builder` -> `assertion-engine`
- `llm-decision-adapter` -> `run-logger`
- `ros-skill-executor` -> `run-logger`
- `assertion-engine` -> `run-logger`
- `observation-builder` -> `pm3-live-observation`
- `llm-decision-adapter` -> `replay-mode`
- `assertion-engine` -> `replay-mode`
- `run-logger` -> `replay-mode`
- `replay-mode` -> `pm2-replay-loop`
- `ros-skill-executor` -> `pm4-one-skill-execution`
- `pm4-one-skill-execution` -> `skill-baseline-capture`
- `assertion-engine` -> `skill-baseline-capture`
- `run-logger` -> `skill-baseline-capture`
- `skill-baseline-capture` -> `pm5-skill-baselines`
- `pm5-skill-baselines` -> `delivery-recipe`
- `delivery-recipe` -> `pm6-delivery-loop-replay`
- `pm6-delivery-loop-replay` -> `supervised-hardware-run`
- `supervised-hardware-run` -> `pm7-supervised-delivery-run`
- `pm7-supervised-delivery-run` -> `generalized-recipes`
- `generalized-recipes` -> `pm8-expansion-proof`

## Shared Constraints

- The pilot may only execute commands that validate against a closed skill schema.
- Deterministic Python owns loop iteration, timing, validation, interrupts, and stop logic.
- The LLM may judge observations and select the next bounded skill, but it may not publish directly to
  robot topics, execute shell commands, edit source code, bypass validation, or emit raw unbounded
  motor motion.
- The LLM receives compact snapshots and recent outcomes, not raw unbounded logs.
- Every executable skill must define preconditions, parameters, postconditions, timeout, failure
  reasons, telemetry output, maximum duration, and maximum movement envelope.
- Task progress is judged by fused assertions from vision, localization, operator state, bridge
  health, and motor feedback.
- Hardware mode must stop on stale bridge ack, stale telemetry, estop, disabled motion, command
  rejection, bridge fault, or missing human supervision.
- Every loop run must have max iterations and max wall-clock runtime.
- Invalid LLM output must not reach the robot.
- Runs must be replayable from saved observations and results.
- The first physical task may use current operator actions, but pilot abstractions must remain
  skill-based so additional tasks can reuse the loop.
- High-level one-off task commands must not become the only action surface.
- Raw low-level drive/turn commands are allowed only behind short TTLs, strict clamps, and safety
  preconditions.
- Tooling remains `uv` for dependencies/environments and `ruff` for lint/format.

## Verification Targets

Program-level validation is expected to include:

```bash
uv sync
make test
make validate
```

Pilot-specific checks should cover:

- schema validation for example observations, decisions, skills, assertions, and run traces
- prompt adapter rejection of malformed LLM output
- safety validator rejection of stale telemetry and oversized motion
- replay loop termination on success, failure, and max-iteration stop
- executor mapping for each skill to the correct ROS command path
- assertion classification for grasp/drop examples from recorded fused evidence
- complete JSONL traces from the run logger

Hardware verification remains staged:

```bash
pilot observe --duration-s 30
pilot run --mode replay --trace fixtures/pilot_delivery_trace.jsonl
pilot skill --hardware --skill survey_scene --duration-s 3.0
pilot run --hardware --task deliver-yellow-ball --max-iterations 20
```

## Decisions

All decisions below were approved by the human before the master graph was emitted.

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| PPROG-001 | closed | Program slug is `pilot-online-task-loop`. | Matches the source brief title and avoids colliding with existing `.ai-sdd/programs/self-model-loop`. | Other slugs. |
| PPROG-002 | closed | Use source task names as feature slugs without the `P#` prefixes. | Keeps feature paths meaningful while preserving P1-P13 traceability in the requirements. | Feature IDs named only `P1` through `P13`. |
| PPROG-003 | closed | Owners are exactly those listed in the source brief: P1-P4 and pm1/pm3 to 215eight; P5-P13 and pm2/pm4-pm8 to David. | The brief now provides explicit ownership. | Reassigning ownership during graph generation. |
| PPROG-004 | closed | Milestone modes are exactly those listed in the source brief. | The source brief marks automated versus manual based on deterministic checks versus live hardware requirements. | Inferring modes from implementation convenience. |
| PPROG-005 | closed | Preserve source sequencing exactly, including `pm2-replay-loop` and `pm3-live-observation` as proof milestones with no downstream unblock edges. | The source Mermaid graph shows these as validation branches rather than blockers for later nodes. | Adding implicit downstream edges not shown in the brief. |
| PPROG-006 | closed | Deterministic harness owns the loop. | Safety, replayability, and testability require code-level control of iteration and stop conditions. | Free-running LLM terminal loop. |
| PPROG-007 | closed | Skills are the execution unit. | Skills can be calibrated, verified, logged, and recombined across tasks. | Task-specific script-only actions. |
| PPROG-008 | closed | LLM output is advisory until validated. | Prevents invalid or unsafe commands from reaching ROS or Brain. | Direct LLM publication to `/operator/command`. |
| PPROG-009 | closed | Assertions fuse camera and motor evidence. | Grasp, drop, and arrival cannot be proven from one source alone. | Trusting object detection or motor ack alone. |
| PPROG-010 | closed | Build skill baselines before full task attempts. | Smaller proofs reduce the search space before unreliable full delivery attempts. | Jumping directly to full delivery loops. |
| PPROG-011 | closed | Replay mode is first-class. | Debugging the pilot should not require moving hardware on every iteration. | Hardware-only development. |
| PPROG-012 | closed | Current operator actions may back MVP skills. | This reduces scope for the first task while preserving a reusable pilot abstraction. | Rewriting all controllers before proving the loop. |

## Open Questions And Proposed Resolutions

| ID | Status | Proposed Resolution |
|---|---|---|
| O1 | closed | `grasp_likely` requires at least two evidence classes: recent claw-close/arm result plus either object disappearance from the pre-grasp corridor, motor current/position evidence, or a post-lift carried-object estimate. The assertion may return `unknown` when evidence conflicts. |
| O2 | closed | Treat current yellow-ball localization as sufficient only after supervised `center_object_in_gripper` baseline runs; until then, the skill may be exposed in replay and hardware-supervised modes but should report explicit uncertainty and recovery hints. |
| O3 | closed | Use a tag-relative pose for first destination B, with fixed map pose as a fallback only when localization confidence is high. A physical bin/object target remains a later recipe extension. |
| O4 | closed | Start with a remote API or desktop-assisted LLM adapter behind the same interface, and keep local Pi model support as a later adapter if latency/connectivity require it. |
| O5 | closed | Do not expose raw `drive` / `turn` directly to the LLM for normal task selection. Allow them only as internal implementations of named bounded skills with short TTLs and strict safety preconditions. |
| O6 | closed | Require an explicit hardware CLI flag plus a live operator/joystick deadman or ROS supervision signal for hardware execution. Either signal missing stops the loop. |
| O7 | closed | Version skill memory by schema version, robot hardware/calibration fingerprint, skill name, and capture timestamp. New calibration after hardware changes creates a new memory revision rather than mutating old traces. |

## Approval Gate

Approved by the human in-session. `.ai-sdd/programs/pilot-online-task-loop/pipeline.yaml` may be emitted.
