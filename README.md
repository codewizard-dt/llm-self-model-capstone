# LLM Self-Modeled Robot

This repo is the source of truth for a capstone project: a VEX V5 robot plus a
Raspberry Pi runtime where an LLM helps the robot describe, test, and revise its
own self-model from telemetry and vision evidence.

If you are new here, start with this page, then drill into the linked docs.

## Send A Task To The Robot

With the Pi runtime already running and the V5 Brain program in slot 8, drop a
validated task envelope into the operator inbox from the repo root:

```bash
make send-task robot/ros2-runtime/fixtures/task_deliver_ball.json
```

`scripts/send_task_to_pi.sh` loads SSH settings from repo-root `.env`, validates
the file as [`contracts.TaskEnvelope`](contracts/src/contracts/task_envelope.py),
copies it to `/vexy/tasks/inbox` on the Pi, and prints the newest
`/home/vexy/telemetry/run-*` folder. The older `FILE=...` form still works:

```bash
make send-task FILE=robot/ros2-runtime/fixtures/task_deliver_ball.json
```

A task envelope has exactly two top-level fields: `contract`, the frozen
`ContractLine` evidence/prediction record, and `outline`, the ordered operator
method calls the robot will execute.

Very small example:

```json
{
  "contract": {
    "schema_version": "1.0",
    "session_id": "manual-grab",
    "generation": 0,
    "round": 0,
    "task": "manual_grab",
    "motor_samples": [{ "device": "left_drive" }],
    "predicted": { "success": true },
    "gap": { "distance_error_m": 0.0 }
  },
  "outline": [["grab", [], { "duration_ms": 700 }]]
}
```

If multiple task files are sent, the operator consumes one `*.json` file at a
time and does not start the next inbox task until the active task completes or
fails.

## What To Read First

1. [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md) - the authoritative product
   and architecture requirements. If docs disagree, this wins.
2. [AGENTS.md](AGENTS.md) - how coding agents and contributors should build,
   verify, and respect the repo structure.
3. [DEVOPS.md](DEVOPS.md) - branch, deploy, Pi setup, and device-safety workflow.
4. [wiki/index.md](wiki/index.md) - the knowledge base map for research,
   decisions, requirements, tasks, bugs, and UAT.
5. [robot/README.md](robot/README.md) - entry point for the deployable robot
   runtime code.

## Repo Map

```text
.
|-- MASTER_REQUIREMENTS.md      Product, scope, and architecture source of truth.
|-- AGENTS.md                   Contributor and coding-agent operating rules.
|-- DEVOPS.md                   Branching, Pi deployment, and safety workflow.
|-- PLAN.md / ARCHITECTURE.md   Planning docs; defer to MASTER_REQUIREMENTS.md.
|-- raw/                        Source material, research notes, PDFs, and CAD files.
|-- wiki/                       Structured knowledge base and work lifecycle docs.
|-- telemetry-fixtures/         Fixture-backed ContractLine JSONL evidence for MVP self-modeling.
|-- robot/
|   |-- ros2-runtime/           Raspberry Pi ROS 2 runtime: vision, V5 bridge, capture/export.
|   |-- v5-brain/               VEX V5 Brain PROS C++ code and bring-up notes.
|-- build-history/              Hardware build photos and screenshots.
```

## Evidence Handoff Scope

Downstream MVP self-modeling features consume `contracts.ContractLine` JSONL as
their semantic evidence input. The checked-in `telemetry-fixtures/` runs are
fixture-backed evidence for F8, F9, F10, F11, F12, and `make demo`; they do not
represent a real robot run and do not require ROS, hardware, or MCAP files.

Real hardware capture remains a later integration requirement. Those runs should
record replayable MCAP as the raw audit artifact and export the same
contract-valid JSONL shape for the self-model loop. PR #43 is useful as a JSONL
baseline with partial MCAP capture, but it is not completion of the full
hardware-capture and replay/audit requirement.

## Current Code Surfaces

Most of the current runnable code lives under `robot/`.

- `robot/ros2-runtime/src/vexy_ros/vex_bridge_node.py` - ROS 2 V5 serial bridge.
- `robot/ros2-runtime/src/vexy_ros/operator/node.py` - live robot-control operator.
- `robot/ros2-runtime/src/vexy_ros/evidence_export.py` - ContractLine JSONL export.
- `robot/ros2-runtime/scripts/setup_pi.sh` - Pi bootstrap for the ROS 2 stack.
- `robot/v5-brain/v5-test/src/main.cpp` - working PROS C++ arm telemetry test.
- `robot/v5-brain/BRINGUP.md` - detailed VEX Brain setup and debugging notes.

Some directories described in `AGENTS.md`, such as `contracts/`,
`self_model_generator/`, and `pilot/`, are planned verticals and may not exist
yet in the current tree. A repo-root `operator/` directory is intentionally not
a vertical name; `operator` is reserved for the live robot-control surface under
`robot/ros2-runtime/`.

## Run The Local Smoke Test

From the repo root:

```bash
cd robot/ros2-runtime
uv sync
PYTHONPATH=src:../../contracts/src uv run pytest tests/test_operator.py tests/test_evidence_export.py -q
```
This does not require the physical robot or a running ROS daemon.

## Contribution Workflow

For normal work:

```bash
git checkout main
git pull --ff-only
git switch -c feature/short-description
```

Make the smallest useful change, then run the relevant check. For Pi runtime
changes, start with:

```bash
cd robot/ros2-runtime && PYTHONPATH=src:../../contracts/src uv run pytest tests/test_operator.py tests/test_evidence_export.py -q
```

Before opening a pull request, make sure your PR explains:

- what changed;
- whether the Pi runtime changed;
- whether the V5 Brain code changed;
- what check you ran;
- whether physical safety, watchdog, telemetry, or local Pi config are affected.

For runtime behavior changes, also use the checklist in [DEVOPS.md](DEVOPS.md).
