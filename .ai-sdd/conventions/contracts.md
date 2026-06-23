# ai-sdd Conventions — `contracts` vertical

> **Seed mode.** This file was bootstrapped from [`MASTER_REQUIREMENTS.md`](../../MASTER_REQUIREMENTS.md),
> the decision-closed authoritative source — **not** from code evidence (greenfield). Every row's
> Evidence column cites the requirements section it transcribes. Rows marked `open gap` have no
> decision in the authoritative source and must be confirmed before being treated as policy.
> Authority: where `PLAN.md`/`ARCHITECTURE.md` disagree, `MASTER_REQUIREMENTS.md` wins.

**Vertical.** `contracts` — the cross-vertical source of truth: the three frozen schemas, the
adapter interfaces, the `Synthetic` oracle, and the `Replay` sources. This vertical is its own
Stack/Factory (ADR-0024/0012). Root: `contracts/`. Owner: **Erick** (per ADR-18; contracts +
oracle). Remaining contracts sub-feature owners **TBD** (slices inherit the vertical lead, ADR-0027).
*(Evidence: Tech stacks · Components · Sub-features.)*

## Discovery Record

| Change type | Evidence (MASTER_REQUIREMENTS §) | Convention | Status |
|---|---|---|---|
| Build / install | Tech stacks (Shared tooling); ADR-15 | Python deps + venv via **`uv`** (`uv sync` / `uv add` / `uv run`). No pip/poetry/pip-tools/conda. Reviewer baseline: `uv sync`. | confirmed |
| Test | Verification & Reviewer Runbook | `make test` — unit tests (gap math, revision-consumes-residuals, critic flags planted torque error). Run via `uv run`. | confirmed |
| Lint / format | Tech stacks (Shared tooling); ADR-16 | **`ruff`** only (`ruff check` / `ruff format`); `make lint` = `ruff check` + `ruff format --check`. No black/isort/flake8/pylint. | confirmed |
| Validate | Verification & Reviewer Runbook; ADR-06 | `make validate` — pydantic-v2 validation of all fixtures against the three frozen schemas. | confirmed |
| Run commands | Verification & Reviewer Runbook | Reviewer runs `uv sync`, `make demo`, `make test`, `make validate`, `make lint`. `make demo` is the **m2 milestone** step, not a per-slice gate. | confirmed |
| Language | ADR-05 | **Python 3.12** for this vertical (dev machine, off-hardware). | confirmed |
| Module / feature | Components; Tech stacks | New cross-vertical contract code lives under `contracts/`. A schema, an adapter interface, the oracle, and the replay sources are each their own module. | confirmed |
| Model / entity | Constraints → Frozen Contracts; ADR-06 | Domain data models are **pydantic v2** models with JSON-Schema export. The canonical runtime copies of the three frozen contracts live **here** in `contracts/`. | confirmed |
| Migration | — (no database/storage migration in the authoritative source; ADR-11 = JSONL files) | **Not applicable.** Storage is append-only JSONL; there is no migration concept. Do not invent one. | N/A |
| Test (placement) | Verification & Reviewer Runbook | Tests live close to the behavior; gap math, revision-consumes-residuals, and the planted-torque-error critic test are required. | confirmed |
| Endpoint | OUT of scope (no web UI); ADR-04 | **Not applicable.** No HTTP server / endpoints; presentation is markdown/terminal. | N/A |
| Config / secrets | ADR-03; ADR-08 | **None.** Runtime is the Claude Code subscription (ADR-08); there are no API keys, billing, or secret material (ADR-03). Do not add a secret-handling convention. | confirmed |
| Dependency / new package | ADR-06; ADR-15 | Add deps with `uv add`; pin via the lockfile. Required: `pydantic` (v2). | confirmed |
| Naming / layering | Components (Boundary rule); Oracle grounding | See Boundary rules below. | confirmed |
| CI / release | — (not decided in the authoritative source) | **Open gap.** No CI/release convention is defined in `MASTER_REQUIREMENTS.md`. (`.github/` and `DEVOPS.md` exist outside the authoritative source.) Confirm before treating any as policy. | open gap |

## Boundary rules (non-negotiable)

- **No schema is defined outside `contracts`.** Every other vertical *imports* the frozen schemas; none redefines them. *(Evidence: Components — Boundary rule.)*
- **The loop depends only on the adapter interfaces** `TelemetrySource` and `VisionSource` defined here — never on a concrete provider (`Serial`/`Camera`/`Replay`/`Synthetic`). Swapping an implementation is a config flag, not a contract change. *(Evidence: ADR-01; Integration Boundaries & Swap Paths.)*
- **Oracle information separation.** `SyntheticTelemetrySource` is a parametric hidden-ground-truth oracle (ADR-17); its true parameters are **hidden from the Generator**. The oracle config is never readable by the operator's Generator. *(Evidence: Oracle grounding & information separation; ADR-17.)*

## Frozen contracts owned here

The three frozen contracts are specified in `MASTER_REQUIREMENTS.md → Constraints → Frozen
Contracts`, frozen at milestone `m1-contracts-frozen`. Their ai-sdd-layer freeze lives at
`.ai-sdd/schemas/{task-telemetry,self-model,parts-catalog}.schema.yaml` with canonical fixtures at
`.ai-sdd/schemas/examples/`; the canonical **runtime** copies (pydantic v2) live in `contracts/`.

A **fourth contract — the control grammar** — is owned here too (added for the online-control loop;
see the [`pilot`](pilot.md) vertical). `.ai-sdd/schemas/control-command.schema.yaml` defines the
**fixed command vocabulary + command/ack envelope** the online LLM uses to drive the robot, grounded
in `robot/pi-runtime/docs/PROTOCOL.md` + `BRAIN_INTERFACE.md`. It is **draft, not yet frozen**: the
arm command vocabulary and the telemetry-vs-ack multiplex strategy are open (BRAIN_INTERFACE §3.3/§5).

## Two loops (this project has two)

1. **Offline self-model loop** (the spec's MVP): the `operator` Generator revises a readable
   *self-model/design* across generations; gap residuals collapse over Replay/Synthetic data.
2. **Online control loop** (first-class expansion): the [`pilot`](pilot.md) harness runs an online
   LLM on the Pi that reads live telemetry + vision and issues **control-grammar** commands to perform
   an open-ended task in real time, informed by the offline analysis.

Both import their schemas from here; no schema is defined outside `contracts`.
