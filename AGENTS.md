# AGENTS.md

General repo guide for coding agents. The authoritative spec for *what* to build is
[`MASTER_REQUIREMENTS.md`](MASTER_REQUIREMENTS.md) (where `PLAN.md`/`ARCHITECTURE.md` disagree, it
wins). This file says *how* the repo is built and driven.

## What this project is

A VEX-V5 robot with **two LLM loops** (see [`MASTER_REQUIREMENTS.md`](MASTER_REQUIREMENTS.md)):

1. **Offline self-model loop** — an LLM authors a human-readable self-model from a typed parts
   vocabulary; an adversarial critic panel attacks it; telemetry + vision produce signed **gap**
   residuals; the LLM revises the model; the next generation is built.
2. **Online control loop** — an LLM on the Pi reads live telemetry + vision and issues fixed
   control-grammar commands to perform an open-ended task in real time (bounded + interruptible),
   informed by the offline analysis.

Five verticals (each its own stack; logical names map onto the repo):

- `contracts/` — Python 3.12 · frozen schemas (pydantic v2) + the draft control grammar, adapter
  interfaces, `Synthetic` oracle, `Replay` sources. **All schemas live here.**
- `operator/` — Python 3.12 · the offline loop: Generator, 3-critic panel, gap analyzer, presenter, demo replay.
- `pilot/` — Python 3.11 · the online control loop (LLM-on-Pi). *(new; name provisional.)*
- `coprocessor` → `robot/ros2-runtime/` — Python 3.12 · ROS 2 Jazzy on Ubuntu 24.04 ·
  PiCam2 via `camera_ros`, rectification, AprilTag scene mapping, V5 serial bridge, MCAP capture,
  and contract-valid JSONL export. `robot/pi-runtime/` remains the legacy/fallback runtime.
- `brain` → `robot/v5-brain/` — **PROS C++** (FreeRTOS two-task) · emits telemetry + executes clamped commands.

## Build / verify

Toolchain is non-negotiable: **`uv`** for deps/envs, **`ruff`** for lint/format (no
pip/poetry/black/isort/flake8). A reviewer runs:

```bash
uv sync          # install pinned deps per vertical
make test        # unit tests (gap math, revision-consumes-residuals, planted-torque critic)
make validate    # pydantic fixtures vs the frozen schemas
make lint        # ruff check + ruff format --check
make demo        # deterministic Gen 0 → Gen 2 replay  (this is the m2 milestone step)
```

<!-- ai-sdd:begin — managed by ai-sdd-bootstrap; edits between these markers are overwritten on re-bootstrap -->
## AI Software Factory (`.ai-sdd/`)

This repo is built by **ai-sdd**, a provider-neutral software factory. One source of truth lives in
`.ai-sdd/` (committed, except `runs/` + `artifacts/` which are runtime); any coding agent drives it.

**Layout**

- `.ai-sdd/pipeline.yaml` — the per-slice build pattern: **planner → implementer → reviewer**
  (reviewer required). An acceptance checklist is threaded planner → implementer → reviewer.
- `.ai-sdd/workers/` — role signatures (`consumes`/`produces`/`checks`/`task.skill`); no inline prompts.
- `.ai-sdd/schemas/` — artifact schemas (`feature-plan`, `changeset`, `review`, `validation-result`)
  **and** the domain contracts: the three frozen ones (`task-telemetry`, `self-model`, `parts-catalog`)
  plus the draft `control-command` grammar, with canonical fixtures under `schemas/examples/`.
- `.ai-sdd/checks/` — the deterministic gates compiled from the schemas.
- `.ai-sdd/conventions/<vertical>.md` — house style per vertical, bootstrapped from
  `MASTER_REQUIREMENTS.md`.
- `.ai-sdd/skills/` — worker skills (`plan-feature`, `implement-feature`, `review-feature`) + the
  copied framework skills (`ai-sdd-plan`, `ai-sdd-plan-program`, `ai-sdd-run`,
  `ai-sdd-compile-schema`, `ai-sdd-bootstrap`).

**Skill discovery is per-agent, not prose.** Framework skills are surfaced through each agent's native
skill dir: `.agents/skills/<name>` (Codex, committed) and `.claude/skills/<name>` (Claude Code, local)
symlink into `.ai-sdd/skills/<name>`. Worker skills are resolved by the driver via `task.skill`.

**How to drive a run (the `ai-sdd-run` loop)**

```bash
ai-sdd validate .ai-sdd                       # wiring must pass before any run
/ai-sdd-plan "<feature brief>"                # → .ai-sdd/features/<slug>/
ai-sdd start .ai-sdd/features/<slug> --id <slug>
/ai-sdd-run <slug>                            # next → dispatch sub-agent → submit → commit per slice
```

For a multi-feature program (milestones + owners, e.g. the m1–m5 milestones), use
`/ai-sdd-plan-program` then `ai-sdd-run`. Gates are blocking and deterministic; a failed gate routes
rework to the indicted producer. `make demo` is the m2 milestone step, not a per-slice gate.
<!-- ai-sdd:end -->
