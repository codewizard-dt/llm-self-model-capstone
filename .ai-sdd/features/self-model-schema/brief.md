# self-model-schema — Brief

| Field | Value |
|---|---|
| Feature ID | F2 |
| Vertical | `contracts` |
| Root | `contracts/` |
| Stack | Python 3.12 · uv · ruff · pydantic v2 |
| Deps | — · shares the `contracts.vocabulary` enum atom with F3 parts-catalog-grammar (coordination, not ordering); shares a residual-key convention with F1 telemetry-contract |
| Gates | `m1` contracts-frozen |
| Unblocks | F8 generator · F9 critic-panel · F11 markdown-presenter |
| Owner | TBD |

> Sources: [MASTER_REQUIREMENTS.md](../../MASTER_REQUIREMENTS.md) (Frozen Contracts → Self-Model Schema; ADR-05/06/15/16), [llm-authored-self-model](../../wiki/knowledge/concepts/llm-authored-self-model.md) (4-layer model), [vex-v5-customization-grab-pull-throw](../../raw/research/vex-v5-customization-grab-pull-throw/index.md) and [vex-v5-starter-kit-configurations](../../raw/research/vex-v5-starter-kit-configurations/index.md) (config axes, capability envelopes). Mirrors the conventions frozen by [telemetry-contract requirements](../../.ai-sdd/features/telemetry-contract/requirements.md). Open questions O-A…O-D resolved 2026-06-23 (see Decisions D1–D5).

---

## Goal

Freeze the **Self-Model Schema** as the runtime source of truth for the versioned, human-readable robot self-model — one JSON document per generation. Ship pydantic v2 models that validate the four self-model layers (`structural` · `capability` · `predictive` · `gap_model`) plus the generation lineage (`generation` / `parent_generation`), the typed `config` selection (validated against the shared parts vocabulary), and the first-class free-text `reasoning` field, export a JSON Schema, and include fixtures for a Gen-0 authored model and a Gen-1 gap-driven revision. This is the artifact the Generator (F8) authors and revises, the Critic panel (F9) attacks pre-build, and the Markdown presenter (F11) diffs — it gates `m1` and depends on no other feature's runtime code.

---

## In scope

- **Shared vocabulary atom** — `contracts/src/contracts/vocabulary.py`: one `StrEnum` per config axis (`MotorAllocation`, `ArmPosition`, `EndEffector`, `WheelConfig`, `ArmGearRatio`, `Cartridge`) holding the finite typed value sets. **Single source of truth** imported by both `SelfModelConfig` (F2) and `parts_catalog.json` generation (F3) — defined once, never duplicated. Whichever of F2/F3 is implemented first creates the file; the other imports (see D1, Coordination C1).
- `SelfModel` pydantic v2 model in `contracts/src/contracts/self_model.py`, re-exported as `from contracts import SelfModel`. Envelope + four layers:
  - `schema_version: Literal["1.0"]` — locked; bump requires new frozen-contract approval (parallels F1).
  - `generation: int` (≥0) · `parent_generation: int | None` — `None` for Gen 0; an int for every revision. A `model_validator` enforces *gen 0 ⇒ parent is None* and *gen > 0 ⇒ parent is an int < generation*.
  - `config: SelfModelConfig` — the parts selection, each axis typed against the shared `contracts.vocabulary` enums; an out-of-vocabulary value fails to parse. F2 enforces **per-axis** legality only; whether a *combination* is buildable is F3's valid-config rules + the critic panel (D1).
  - `structural: StructuralLayer` — `parts: list[Part]` where `Part = {id: str, type: str}`; `connections: list[Connection]` where `Connection = {source: str, target: str, kind: str}` (edges use `source`/`target`, not `from`/`to`, to dodge the Python keyword). Both sub-models `extra="allow"` so the generator can extend without a schema change. May be empty in early generations (D4).
  - `capability: CapabilityLayer` — strictly typed numeric envelope: `reach_mm`, `max_grip_force_N`, `max_pull_force_N`, `com_height_mm` (all `float`, default `0`), `extra="forbid"`. Derived from catalog specs (V5 11W motor: stall 2.1 Nm, continuous ≤0.735 Nm — research-grounded).
  - `predictive: dict[str, dict[str, float | bool | str]]` — per-task predicted behavior, keyed by **free task string** (`grab`/`pull`/`throw`/…), inner block a flexible dict. Mirrors F1's free-string `task` so a new primitive never forces a schema change (D2).
  - `gap_model: dict[str, dict[str, float]]` — per-task the self-model's *learned belief about its own residual* — distinct from F1's telemetry `gap` block (the per-execution **measured** residual). **Naming invariant (D5):** `gap_model[task]` carries the **same residual keys** as the telemetry `gap` block (e.g. `force_error_N`, `duration_error_s`) so the Generator updates belief from measurement key-for-key. Same free-string task keys as `predictive`.
  - `reasoning: str` — required, non-empty (`min_length=1`). First-class audit trail: why each structural choice was made and what gap evidence drove each parameter change.
- JSON Schema export: `contracts/schemas/self_model.json` via `model_json_schema()`; committed. Config enums surface as JSON-Schema `enum` arrays (self-documenting).
- Fixtures in `contracts/fixtures/`:
  - `self_model_gen0.json` — authored Gen-0 Clawbot (`2drive+1arm+1claw`, arm `front`, `claw_grasper`, `7:1`, `200rpm`); `parent_generation: null`.
  - `self_model_gen1.json` — `parent_generation: 0`; at least one `capability`/`predictive` value moved toward observed reality, its `gap_model.grab` keys matching the telemetry `gap` keys, with `reasoning` citing the gap evidence (the revision the Generator/presenter consume).
- `contracts/Makefile` `schema` / `validate` targets extended to cover the new model + fixtures (root `Makefile` already delegates per F1 D3).
- Unit tests in `contracts/tests/`.

## Out of scope

- Authoring or revision *logic* — the Generator (F8) produces these documents; F2 only freezes the shape.
- Critic evaluation logic (F9), gap computation (F10), diff rendering (F11).
- The `parts_catalog.json` file itself and the **valid-combination rules** (which configs are buildable) — F3. F2 shares only the per-axis enum vocabulary.
- Enforcing that a config *combination* is buildable, or that `structural.parts` reference real catalog parts (F3 valid-config rules + F9 critic, not this schema).
- Telemetry contract (F1), adapter protocols (F4), control grammar (F19).
- Any robot-runtime migration; PROS C++.

---

## Acceptance

Each item is independently runnable from `contracts/`:

1. `uv sync` exits 0.
2. `make lint` exits 0 (`ruff check` + `ruff format --check`).
3. `make schema` exits 0; `contracts/schemas/self_model.json` is non-empty, committed, and lists the config axis enums as JSON-Schema `enum` arrays.
4. `make validate` exits 0 against `self_model_gen0.json` and `self_model_gen1.json`.
5. `make test` exits 0, covering:
   - round-trip parse of both fixtures;
   - Gen-0 fixture with `parent_generation: 0` → `ValidationError`; Gen-1 fixture with `parent_generation: null` → `ValidationError`; `parent_generation >= generation` → `ValidationError`;
   - empty `reasoning` (`""`) → `ValidationError`;
   - missing required field (`config`, `capability`, `generation`) → `ValidationError`;
   - an out-of-vocabulary `config` value (e.g. `cartridge: "999rpm"`) → `ValidationError`;
   - `SelfModelConfig` field types resolve to the shared `contracts.vocabulary` enums (import-identity check — a redefined copy fails the test);
   - `predictive` / `gap_model` accept an arbitrary task key (e.g. `"score"`) without error;
   - extra field on a strict sub-model (`SelfModelConfig` / `CapabilityLayer`) → `ValidationError`.
6. `from contracts import SelfModel` works in `uv run python` after `uv sync`.
7. Root `make validate` / `make test` / `make lint` include the self-model checks and exit 0.
8. A Gen-1 → Gen-0 diff of the two fixtures shows a changed `capability`/`predictive` value, a `gap_model.grab` block whose keys match F1's telemetry `gap` keys, and a `reasoning` string referencing the gap evidence (manual reviewer check; underpins the demo's "self-knowledge improving in prose" moment).

---

## Constraints

- Python 3.12 · uv (`uv sync` / `uv add` / `uv run`) · ruff · pydantic v2 — no pip/poetry/black/flake8 (ADR-05, ADR-15, ADR-16).
- `root: contracts/` · `ignore_folders: .venv, __pycache__, dist, .pytest_cache, captures`.
- pydantic v2 only: `model_config = ConfigDict(...)`; no v1 compat shim. JSON Schema via `model_json_schema()` (ADR-06).
- `schema_version: Literal["1.0"]` is locked.
- Strict sub-models (`SelfModelConfig`, `CapabilityLayer`) use `extra="forbid"`; `Part` / `Connection` use `extra="allow"`; the top-level `SelfModel` may use `extra="allow"` for forward-compatibility (consistent with F1's `ContractLine`).
- Config axis values come **only** from `contracts.vocabulary`; no axis value sets are redefined in F2.
- Task keys in `predictive` / `gap_model` are free strings, never an enum — adding a primitive must not require a schema change (consistent with F1's `task: str`).
- No hardware access, no network, no schema defined outside `contracts`.

---

## Decisions (closed)

| # | Decision | Resolution |
|---|---|---|
| D1 | `config` value validation (was O-A) | **Shared per-axis enum vocabulary.** `config` is validated against `StrEnum`s in `contracts/src/contracts/vocabulary.py` — the single source both F2 and F3 import (no duplication, no drift). F2 enforces per-axis legality; combination-legality is F3 + the critic panel. |
| D2 | `predictive` / `gap_model` inner typing | Flexible dicts keyed by free task string (typed core / flexible edges), mirroring F1 D2. No per-task sub-models. |
| D3 | `capability` field set | Frozen to the four contract fields (`reach_mm`, `max_grip_force_N`, `max_pull_force_N`, `com_height_mm`), strict (`extra="forbid"`). Adding a capability is a deliberate contract change. |
| D4 | `structural` shape (was O-B) | **Lightweight typed.** `Part{id,type}` + `Connection{source,target,kind}`, both `extra="allow"`; edges named `source`/`target` to avoid the `from` keyword. Empty lists allowed early. Gives F9's CoM/geometry critic a traversable graph at near-zero cost. |
| D5 | `gap_model` vs telemetry `gap` (was O-D) | **Keep both names** (frozen in MASTER + concept lineage; distinct concepts). Invariant: `gap_model[task]` uses the **same residual keys** as F1's `gap` block. F1 is still in progress; its only required updates are a docstring on `ContractLine.gap` (measured residual; belief counterpart is `gap_model`) and fixture gap keys that match the `gap_model` keys. No shared residual-key enum (would contradict F1 D2's flexible `gap` dict). |
| D6 | Gen-1 fixture provenance (was O-C) | **Hand-authored** deterministic example. The real generated revision lands at `m2` via F8 (generator); F2 only needs a valid, illustrative revision. |

---

## Milestones

| id | Validates | Mode | Owner |
|---|---|---|---|
| `s1` vocabulary + model | `contracts.vocabulary` enums exist; `SelfModel` + sub-models parse; lineage / `reasoning` / out-of-vocabulary validators fire; `make schema` emits committed JSON Schema with enum arrays | automated (`make test`, `make schema`) | TBD |
| `s2` fixtures + gates | Gen-0 + Gen-1 fixtures validate; Gen-1 shows a gap-driven revision with `gap_model` keys aligned to F1; root + contracts `make validate`/`test`/`lint` green | automated (`make validate`) + manual diff check (Acceptance 8) | TBD |
| (gate) `m1` contracts-frozen | All contracts (F1–F4, F19) load and round-trip cleanly | manual — human gate | TBD |

---

## Coordination items (cross-feature; resolved approach, just needs sequencing)

- **C1 — shared vocabulary atom (with F3).** `contracts.vocabulary` is created by whichever of F2/F3 is implemented first; the other imports it. Recommended: F3 owns the file's *content* (it's the parts-catalog grammar's vocabulary), but the file lands with whichever feature is built first. No hard ordering between F2 and F3.
- **C2 — F1 touch-ups (with telemetry-contract).** D5's naming invariant requires two small edits folded into F1's remaining slices (F1 is not yet frozen): a docstring on `ContractLine.gap`, and `session_example.jsonl` gap keys that become the canonical residual names F2's `gap_model` fixtures reuse.
