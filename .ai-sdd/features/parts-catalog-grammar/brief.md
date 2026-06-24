# parts-catalog-grammar — Brief

| Field | Value |
|---|---|
| Feature ID | F3 |
| Vertical | `contracts` |
| Root | `contracts/` |
| Stack | Python 3.12 · uv · ruff · pydantic v2 |
| Deps | F1 telemetry-contract **frozen** · F2 self-model-schema **landed** — F3 **imports** the `contracts.vocabulary` enums F2 creates (C1) and reuses F2's `SelfModelConfig` as the `validate_config` input. MASTER lists F3 deps as `—`, but the shared-vocabulary atom (C1) makes **F2 a hard prerequisite**. |
| Gates | `m1` contracts-frozen |
| Unblocks | F8 generator (deps F2, F3, F10) — reads `parts_catalog.json` + checks config buildability |
| Owner | TBD |

> Sources: [MASTER_REQUIREMENTS.md](../../../MASTER_REQUIREMENTS.md) (Frozen Contracts → Parts Catalog Grammar; Components → "Parts catalog grammar `(contracts)` — owns `parts_catalog.json`, the finite typed design vocabulary (~10–15 valid configs)"; ADR-05/06/14/15/16), [typed-assembly-grammar](../../../wiki/knowledge/concepts/typed-assembly-grammar.md) (grammar = vocabulary + rules; corrected Starter-Kit-only value sets; 96 raw slots → ~10–15 valid), [vex-v5-starter-kit-configurations](../../../raw/research/vex-v5-starter-kit-configurations/index.md) (motor budget, what the kit can/can't build, recommended catalog JSON). Builds on the **landed** F1 + F2 contracts package — mirror its conventions exactly: `make sync` build entry (the routed build gate, F1 D7), `StrictModel` base, `Literal["1.0"]` schema lock, single-source `schema`/`validate` entrypoints extended **additively** (F2's *as-shipped* `schema.py` is a registry that **writes files directly** + a new `schema-check` drift gate — F3 mirrors this, not the stdout-redirect in F2's brief), `contracts.vocabulary` as the one place axis values live.

---

## Goal

Freeze the **Parts Catalog Grammar** as the runtime source of truth for the finite, typed VEX V5 Classroom Starter Kit design vocabulary — the "words" the Generator (F8) may use and the **rules** for which combinations are physically buildable. Ship (1) a committed, machine-readable `parts_catalog.json` materialized **from** F2's `contracts.vocabulary` enums (so vocabulary and catalog can never drift), carrying the six config axes from MASTER's frozen block plus a `constraints` block expressing combination legality; (2) a deterministic `validate_config()` rules engine in `contracts/src/contracts/parts_catalog.py` that, given a config (F2's `SelfModelConfig`), returns **buildable / not-buildable + human-readable reasons**; and (3) the extension of the package's `catalog`/`validate` entrypoints **additively** (no F1/F2 regression). This is what bounds the Generator's search to the ~10–15 valid sentences of the grammar and gives F9's critics a pre-filtered, structurally-legal config to attack on physics grounds. It gates `m1`.

---

## In scope

- **`parts_catalog.py`** in `contracts/src/contracts/`, re-exported as `from contracts import PartsCatalog, validate_config`:
  - `PartsCatalog` pydantic v2 model — `schema_version: Literal["1.0"]` (locked, parallels F1/F2) + one `list[Enum]` field per axis (`motor_allocation`, `arm_position`, `end_effector`, `wheel_config`, `arm_gear_ratio`, `cartridge`), each typed against the **shared `contracts.vocabulary` enums F2 owns** (imported, never redefined — C1) + a typed `constraints` sub-model holding the machine-readable valid-config rules. `extra="forbid"`.
  - `validate_config(config: SelfModelConfig) -> CatalogVerdict` — the deterministic combinatorial-buildability rules engine. Returns `{buildable: bool, violations: list[str]}` (each violation a human-readable reason, e.g. `"end_effector 'claw_grasper' requires motor_allocation '2drive+1arm+1claw' (claw is motorized); got '4drive'"`). Reuses F2's `SelfModelConfig` so the Generator has one call: author a `SelfModel`, then ask the catalog if its `config` is buildable.
  - **Proposed valid-config rules** (research-grounded; the precise set finalized at planning per O-A):
    - Motor budget = 4. `claw_grasper` is **motorized** (needs both an arm motor and a claw motor) ⇒ requires `motor_allocation == "2drive+1arm+1claw"`.
    - `arm_position != "absent"` ⇒ the allocation must reserve ≥1 manipulator motor (`2drive+1arm+1claw`, `3drive+1manip`, or `2drive+2free`); `4drive` ⇒ `arm_position == "absent"`.
    - `arm_position == "absent"` ⇒ `end_effector == "none"` (no arm to mount an effector).
    - `motor_allocation == "4drive"` ⇒ `arm_position == "absent"` **and** `end_effector == "none"`.
    - `motor_allocation == "3drive+1manip"` ⇒ one manipulator motor only ⇒ `end_effector ∈ {bare_arm, none}` (cannot also power a claw).
    - `wheel_config`/`cartridge` are single-value axes (Starter-Kit-only); any value passes per-axis but the catalog still enumerates exactly one.
- **`parts_catalog.json`** — committed, emitted by a new `catalog` entrypoint (`contracts/src/contracts/catalog.py`) that **writes the file directly** (mirroring F2's *as-shipped* `schema.py`: a `{filename: payload}` registry + `write_text`, **not** a stdout redirect). The six axis arrays are generated **from the vocabulary enums** (their values, in declared order) so the file is a faithful, drift-free materialization of MASTER's frozen Parts Catalog Grammar block, enriched with `schema_version` + the `constraints` block. `parts_catalog.json` is a *data* document, distinct from the JSON-Schema files in `schemas/`. The Generator (F8) reads this file directly.
- **`catalog` + `catalog-check` Makefile targets** — `catalog: $(UV) python -m contracts.catalog` (no redirect); `catalog-check: catalog` then `git diff --exit-code` on the catalog file (mirrors F2's new `schema-check` drift gate). `catalog` is added to both `contracts/Makefile` and the root `Makefile` (which today delegates `sync`/`validate`/`test`/`lint`/`schema`).
- **`validate` entrypoint, extended additively** — add a third dispatch: round-trip `parts_catalog.json` against `PartsCatalog`, **and** assert each F2 self-model fixture's `config` block is `buildable` under `validate_config`. The existing `*.jsonl → ContractLine` (F1) and `self_model_*.json → SelfModel` (F2) paths must keep passing unchanged.
- **Tests** in `contracts/tests/`:
  - the catalog's axis arrays equal the `contracts.vocabulary` enum value sets (**drift guard** — a redefined/forked copy fails);
  - the Gen-0 Clawbot config (`2drive+1arm+1claw`, arm `front`, `claw_grasper`, `7:1`, `200rpm`, `front_omni+rear_standard`) → `buildable: True`;
  - planted illegal combos each → `buildable: False` with a matching reason: `4drive` + arm `front`; `claw_grasper` + `3drive+1manip`; `claw_grasper` + arm `absent`;
  - the full enumeration of legal sentences over the grammar has the expected count (**~10–15** per MASTER / research — exact number pinned at O-A);
  - `parts_catalog.json` round-trips through `PartsCatalog`.

## Out of scope

- **Physics judgment** — torque budget, CoM/geometry, reach feasibility. F3 answers only *"does this combination map to real, assemblable Starter-Kit parts?"* (deterministic, combinatorial). Whether a buildable config is *physically sound* is **F9 critic-panel**. MASTER's "F3's valid-config rules **+** the critic panel" — F3 is the structural pre-filter, F9 the physics gate.
- The `contracts.vocabulary` enum **value sets** — owned and created by **F2** (C1). F3 imports them; redefining them here is a hard violation.
- The `SelfModel` shape and its per-axis `config` typing (F2). F3 consumes `SelfModelConfig`; it does not modify it.
- Generator authoring/mutation logic (F8), gap math (F10), critic logic (F9), diff rendering (F11).
- Any change to F1's `ContractLine`/`contract_line.json` or F2's `SelfModel`/`self_model.json` outputs. F3 is **strictly additive** to the package.
- Booster Kit / extra cartridges / flywheel / scoop / aesthetic vocabulary expansions (documented in [typed-assembly-grammar](../../../wiki/knowledge/concepts/typed-assembly-grammar.md) but out of MVP scope per ADR-14 — Starter Kit only).
- Adapter protocols (F4), control grammar (F19); hardware, network, PROS C++.

---

## Acceptance

Each item is independently runnable from `contracts/` (or repo root, which delegates):

1. `make sync` exits 0.
2. `make lint` exits 0 (`ruff check` + `ruff format --check`).
3. `make catalog` exits 0 and writes `contracts/parts_catalog.json` directly (no stdout redirect); the file is non-empty, committed, lists all six config axes with value sets **identical to** `contracts.vocabulary`, and matches MASTER's frozen Parts Catalog Grammar block (plus `schema_version` + `constraints`). `make catalog-check` exits 0 (committed file is current). `contract_line.json` and `self_model.json` are **unchanged** (no F1/F2 regression).
4. `make validate` exits 0 — round-trips `parts_catalog.json` against `PartsCatalog`, asserts each F2 self-model fixture `config` is `buildable`, **and** still validates the F1 `*.jsonl` and F2 `self_model_*.json` fixtures.
5. `make test` exits 0, covering: catalog axes == `contracts.vocabulary` enums (drift/import-identity guard); Gen-0 Clawbot config → `buildable`; each planted illegal combo → `not buildable` with a matching human-readable reason; the enumerated legal-sentence count equals the agreed value (~10–15, O-A); `parts_catalog.json` round-trips through `PartsCatalog`.
6. `from contracts import PartsCatalog, validate_config` works in `uv run python` after `make sync`.
7. Root `make sync`/`validate`/`test`/`lint`/`catalog` (delegating into `contracts/`) all include the parts-catalog checks and exit 0; the F1 **and** F2 suites still pass (no regression). *(`make sync` is the routed build gate — F1 D7 / F2 fixtures-and-gates convention.)*
8. Manual reviewer check: the Gen-0 fixture config is reported buildable, and an obviously-illegal config (`4drive` with a front claw) is rejected with a reason a human can read — the structural pre-filter that hands F9 only legal configs and gives the Generator a cheap buildability guard.

---

## Constraints

- Python 3.12 (`requires-python = ">=3.12,<3.13"`) · uv · ruff · pydantic v2 — no pip/poetry/black/flake8 (ADR-05, ADR-15, ADR-16). Build entry is **`make sync`** (the F1 convention + routed build gate per F1 D7), not bare `uv sync`.
- `root: contracts/` · `ignore_folders: .venv, __pycache__, dist, .pytest_cache, captures`.
- pydantic v2 only: `model_config = ConfigDict(...)`; JSON via `model_json_schema()` / `model_dump` (ADR-06). Reuse F1's `StrictModel` base for strict sub-models.
- `schema_version: Literal["1.0"]` is locked.
- **Single source of vocabulary (C1):** every axis value comes **only** from `contracts.vocabulary`; F3 imports the enums and materializes them — it never re-lists or hard-codes a value set. The drift-guard test enforces this.
- **Starter Kit only** (ADR-14): the value sets are the *corrected* Starter-Kit-only ones (single `wheel_config`, single `cartridge`); no Booster Kit / add-on options.
- **Additive only:** `catalog` is new; `validate` gains a parts-catalog path without altering F1's `ContractLine` / F2's `SelfModel` behaviour or their committed schema outputs. No hardware, no network, no schema or vocabulary defined outside `contracts`.
- **Mirror F2's *as-shipped* entrypoint conventions:** generated JSON is written by a **direct-file-write** module (à la `schema.py`), regenerated by `make <target>` (no redirect), and drift-gated by a `*-check` target (`git diff --exit-code`). Dev dependencies use **PEP 735 `[dependency-groups]`** (F2 migrated to this in `1266a4d`), not `[project.optional-dependencies]`.

---

## Decisions (proposed — to confirm at planning)

| # | Decision | Proposed resolution |
|---|---|---|
| D1 | Where vocabulary lives | **Import from F2's `contracts.vocabulary` (C1).** F3 never redefines value sets; `parts_catalog.json` is materialized from those enums. F2 is therefore a hard prerequisite despite MASTER's `—` dep. |
| D2 | F3 vs F9 boundary | **F3 = deterministic combinatorial buildability** (motor budget, part availability, kit constraints). **F9 = physics judgment** (torque/CoM/geometry). MASTER's "valid-config rules **+** critic panel" splits exactly here. |
| D3 | `validate_config` input | **Reuse F2's `SelfModelConfig`** so the Generator authors a `SelfModel` then asks one buildability question. F2 ships it in `contracts.self_model` but does **not** re-export it — import `from contracts.self_model import SelfModelConfig`, or additively add it to `contracts.__all__` (O-E). It uses `strict=False`, so raw JSON string axis values coerce into the StrEnums. |
| D4 | Rules: code-only or in JSON? | **Both.** `parts_catalog.json` carries a machine-readable `constraints` block (so F8 sees what's legal by reading one file), and `parts_catalog.py` carries the executable `validate_config` the block documents. |
| D5 | Catalog file location | **Proposed `contracts/parts_catalog.json`** (data vocabulary the Generator reads), distinct from `contracts/schemas/*.json` (JSON-Schema exports). Confirm at O-B. |

---

## Milestones (optional)

| id | Validates | Mode | Owner |
|---|---|---|---|
| `s1` catalog model + rules | `PartsCatalog` model imports the `contracts.vocabulary` enums; `validate_config` rules engine returns buildable/not + reasons; drift-guard, Gen-0-buildable, and planted-illegal-combo tests fire; `catalog` entrypoint emits committed `parts_catalog.json` with the six axes + `constraints` block, `contract_line.json`/`self_model.json` unchanged | automated (`make test`, `make catalog`) | TBD |
| `s2` fixtures + gates | `validate` extension round-trips `parts_catalog.json` and asserts F2 fixture configs are buildable; enumerated-legal-config count matches the agreed value; root + contracts `make sync`/`validate`/`test`/`lint`/`catalog` green; F1 **and** F2 suites still passing | automated (`make validate`) + manual buildability check (Acceptance 8) | TBD |
| (gate) `m1` contracts-frozen | All contracts (F1–F4, F19) load and round-trip cleanly | manual — human gate | TBD |

---

## Open questions

- **O-A — exact valid-config rule set + canonical count.** The proposed rules (In scope) yield ~10–15 legal sentences (96 raw slots per research), but three edges need a decision: (a) when `arm_position == "absent"`, is `arm_gear_ratio` a meaningless-but-required enum value, or do we canonicalize it so the legal-config count is clean? (b) does `2drive+2free` admit an arm (a free motor *as* the arm motor) or only non-arm free uses? (c) is `claw_grasper` strictly `2drive+1arm+1claw`-only, or also reachable from `2drive+2free`? Finalize the rule set and the asserted count at planning, grounded in [vex-v5-starter-kit-configurations](../../../raw/research/vex-v5-starter-kit-configurations/index.md).
- **O-B — catalog file path + JSON-Schema export.** Confirm `contracts/parts_catalog.json` (D5) vs `contracts/schemas/parts_catalog.json`; decide whether to *also* emit a JSON Schema for `PartsCatalog` (consistency with F1/F2's `schemas/*.json`) or only the data file.
- **O-C — `CatalogVerdict` shape.** `{buildable: bool, violations: list[str]}` is proposed; confirm whether F8/F9 want structured violation codes (machine-routable) in addition to human-readable strings.
- **O-D — schema-version coupling.** F1, F2, and F3 all lock `schema_version: "1.0"` independently. Confirm they bump independently (per-contract) rather than as one repo-wide version, consistent with F1/F2 freeze handling.
- **O-E — export `SelfModelConfig`?** F3 needs it as the `validate_config` input, but F2 exports only `SelfModel`. Decide: import from the `contracts.self_model` submodule, or additively add `SelfModelConfig` to `contracts.__all__` (cleaner public API for F8). Recommend the latter (one-line additive change to F2's `__init__.py`).
