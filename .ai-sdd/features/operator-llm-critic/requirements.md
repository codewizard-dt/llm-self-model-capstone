# operator-llm-critic - Requirements

| Field | Value |
|---|---|
| Feature | operator-llm-critic |
| Feature mapping | F8 generator + F9 critic-panel |
| Vertical | `operator` |
| Root | `operator/` for runtime work; `contracts/` for durable schemas only |
| Depends on | F1 telemetry-contract, F2 self-model-schema, F4 adapter-interfaces |
| Blocked for full implementation | F3 parts-catalog grammar, F10 gap-analyzer |
| Unblocks | F11 presenter, F12 replay/demo loop, m2 Gen 0 -> Gen 2 replay |

---

## Goal

Plan the next LLM/Critic build step for Grace's offline self-model loop. The
feature turns `operator/docs/llm_critic_architecture.md` into six small
AI-SDD slices that prepare F8 Generator and F9 Critic Panel implementation while
preserving the thesis boundary: `operator/` orchestrates prompts, packets,
reviews, and reports; all durable schemas remain in `contracts/`.

Full F8 implementation is blocked until F3 provides valid parts-catalog grammar
and F10 provides the signed gap analyzer residual summary. Until those land,
the Generator work must expose missing inputs as blocked or fixture-backed
instead of inventing field names, build rules, telemetry shapes, or residual
keys.

## In Scope

- F8 support packet planning for an operator packet builder that collects
  `contracts.ContractLine`, `contracts.SelfModel`, shared vocabulary, human
  constraints, blocked-state notes, and future F10 gap summaries.
- F8 Generator prompt/fixture planning for Gen 0 and Gen N+1 candidate
  `SelfModel` outputs that validate against `contracts.SelfModel`.
- F8 gap-revision planning using fixture-backed F10 residual summaries until
  the real F10 analyzer exists.
- F9 Critic Panel planning for exactly three stateless critic lanes: physics,
  torque, and CoM/geometry.
- F9 aggregation planning that produces a human-gate report and never lets the
  critic panel self-approve.
- Planted-fault test planning that proves each critic catches a known bad
  self-model.

## Out of Scope

- Runtime code, prompt text, API calls, provider setup, or model execution.
- New durable schemas under `operator/`.
- Duplicate telemetry, self-model, parts-catalog, critic-review, or residual
  schema definitions outside `contracts/`.
- Implementing F3 parts catalog valid-config rules.
- Implementing F10 gap analyzer residual computation.
- Presenter, replay, online control, robot runtime, or PROS work.

## Contract Boundary

The feature must preserve the boundary from `operator/docs/llm_critic_architecture.md`:

- `contracts.ContractLine` is the source of truth for task evidence.
- `contracts.SelfModel` is the source of truth for Generator candidates and
  approved generations.
- Shared vocabulary comes from `contracts.vocabulary` and future F3 catalog
  rules.
- F10 residual summaries must be treated as inputs to operator orchestration,
  not as a second telemetry schema.
- If F9 later needs a durable `CriticReview` model, the team must first decide
  whether that schema belongs in `contracts/`.

No duplicate telemetry or self-model schema may be created under `operator/`.

## Blocked-State Rules

The first slice, `operator-packet-builder`, must use the exact blocked labels
and fixture language from the architecture doc:

- `[BLOCKED: awaiting F3 parts-catalog valid-config rules]`
- `[BLOCKED: awaiting F10 gap analyzer residual summary]`
- `[BLOCKED: no ContractLine evidence for this task]`
- `[BLOCKED: hardware proof not recorded as contract-valid JSONL]`

F3 parts-catalog grammar and F10 gap analyzer are blockers for full F8. Fixture
summaries are allowed only when clearly labeled fixture-backed.

## Slice Order

1. `operator-packet-builder`
2. `generator-prompt-and-fixtures`
3. `generator-gap-revision`
4. `critic-prompt-panel`
5. `critic-review-aggregation`
6. `planted-fault-critic-tests`

## Acceptance

1. The feature is named `operator-llm-critic`.
2. The plan explicitly maps to F8 generator and F9 critic-panel.
3. The plan states F10 gap-analyzer is a dependency and blocker for full
   implementation.
4. The plan states F3 parts-catalog grammar and F10 gap analyzer are blockers
   for full F8.
5. The first slice requires the exact blocked labels above and fixture-backed
   treatment from `operator/docs/llm_critic_architecture.md`.
6. Durable schemas remain in `contracts/`; no duplicate telemetry/self-model
   schema is planned under `operator/`.
7. The slice order matches the order listed above.
8. Every slice includes scope, acceptance, out of scope, dependencies, and
   test/validation notes.
9. `pipeline.yaml` uses the repo's simple feature pipeline style with nodes and
   edges.
10. The plan does not implement runtime code or prompts.
