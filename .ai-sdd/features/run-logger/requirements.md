# Run Logger Feature Requirements

Status: approved
Source brief: `PILOT_MASTER_REQUIREMENTS.md` (`P8 run-logger`)
Program: `pilot-online-task-loop`
Feature slug: `run-logger`
Owner: David
Vertical: `pilot`
Depends on: `observation-builder`, `llm-decision-adapter`, `ros-skill-executor`, `assertion-engine`

## Goal

Build the pilot run logger: a deterministic, append-only JSONL trace writer for the online pilot loop.
It records every observation, LLM decision, validated command, execution result, assertion, and stop
reason using the contract-owned `PilotTraceRecord` schema so physical runs, replay runs, supervised
skill proofs, and later calibration work are diagnosable from one structured trace format.

The logger is an audit and replay boundary, not a control loop. It must not publish to ROS, choose
skills, execute commands, compute assertions, or define schemas outside `contracts/`.

## In Scope

- Add a `pilot` run-logging module with a small public API for opening a run trace and appending
  typed pilot events.
- Write newline-delimited JSON records compatible with the existing `contracts.PilotTraceRecord`
  variants: `observation`, `decision`, `command`, `result`, `assertion`, and `stop`.
- Assign stable trace metadata for each record: `session_id`, monotonically increasing `seq`, and
  caller/injected monotonic timestamp in milliseconds.
- Provide typed append helpers for `contracts.PilotObservation`, `contracts.PilotDecision`,
  `contracts.PilotSkillCommand`, `contracts.PilotSkillResult`, `contracts.PilotAssertion`, and stop
  reasons.
- Validate every event through the contract-owned trace record union before a line is written.
- Preserve event order exactly as appended by the deterministic harness.
- Support caller-supplied output paths and a default run-file naming policy suitable for ignored
  runtime directories such as `pilot/runs/`.
- Flush writes in a predictable way so supervised hardware runs can be inspected after interruption or
  process failure.
- Provide a ROS-free trace reader/parser utility that validates JSONL records back into trace records
  for tests and later replay-mode consumption.
- Provide a compact recent-history formatter or selector over logged trace records for downstream LLM
  prompts, without exposing raw unbounded logs.
- Add deterministic tests for successful writes, schema rejection, sequence numbering, stop records,
  parse/readback, malformed JSONL handling, recent-history selection, and no ROS dependency.

## Out Of Scope

- Implementing the full pilot loop, replay runner, task recipe engine, hardware run orchestration, or
  skill-baseline capture workflow.
- Building live ROS subscriptions, publishing commands, waiting for operator results, or changing
  `robot/ros2-runtime`.
- Calling an LLM provider, constructing prompts, parsing LLM output, validating safety, executing
  skills, or computing assertions.
- Defining or changing pydantic schemas in `pilot/`; `contracts/` remains the only schema owner.
- Capturing raw camera frames, large binary artifacts, full ROS bag/MCAP payloads, provider secrets,
  environment variables, or unbounded terminal logs.
- Guaranteeing multi-process concurrent append safety. The MVP logger is for one deterministic pilot
  harness process writing one trace.

## Acceptance

- `pilot` exposes a ROS-free run logger API importable on a dev machine without ROS packages.
- The logger writes one valid JSON object per line and no partial/extra text lines.
- Every written line validates as a `contracts.PilotTraceRecord`.
- The logger supports all MVP trace event variants: observation, decision, command, result, assertion,
  and stop.
- `session_id` is stable across a run, `seq` starts from zero unless an explicit resume/readback path
  is used, and `seq` increments by exactly one for every appended record.
- `monotonic_ms` comes from an injected clock or explicit caller value so tests are deterministic.
- Invalid event payloads are rejected before writing and leave the trace file unchanged for that
  append attempt.
- Writes are append-only and preserve the caller's event order.
- Stop records capture success, failure, operator interrupt, fault, and request-human outcomes using
  the contract-owned stop reason vocabulary.
- Trace readback returns validated typed records and reports malformed JSONL or schema-invalid records
  with useful line-number context.
- Recent-history selection is bounded and deterministic, and can include recent decisions, commands,
  results, assertions, failures, and stop records without handing raw unbounded logs to the LLM.
- Tests cover all event variants, validation failure, deterministic sequencing, injected clock/session
  behavior, readback, malformed line reporting, recent-history bounds, and no ROS import requirement.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Constraints

- Use the existing contract-owned trace schema from `contracts.PilotTraceRecord`; do not create a
  parallel trace schema in `pilot/`.
- The logger must remain deterministic and replay-friendly; no hidden wall-clock reads in core tests
  unless the caller does not inject a clock.
- Runtime trace output belongs in ignored run/capture directories by default and must not require
  committing generated traces.
- The LLM receives compact recent history derived from trace records, not raw logs or binary artifacts.
- The logger must not alter, clamp, execute, or reinterpret commands; it records the outputs of the
  validator, executor, assertion engine, and loop harness.
- Tooling remains `uv` and `ruff`; do not introduce pip, poetry, black, isort, flake8, or new logging
  frameworks for the MVP.

## Proposed Decisions

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| RL-001 | closed | Implement the logger in `pilot/src/pilot/run_logger.py` with tests in `pilot/tests/test_run_logger.py`. | The feature belongs to the `pilot` vertical and should stay separate from observation, decision, execution, and assertion modules. | Adding logging behavior inside `pilot.cli`, `pilot.decision`, `pilot.executor`, or `pilot.assertions`. |
| RL-002 | closed | Use `contracts.PilotTraceRecord` and its existing event variants as the durable JSONL line schema. | `pilot-schemas` already created the replayable trace boundary and `contracts/` owns schemas. | Defining pilot-local pydantic log schemas or writing untyped dictionaries. |
| RL-003 | closed | Make `session_id`, `seq`, and `monotonic_ms` logger-managed metadata, with injectable session id and clock for tests. | The harness should not duplicate sequence bookkeeping, and deterministic tests need stable timestamps. | Requiring every caller to hand-build full trace records. |
| RL-004 | closed | Validate the full trace record before appending; if validation fails, raise/return a structured logger error and do not write the line. | Invalid traces would break replay and diagnosis, and partial writes hide the real failure. | Best-effort logging of malformed records. |
| RL-005 | closed | Write append-only UTF-8 JSONL with one compact JSON object per event and predictable flushing after each append by default. | Hardware runs may be interrupted; the latest completed event should be available for diagnosis. | Buffered-only writes that may lose the last several events, or pretty-printed multi-line JSON. |
| RL-006 | closed | Keep the core logger single-process and ROS-free for the MVP. | The deterministic pilot harness is the single trace owner, and tests/replay must run without ROS. | Multi-process locking, ROS bag integration, or MCAP export in this feature. |
| RL-007 | closed | Add a readback/parser utility that validates JSONL into typed trace records and reports line-level errors. | `replay-mode` and diagnostics need a trustworthy way to consume traces produced by this feature. | Deferring all readback behavior to the replay feature. |
| RL-008 | closed | Add a bounded recent-history formatter over typed trace records for the decision adapter input. | The source brief requires compact recent outcomes for the LLM, and the logger is the natural source of that history. | Passing raw JSONL tails directly into prompts. |
| RL-009 | closed | Exclude raw images, binary payloads, secrets, environment variables, and full unbounded ROS/provider logs from JSONL trace records. | Trace records should be compact, safe to inspect, and contract-valid; large artifacts need separate artifact references later. | Embedding raw frames or provider transcripts in every trace line. |
| RL-010 | closed | Default run files should live under an ignored runtime path such as `pilot/runs/<session_id>.jsonl`, while allowing explicit paths for tests and CLI/harness callers. | Generated traces should not pollute source control, but tests and future CLI commands need deterministic paths. | Hard-coding one global trace path or requiring callers to manage all file naming. |

## Open Questions

None for this feature draft. The program-level decisions and open-question resolutions from
`.ai-sdd/programs/pilot-online-task-loop/requirements.md` are carried forward.

## Approval Gate

Approved by the human in-session. `.ai-sdd/features/run-logger/pipeline.yaml` and `slices/*.md` files
may be emitted.
