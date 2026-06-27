# DevOps And Device Workflow

This repo has two jobs:

1. Keep the capstone team aligned on the architecture, self-model, telemetry contract, and research evidence.
2. Ship a small, reproducible runtime to the Raspberry Pi mounted on the VEX robot.

The repository should be the source of truth for code and contracts. The Pi should hold only local config, logs, model artifacts, camera frames, and generated session data.

## Recommended Branch Model

Use `main` as the shared source of truth.

- `main`: reviewed specs, docs, schemas, ROS 2 Pi runtime code, and V5 Brain code.
- `feature/<short-topic>`: normal development branches.
- `devops/<short-topic>`: repo/process changes.
- `deploy/vexy-pi`: optional device deployment branch. This branch must not receive direct commits. Move it only to a reviewed commit from `main`.
- `pi-vexy-YYYYMMDD-HHMM` tags: immutable snapshots of what was deployed to the Pi.

The important rule: the Pi can track `deploy/vexy-pi`, but all real development still lands through `main`.

## Repository Layout

```text
raw/                         Immutable source/reference material.
wiki/                        Team knowledge base and lifecycle work items.
robot/ros2-runtime/          Raspberry Pi ROS 2 runtime: camera, bridge, capture/export.
robot/v5-brain/              VEX V5 Brain starter code and notes.
DEVOPS.md                    This operating model.
```

## Pi Runtime

The Pi runtime lives in:

```text
robot/ros2-runtime/
```

It contains:

- `src/vexy_ros/vex_bridge_node.py`: V5 Brain serial bridge and demux.
- `src/vexy_ros/operator/node.py`: live robot-control operator.
- `src/vexy_ros/evidence_export.py`: ContractLine JSONL export.
- `launch/`: ROS 2 launch files for the Pi stack.
- `scripts/setup_pi.sh`: one-shot Pi bootstrap for Ubuntu 24.04 + ROS 2 Jazzy.
- `docs/`: architecture, protocol, and usage notes.

## Device Config

Committed defaults live at:

```text
robot/ros2-runtime/config/
```

Machine-local overrides live only on the Pi:

```text
~/.config/vexy-system2/local
```

Do not commit real device-local config, API keys, model weights, logs, camera frames, or generated sessions.

Example local override:

```bash
VEXY_BRIDGE_MODE=serial
VEXY_SERIAL_PORT=/dev/serial/by-id/YOUR_V5_USER_PORT
VEXY_SERIAL_BAUD=115200
```

## First-Time Pi Setup

On the Pi:

```bash
cd ~
git clone https://github.com/codewizard-dt/llm-self-model-capstone.git
cd ~/llm-self-model-capstone
bash robot/ros2-runtime/scripts/setup_pi.sh
```
Then launch the ROS 2 stack with the runbook in
`robot/ros2-runtime/README.md`.

## Deploying To The Pi

Recommended reviewed deployment:

```bash
git checkout main
git pull --ff-only
git tag pi-vexy-YYYYMMDD-HHMM
git push origin pi-vexy-YYYYMMDD-HHMM
git branch -f deploy/vexy-pi pi-vexy-YYYYMMDD-HHMM
git push -f origin deploy/vexy-pi
```

On the Pi:

```bash
cd ~/llm-self-model-capstone
git fetch origin
git checkout deploy/vexy-pi
git reset --hard origin/deploy/vexy-pi
make rebuild-pi
systemctl --user --no-pager --plain status vexy-ros-stack.service
```

During rapid prototyping, it is acceptable for the Pi to track a feature branch temporarily, but record that in the PR and switch back to `deploy/vexy-pi` before a demo.

## Review Checklist

Every PR that changes robot runtime behavior should answer:

- What changes on the Pi?
- What changes on the V5 Brain?
- What telemetry or JSON schema fields changed?
- What ROS 2/runtime tests or capture proof were run?
- Does this affect the physical safety envelope or watchdog behavior?
- Does the Pi need a local config update under `~/.config/vexy-system2/local`?

## Safety Rules

- V5 Brain owns motors and timing.
- Pi sends short-lived, high-level commands.
- Moving commands require TTLs and Brain-side watchdog enforcement.
- Pi-side services may fail or reboot without leaving motors running.
- Stop command and stale heartbeat behavior must stay testable in simulator mode.
