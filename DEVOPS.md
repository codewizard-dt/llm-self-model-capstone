# DevOps And Device Workflow

This repo has two jobs:

1. Keep the capstone team aligned on the architecture, self-model, telemetry contract, and research evidence.
2. Ship a small, reproducible runtime to the Raspberry Pi mounted on the VEX robot.

The repository should be the source of truth for code and contracts. The Pi should hold only local config, logs, model artifacts, camera frames, and generated session data.

## Recommended Branch Model

Use `main` as the shared source of truth.

- `main`: reviewed specs, docs, schemas, Pi runtime code, and V5 Brain code.
- `feature/<short-topic>`: normal development branches.
- `devops/<short-topic>`: repo/process changes.
- `deploy/vexy-pi`: optional device deployment branch. This branch must not receive direct commits. Move it only to a reviewed commit from `main`.
- `pi-vexy-YYYYMMDD-HHMM` tags: immutable snapshots of what was deployed to the Pi.

The important rule: the Pi can track `deploy/vexy-pi`, but all real development still lands through `main`.

## Repository Layout

```text
raw/                         Immutable source/reference material.
wiki/                        Team knowledge base and lifecycle work items.
robot/pi-runtime/            Raspberry Pi runtime: camera, bridge, dashboard, planner stubs.
robot/v5-brain/              VEX V5 Brain starter code and notes.
DEVOPS.md                    This operating model.
```

## Pi Runtime

The Pi runtime lives in:

```text
robot/pi-runtime/
```

It contains:

- `src/vexy_system2/bridge.py`: local TCP bridge to simulated or real V5 Brain.
- `src/vexy_system2/camera_broker.py`: single-owner Pi Camera broker.
- `src/vexy_system2/dashboard.py`: local operator/dashboard surface.
- `scripts/`: smoke tests, serial discovery, service install scripts.
- `services/`: user-level systemd service templates.
- `docs/`: architecture, protocol, and V5 bring-up notes.

## Device Config

Committed defaults live at:

```text
robot/pi-runtime/config/defaults
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
cd ~/llm-self-model-capstone/robot/pi-runtime
PYTHONPATH=src scripts/smoke_test.sh
scripts/install_user_services.sh
systemctl --user enable vexy-bridge.service vexy-dashboard.service vexy-camera.service
systemctl --user restart vexy-bridge.service vexy-dashboard.service vexy-camera.service
```

Then browse:

```text
http://vexy.local:8080
```

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
cd robot/pi-runtime
PYTHONPATH=src scripts/smoke_test.sh
systemctl --user restart vexy-bridge.service vexy-dashboard.service vexy-camera.service
systemctl --user --no-pager --plain status vexy-bridge.service vexy-dashboard.service vexy-camera.service
```

During rapid prototyping, it is acceptable for the Pi to track a feature branch temporarily, but record that in the PR and switch back to `deploy/vexy-pi` before a demo.

## Review Checklist

Every PR that changes robot runtime behavior should answer:

- What changes on the Pi?
- What changes on the V5 Brain?
- What telemetry or JSON schema fields changed?
- Was `robot/pi-runtime/scripts/smoke_test.sh` run?
- Does this affect the physical safety envelope or watchdog behavior?
- Does the Pi need a local config update under `~/.config/vexy-system2/local`?

## Safety Rules

- V5 Brain owns motors and timing.
- Pi sends short-lived, high-level commands.
- Moving commands require TTLs and Brain-side watchdog enforcement.
- Pi-side services may fail or reboot without leaving motors running.
- Stop command and stale heartbeat behavior must stay testable in simulator mode.

