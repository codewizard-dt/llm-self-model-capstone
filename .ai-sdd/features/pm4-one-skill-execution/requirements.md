# PM4 One Skill Execution Feature Requirements

Status: approved
Source brief: `PILOT_MASTER_REQUIREMENTS.md` (`pm4` one-skill-execution milestone)
Program: `pilot-online-task-loop`
Feature slug: `pm4-one-skill-execution`
Owner: David
Verticals: `pilot`, `coprocessor`

## Goal

Prove the pilot can execute exactly one contract-valid, safety-validated skill against the live robot
under human supervision, wait for one terminal result, log the command outcome as pilot trace records,
and stop safely. The PM4 proof is the first motion-producing and manipulator-facing pilot milestone:
it bridges the existing pilot skill registry and safety validator to the current ROS command surface
for a small approved skill set without introducing a full observe-decide-act loop or calibrated skill
baseline workflow.

## In Scope

- Add a bounded one-skill execution path in `pilot` that accepts a `contracts.PilotSkillCommand`,
  validates it with `pilot.safety.validate_skill_command` in hardware mode, dispatches it once, waits
  for a terminal result, records the outcome, and exits.
- Support this approved PM4 hardware proof skill set: `survey_scene`, `claw_open`, `claw_close`,
  `verify_grasp`, and `verify_drop`.
- Keep `survey_scene` as the canonical base-motion proof because `PILOT_MASTER_REQUIREMENTS.md` names
  `pilot skill --hardware --skill survey_scene --duration-s 3.0` as the staged one-skill verification
  command and the ROS runtime already exposes `/survey/goal`, `/survey/result`, and `/survey/cancel`.
- Add ball-handling proof support for `claw_open`, `claw_close`, `verify_grasp`, and `verify_drop` so
  PM4 can also exercise the supervised grab/drop boundary before baseline capture.
- Implement the executor behind a small testable abstraction so unit tests can exercise dispatch,
  result waiting, timeout, cancellation, validation failure, and trace writing without importing
  `rclpy`.
- Add a hardware CLI path, exposed through the existing `pilot` console command or an equivalent
  subcommand, that can run one supervised skill with explicit objective, skill parameters, output
  trace path, timeout, and human-supervision flag.
- Convert the terminal `/survey/result` payload into a contract-valid `contracts.PilotSkillResult`
  with the original `command_id`, skill name, status, completion time when known, message, and fault.
- Write a JSONL proof trace containing at least command, result, and stop records using
  `contracts.PilotTraceRecord`; include validation rejection and timeout/interrupt stop records when
  the skill is not executed or does not finish.
- Send the matching cancel/stop path when the wait times out or the operator interrupts the command,
  then exit with a nonzero status and a clear failure reason.
- Add focused unit tests and manual live-robot proof documentation for the one-skill execution path.

## Out Of Scope

- Running the full observe-decide-act pilot loop, invoking an LLM, parsing LLM output, or choosing a
  next skill after the first command finishes.
- Calibrating skill baselines, building skill memory, or proving all required primitive skills; that is
  owned by `skill-baseline-capture` and `pm5-skill-baselines`.
- Implementing delivery-task recipes, retry/recovery strategy, full task assertions, or replay-loop
  orchestration.
- Redesigning `contracts/` schemas or adding new skill names beyond the closed MVP vocabulary.
- Reworking PROS firmware, Brain watchdog behavior, or low-level serial packet clamps.
- Making every registry skill fully executable through ROS in this slice. PM4 proves the executor
  boundary with the approved supervised proof set; broader skill coverage belongs in later baseline
  capture work.

## Acceptance

- `pilot` exposes a public one-skill executor API that accepts a `PilotSkillCommand`, an observation or
  live-observation source, validation mode, human-supervision state, result timeout, and trace sink.
- The executor rejects invalid commands, missing/unsafe observations, stale bridge/telemetry,
  estop/fault states, and missing hardware supervision before publishing any motion-producing ROS
  message.
- The canonical base-motion hardware proof command validates and dispatches one `survey_scene`
  command to `/survey/goal`, waits for `/survey/result`, records the terminal status, and stops
  without issuing a second skill command.
- The ball-handling proof commands can validate and dispatch exactly one `claw_open`, `claw_close`,
  `verify_grasp`, or `verify_drop` skill, wait for one terminal result or verification outcome, record
  it, and stop without chaining into another skill.
- Timeout and `KeyboardInterrupt` paths publish `/survey/cancel` or an equivalent safe stop/cancel
  request, write a stop trace record, and exit nonzero.
- Successful proof output includes contract-valid JSONL trace records for command, result, and stop;
  failed validation, rejected result, timeout, and interrupt paths also produce contract-valid trace
  records explaining why motion did not continue.
- Unit tests cover validation pass/fail behavior, fake transport dispatch payloads, result mapping,
  terminal success/failure/rejection, timeout cancellation, interrupt cancellation, JSONL trace record
  validation, and import behavior on a development machine without ROS packages.
- The hardware CLI is bounded by explicit timeout and requires an explicit human-supervision flag
  before hardware dispatch.
- Manual verification docs identify the required ROS nodes/topics, the staged command to run, expected
  JSONL output shape, expected `/survey/result` behavior, and evidence that the command stopped after
  exactly one skill.
- Existing affected gates pass: focused `uv run pytest`/`ruff` in `pilot`, plus root `make validate`
  where contract fixture/schema validation is affected.

## Constraints

- `contracts/` remains the only schema-owning vertical. `pilot/` may add dataclasses, protocols, and
  helpers, but not new pydantic schemas for pilot commands, results, observations, or trace records.
- Hardware execution must require an explicit operator/human supervision input and must reject missing
  supervision before publishing to ROS.
- The executor must remain bounded by a caller-supplied timeout and must be safe to interrupt at any
  point.
- ROS integration must be optional at import time; core executor tests must run without ROS 2 Jazzy or
  `rclpy` installed.
- Motion-producing behavior is limited to the validated command and its cancel/stop path. PM4 must not
  loop into additional skills or retries.
- Logging must use contract-valid `PilotTraceRecord` JSONL so later replay and run-logger work can
  consume the proof artifact.
- Tooling remains `uv` and `ruff`; do not introduce pip/poetry/black/isort/flake8.

## Proposed Decisions

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| PM4-001 | closed | Treat `pm4-one-skill-execution` as a feature-plan target even though the program graph models PM4 as a manual milestone gate. | The user wants a runnable feature slice, and no `.ai-sdd/features/pm4-one-skill-execution/` exists yet. | Leaving PM4 as only a manual validation node with no implementable requirements. |
| PM4-002 | closed | Support the approved PM4 hardware proof set: `survey_scene`, `claw_open`, `claw_close`, `verify_grasp`, and `verify_drop`. | `survey_scene` proves bounded base motion; the claw and verify skills exercise grabbing/dropping ball behavior before baseline capture. | Choosing target-dependent navigation skills for PM4. |
| PM4-003 | closed | Implement only the minimum ROS dispatch/result mapping needed for the approved PM4 proof set, with the core executor structured so additional skills can be added later. | PM4 proves supervised one-skill execution; broad registry coverage belongs to baseline capture and later executor expansion. | Attempting full registry-to-ROS coverage in this slice. |
| PM4-004 | closed | Keep the executor core ROS-free behind a transport abstraction, and isolate `rclpy` in the hardware CLI/transport module. | CI-style tests and off-robot development must run without ROS packages. | Making all `pilot` imports require ROS. |
| PM4-005 | closed | Require an explicit hardware supervision flag for the PM4 CLI and pass that state into `validate_skill_command(..., mode=hardware)`. | Program decision O6 and safety requirements require explicit hardware supervision before PM4 live motion. | Treating the CLI command itself as implicit supervision. |
| PM4-006 | closed | Log PM4 proof artifacts as contract `PilotTraceRecord` JSONL instead of inventing a separate proof-log schema. | Later replay, run logger, and diagnostics can consume the same event shape. | Ad hoc text logs or a PM4-only JSON schema. |
| PM4-007 | closed | Map terminal ROS proof results to `PilotSkillResult` statuses: success to `CommandStatus.OK`, explicit unsuccessful/rejected/fault payloads to `REJECTED` or `FAILED`, and missing terminal result to `STALE`. | This preserves contract semantics while normalizing existing ROS result payloads. | Treating every non-success as a free-form failure string only. |
| PM4-008 | closed | On timeout or interrupt, publish the skill-specific cancel path before writing a stop trace and exiting nonzero. | The milestone requires stopping safely after the one skill attempt. | Waiting indefinitely or relying only on process exit. |
| PM4-009 | closed | Accept a contract JSON command input for tests and automation, while the CLI may provide convenience flags for the approved PM4 proof skills. | JSON preserves exact schema validation; convenience flags make supervised hardware proof practical. | A CLI-only surface that is hard to replay or test. |

## Open Questions And Proposed Resolutions

| ID | Status | Proposed Resolution |
|---|---|---|
| PM4-O1 | closed | PM4's live proof skill set is `survey_scene`, `claw_open`, `claw_close`, `verify_grasp`, and `verify_drop`; later features may add other ROS skill mappings after this boundary is proven. |
| PM4-O2 | closed | The PM4 CLI requires both `--hardware` and an explicit `--human-supervised` flag before motion. For PM4 this means an operator is present for the supervised proof and can interrupt/estop if the bounded skill behaves unexpectedly; it does not mean the human teleoperates the skill. |
| PM4-O3 | closed | The proof trace defaults to JSONL written to a caller-provided `--out` path; stdout may be used only for status messages so the artifact stays machine-readable. |

## Approval Gate

Approved by the human in-session. `.ai-sdd/features/pm4-one-skill-execution/pipeline.yaml` and
`slices/*.md` files may be emitted.
