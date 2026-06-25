# Slice: operator-packet-builder

| Field | Value |
|---|---|
| Feature | operator-llm-critic |
| Maps to | F8 generator support, F10 dependency intake |
| Stack | operator |
| Depends on | F1 `ContractLine`, F2 `SelfModel`, F3 parts-catalog grammar, F4 adapter interfaces |
| Blocks on for full F8 | F10 gap-analyzer |

## Scope

Implement the first operator packet builder for the offline LLM loop. The packet
builder gathers visible inputs for F8/F9 work: current or prior
`contracts.SelfModel`, task evidence from `contracts.ContractLine` JSONL,
ROS proof bundles exported through `robot/ros2-runtime/src/vexy_ros`,
`contracts.PartsCatalog` / `contracts.validate_config` buildability checks,
human constraints, source references, future F10 residual summaries, and
blocked-state notes. The packet is the evidence boundary for F8 Generator work
and must make missing evidence explicit.

This slice creates two practical tracks:

- Track 1: M1 + ROS proof intake, anchored to merged contracts and
  `vexy_ros.evidence_export.contract_jsonl_from_bundle`.
- Track 2: Operator LLM packet assembly, producing a markdown packet for the
  offline Generator/Critic flow.

The packet builder must use these exact blocked labels:

- `[BLOCKED: awaiting F10 gap analyzer residual summary]`
- `[BLOCKED: no ContractLine evidence for this task]`
- `[BLOCKED: hardware proof not recorded as contract-valid JSONL]`

F3 parts valid-config sections must use the committed catalog contract surface.
Until F10 lands, gap summary sections are blocked or fixture-backed exactly as
described in `operator/docs/llm_critic_architecture.md`.

## Acceptance

1. Packet contents reference `contracts.ContractLine`, `contracts.SelfModel`,
   `contracts.vocabulary`, `contracts.PartsCatalog`, and
   `contracts.validate_config` as the source inputs.
2. Missing F10 data appears with the exact blocked label above.
3. Fixture-backed gap summaries are visibly labeled fixture-backed and do not
   masquerade as real F10 output.
4. Packet source references distinguish observed contract evidence from human
   constraints and blocked assumptions.
5. The packet does not define telemetry, self-model, parts-catalog, or residual
   schemas under `operator/`.
6. ROS proof-bundle intake reuses `vexy_ros.evidence_export` instead of
   duplicating proof-to-ContractLine export logic.
7. Root `make test`, `make validate`, `make lint`, and `make sync` delegate to
   the new operator vertical.

## Out of Scope

- Writing final prompt text.
- Computing gap residuals.
- Changing F3 valid-config grammar.
- Reading hidden synthetic oracle parameters.
- Implementing Generator or Critic prompt execution.

## Dependencies

- F1 telemetry-contract for `ContractLine` evidence.
- F2 self-model-schema for candidate and prior `SelfModel` shape.
- F3 parts-catalog grammar for full valid-config rules, landed in
  `contracts.PartsCatalog` and `contracts.validate_config`.
- F10 gap-analyzer for real signed residual summaries, blocked until landed.

## Test / Validation Notes

- Plan fixture cases for: no `ContractLine` evidence, no hardware proof JSONL,
  and missing F10 residual summary.
- Validate that fixture packets contain the exact blocked labels and no invented
  schema fields.
- Include a reviewer check that hidden oracle parameters never appear in the
  packet.
