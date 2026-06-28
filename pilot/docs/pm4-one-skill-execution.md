# PM4 One Skill Execution Proof

PM4 proves one approved pilot skill against live hardware, under direct human supervision, and then
stops. It is not a delivery recipe, a retry policy, an LLM loop, or a baseline capture run.

## Supervision

`--human-supervised` is a safety gate for this proof. It means:

- a human operator is physically present and watching the robot;
- the workspace is clear, bounded, and prepared before the command starts;
- the operator can interrupt the process with `Ctrl-C` or estop the robot;
- the operator does not teleoperate, steer, recover, or chain the skill.

If the operator needs to intervene beyond interrupting or estopping, the PM4 run fails and the trace
should be kept as failure evidence.

## Setup

Run the proof on the Pi or a host with the robot ROS 2 environment sourced. Required observation
topics must be active before dispatch:

- `/vision/agent_scene`
- `/vision/object_tracks`
- `/vex/telemetry`
- `/vex/bridge_status`

Optional read-only context improves verification evidence when present:

- `/vision/scene_map`
- `/task_plan/current`
- `/operator/status`

Motion-producing proof topics are limited to these implemented PM4 surfaces:

- `survey_scene`: publishes `/survey/goal`, waits on `/survey/result`, cancels on `/survey/cancel`.
- `claw_open`: publishes action `release` on `/operator/command`, waits on `/operator/results`.
- `claw_close`: publishes action `grab` on `/operator/command`, waits on `/operator/results`.
- `verify_grasp`: read-only check from the bound live observation; publishes no command topic.
- `verify_drop`: read-only check from the bound live observation; publishes no command topic.

`pilot skill` exits before dispatch if strict observation readiness is not met, the command is not
contract-valid, bridge health is stale or faulted, estop is active, or `--hardware`,
`--human-supervised`, or `--out` is missing.

## Commands

Use one command per proof run and keep each trace file separate.

Canonical survey proof:

```bash
pilot skill --hardware --human-supervised --skill survey_scene --duration-s 3.0 --out traces/pm4-survey.jsonl
```

Claw open:

```bash
pilot skill --hardware --human-supervised --skill claw_open --opening-pct 100 --out traces/pm4-claw-open.jsonl
```

Claw close:

```bash
pilot skill --hardware --human-supervised --skill claw_close --grip-force-n 8 --out traces/pm4-claw-close.jsonl
```

Verify grasp from live observation evidence:

```bash
pilot skill --hardware --human-supervised --skill verify_grasp --object-id ball-1 --min-confidence 0.65 --out traces/pm4-verify-grasp.jsonl
```

Verify drop from live observation evidence:

```bash
pilot skill --hardware --human-supervised --skill verify_drop --destination-id goal-1 --min-confidence 0.65 --out traces/pm4-verify-drop.jsonl
```

For automation, `--command-json command.json` may replace the convenience flags. The JSON file must
be a contract `PilotSkillCommand`, and any simultaneous `--skill` value must match the JSON command.

## Trace JSONL

The trace is newline-delimited `contracts.PilotTraceRecord` JSON. Sequence numbers are monotonic
within the session. Successful dispatched runs produce `command`, `result`, and `stop` records:

```json
{"v":1,"event":"command","session_id":"pm4-survey_scene-555","seq":0,"monotonic_ms":555,"command":{"v":1,"command_id":"pm4-survey_scene-555","issued_ms":555,"skill":"survey_scene","params":{"yaw_span_deg":180.0,"timeout_ms":3000}}}
{"v":1,"event":"result","session_id":"pm4-survey_scene-555","seq":1,"monotonic_ms":556,"result":{"v":1,"command_id":"pm4-survey_scene-555","skill":"survey_scene","status":"ok","completed_ms":3555,"message":"success"}}
{"v":1,"event":"stop","session_id":"pm4-survey_scene-555","seq":2,"monotonic_ms":557,"reason":"success","message":"success"}
```

Validation rejection writes a stop record before dispatch:

```json
{"v":1,"event":"stop","session_id":"pm4-survey_scene-888","seq":0,"monotonic_ms":888,"reason":"failure","message":"validation rejected: bridge_stale: bridge health is stale"}
```

Missing hardware supervision writes a stop record with `request_human`:

```json
{"v":1,"event":"stop","session_id":"session-1","seq":0,"monotonic_ms":10,"reason":"request_human","message":"validation rejected: human_supervision_required: hardware execution requires --human-supervised"}
```

Unsupported or unavailable live surfaces are rejected before dispatch and write `result` then `stop`:

```json
{"v":1,"event":"result","session_id":"pm4-claw_open-777","seq":0,"monotonic_ms":777,"result":{"v":1,"command_id":"pm4-claw_open-777","skill":"claw_open","status":"rejected","message":"claw_open requires /operator/command and /operator/results; operator claw surface is unavailable","fault":"operator_surface_unavailable"}}
{"v":1,"event":"stop","session_id":"pm4-claw_open-777","seq":1,"monotonic_ms":778,"reason":"failure","message":"claw_open requires /operator/command and /operator/results; operator claw surface is unavailable"}
```

Timeout writes a dispatched `command` record, publishes the skill-specific cancel path, then writes a
failure stop:

```json
{"v":1,"event":"stop","session_id":"pm4-survey_scene-555","seq":1,"monotonic_ms":3555,"reason":"failure","message":"timed out waiting for terminal result after 3000 ms"}
```

Operator interrupt writes a dispatched `command` record, sends cancel, and then writes:

```json
{"v":1,"event":"stop","session_id":"pm4-survey_scene-555","seq":1,"monotonic_ms":1555,"reason":"operator","message":"execution interrupted by operator"}
```

## Pass Criteria

A PM4 run passes only when all of these are true:

- exactly one approved skill is requested: `survey_scene`, `claw_open`, `claw_close`,
  `verify_grasp`, or `verify_drop`;
- `--hardware`, `--human-supervised`, and `--out` are present;
- the live observation is ready and contract-valid before dispatch;
- the JSONL file validates as `PilotTraceRecord` records;
- dispatched success traces contain exactly one `command`, one terminal `result`, and one `stop`;
- the final `stop.reason` is `success` and the terminal `result.status` is `ok`;
- the CLI exits `0`;
- ROS evidence shows no second motion-producing publish and no fallback command after the one skill
  or its cancel path.

Nonzero exit codes are expected failure evidence:

- `2`: usage, missing PM4 gates, invalid CLI command, or unapproved skill;
- `20`: validation rejection, rejected result, stale result, or unavailable preflight surface;
- `21`: terminal result timeout after cancel;
- `22`: operator interrupt after cancel;
- `23`: ROS dependencies unavailable;
- `24`: runtime or ROS execution failure;
- `25`: trace output could not be opened or written.

## Unsupported Behavior

PM4 does not invent fallback motion. If a ball-handling surface is unavailable, the proof must reject
before publishing a motion-producing command. For claw skills, unavailable `/operator/command` or
`/operator/results` is represented as a rejected `PilotSkillResult` with
`fault="operator_surface_unavailable"`, followed by a failure stop record.

The following are out of scope and fail PM4 if observed:

- chaining multiple skills in one process;
- retrying after a failed or stale result;
- replacing `claw_open` or `claw_close` with raw arm, motor, serial, or teleop commands;
- treating `verify_grasp` or `verify_drop` as permission to move the robot;
- editing contract schemas or creating pilot-local trace schemas for the proof.

## Final Gates

Before submitting PM4, run the focused pilot checks and the repo gates when feasible:

```bash
cd pilot && PYTHONPATH=src:../contracts/src uv run pytest tests/test_skill_cli.py tests/test_ros_execution.py tests/test_execution.py tests/test_observe_cli.py -v
cd pilot && PYTHONPATH=src:../contracts/src uv run ruff check src/pilot/__init__.py src/pilot/skill_cli.py src/pilot/ros_execution.py src/pilot/execution.py src/pilot/trace.py tests/test_skill_cli.py tests/test_ros_execution.py tests/test_execution.py
cd pilot && PYTHONPATH=src:../contracts/src uv run ruff format --check src/pilot/__init__.py src/pilot/skill_cli.py src/pilot/ros_execution.py src/pilot/execution.py src/pilot/trace.py tests/test_skill_cli.py tests/test_ros_execution.py tests/test_execution.py
uv sync
make test
make validate
make lint
```

`make demo` is not a PM4 gate; it remains the m2 offline self-model milestone step.
