# parts-catalog-grammar — Requirements

| Field | Value |
|---|---|
| Feature ID | F3 |
| Vertical | `contracts` |
| Root | `contracts/` |
| Stack | Python 3.12 · uv · ruff · pydantic v2 |
| Gates | `m1` contracts-frozen |
| Depends on | F1 telemetry-contract (frozen) · F2 self-model-schema (merged to main, `e961866`) |
| Unblocks | F8 generator (reads `parts_catalog.json` + checks config buildability) |
| Prerequisite done | `s0` vocabulary amendment — `4drive` dropped from `MotorAllocation` (commit `8c3bb99`, decision D6) |

---

## Goal

Freeze the **Parts Catalog Grammar** as the runtime source of truth for the finite, typed VEX V5 Classroom Starter Kit design vocabulary — the "words" the Generator (F8) may use and the **rules** for which combinations are physically buildable. Ship a deterministic `validate_config()` rules engine and a committed, machine-readable `parts_catalog.json` materialized **from** F2's `contracts.vocabulary` enums (so vocabulary and catalog can never drift), carrying the six config axes plus a `constraints` block; extend the package's emit/`validate` entrypoints **additively** (no F1/F2 regression). This bounds the Generator's search to the **60** valid sentences of the grammar and hands F9's critics a pre-filtered, structurally-legal config to attack on physics grounds. It gates `m1`.

---

## In scope

- **`contracts/src/contracts/parts_catalog.py`**, re-exported as `from contracts import PartsCatalog, validate_config`:
  - `PartsCatalog` pydantic v2 model — `schema_version: Literal["1.0"]` (locked) + one `list[Enum]` field per axis (`motor_allocation`, `arm_position`, `end_effector`, `wheel_config`, `arm_gear_ratio`, `cartridge`), each typed against the **shared `contracts.vocabulary` enums** (imported, never redefined — D1) + a typed `constraints` sub-model. `extra="forbid"`.
  - `CatalogVerdict` + `validate_config(config: SelfModelConfig) -> CatalogVerdict` — deterministic combinatorial-buildability rules engine. `CatalogVerdict = {buildable: bool, violations: list[Violation]}`; `Violation = {code: str, message: str}` (D9). Reuses F2's `SelfModelConfig` (D3).
  - **Valid-config rules:** **R1** `claw_grasper` ⇒ `motor_allocation == "2drive+1arm+1claw"` (claw needs arm-lift + claw motor = 2 manipulator motors; D7). **R2** `scoop`/`flywheel` need ≥1 manipulator motor — valid on all three allocations. **R3** `flywheel` ⇒ `cartridge == "600rpm"` (forward-only; whether 600rpm suits claw/scoop is F9's torque call — D8). `wheel_config` single-value (passes trivially).
- **`contracts/src/contracts/catalog.py`** — a `catalog` entrypoint that **writes `contracts/parts_catalog.json` directly** (mirroring F2's as-shipped `schema.py`: a `{filename: payload}` registry + `write_text`, no stdout redirect). Axis arrays generated **from the vocabulary enums** (drift-free), enriched with `schema_version` + the machine-readable `constraints` block (D4). It is a *data* document at the contracts root, distinct from `schemas/*.json`; **no** JSON Schema is emitted for `PartsCatalog` itself (D5).
- **Makefile targets** — `catalog` (`$(UV) python -m contracts.catalog`, no redirect) + `catalog-check` (`catalog` then `git diff --exit-code` on the catalog file), mirroring F2's `schema`/`schema-check`. Added to `contracts/Makefile` and delegated from the root `Makefile`.
- **`validate` entrypoint, additive** — third dispatch: round-trip `parts_catalog.json` against `PartsCatalog`, and assert each F2 `self_model_*.json` fixture's `config` is `buildable`. Existing `*.jsonl → ContractLine` (F1) and `self_model_*.json → SelfModel` (F2) paths unchanged.
- **`SelfModelConfig` export** — additively add `SelfModelConfig` to `contracts.__all__` (one line in `contracts/__init__.py`) so F8 and F3's own code import it from the package root (D11).
- **`contracts/parts_catalog.json`** — committed.
- Unit tests in `contracts/tests/`.

## Out of scope

- **Physics judgment** — torque budget, CoM/geometry, reach, and "is `600rpm` sensible for claw/scoop" (R3 forward-only). That is **F9 critic-panel**. F3 answers only structural/combinatorial buildability (D2).
- The `contracts.vocabulary` enum **value sets** — owned by F2 (D1). The one change F3 required (`drop 4drive`) already landed as `s0` (D6); no further vocabulary edits.
- The `SelfModel` shape / `config` typing (F2) — consumed, not modified (beyond the additive `__all__` export).
- Generator logic (F8), gap math (F10), critic logic (F9), diff rendering (F11).
- Any change to F1's `ContractLine`/`contract_line.json` behaviour. F3 is additive to the package.
- Booster Kit / extra parts / aesthetic vocabulary. (`scoop`/`flywheel` are first-class catalog values; their physical add-on parts are not F3's concern.)
- Adapter protocols (F4), control grammar (F19); hardware, network, PROS C++.

---

## Acceptance

Runnable from `contracts/` (or root, which delegates):

1. `make sync` exits 0.
2. `make lint` exits 0.
3. `make catalog` writes `contracts/parts_catalog.json` directly (no redirect); the file is non-empty, committed, lists the six axes with value sets **identical to** `contracts.vocabulary` (incl. `motor_allocation` **without** `4drive`), and carries `schema_version` + `constraints`. `make catalog-check` exits 0. `contract_line.json` and `self_model.json` are unchanged.
4. `make validate` exits 0 — round-trips `parts_catalog.json` against `PartsCatalog`, asserts each F2 fixture `config` is `buildable`, and still validates the F1 `*.jsonl` and F2 `self_model_*.json` fixtures.
5. `make test` exits 0, covering: catalog axes == `contracts.vocabulary` enums (drift/import-identity guard; `4drive` absent); Gen-0 Clawbot config (`2drive+1arm+1claw`, `front`, `claw_grasper`, `front_omni+rear_standard`, `7:1`, `200rpm`) → `buildable`; each planted illegal combo → `not buildable` with the matching `code` — `claw_grasper`+`2drive+2free` (`CLAW_MOTOR_BUDGET`), `claw_grasper`+`3drive+1manip` (`CLAW_MOTOR_BUDGET`), `flywheel`+`200rpm` (`FLYWHEEL_CARTRIDGE`); the legal-sentence enumeration has **exactly 60** entries; `parts_catalog.json` round-trips through `PartsCatalog`.
6. `from contracts import PartsCatalog, validate_config` (and `SelfModelConfig`) works in `uv run python` after `make sync`.
7. Root `make sync`/`validate`/`test`/`lint`/`catalog`/`catalog-check` include the parts-catalog checks and exit 0; the F1 **and** F2 suites still pass (no regression).
8. Manual reviewer check: the Gen-0 fixture config is reported buildable, and `flywheel`+`200rpm` is rejected with a human-readable reason.

---

## Constraints

- Python 3.12 (`>=3.12,<3.13`) · uv · ruff · pydantic v2 — no pip/poetry/black/flake8 (ADR-05/15/16). Build entry is **`make sync`** (routed build gate, F1 D7).
- `root: contracts/` · `ignore_folders: .venv, __pycache__, dist, .pytest_cache, captures`.
- pydantic v2 `ConfigDict` style; `model_json_schema()`/`model_dump` (ADR-06); reuse F1's `StrictModel` for strict sub-models.
- `schema_version: Literal["1.0"]` locked; bumped per-contract, independently of F1/F2 (D10).
- **Single source of vocabulary (D1):** axis values come only from `contracts.vocabulary`; F3 imports and materializes them, never hard-codes a value set. The drift-guard test enforces this.
- **Starter Kit only** (ADR-14): the PR #13 + `s0` feasibility-revised value sets.
- **Additive only** (the `s0` `4drive` removal already landed): `catalog`/`catalog-check` are new; `validate` gains a parts-catalog path without altering F1 behaviour. No hardware, no network, no schema/vocabulary defined outside `contracts`.
- **Mirror F2's as-shipped conventions:** generated JSON via a **direct-file-write** module, regenerated by `make <target>` (no redirect), drift-gated by a `*-check` target. Dev deps use PEP 735 `[dependency-groups]`.

---

## Decisions

| # | Decision | Resolution | Status |
|---|---|---|---|
| D1 | Where vocabulary lives | Import F2's `contracts.vocabulary`; catalog materialized from those enums, never redefined. | `closed` |
| D2 | F3 vs F9 boundary | F3 = deterministic combinatorial buildability (motor budget, part availability). F9 = physics (torque/CoM/geometry). | `closed` |
| D3 | `validate_config` input | Reuse F2's `SelfModelConfig` (`strict=False`, JSON strings coerce to StrEnums). | `closed` |
| D4 | Rules: code or JSON? | **Both** — machine-readable `constraints` block in `parts_catalog.json` (F8 reads it) + executable `validate_config`. | `closed` |
| D5 | Catalog file path / schema export | Data file at `contracts/parts_catalog.json`; **no** JSON Schema emitted for `PartsCatalog`. | `closed` |
| D6 | `4drive` (was O-A a) | **Removed from the vocabulary** (0 manipulator motors → no buildable config). Landed as `s0` (commit `8c3bb99`); not an F3 rule. | `closed` |
| D7 | claw allocation (was O-A b) | `claw_grasper` only on `2drive+1arm+1claw` (needs 2 manipulator motors); `2drive+2free` supports only the 1-motor effectors. | `closed` |
| D8 | cartridge rule (was O-A c) | **Forward-only:** F3 enforces `flywheel ⇒ 600rpm`. Whether 600rpm suits claw/scoop is F9's call; claw/scoop accept any cartridge. | `closed` |
| D9 | `CatalogVerdict` shape (was O-C) | `{buildable: bool, violations: [{code, message}]}` — stable machine `code` + human message, so F8/F9 can route on it. | `closed` |
| D10 | schema-version coupling (was O-D) | Per-contract independent bumps, consistent with F1/F2. | `closed` |
| D11 | export `SelfModelConfig` (was O-E) | Additively add to `contracts.__all__` (one line in F2's `__init__.py`). | `closed` |
| D12 | Slice decomposition | Two slices: **`catalog-model-and-rules`** (`PartsCatalog` + `validate_config` rules + `catalog` emit + `catalog-check` + `SelfModelConfig` export + unit tests incl. drift-guard, Gen-0-buildable, planted-illegal, enumeration==60) → **`validate-and-gates`** (`validate` extension: catalog round-trip + F2-fixture-buildable assertion + root delegation + full green / no F1/F2 regression). | `closed` |
| D13 | Design space size (was O-A d / C3) | **60 valid configs** (claw 12 + scoop 36 + flywheel 12). MASTER's stale "~10–15" reconciled to 60 in `s0`. Asserted by the enumeration test. | `closed` |

> All decisions were settled with the maintainer across the briefing turns (O-A…O-E → D6–D13); the `s0` vocabulary amendment is already committed. This requirements draft awaits explicit approval before slices + `pipeline.yaml` are emitted (planning gate).
