# LLM Self-Modeled Robot

This repo is the source of truth for a capstone project: a VEX V5 robot plus a
Raspberry Pi runtime where an LLM helps the robot describe, test, and revise its
own self-model from telemetry and vision evidence.

If you are new here, start with this page, then drill into the linked docs.

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
|-- robot/
|   |-- pi-runtime/             Raspberry Pi runtime: bridge, camera, dashboard, demo.
|   `-- v5-brain/               VEX V5 Brain PROS C++ code and bring-up notes.
`-- build-history/              Hardware build photos and screenshots.
```

## Current Code Surfaces

Most of the current runnable code lives under `robot/`.

- `robot/pi-runtime/src/vexy_system2/bridge.py` - TCP bridge to a simulated or
  serial-connected V5 Brain.
- `robot/pi-runtime/src/vexy_system2/dashboard.py` - local operator dashboard.
- `robot/pi-runtime/src/vexy_system2/planner_demo.py` - small simulated planner
  that sends heartbeat, drive, and stop commands.
- `robot/pi-runtime/scripts/smoke_test.sh` - fastest local health check.
- `robot/v5-brain/v5-test/src/main.cpp` - working PROS C++ arm telemetry test.
- `robot/v5-brain/BRINGUP.md` - detailed VEX Brain setup and debugging notes.

Some directories described in `AGENTS.md`, such as `contracts/`, `operator/`,
and `pilot/`, are planned verticals and may not exist yet in the current tree.

## Run The Local Smoke Test

From the repo root:

```bash
robot/pi-runtime/scripts/smoke_test.sh
```

Expected ending:

```text
smoke test ok
```

This test uses the simulated bridge. It does not require the physical robot.

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
robot/pi-runtime/scripts/smoke_test.sh
```

Before opening a pull request, make sure your PR explains:

- what changed;
- whether the Pi runtime changed;
- whether the V5 Brain code changed;
- what check you ran;
- whether physical safety, watchdog, telemetry, or local Pi config are affected.

For runtime behavior changes, also use the checklist in [DEVOPS.md](DEVOPS.md).
