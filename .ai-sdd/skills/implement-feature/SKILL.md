---
name: implement-feature
description: Implement an ai-sdd feature plan within this repo's conventions and record the acceptance ids covered.
---

# Implement a feature (VEX self-model factory)

Read `.ai-sdd/artifacts/feature-plan.v1.yaml` and `.ai-sdd/conventions/<stack>.md` (this slice's
vertical) first. Stay strictly inside the plan's `files` scope — the `changeset.diff-in-scope` gate
compares the working tree against it.

Per-vertical layout & toolchain (from the conventions):

- `contracts/` — Python 3.12 · the frozen schemas (pydantic v2, ADR-06), adapter interfaces,
  `Synthetic` oracle, `Replay` sources. **All schemas live here; nowhere else.**
- `operator/` — Python 3.12 · Generator, 3-critic panel, gap analyzer, markdown presenter, demo
  replay. The Generator must not read the oracle config (information separation).
- `coprocessor/` — Python 3.11 · live `Serial`/`Camera` sources, vision pipeline (YOLO11n + AprilTag),
  `serial_bridge.py` merge → `session_*.jsonl`.
- `brain/` — VEXcode Python single file, ruff dev-lint only, no runtime package manager.

Toolchain (non-negotiable): `uv` for deps/envs (`uv sync` / `uv add` / `uv run`); `ruff` for
lint/format. No pip/poetry/black/isort/flake8.

Run the commands in the plan's `tests` field. At minimum: `uv sync`, `make test`, `make validate`
(pydantic fixtures vs frozen schemas), `make lint` (ruff check + ruff format --check). Any change to
a frozen contract must keep `.ai-sdd/schemas/examples/*.json` valid — the `task-telemetry.structure`,
`self-model.structure`, and `parts-catalog.structure` gates run every slice.

Write `.ai-sdd/artifacts/changeset.v1.yaml` with:

- `summary`: what changed.
- `satisfies`: the acceptance item ids addressed.

The deterministic gates run after submit and reject missing artifacts, failed build/test/validate/
lint, files outside scope, or a broken frozen contract. Discovered out-of-scope work is a **new
slice** (flag it), never an inline change.
