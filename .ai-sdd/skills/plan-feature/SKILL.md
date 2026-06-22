---
name: plan-feature
description: Produce a decision-closed ai-sdd feature plan with a verifiable acceptance checklist, grounded in this repo's conventions and the frozen contracts.
---

# Plan a feature (VEX self-model factory)

Read first, before planning:

- `MASTER_REQUIREMENTS.md` — the decision-closed authoritative source (where `PLAN.md`/
  `ARCHITECTURE.md` disagree, it wins).
- `.ai-sdd/conventions/<stack>.md` for **this slice's vertical** (`stack` is supplied by the slice
  node: `contracts` | `operator` | `coprocessor` | `brain`).
- The three frozen contracts: `.ai-sdd/schemas/{task-telemetry,self-model,parts-catalog}.schema.yaml`.

Write the artifact to `.ai-sdd/artifacts/feature-plan.v1.yaml`. It must contain:

- `summary`: concise description of the intended change.
- `scope`: a mapping with at least `in` and `out` lists.
- `acceptance`: one verifiable item per outcome, each `{ id, description }` with a stable `id`. This
  checklist is the thread — the implementer records the ids it covers in `satisfies`, the reviewer
  returns a verdict per id.
- `decisions`: every planning decision, each `status: closed`. Cite the MASTER_REQUIREMENTS section
  or ADR that grounds it.
- `files`: exact repo-relative files/prefixes the implementation may touch — must stay within the
  slice's vertical root (`contracts/` | `operator/` | `coprocessor/` | `brain/`) plus shared
  surfaces (`tests/`, `docs/`, `Makefile`, `pyproject.toml`, `.ai-sdd/`, …).
- `tests`: the gate commands the implementer must run — at minimum `uv sync`, `make test`,
  `make validate`, `make lint` (per the Verification & Reviewer Runbook).

Honor the boundary rules from the convention file:

- **No schema is defined outside `contracts`** — other verticals import the frozen schemas.
- The loop depends only on the `TelemetrySource`/`VisionSource` adapter interfaces, never a concrete
  provider.
- **Oracle information separation**: the Generator reads only `parts_catalog.json` + prior gap
  residuals — never the oracle's hidden parameters.

Do not leave open architecture questions inside the artifact. If the work needs a new architecture
decision not closed in `MASTER_REQUIREMENTS.md`, **stop and surface the options to the maintainer**
instead of guessing. `make demo` is an m2-milestone concern — do not add it as a per-slice gate.
