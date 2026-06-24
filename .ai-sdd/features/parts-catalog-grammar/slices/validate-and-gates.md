# Slice: validate-and-gates

| Field | Value |
|---|---|
| Feature | parts-catalog-grammar (F3) |
| Stack | contracts |
| Depends on | `catalog-model-and-rules` |

## What this slice delivers

The additive `validate`-entrypoint dispatch for the parts catalog, the root `Makefile` delegation for `catalog`/`catalog-check`, and the full green gate sweep proving no F1/F2 regression. This closes F3 for `m1`. Strictly additive: the existing `*.jsonl → ContractLine` (F1) and `self_model_*.json → SelfModel` (F2) validate paths keep passing unchanged.

## Files to create / change

```
contracts/
  src/contracts/
    validate.py           CHANGE — add a third dispatch (see below); keep F1 + F2 paths intact
  tests/
    test_validate.py      CHANGE/NEW — cover the new dispatch (catalog round-trip + fixture buildability)
Makefile (root)           CHANGE — delegate `catalog` + `catalog-check` into contracts/ (next to sync/validate/test/lint/schema)
```

## `validate.py` third dispatch

Add to the existing collect-errors / stderr / exit-1 harness, without touching the F1 (`*.jsonl → ContractLine`) or F2 (`self_model_*.json → SelfModel`) dispatches:

- **Round-trip the catalog:** load `contracts/parts_catalog.json` and validate it against `PartsCatalog`; a parse/validation failure is reported as `parts_catalog.json: <error>` and exits 1.
- **Assert fixture buildability:** for each `self_model_*.json` fixture, run `validate_config(model.config)` and require `buildable is True`; a non-buildable fixture is reported as `<fixture>: not buildable — <violation messages>` and exits 1. (Both shipped F2 fixtures are the Gen-0/Gen-1 Clawbot, which is buildable.)

An empty/absent fixtures dir or a missing `parts_catalog.json` is handled consistently with the existing entrypoint behaviour.

## Root Makefile delegation

The root `Makefile` currently delegates `sync`/`validate`/`test`/`lint`/`schema` into `contracts/`. Add `catalog` and `catalog-check` delegations so `make catalog` / `make catalog-check` are runnable from the repo root.

## Acceptance

1. `make validate` (contracts + root) exits 0 — round-trips `parts_catalog.json` against `PartsCatalog`, asserts each F2 `self_model_*.json` fixture `config` is `buildable`, **and** still validates the F1 `*.jsonl` and F2 `self_model_*.json` fixtures.
2. A temporarily-mutated fixture with an unbuildable `config` (e.g. `flywheel`+`200rpm`) makes `make validate` exit non-zero with a readable reason (demonstrated in a test; the committed fixtures stay buildable).
3. `make catalog` and `make catalog-check` are runnable from the repo root (delegation works) and exit 0.
4. Root `make sync`/`validate`/`test`/`lint`/`catalog`/`catalog-check` all exit 0.
5. The full F1 **and** F2 test suites still pass (no regression); `make test` green at contracts + root.
6. `make lint` exits 0.
