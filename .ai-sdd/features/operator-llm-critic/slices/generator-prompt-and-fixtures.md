# Slice: generator-prompt-and-fixtures

| Field | Value |
|---|---|
| Feature | operator-llm-critic |
| Maps to | F8 generator |
| Stack | operator |
| Depends on | `operator-packet-builder`, F2 `SelfModel`, F3 parts-catalog grammar |
| Blocks on for full F8 | F10 gap-analyzer |

## Scope

Plan the Generator prompt skeleton and validation fixtures for Gen 0 and Gen
N+1 candidate self-models. The Generator consumes the operator packet and
returns one candidate `contracts.SelfModel` plus a short handoff note covering
changed fields, evidence used, blocked assumptions, and critic review request
scope.

The fixtures should prove that generated candidates can validate against
`contracts.SelfModel` without adding a duplicate self-model schema in
`operator/`.

## Acceptance

1. Gen 0 fixture has `parent_generation = null`.
2. Gen N+1 fixture uses a prior `SelfModel` and sets `parent_generation` to an
   earlier generation.
3. Candidate fields align to the existing `SelfModel` contract:
   `schema_version`, `generation`, `parent_generation`, `config`,
   `structural`, `capability`, `predictive`, `gap_model`, and keyed
   `reasoning`.
4. Handoff notes cite evidence used and blocked assumptions without becoming a
   durable schema.
5. Prompt planning forbids hidden synthetic oracle parameters and private
   critic chain-of-thought.
6. Candidate config values are checkable against F3 `validate_config` instead
   of prompt-invented buildability rules.

## Out of Scope

- Implementing runtime LLM calls.
- Writing production prompt text.
- Implementing F10 gap revision behavior.
- Creating new durable schemas or formal review models.

## Dependencies

- `operator-packet-builder` for visible evidence packets.
- F2 `contracts.SelfModel` for validation.
- F3 parts-catalog valid-config rules for buildability enforcement.
- F10 gap analyzer for real residual summaries in later revisions.

## Test / Validation Notes

- Plan validation that fixtures load through the existing `contracts.SelfModel`
  model.
- Include negative fixture planning for out-of-vocabulary config values and
  missing required self-model fields.
- Add manual review notes that prompt fixtures preserve residual-key
  traceability instead of renaming gap keys in prose.
