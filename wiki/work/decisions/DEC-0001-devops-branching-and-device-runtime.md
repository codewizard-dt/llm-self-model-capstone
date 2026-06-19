---
id: DEC-0001
title: DevOps Branching And Device Runtime Layout
created: 2026-06-19
updated: 2026-06-19
tags: [devops, raspberry-pi, vex-v5, runtime]
---

# DEC-0001 — DevOps Branching And Device Runtime Layout

## D1. Keep runtime code on main and use deploy/vexy-pi as a reviewed device pointer

Status: proposed  
Date: 2026-06-19  
Deciders: project team  
Consulted: Vexy System 2 Pi setup, capstone architecture docs  
Informed: all contributors  
Supersedes: none  
Tags: [branching, deploy, raspberry-pi]

### Context

The project needs to keep everyone aligned while also letting the Raspberry Pi run a known-good version of the robot runtime. A long-lived Pi-only development branch would make the device easy to update but would also hide robot changes from normal review and team context.

The repo already contains the capstone wiki/research structure, and the Pi runtime now has real service code: camera broker, bridge, dashboard, simulated V5 Brain loop, and bring-up scripts.

### Decision

All source code and shared contracts should land through `main`. The Pi may track `deploy/vexy-pi`, but that branch is only a deployment pointer to reviewed commits from `main`; it should not receive direct edits.

Runtime code lives in `robot/pi-runtime/`. V5 Brain code lives in `robot/v5-brain/`. Device-local overrides live outside the repo at `~/.config/vexy-system2/local`.

### Consequences

- Teammates review robot code through normal PRs.
- The Pi can still update from a stable branch with one `git pull`/`systemctl restart` workflow.
- Demo deployments can be reproduced from tags like `pi-vexy-YYYYMMDD-HHMM`.
- Local serial ports, camera settings, and other hardware-specific values do not pollute repo history.

### Alternatives Considered

| Option | Upside | Downside |
| --- | --- | --- |
| Put all Pi work directly on `main` and run the Pi from `main` | Simplest | Demo device can accidentally track untested work |
| Develop only on a long-lived `pi-runtime` branch | Easy device isolation | Team loses shared source of truth; merge drift grows |
| Use tags only, no deploy branch | Immutable and clean | Slightly slower for rapid hardware iteration |

### Recommended Flow

1. Develop on `feature/*` or `devops/*`.
2. Merge reviewed PRs to `main`.
3. Tag a known-good commit.
4. Move `deploy/vexy-pi` to that tag.
5. Pull/restart services on the Pi.

