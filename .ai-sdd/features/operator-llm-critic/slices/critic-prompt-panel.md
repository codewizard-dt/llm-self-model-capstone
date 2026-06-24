# Slice: critic-prompt-panel

| Field | Value |
|---|---|
| Feature | operator-llm-critic |
| Maps to | F9 critic-panel |
| Stack | operator |
| Depends on | `generator-gap-revision`, F2 `SelfModel`, F3 parts-catalog grammar |
| Related blockers | F10 gap-analyzer |

## Scope

Plan the three stateless critic lanes from
`operator/docs/llm_critic_architecture.md`: physics, torque, and CoM/geometry.
Each critic receives the same candidate `contracts.SelfModel` and evidence
packet, but a different review scope.

The MVP critic output can be markdown with a strict heading template. If the
team later needs a durable `CriticReview` model, that decision must route
through `contracts/` before it is treated as a schema.

## Acceptance

1. Exactly three critic lanes are planned: physics, torque, CoM/geometry.
2. Physics focuses on `capability`, `predictive`, `gap_model`, and
   `structural` plausibility.
3. Torque focuses on `capability`, `predictive`, `motor_samples`, parts specs,
   load, heat, current, and force evidence.
4. CoM/geometry focuses on `config`, `structural`, `capability`, catalog rules,
   reach, center of mass, connections, and line of sight.
5. Each critic returns pass or flag, cited field or section, rationale,
   suggested correction when useful, and uncertainty or blocked dependency.
6. Critics remain stateless and cannot self-approve a candidate.

## Out of Scope

- Implementing provider calls.
- Writing final production prompts.
- Creating durable critic schemas in `operator/`.
- Replacing F3 parts-catalog grammar or F10 gap summaries.

## Dependencies

- Candidate `SelfModel` fixture from F8 planning.
- Evidence packet from `operator-packet-builder`.
- F3 valid-config rules for buildability review.
- F10 residual summaries for full gap-sign review.

## Test / Validation Notes

- Plan fixture reviews where each lane receives the same candidate and packet
  but produces scoped output.
- Include checks that critic outputs cite candidate fields or packet sections.
- Include a reviewer check that critic prompt planning does not include private
  chain-of-thought persistence or hidden memory.
