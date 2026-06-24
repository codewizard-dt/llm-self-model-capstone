# Slice: operator-packet-builder

| Field | Value |
|---|---|
| Feature | operator-llm-critic |
| Maps to | F8 generator support, F10 dependency intake |
| Stack | operator |
| Depends on | F1 `ContractLine`, F2 `SelfModel`, F4 adapter interfaces |
| Blocks on for full F8 | F3 parts-catalog grammar, F10 gap-analyzer |

## Scope

Plan an operator packet builder that gathers visible inputs for the offline LLM
loop: current or prior `contracts.SelfModel`, task evidence from
`contracts.ContractLine` JSONL, shared vocabulary constraints, human operator
constraints, source references, future F10 residual summaries, and blocked-state
notes. The packet is the evidence boundary for F8 Generator work and must make
missing evidence explicit.

The packet builder must use these exact blocked labels:

- `[BLOCKED: awaiting F3 parts-catalog valid-config rules]`
- `[BLOCKED: awaiting F10 gap analyzer residual summary]`
- `[BLOCKED: no ContractLine evidence for this task]`
- `[BLOCKED: hardware proof not recorded as contract-valid JSONL]`

Until F3 and F10 land, parts valid-config sections and gap summary sections are
blocked or fixture-backed exactly as described in
`operator/docs/llm_critic_architecture.md`.

## Acceptance

1. Packet contents reference `contracts.ContractLine`, `contracts.SelfModel`,
   and `contracts.vocabulary` as the source inputs.
2. Missing F3 and F10 data appears with the exact blocked labels above.
3. Fixture-backed gap summaries are visibly labeled fixture-backed and do not
   masquerade as real F10 output.
4. Packet source references distinguish observed contract evidence from human
   constraints and blocked assumptions.
5. The packet does not define telemetry, self-model, parts-catalog, or residual
   schemas under `operator/`.

## Out of Scope

- Implementing packet builder code.
- Writing final prompt text.
- Computing gap residuals.
- Building F3 valid-config grammar.
- Reading hidden synthetic oracle parameters.

## Dependencies

- F1 telemetry-contract for `ContractLine` evidence.
- F2 self-model-schema for candidate and prior `SelfModel` shape.
- F3 parts-catalog grammar for full valid-config rules, blocked until landed.
- F10 gap-analyzer for real signed residual summaries, blocked until landed.

## Test / Validation Notes

- Plan fixture cases for: no `ContractLine` evidence, no hardware proof JSONL,
  missing F3 catalog rules, and missing F10 residual summary.
- Validate that fixture packets contain the exact blocked labels and no invented
  schema fields.
- Include a reviewer check that hidden oracle parameters never appear in the
  packet.
