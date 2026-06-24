# Slice: critic-review-aggregation

| Field | Value |
|---|---|
| Feature | operator-llm-critic |
| Maps to | F9 critic-panel |
| Stack | operator |
| Depends on | `critic-prompt-panel` |

## Scope

Plan aggregation of the three critic reviews into a human-gate report. The
report should preserve each critic's pass/flag state, cited fields, rationale,
suggested correction, uncertainty, and blocked dependencies. Aggregation may
summarize and group issues, but it cannot convert critic consensus into
approval without a human gate.

## Acceptance

1. Aggregated report includes all three critic lanes.
2. Flags are grouped by candidate field or packet section when useful.
3. Blocked dependencies remain visible in the report.
4. The report has an explicit human-gate decision placeholder.
5. No critic panel path can self-approve a candidate.
6. The aggregation output is treated as an operator report, not a durable schema
   under `operator/`.

## Out of Scope

- Implementing report rendering code.
- Building F11 presenter output.
- Creating a formal durable `CriticReview` or `HumanGate` schema.
- Auto-applying critic fixes to a candidate.

## Dependencies

- `critic-prompt-panel` review output shape.
- F8 candidate `SelfModel` references.
- Human reviewer gate outside the critic panel.

## Test / Validation Notes

- Plan fixture aggregation for all-pass, single-flag, multi-flag, and blocked
  dependency cases.
- Include a validation note that every source critic review appears in the
  aggregate report.
- Include a negative check that an aggregate with no human-gate placeholder is
  invalid for MVP acceptance.
