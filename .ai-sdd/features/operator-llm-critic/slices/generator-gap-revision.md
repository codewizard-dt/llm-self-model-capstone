# Slice: generator-gap-revision

| Field | Value |
|---|---|
| Feature | operator-llm-critic |
| Maps to | F8 generator |
| Stack | operator |
| Depends on | `generator-prompt-and-fixtures` |
| Blocks on for full F8 | F10 gap-analyzer |

## Scope

Plan the gap-driven revision path for a Generator run that updates an existing
candidate from residual evidence. Until F10 exists, this slice uses
fixture-backed residual summaries and labels them as fixture-backed. The
revision path should preserve residual-key traceability: if a gap key is
`force_error_N`, the Generator updates or explains `gap_model` using that same
key.

The intended revision targets are `predictive`, `gap_model`, and keyed
`reasoning`, with any `capability` or `structural` change justified by visible
contract evidence.

## Acceptance

1. Revision fixtures start from an approved prior `SelfModel`.
2. Fixture-backed F10 residual summaries are explicitly labeled
   fixture-backed.
3. Updated `gap_model` keys reuse the residual keys from the input summary.
4. `reasoning` contains keyed rationale for each changed field.
5. The plan states that real implementation remains blocked until F10
   gap-analyzer lands.

## Out of Scope

- Computing residuals.
- Implementing F10.
- Authoring production prompts or code.
- Allowing hidden oracle answer keys into the Generator packet.

## Dependencies

- `generator-prompt-and-fixtures` for the candidate output shape.
- F10 gap-analyzer for real signed residual summaries.
- F1 `ContractLine` residual key conventions.
- F2 `SelfModel` validation.

## Test / Validation Notes

- Plan tests that compare prior and revised candidates for expected changes in
  `predictive`, `gap_model`, and `reasoning`.
- Include a validation note that fixture residual keys must survive unchanged
  into the revised `gap_model`.
- Include a reviewer check that fixture-backed data is not presented as real
  hardware proof.
