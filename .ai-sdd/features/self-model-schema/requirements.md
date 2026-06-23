# self-model-schema — Requirements

| Field | Value |
|---|---|
| Feature ID | F2 |
| Vertical | `contracts` |
| Root | `contracts/` |
| Stack | Python 3.12 · uv · ruff · pydantic v2 |
| Gates | `m1` contracts-frozen |
| Depends on | F1 telemetry-contract (landed/frozen) |
| Unblocks | F8 generator · F9 critic-panel · F11 markdown-presenter |
| Creates for F3 | `contracts.vocabulary` enum atom |

---

## Goal

Freeze the **Self-Model Schema** as the runtime source of truth for the versioned, human-readable robot self-model — one JSON document per generation. Ship pydantic v2 models that validate the four self-model layers (`structural` · `capability` · `predictive` · `gap_model`) plus the generation lineage (`generation` / `parent_generation`), the typed `config` selection (validated against a new shared parts vocabulary), and the first-class free-text `reasoning` field; extend the contracts package's `schema` and `validate` entrypoints **additively** (no F1 regression); and ship a Gen-0 authored fixture and a Gen-1 gap-driven revision fixture. This is the artifact the Generator (F8) authors and revises, the Critic panel (F9) attacks pre-build, and the Markdown presenter (F11) diffs.

---

## In scope

- **Shared vocabulary atom** — `contracts/src/contracts/vocabulary.py`: one `StrEnum` per config axis (`MotorAllocation`, `ArmPosition`, `EndEffector`, `WheelConfig`, `ArmGearRatio`, `Cartridge`). F2 creates it (F1 frozen, F3 not yet built); re-exported from `contracts/__init__.py`. Value sets seeded from MASTER_REQUIREMENTS Parts Catalog Grammar.
- `SelfModel` pydantic v2 model in `contracts/src/contracts/self_model.py`, re-exported as `from contracts import SelfModel`:
  - `schema_version: Literal["1.0"]` (locked) · `generation: int` (≥0) · `parent_generation: int | None`, with a `model_validator`: gen 0 ⇒ parent None; gen > 0 ⇒ int < generation.
  - `config: SelfModelConfig` — six axes typed against `contracts.vocabulary` enums; `extra="forbid"`.
  - `structural: StructuralLayer` — `parts: list[Part]` (`Part{id,type}`), `connections: list[Connection]` (`Connection{source,target,kind}`); sub-models `extra="allow"`; empty lists allowed.
  - `capability: CapabilityLayer` — `reach_mm`, `max_grip_force_N`, `max_pull_force_N`, `com_height_mm` (float, default 0); `extra="forbid"`.
  - `predictive: dict[str, dict[str, float | bool | str]]` — free task-string keys, flexible inner dict.
  - `gap_model: dict[str, dict[str, float]]` — free task-string keys; `gap_model[task]` reuses F1's frozen `gap` residual keys (`force_error_N`, `duration_error_s` for grab).
  - `reasoning: str` — required, `min_length=1`.
- **`schema` entrypoint + freeze gate** — `make schema` regenerates `contracts/schemas/self_model.json` (config enums → JSON-Schema `enum` arrays) and `schemas/contract_line.json` from the pydantic models (single source of truth). A freshness gate (`make schema` then `git diff --exit-code schemas/`), wired into `make validate`/m1, asserts the committed schemas equal the generated output — so `contract_line.json` is byte-stable by construction.
- **`validate` entrypoint, additive** — add a `fixtures/self_model_*.json → SelfModel` dispatch beside the existing `fixtures/*.jsonl → ContractLine` path.
- Fixtures: `contracts/fixtures/self_model_gen0.json` (Gen-0 Clawbot, `parent_generation: null`) and `self_model_gen1.json` (`parent_generation: 0`, a revised `capability`/`predictive` value, `gap_model.grab` keyed like F1, `reasoning` citing gap evidence).
- Unit tests in `contracts/tests/`.

## Out of scope

- Authoring/revision logic (F8); critic logic (F9); gap computation (F10); diff rendering (F11).
- The `parts_catalog.json` file and valid-combination rules (F3) — F2 ships only the per-axis enum vocabulary F3 imports.
- Enforcing config-combination buildability or that `structural.parts` are real catalog parts.
- Any change to F1's frozen `ContractLine`/`MotorApiSample`/`VisionBlock` or the `contract_line.json` output — F2 is strictly additive.
- Adapter protocols (F4), control grammar (F19); robot-runtime migration; PROS C++.

---

## Acceptance

Runnable from `contracts/` (or root, which delegates):

1. `make sync` exits 0.
2. `make lint` exits 0.
3. `make schema` regenerates `schemas/self_model.json` (non-empty, config enums as `enum` arrays) and `schemas/contract_line.json` from the models; both are committed and the freshness gate (`make schema` + `git diff --exit-code schemas/`) passes — committed == generated, `contract_line.json` byte-stable.
4. `make validate` exits 0 — `self_model_gen0.json` + `self_model_gen1.json` against `SelfModel`, existing `*.jsonl` against `ContractLine`.
5. `make test` exits 0, covering: round-trip both fixtures; Gen-0 with `parent_generation:0` → error; Gen-1 with `parent_generation:null` → error; `parent_generation >= generation` → error; empty `reasoning` → error; missing `config`/`capability`/`generation` → error; out-of-vocabulary `config` value → error; `SelfModelConfig` fields resolve to the shared `contracts.vocabulary` enums (import-identity); `predictive`/`gap_model` accept an arbitrary task key; extra field on a strict sub-model → error.
6. `from contracts import SelfModel` (and the vocabulary enums) works in `uv run python` after `make sync`.
7. Root `make validate`/`test`/`lint`/`schema` include self-model checks and exit 0; F1 suite still passes.
8. Gen-1 → Gen-0 fixture diff shows a changed `capability`/`predictive` value, a `gap_model.grab` block keyed like F1's `gap`, and `reasoning` referencing the gap evidence (manual reviewer check).

---

## Constraints

- Python 3.12 (`>=3.12,<3.13`) · uv · ruff · pydantic v2 — no pip/poetry/black/flake8 (ADR-05/15/16). Build entry is **`make sync`** (F1 convention).
- `root: contracts/` · `ignore_folders: .venv, __pycache__, dist, .pytest_cache, captures`.
- pydantic v2 `ConfigDict` style; `model_json_schema()` (ADR-06); reuse F1's `StrictModel` base for strict sub-models.
- `schema_version: Literal["1.0"]` locked. Strict sub-models `extra="forbid"`; `Part`/`Connection` `extra="allow"`; `SelfModel` may use `extra="allow"`.
- Config axis values come only from `contracts.vocabulary`. `predictive`/`gap_model` task keys are free strings.
- **Additive only**: `schema`/`validate` gain self-model paths without altering F1 behaviour. No hardware, no network, no schema outside `contracts`.

---

## Decisions

| # | Decision | Resolution | Status |
|---|---|---|---|
| D1 | `config` value validation | **Shared per-axis enum vocabulary** in `contracts/vocabulary.py`, the single source F2 + F3 use. F2 enforces per-axis legality only; combination-legality is F3 + critic. | `closed` |
| D2 | `predictive` / `gap_model` inner typing | Flexible dicts keyed by free task string (typed core / flexible edges, mirrors F1 D2). No per-task sub-models. | `closed` |
| D3 | `capability` field set | Frozen to the four contract fields, strict (`extra="forbid"`). | `closed` |
| D4 | `structural` shape | Lightweight typed `Part{id,type}` + `Connection{source,target,kind}`, `extra="allow"`; edges `source`/`target` (avoid `from` keyword); empty lists allowed. | `closed` |
| D5 | `gap_model` vs telemetry `gap` | Keep both names; invariant: `gap_model[task]` reuses F1's frozen `gap` residual keys. F1 frozen — no F1 changes. No shared residual-key enum (would break F1 D2's flexible `gap`). | `closed` |
| D6 | Gen-1 fixture provenance | Hand-authored deterministic example; real generated revision lands at `m2` via F8. | `closed` |
| D7 | Slice decomposition | Two slices: **`vocabulary-and-model`** (vocab atom + `SelfModel` + validators + `schema` emit + tests) → **`fixtures-and-gates`** (Gen-0/Gen-1 fixtures + `validate` extension + root-delegation green). | `closed` |
| D8 | `schema` generation + freeze gate | `make schema` is the **single generator** (source of truth = the pydantic models): it regenerates every `schemas/*.json` in place. Files stay **committed** (reviewable, diffable — the human-readable face of the freeze), and a **freshness gate** wired into `make validate`/m1 runs `make schema` then `git diff --exit-code schemas/`, so committed == generated and `contract_line.json` is byte-stable by construction. Emit mechanism (refactor `schema.py` to write both files, or a second emitter) is the architect's choice. | `closed` |
