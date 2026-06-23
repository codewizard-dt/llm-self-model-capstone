# Slice: fixtures-and-gates

| Field | Value |
|---|---|
| Feature | self-model-schema (F2) |
| Stack | contracts |
| Depends on | vocabulary-and-model |

## What this slice delivers

The two hand-authored self-model fixtures (a Gen-0 authored model and a Gen-1 gap-driven revision), the `make validate` extension that validates them against `SelfModel`, and the proof that the whole contracts gate set — at the contracts root and via root-`Makefile` delegation — stays green with no F1 regression. This closes F2's contribution to the `m1` contracts-frozen milestone.

## Files to create / change

```
contracts/
  fixtures/
    self_model_gen0.json   NEW — Gen-0 authored Clawbot, parent_generation: null
    self_model_gen1.json   NEW — Gen-1 revision, parent_generation: 0
  src/contracts/
    validate.py            CHANGE — add a fixtures/self_model_*.json -> SelfModel dispatch
  tests/
    test_self_model.py     CHANGE (or add) — round-trip both fixtures; assert the Gen-1 diff (acceptance 5)
```

## Fixtures

`self_model_gen0.json` — authored Gen-0 Clawbot:
- `generation: 0`, `parent_generation: null`
- `config`: `motor_allocation:"2drive+1arm+1claw"`, `arm_position:"front"`, `end_effector:"claw_grasper"`, `wheel_config:"front_omni+rear_standard"`, `arm_gear_ratio:"7:1"`, `cartridge:"200rpm"`
- `capability`, `predictive.grab`, `gap_model.grab` populated with research-grounded starting values
- `reasoning`: why each structural choice was made

`self_model_gen1.json` — Gen-1 revision (hand-authored, D6):
- `generation: 1`, `parent_generation: 0`
- at least one `capability` and/or `predictive.grab` value moved toward observed reality vs Gen-0
- `gap_model.grab` keyed with F1's frozen residual keys — `force_error_N`, `duration_error_s` (D5)
- `reasoning`: cites the gap evidence that drove the change

## `validate.py` extension

Add a second dispatch beside the existing `fixtures/*.jsonl → ContractLine` path: glob `fixtures/self_model_*.json`, validate each against `SelfModel`, report `name: error` on stderr and exit 1 on any failure. The existing `*.jsonl → ContractLine` path must keep passing unchanged.

## Acceptance

1. `make validate` exits 0 — `self_model_gen0.json` + `self_model_gen1.json` validate against `SelfModel`; existing `*.jsonl` fixtures still validate against `ContractLine`.
2. `make test` exits 0, adding: round-trip parse of both fixtures; an assertion that Gen-1 vs Gen-0 has a changed `capability`/`predictive` value and that `gap_model.grab`'s keys are a subset of F1's grab `gap` keys.
3. `make lint` exits 0; the `make schema` freshness gate from the prior slice still passes.
4. Root `make sync`/`validate`/`test`/`lint`/`schema` (delegating into `contracts/`) all exit 0; F1's suite still passes (no regression).
5. Manual reviewer check (Acceptance 8 of requirements): the Gen-1 → Gen-0 diff reads as self-knowledge improving in prose — a numeric value moved toward reality with `reasoning` explaining why.
