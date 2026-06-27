# ai-sdd Conventions - `self_model_generator` vertical

> **Seed mode.** Bootstrapped from [`MASTER_REQUIREMENTS.md`](../../MASTER_REQUIREMENTS.md) (the
> decision-closed authoritative source), not from code evidence. Each row cites its section. Rows
> marked `open gap` have no decision in the source and must be confirmed.

**Vertical.** `self_model_generator` - the **offline self-model loop** (LLM
authoring/critique/replay/presentation): the Generator, the 3-critic panel, the gap analyzer, the
markdown presenter, and the demo replay. Root: `self_model_generator/`. Python package:
`self_model_generator`. Project name: `self-model-generator`. Owner: **TBD**.

> **Naming boundary.** Do not create a repo-root `operator/` vertical, `self_model_operator` Python
> package, or `self-model-operator` project. The name `operator` is reserved for the live
> robot-control operator under `robot/ros2-runtime/src/vexy_ros/operator` and its ROS topics/docs.

> **Scope boundary vs `pilot`.** `self_model_generator` is the **offline, generational** loop - it
> revises a readable self-model/design over recorded/synthetic data (`make demo`). The **online,
> real-time** control loop (an LLM on the Pi piloting the robot via the control grammar) is a
> separate vertical, [`pilot`](pilot.md). Keep them distinct:
> `self_model_generator` writes design documents; `pilot` issues commands.

## Discovery Record

| Change type | Evidence (MASTER_REQUIREMENTS section) | Convention | Status |
|---|---|---|---|
| Build / install | Tech stacks (Shared tooling); ADR-15 | `uv` (`uv sync` / `uv add` / `uv run`). No pip/poetry/conda. Reviewer baseline: `uv sync`. | confirmed |
| Test | Verification & Reviewer Runbook | `make test` - gap math, revision-consumes-residuals, critic flags planted torque error. | confirmed |
| Lint / format | ADR-16 | `ruff` only; `make lint` = `ruff check` + `ruff format --check`. | confirmed |
| Validate | ADR-06; Verification & Reviewer Runbook | `make validate` - pydantic fixtures vs frozen schemas (schemas imported from `contracts`). | confirmed |
| Run commands | Verification & Reviewer Runbook | `make demo` = deterministic Gen 0 -> Gen 2 replay; it is the **m2 milestone** step, not a per-slice gate. | confirmed |
| Language | ADR-05 | **Python 3.12** (dev machine). | confirmed |
| Module / feature | Components | Generator, Critic panel (3 critics), Gap analyzer, Markdown Presenter, Demo Replay are modules under `self_model_generator/`. | confirmed |
| Model / entity | Components (Boundary rule) | **No schema is defined here.** Import the frozen schemas from `contracts`. | confirmed |
| Config / secrets | ADR-08; ADR-03 | **None.** Claude Code subscription runtime; no keys/billing. | confirmed |
| Dependency / new package | ADR-15 | `uv add`; pin via lockfile. | confirmed |
| Naming / layering | Components (Boundary rule); Vertical roots | See Boundary rules. | confirmed |

## Boundary rules (non-negotiable)

- **No root `operator/` for offline LLM work.** Offline self-modeling code belongs in
  `self_model_generator/` only. Use `operator` only for live robot-control code under
  `robot/ros2-runtime/src/vexy_ros/operator`.
- **Information separation (the Generator).** The Generator (F8) reads **only**
  `parts_catalog.json` + prior gap residuals. It **never** reads the oracle config or the oracle's
  hidden parameters. Gap-tightening must come from the self-model converging on the hidden truth, not
  from steering.
- **No schema defined here** - import from `contracts`.
- **Loop depends on adapter interfaces, never a concrete provider.**
- **3 critics, fixed set:** physics validity, torque budget, CoM/geometry; stateless, pass/flag +
  rationale.
- **LLM runtime:** Claude Code interactive for authoring; cached transcripts replay deterministically
  for `make demo`.
