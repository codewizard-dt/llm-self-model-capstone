---
id: REQ-001
title: LLM and Critic Architecture Before Schema
status: draft
created: 2026-06-23
updated: 2026-06-24
owner: Grace Huang
stakeholders:
  - codewizard-dt
  - 215eight
  - Jake Kinchen
tags:
  - llm
  - critic
  - operator
  - contracts
  - m1
  - ai-sdd
---

# REQ-001: LLM and Critic Architecture Before Schema

## Summary

Grace's current assignment is to define the high-level architecture for the LLM Generator and Critic system while the schema/contracts work is still being frozen. This is a planning and requirements artifact, not the final implementation of F8 or F9.

The output of this requirement should help the team answer: what the Generator consumes, what it produces, what the Critics inspect, what data the contracts must expose, and whether the agent team can run on a Raspberry Pi or needs an external runtime.

This requirement must stay aligned with the current GitHub state, especially merged PR #9, because PR #9 moved the project toward a top-level `contracts/` package that downstream LLM/operator work should import rather than duplicate.

## Current GitHub Snapshot

Checked on 2026-06-23 after PR #9 merged into `main`.

Update on 2026-06-24: PR #13 `self-model-schema` and PR #14
`adapter-interfaces` are merged, so this requirement no longer has to treat F2
and F4 as hypothetical. The architecture brief should consume
`contracts.SelfModel`, `contracts.vocabulary`, and the `TelemetrySource` /
`VisionSource` adapter protocols directly. PR #15 `ROS 2 align-to-tag bridge
and tag slices` is merged; hardware proof remains a separate truth gate. PR
#16 `parts-catalog-grammar` is merged, so F3 is no longer hypothetical: the
operator LLM/Critic work should consume `contracts.PartsCatalog`,
`contracts/parts_catalog.json`, and `contracts.validate_config` directly.

| PR | State | Review | Author | Assignee | Alignment note |
|---|---|---|---|---|---|
| [#16 [parts-catalog-grammar] F3: freeze the parts-catalog grammar + valid-config rules](https://github.com/codewizard-dt/llm-self-model-capstone/pull/16) | merged | approved | `215eight` | none | Landed F3 `PartsCatalog`, `parts_catalog.json`, `validate_config`, validation, and catalog gates. |
| [#15 [codex] ROS 2 align-to-tag bridge and tag slices](https://github.com/codewizard-dt/llm-self-model-capstone/pull/15) | merged | approved | `jakekinchen` | none | Landed the ROS bridge/tag software path; hardware proof remains a separate verification docket. |
| [#10 [codex] docs: add LLM/Critic requirements](https://github.com/codewizard-dt/llm-self-model-capstone/pull/10) | open | review required | `ghuang123` | none | This requirement PR; documents Grace's pre-m1 LLM/Critic architecture lane and now aligns with merged PRs #9, #13, #14, #15, and #16. |
| [#9 Dt typed assembly grammar](https://github.com/codewizard-dt/llm-self-model-capstone/pull/9) | merged | approved | `codewizard-dt` | `215eight` | Landed F1 telemetry-contract planning/implementation, top-level `contracts/` package work, fixture gates, and an F2 self-model-schema draft brief. |
| [#8 docs: add repo navigation readme](https://github.com/codewizard-dt/llm-self-model-capstone/pull/8) | merged | approved | `ghuang123` | none | Beginner repo map is in `main`. Use it as the onboarding front door. |
| [#7 Eac/ai sdd plan](https://github.com/codewizard-dt/llm-self-model-capstone/pull/7) | merged | approved | `215eight` | none | AI-SDD program plan is in `main`; use `.ai-sdd/programs/self-model-loop/requirements.md` as the program-level planning source. |

There are no GitHub issues at time of check.

Important PR #9 caveat: its PR body still describes an earlier motor-telemetry/research diff, but the merged files show the live direction: a `contracts/` package, F1 telemetry-contract requirements/slices, and an F2 self-model-schema draft. Treat merged `main` as the source of truth.

## Meeting-Derived Assignment

Source: Plaud note "06-22 Team Planning: AI Agent Framework Architecture Review".

Relevant transcript points:

- Around 00:53:35, the team separated current work into plan, vision-to-contract, telemetry-to-contract, and architecture lanes.
- Around 00:54:33, Grace's lane was described as starting the architecture for the "LLM and the critic."
- The response in the transcript was high-level architecture only, because the schema was not ready yet.
- The architecture sketch should help the schema owners understand what data fields the LLM/Critic components need.
- Once the architecture sketch exists, the team should run a resource assessment to estimate whether the full agent setup fits on Raspberry Pi class hardware.

Interpretation: Grace is not being asked to implement the Generator or Critic panel yet. Grace is being asked to define the pre-schema architecture and requirements that will feed F2/F3/F8/F9 and prevent downstream agent work from guessing.

## Repo Alignment

The authoritative program shape in `MASTER_REQUIREMENTS.md` says:

- `m1 contracts-frozen` gates downstream work.
- `F1 telemetry-contract`, `F2 self-model-schema`, `F3 parts-catalog-grammar`, `F4 adapter-interfaces`, and `F19 control-grammar` feed `m1`.
- `F8 generator` depends on F2, F3, and F10.
- `F9 critic-panel` depends on F2.
- The Critic count is fixed by ADR-07: physics validity, torque budget, and CoM/geometry.
- The LLM runtime decision is Claude Code subscription/inherited runtime for authoring and replay.

The approved AI-SDD program in `.ai-sdd/programs/self-model-loop/requirements.md` says:

- F1 telemetry-contract is in `contracts/` and unblocks F4, F7, F10, F14, and F15.
- F2 self-model-schema is in `contracts/` and unblocks F8, F9, and F11.
- F8 and F9 are operator-layer work after the schema is stable enough to consume.

Merged PR #9 adds or stages:

- `contracts/src/contracts/contract_line.py`: `ContractLine` with `task`, `motor_samples`, `predicted`, `gap`, `outcome`, optional `vision`, and optional `source`.
- `contracts/src/contracts/motor_telemetry.py`: strict VEX motor sample models and VEXcode/PROS mapping helpers.
- `contracts/fixtures/session_example.jsonl`: contract-line examples.
- `.ai-sdd/features/telemetry-contract/requirements.md`: F1 requirements and constraints.
- `.ai-sdd/features/self-model-schema/brief.md`: draft F2 brief for `SelfModel`, shared vocabulary, fixtures, JSON Schema export, and validation gates.

Therefore this requirement must not create any competing schema in `operator/`. The operator architecture must depend on the merged `contracts/` package as the cross-vertical source of truth.

## Problem

The team needs to design the LLM/operator side while contract work is still in motion. Without a written LLM and Critic architecture, the project risks:

- inventing prompt fields that do not map to F1 telemetry or F2 self-model schema;
- duplicating contract definitions outside `contracts/`;
- building a Generator that cannot be validated by the Critic panel;
- building Critics that only give prose opinions instead of schema-aligned flags;
- discovering too late that the full agent team cannot fit on the intended hardware/runtime.

## Goals

1. Define the Generator and Critic responsibilities in repo terms.
2. Define the expected inputs and outputs without freezing new schemas outside `contracts/`.
3. Identify the minimum fields F2 and F1 must expose for F8/F9 to work.
4. Define how the system behaves when contracts are missing or ambiguous.
5. Define a resource-assessment checklist for the planned agent team.
6. Produce requirements that can be converted into `/ai-sdd-plan` slices using
   the landed F2/F3 contract surfaces.

## Non-Goals

- Do not implement F8 Generator.
- Do not implement F9 Critic panel.
- Do not create model API calls or billing infrastructure.
- Do not create a second telemetry, self-model, or parts-catalog schema outside `contracts/`.
- Do not decide final hardware runtime placement.
- Do not change PR #9 contents from this requirement.
- Do not require live robot access.

## Personas

### Grace: LLM/operator architecture owner

Needs a clear, nontechnical-to-technical bridge: what she is supposed to produce, how it maps to repo features, and how to avoid stepping on contracts work.

### Contract owners

Need a list of LLM-facing fields and residual-key expectations so F1/F2/F3 can support downstream Generator/Critic work.

### Future Generator implementer

Needs a prompt/input/output contract that consumes landed F2/F3 surfaces and
stays blocked on F10 residual summaries for the full revision path.

### Future Critic implementer

Needs a fixed Critic panel shape and pass/flag/rationale outputs tied to F2 self-model fields.

## Functional Requirements

### LLM-001: Define the Operator Agent Team

The architecture must define at least four operator roles:

| Role | Purpose | Build timing |
|---|---|---|
| Generator | Authors Gen-0 self-model and revises Gen-N+1 from gap evidence. | F8, after F2/F3; full gap revision after F10 |
| Physics Critic | Checks whether the self-model's physical claims are plausible. | F9, after F2 |
| Torque Critic | Checks motor force/torque/load claims against VEX motor constraints. | F9, after F2 and F1 data conventions |
| CoM/Geometry Critic | Checks reach, center of mass, structural connections, and build plausibility. | F9, after F2/F3 |

The architecture may also describe a Coordinator/Router, but it must not assume a new schema. Any coordinator output should be plain markdown until F2/F9 schemas are explicitly planned.

### LLM-002: Define Generator Inputs

The Generator architecture must list the data it will need, grouped by source:

| Source | Required data |
|---|---|
| F2 SelfModel | `generation`, `parent_generation`, `config`, `structural`, `capability`, `predictive`, `gap_model`, `reasoning` |
| F3 parts catalog | finite valid vocabulary, buildable configuration rules, physical specs for selected parts |
| F1 telemetry contract | `ContractLine.task`, `predicted`, `gap`, `outcome`, `vision`, and `motor_samples` |
| F10 gap analyzer | computed residuals and summary of which predicted values were wrong |
| Human constraints | demo task, time limit, available hardware, safety constraints |

If an input is not yet available, the architecture must label it as blocked rather than invent it.

### LLM-003: Define Generator Outputs

The Generator output is a candidate `SelfModel` document, not arbitrary prose.

The architecture must require:

- schema-aligned JSON or markdown-with-JSON-block output against the landed F2
  `SelfModel`;
- required `reasoning` text explaining what changed and why;
- generation lineage (`generation`, `parent_generation`);
- a `gap_model` update that uses the same residual keys as F1/F10 gap evidence;
- no access to hidden oracle parameters.

The output may be a placeholder interface document in this planning slice, but
it must name the landed `SelfModel` fields rather than create new names.

### LLM-004: Define Critic Inputs and Outputs

Each Critic must receive:

- candidate `SelfModel`;
- relevant parts catalog entries;
- relevant telemetry/gap evidence when available;
- explicit review scope.

Each Critic must return:

- `pass` or `flag`;
- concise rationale;
- cited field or model section;
- optional suggested correction;
- uncertainty if the schema/data is insufficient.

The Critic panel must not self-approve the Generator's output. A separate reviewer, orchestrator, or human gate decides whether flags are resolved.

### LLM-005: Schema-Gated Behavior

The architecture must define a strict blocked-state rule:

If required schema/data is missing, the LLM must mark the section as blocked and name the missing dependency.

Examples:

- `[BLOCKED: awaiting F10 gap analyzer residual summary]`
- `[BLOCKED: no ContractLine evidence for this task]`
- `[BLOCKED: hardware proof not recorded as contract-valid JSONL]`

The Generator and Critics must not hallucinate field names, unit conventions, or buildability rules.

### LLM-006: Contract Boundary

The architecture must keep all schema definitions in `contracts/`.

Allowed:

- reference `contracts.ContractLine`;
- reference landed `contracts.SelfModel`;
- reference `contracts.vocabulary`, `contracts.PartsCatalog`, and
  `contracts.validate_config` from landed F2/F3;
- write prompt/interface docs in `operator/` or `wiki/work/`.

Not allowed:

- define telemetry JSON shapes under `operator/`;
- define self-model JSON shapes under `operator/`;
- duplicate `contracts.vocabulary` enums;
- assume task names are enums if F1 keeps `task: str`.

### LLM-007: Resource Assessment

The architecture must include a resource checklist for the full agent team:

- model/runtime candidate;
- local vs external execution;
- memory footprint estimate;
- prompt/token size estimate for one run;
- number of Critic calls per generation;
- latency tolerance for offline loop;
- whether Raspberry Pi 5 8GB is feasible;
- fallback if not feasible.

The initial resource assessment can be qualitative, but it must identify the heaviest components.

### LLM-008: Traceability

The architecture must map each LLM role to existing repo features:

| Architecture item | Repo feature |
|---|---|
| Generator | F8 |
| Critic panel | F9 |
| SelfModel shape | F2 |
| Parts vocabulary | F3 |
| Telemetry/gap evidence | F1 and F10 |
| Markdown/demo explanation | F11 |
| End-to-end replay | F12 |

### LLM-009: No Hidden Oracle Leakage

The architecture must preserve the non-negotiable information-separation rule:

- Generator may read parts catalog data and prior gap evidence.
- Generator must not read hidden oracle configuration or ground-truth parameters.
- Any synthetic demo must prove convergence from observed gap evidence, not direct access to answer keys.

### LLM-010: Human-Readable Demo Value

The architecture must support the project's showcase thesis: the robot's self-knowledge improves in readable prose while gap residuals tighten.

Therefore the Generator's `reasoning` field and the Critic rationales are not cosmetic. They are required demo artifacts.

## Proposed Deliverables

### Deliverable A: Architecture Brief

Path: `operator/docs/llm_critic_architecture.md`.

Must include:

- data flow diagram;
- Generator contract;
- Critic panel contract;
- blocked-state rules;
- resource assessment checklist;
- F1/F2/F3 field dependencies.

### Deliverable B: Prompt Skeletons

Prompt skeletons should be plain markdown until F2/F9 have formal runtime schemas:

- `generator_prompt.md`;
- `critic_physics_prompt.md`;
- `critic_torque_prompt.md`;
- `critic_geometry_prompt.md`.

Each skeleton must explicitly say it consumes schemas from `contracts/`.

### Deliverable C: Schema Feedback Notes

Short notes for contract owners:

- F2 needs `reasoning`, `gap_model`, `predictive`, `capability`, and `structural` fields to be visible to Generator and Critics.
- F1/F10 residual keys should be stable enough for `gap_model[task]` to mirror them key-for-key.
- F3 vocabulary and catalog expose both per-axis legal values and buildable
  combination rules.

### Deliverable D: Resource Assessment

A one-page assessment answering:

- Can the full Generator plus three Critics run on Raspberry Pi 5 8GB?
- If not, which roles should run externally?
- Which parts can be cached or replayed?
- What is acceptable latency for the offline loop?

## Acceptance Criteria

This requirement is satisfied when:

1. A reviewer can read the architecture brief and identify what Grace owns before `m1`.
2. The brief references merged PR #9's `contracts/` direction and does not duplicate schemas.
3. The Generator input/output sections mention F2 `SelfModel` fields.
4. The Critic section includes exactly the three ADR-07 critic lanes: physics, torque, CoM/geometry.
5. Missing schema/data behavior is explicit and uses blocked-state language.
6. The resource assessment checklist is present.
7. The requirement can be turned into an AI-SDD feature or roadmap without asking "what does LLM part mean?"

## Suggested Build Order

1. Build on merged PR #9 because it changes the contract root and adds F1/F2 planning surface.
2. Draft the LLM/Critic architecture brief against the merged `contracts/` package direction.
3. Use the landed F2/F3 fields and catalog verdicts in the Generator and
   Critics requirements.
4. With F2/F3 accepted, create an AI-SDD feature plan for
   `operator-llm-critic-architecture` or split directly into F8/F9 planning
   docs.
5. Only after F10 is stable, implement the full gap-revision path for F8
   Generator and F9 Critic panel.

## Open Questions

| ID | Question | Owner |
|---|---|---|
| O1 | Should Grace's artifact become its own AI-SDD feature, or should it be attached as planning input to F8/F9? | Team |
| O2 | Should Critic outputs be plain markdown for MVP, or should F9 define a formal `CriticResult` schema? | F9 owner |
| O3 | Should resource assessment target Raspberry Pi 5 8GB as a hard requirement or a feasibility check only? | Team |
| O4 | Should the first Generator task target `score` only if PR #9's F1 direction keeps flexible task strings? | F8/F10 owners |

## Notes for Handoff

The shortest plain-English handoff for Grace:

> I am owning the pre-schema LLM/Critic architecture. I am not building the final Generator yet. I will define what the Generator and three Critics need from the contracts, how they behave when schema is missing, and what resource assessment we need before deciding whether the agent team can run on the Pi.
