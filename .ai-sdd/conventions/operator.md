# ai-sdd Conventions — `operator` vertical

> **Seed mode.** Bootstrapped from [`MASTER_REQUIREMENTS.md`](../../MASTER_REQUIREMENTS.md) (the
> decision-closed authoritative source), not from code evidence. Each row cites its section. Rows
> marked `open gap` have no decision in the source and must be confirmed.

**Vertical.** `operator` — the **offline self-model loop** (LLM authoring/critique/replay/
presentation): the Generator, the 3-critic panel, the gap analyzer, the markdown presenter, the demo
replay. Its own Stack/Factory (ADR-0024/0012). Root: `operator/`. Owner: **TBD** (per O1; slices
inherit the vertical lead once assigned, ADR-0027). *(Evidence: Tech stacks · Components · Sub-features.)*

> **Scope boundary vs `pilot`.** `operator` is the **offline, generational** loop — it revises a
> readable self-model/design over recorded/synthetic data (`make demo`). The **online, real-time**
> control loop (an LLM on the Pi piloting the robot via the control grammar) is a separate vertical,
> [`pilot`](pilot.md). Keep them distinct: `operator` writes design documents; `pilot` issues commands.

## Discovery Record

| Change type | Evidence (MASTER_REQUIREMENTS §) | Convention | Status |
|---|---|---|---|
| Build / install | Tech stacks (Shared tooling); ADR-15 | `uv` (`uv sync` / `uv add` / `uv run`). No pip/poetry/conda. Reviewer baseline: `uv sync`. | confirmed |
| Test | Verification & Reviewer Runbook | `make test` — gap math, revision-consumes-residuals, critic flags planted torque error. | confirmed |
| Lint / format | ADR-16 | `ruff` only; `make lint` = `ruff check` + `ruff format --check`. | confirmed |
| Validate | ADR-06; Verification & Reviewer Runbook | `make validate` — pydantic fixtures vs frozen schemas (schemas imported from `contracts`). | confirmed |
| Run commands | Verification & Reviewer Runbook | `make demo` = deterministic Gen 0 → Gen 2 replay; it is the **m2 milestone** step, not a per-slice gate. | confirmed |
| Language | ADR-05 | **Python 3.12** (dev machine). | confirmed |
| Module / feature | Components | Generator, Critic panel (3 critics), Gap analyzer, Markdown presenter, Demo replay are each their own module under `operator/`. | confirmed |
| Model / entity | Components (Boundary rule) | **No schema is defined here.** Import the frozen schemas from `contracts`. | confirmed |
| Migration | ADR-11 (JSONL) | **Not applicable.** | N/A |
| Test (placement) | Verification & Reviewer Runbook | Required tests: a planted torque-budget violation is flagged pre-build by the critic panel; a revised self-model's predicted value moves toward observed after consuming a gap block. | confirmed |
| Endpoint | ADR-04; OUT of scope | **Not applicable.** Presentation is markdown/terminal renderer; no web UI. | N/A |
| Config / secrets | ADR-08; ADR-03 | **None.** Claude Code subscription runtime; no keys/billing. | confirmed |
| Dependency / new package | ADR-15 | `uv add`; pin via lockfile. | confirmed |
| Naming / layering | Components (Boundary rule); Oracle grounding | See Boundary rules. | confirmed |
| CI / release | — | **Open gap** (not decided in the authoritative source). | open gap |

## Boundary rules (non-negotiable)

- **Information separation (the Generator).** The Generator (F8) reads **only** `parts_catalog.json`
  + prior gap residuals. It **never** reads the oracle config or the oracle's hidden parameters.
  Gap-tightening must come from the self-model converging on the hidden truth, not from steering.
  *(Evidence: Oracle grounding & information separation; ADR-17.)*
- **No schema defined here** — import from `contracts`. *(Evidence: Components — Boundary rule.)*
- **Loop depends on adapter interfaces, never a concrete provider.** *(Evidence: ADR-01.)*
- **3 critics, fixed set:** physics validity · torque budget · CoM/geometry; stateless, pass/flag +
  rationale. *(Evidence: ADR-07; Components — Critic panel.)*
- **LLM runtime:** Claude Code interactive for authoring; cached transcripts replay deterministically
  for `make demo`. *(Evidence: ADR-08; Integration Boundaries — `LLMRuntime`.)*
