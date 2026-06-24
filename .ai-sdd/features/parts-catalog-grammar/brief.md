# parts-catalog-grammar — Brief

| Field | Value |
|---|---|
| Feature ID | F3 |
| Vertical | `contracts` |
| Root | `contracts/` |
| Stack | Python 3.12 · uv · ruff · pydantic v2 |
| Deps | F1 telemetry-contract **frozen** · F2 self-model-schema **merged to main** (`e961866`) — F3 **imports** the `contracts.vocabulary` enums F2 owns (C1) and reuses F2's `SelfModelConfig`. Plus a small **F2 vocabulary amendment** F3 triggers (drop `4drive` — see Coordination C2). |
| Gates | `m1` contracts-frozen |
| Unblocks | F8 generator (deps F2, F3, F10) — reads `parts_catalog.json` + checks config buildability |
| Owner | TBD |
| Worktree | `/Users/215eight/Dev/galabs/llm-self-model-capstone-parts-catalog-grammar` · branch `parts-catalog-grammar` off `main` |

> Sources: [MASTER_REQUIREMENTS.md](../../../MASTER_REQUIREMENTS.md) (Frozen Contracts → Parts Catalog Grammar, **revised 2026-06-23 PR #13**; Components → "Parts catalog grammar `(contracts)` — owns `parts_catalog.json`"; ADR-05/06/14/15/16), [typed-assembly-grammar](../../../wiki/knowledge/concepts/typed-assembly-grammar.md) (grammar = vocabulary + rules; flywheel⇒600rpm; passive scoop frees a motor), [vex-v5-starter-kit-configurations](../../../raw/research/vex-v5-starter-kit-configurations/index.md) (4-motor budget, kit limits), [vex-launch-disc-parts](../../../raw/research/vex-launch-disc-parts/index.md) (flywheel requires the 6:1/600rpm cartridge; Option A repurposes the arm motor), [clawbot-scoop-replacement](../../../raw/research/clawbot-scoop-replacement/index.md) (passive scoop, no motor, arm-lift motor retained). Mirrors F1+F2 conventions: `make sync` build entry (routed gate, F1 D7), `StrictModel` base, `Literal["1.0"]` lock, registry **direct-file-write** emitters + `*-check` drift gates (F2's as-shipped `schema.py`/`schema-check`), `contracts.vocabulary` as the one place axis values live.

> **Vocabulary as of this brief.** PR #13 + the F3 decisions below set the frozen axes to: `motor_allocation ∈ {2drive+1arm+1claw, 2drive+2free, 3drive+1manip}` (**`4drive` removed** — D6/C2), `arm_position ∈ {front, rear}`, `end_effector ∈ {claw_grasper, scoop, flywheel}`, `wheel_config ∈ {front_omni+rear_standard}`, `arm_gear_ratio ∈ {7:1, 1:1}`, `cartridge ∈ {100rpm, 200rpm, 600rpm}`. Open questions O-A…O-E are **resolved** (Decisions D6–D12). The buildable design space is **60 configs** (see Design Space).

---

## Goal

Freeze the **Parts Catalog Grammar** as the runtime source of truth for the finite, typed VEX V5 Classroom Starter Kit design vocabulary — the "words" the Generator (F8) may use and the **rules** for which combinations are physically buildable. Ship (1) a committed, machine-readable `parts_catalog.json` materialized **from** F2's `contracts.vocabulary` enums (so vocabulary and catalog can never drift), carrying the six config axes plus a `constraints` block expressing combination legality; (2) a deterministic `validate_config()` rules engine in `contracts/src/contracts/parts_catalog.py` that, given a config (F2's `SelfModelConfig`), returns **buildable / not-buildable + structured + human-readable reasons**; and (3) the extension of the package's emit/`validate` entrypoints **additively** (no F1/F2 regression). This bounds the Generator's search to the **60** valid sentences of the grammar and gives F9's critics a pre-filtered, structurally-legal config to attack on physics grounds. It gates `m1`.

---

## Design Space (resolved)

Motor budget = 4. Every config has an arm (`front`/`rear`) and a powered end effector. Motors by end effector ([clawbot-scoop-replacement], [vex-launch-disc-parts]): `claw_grasper` = arm-lift + claw = **2**; `scoop` = arm-lift only (passive) = **1**; `flywheel` = spin motor + mandatory `600rpm` = **1**.

Valid `(motor_allocation, end_effector)` pairs (7), after removing `4drive` and restricting claw to `2drive+1arm+1claw`:

| | claw_grasper | scoop | flywheel |
|---|:---:|:---:|:---:|
| **2drive+1arm+1claw** | ✓ | ✓ | ✓ |
| **2drive+2free** | ✗ | ✓ | ✓ |
| **3drive+1manip** | ✗ | ✓ | ✓ |

Per pair: `arm_position(2) × arm_gear_ratio(2) × cartridge × wheel_config(1)`, with `cartridge` free `{100,200,600}` for claw/scoop and pinned `{600}` for flywheel (forward-only, D8). **Total = claw 12 + scoop 36 + flywheel 12 = 60 valid configs.** (MASTER's "~10–15" predates the flywheel/scoop/3-cartridge vocabulary — flagged stale, C3.)

---

## In scope

- **`parts_catalog.py`** in `contracts/src/contracts/`, re-exported as `from contracts import PartsCatalog, validate_config`:
  - `PartsCatalog` pydantic v2 model — `schema_version: Literal["1.0"]` (locked) + one `list[Enum]` field per axis, each typed against the **shared `contracts.vocabulary` enums F2 owns** (imported, never redefined — C1) + a typed `constraints` sub-model holding the machine-readable valid-config rules. `extra="forbid"`.
  - `validate_config(config: SelfModelConfig) -> CatalogVerdict` — deterministic combinatorial-buildability rules engine. Returns `{buildable: bool, violations: list[Violation]}` where each `Violation` is `{code: str, message: str}` (D9 — stable machine `code` like `CLAW_MOTOR_BUDGET` / `FLYWHEEL_CARTRIDGE`, plus a human string e.g. `"end_effector 'flywheel' requires cartridge '600rpm'; got '200rpm'"`). Reuses F2's `SelfModelConfig` (D3).
  - **Valid-config rules (resolved):**
    - **R1 — claw allocation (D7):** `end_effector == "claw_grasper"` ⇒ `motor_allocation == "2drive+1arm+1claw"` (the only allocation supplying both the arm-lift and claw motors). Claw is **not** valid on `2drive+2free` or `3drive+1manip`.
    - **R2 — manipulator budget:** `scoop`/`flywheel` need ≥1 manipulator motor; all remaining allocations supply ≥1, so both are valid on all three (`4drive`, which supplied 0, is removed at the vocabulary level — D6).
    - **R3 — flywheel cartridge (D8, forward-only):** `end_effector == "flywheel"` ⇒ `cartridge == "600rpm"` (hard part-compatibility fact). The converse — whether `600rpm` suits a claw/scoop — is a torque judgment left to **F9**, so claw/scoop accept any cartridge.
    - `wheel_config` is single-value (passes trivially; the catalog still enumerates exactly one).
- **`parts_catalog.json`** — committed, emitted by a new `catalog` entrypoint (`contracts/src/contracts/catalog.py`) that **writes the file directly** (mirroring F2's as-shipped `schema.py`: a `{filename: payload}` registry + `write_text`, **not** a stdout redirect). The six axis arrays are generated **from the vocabulary enums** (drift-free), enriched with `schema_version` + the `constraints` block. `parts_catalog.json` is a *data* document at the contracts root (D10), distinct from the JSON-Schema files in `schemas/`; **no** JSON Schema is emitted for `PartsCatalog` itself (D10). The Generator (F8) reads this file directly.
- **`catalog` + `catalog-check` Makefile targets** — `catalog: $(UV) python -m contracts.catalog` (no redirect); `catalog-check: catalog` then `git diff --exit-code` on the catalog file (mirrors F2's `schema-check`). Added to both `contracts/Makefile` and the root `Makefile` (which today delegates `sync`/`validate`/`test`/`lint`/`schema`).
- **`validate` entrypoint, extended additively** — third dispatch: round-trip `parts_catalog.json` against `PartsCatalog`, **and** assert each F2 self-model fixture's `config` is `buildable`. Existing `*.jsonl → ContractLine` (F1) and `self_model_*.json → SelfModel` (F2) paths unchanged.
- **Tests** in `contracts/tests/`:
  - catalog axis arrays equal the `contracts.vocabulary` enum value sets (**drift guard**; also asserts `4drive` is absent — C2);
  - the Gen-0/Gen-1 fixture config (`2drive+1arm+1claw`, `front`, `claw_grasper`, `front_omni+rear_standard`, `7:1`, `200rpm`) → `buildable: True`;
  - planted illegal combos → `buildable: False` with the matching `code`: `claw_grasper`+`2drive+2free` (`CLAW_MOTOR_BUDGET`); `claw_grasper`+`3drive+1manip` (`CLAW_MOTOR_BUDGET`); `flywheel`+`200rpm` (`FLYWHEEL_CARTRIDGE`);
  - the full enumeration of legal sentences has **exactly 60** entries (raw slot count post-`4drive` = 3×2×3×1×2×3 = 108);
  - `parts_catalog.json` round-trips through `PartsCatalog`.

## Out of scope

- **Physics judgment** — torque budget, CoM/geometry, reach, and "is `600rpm` sensible for a claw/scoop" (R3 forward-only). F3 answers only *"does this combination map to real, assemblable Starter-Kit parts within the 4-motor budget?"* The physics gate is **F9 critic-panel**.
- The `contracts.vocabulary` enum **value sets** — owned by **F2** (C1). The one change F3 triggers (`drop 4drive`) lands as an explicit F2 vocabulary amendment (C2), not silently inside F3.
- The `SelfModel` shape / `config` typing (F2). F3 consumes `SelfModelConfig`; it does not modify it (beyond adding it to `__all__`, D12).
- Generator logic (F8), gap math (F10), critic logic (F9), diff rendering (F11).
- Any change to F1's `ContractLine`/`contract_line.json` outputs. F3 is **additive** to the package.
- Booster Kit / extra parts / additional motors / aesthetic vocabulary. *(`scoop`/`flywheel` are first-class catalog values now, but their physical add-on parts are not F3's concern.)*
- Adapter protocols (F4), control grammar (F19); hardware, network, PROS C++.

---

## Acceptance

Each item is independently runnable from `contracts/` (or repo root, which delegates):

1. `make sync` exits 0.
2. `make lint` exits 0 (`ruff check` + `ruff format --check`).
3. `make catalog` exits 0 and writes `contracts/parts_catalog.json` directly (no redirect); the file is non-empty, committed, lists the six axes with value sets **identical to** `contracts.vocabulary` (incl. `motor_allocation` **without** `4drive`), and carries `schema_version` + `constraints`. `make catalog-check` exits 0. `contract_line.json` is **unchanged**; `self_model.json` reflects only the `4drive` removal (C2) and nothing else.
4. `make validate` exits 0 — round-trips `parts_catalog.json` against `PartsCatalog`, asserts each F2 fixture `config` is `buildable`, and still validates the F1 `*.jsonl` and F2 `self_model_*.json` fixtures.
5. `make test` exits 0, covering: catalog axes == `contracts.vocabulary` (drift guard + `4drive` absent); Gen-0 config → `buildable`; each planted illegal combo → `not buildable` with the matching `code`; enumeration has **exactly 60** legal configs; `parts_catalog.json` round-trips.
6. `from contracts import PartsCatalog, validate_config` works in `uv run python` after `make sync`.
7. Root `make sync`/`validate`/`test`/`lint`/`catalog` (delegating into `contracts/`) all exit 0; the F1 **and** F2 suites still pass (no regression beyond the deliberate `4drive` removal).
8. Manual reviewer check: the Gen-0 fixture config is reported buildable, and `flywheel`+`200rpm` is rejected with a human-readable reason — the structural pre-filter that hands F9 only legal configs and gives the Generator a cheap buildability guard.

---

## Constraints

- Python 3.12 (`>=3.12,<3.13`) · uv · ruff · pydantic v2 — no pip/poetry/black/flake8 (ADR-05/15/16). Build entry is **`make sync`** (routed gate, F1 D7).
- `root: contracts/` · `ignore_folders: .venv, __pycache__, dist, .pytest_cache, captures`.
- pydantic v2 only: `ConfigDict`; JSON via `model_json_schema()`/`model_dump` (ADR-06). Reuse F1's `StrictModel` for strict sub-models.
- `schema_version: Literal["1.0"]` is locked; bumped per-contract, independently of F1/F2 (D11).
- **Single source of vocabulary (C1):** axis values come **only** from `contracts.vocabulary`; F3 imports and materializes them, never hard-codes a value set. The drift-guard test enforces this.
- **Starter Kit only** (ADR-14): the PR #13 + D6 feasibility-revised value sets (see Vocabulary callout).
- **Additive only** (except the deliberate `4drive` removal, C2): `catalog`/`catalog-check` are new; `validate` gains a parts-catalog path without altering F1's behaviour. No hardware, no network, no schema/vocabulary defined outside `contracts`.
- **Mirror F2's as-shipped conventions:** generated JSON via a **direct-file-write** module, regenerated by `make <target>` (no redirect), drift-gated by a `*-check` target. Dev deps use **PEP 735 `[dependency-groups]`** (F2's `1266a4d`).

---

## Decisions (closed)

| # | Decision | Resolution |
|---|---|---|
| D1 | Where vocabulary lives | Import from F2's `contracts.vocabulary` (C1). Catalog materialized from those enums. |
| D2 | F3 vs F9 boundary | F3 = combinatorial buildability (motor budget, part availability). F9 = physics (torque/CoM/geometry). |
| D3 | `validate_config` input | Reuse F2's `SelfModelConfig` (`strict=False`, so JSON strings coerce into the StrEnums). |
| D4 | Rules: code or JSON? | **Both** — `constraints` block in `parts_catalog.json` (F8 reads it) + executable `validate_config`. |
| D5 | Catalog file location | `contracts/parts_catalog.json` (data document at contracts root). |
| **D6** | **`4drive` (O-A a)** | **Removed from the vocabulary** — it supplies 0 manipulator motors, so no valid config can use it (every config needs a powered manipulator). Lands as an F2 vocabulary amendment (C2), not a rule. |
| **D7** | **claw allocation (O-A b)** | **`claw_grasper` only on `2drive+1arm+1claw`.** `2drive+2free` = 2 uncommitted motors for the 1-motor effectors (scoop/flywheel), not a second encoding of the Clawbot. |
| **D8** | **cartridge rule (O-A c)** | **Forward-only:** F3 enforces `flywheel ⇒ 600rpm`. Whether `600rpm` suits claw/scoop is F9's torque call; claw/scoop accept any cartridge. |
| **D9** | **`CatalogVerdict` shape (O-C)** | `{buildable: bool, violations: [{code, message}]}` — stable machine `code` + human message, so F8/F9 can route on it. |
| **D10** | **catalog path / schema export (O-B)** | Data file at `contracts/parts_catalog.json`; **no** JSON Schema emitted for `PartsCatalog` (the data file is the contract). |
| **D11** | **schema-version coupling (O-D)** | Per-contract independent bumps, consistent with F1/F2. |
| **D12** | **export `SelfModelConfig` (O-E)** | Additively add `SelfModelConfig` to `contracts.__all__` (one line in F2's `__init__.py`) — clean public API for F8. |

---

## Coordination items

- **C1 — shared vocabulary atom (with F2).** F3 imports `contracts.vocabulary`; never redefines value sets.
- **C2 — F2 vocabulary amendment: drop `4drive` (D6).** Requires editing F2-owned `contracts/src/contracts/vocabulary.py` (remove `MotorAllocation.DRIVE4`), the MASTER frozen Parts Catalog Grammar block (remove `"4drive"`), and regenerating `contracts/schemas/self_model.json`. Fixtures are unaffected (Gen-0/Gen-1 use `2drive+1arm+1claw`). **Land as a clearly-labeled vocabulary amendment** (PR #13-style), reviewable as a contract change — planning decides whether it rides this branch or a standalone F2 amendment landed first.
- **C3 — MASTER count estimate is stale.** "~10–15 valid configs" predates the flywheel/scoop/3-cartridge vocabulary; the real count under the resolved rules is **60**. Reconcile MASTER's estimate alongside C2.

---

## Milestones (optional)

| id | Validates | Mode | Owner |
|---|---|---|---|
| `s0` vocabulary amendment (C2) | `4drive` removed from `MotorAllocation`; MASTER block + `self_model.json` reconciled; F2 suite still green | automated + manual contract review | TBD |
| `s1` catalog model + rules | `PartsCatalog` imports the vocab enums; `validate_config` returns verdict+codes; drift-guard, Gen-0-buildable, planted-illegal tests fire; `catalog` writes committed `parts_catalog.json`; `catalog-check` green | automated (`make test`, `make catalog`, `make catalog-check`) | TBD |
| `s2` fixtures + gates | `validate` round-trips the catalog + asserts F2 fixtures buildable; enumeration == 60; root + contracts gates green; F1/F2 suites pass | automated (`make validate`) + manual buildability check | TBD |
| (gate) `m1` contracts-frozen | All contracts (F1–F4, F19) load and round-trip cleanly | manual — human gate | TBD |

---

## Open questions

*(All F3 open questions O-A…O-E are resolved — see Decisions D6–D12.)* Remaining cross-feature follow-ups are tracked as coordination items C2 (the `4drive` vocabulary amendment) and C3 (reconcile MASTER's stale ~10–15 estimate to 60).

---

## Post-merge review (2026-06-24, PR #16)

> **Superseded by post-merge review.** PR #16 merged at commit `610a1b0`; codewizard-dt's 8 inline comments narrowed the grammar substantively. See [requirements.md → Post-merge review](requirements.md) for the full diff. Briefly: `motor_allocation` becomes effector-encoded (`2drive+1arm+1claw` / `2drive+1arm` / `2drive+1flywheel`); `arm_position`, `arm_gear_ratio`, `wheel_config` removed; `cartridge` drops `100rpm`; rule set grows to R1/R1b/R1c/R3/R4; design space collapses from 60 → 4 (claw 1 + scoop 2 + flywheel 1). The narrowing reflects what the V5 Starter Kit can actually build.
