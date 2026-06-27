# LLM Decision Adapter Feature Requirements

Status: approved - ready for ai-sdd run
Source brief: `PILOT_MASTER_REQUIREMENTS.md` (`P4 llm-decision-adapter`)
Program: `pilot-online-task-loop`
Feature slug: `llm-decision-adapter`
Owner: 215eight
Vertical: `pilot`

## Goal

Provide the ROS-free adapter layer that turns a compact `contracts.PilotObservation` plus allowed
skill registry summaries into a short, structured, repeatable LLM prompt, parses the model's JSON
response into `contracts.PilotDecision`, and retries/rejects invalid output before anything can reach
the robot. The deterministic pilot harness remains the loop owner; this feature only prepares,
parses, and validates LLM decisions.

## In Scope

- Add a prompt-building module that includes the required input sections: objective, current phase,
  observation snapshot, assertions, last skill/result, recent history, allowed skills, safety
  constraints, and output schema.
- Use `pilot.skills` registry summaries as the allowed skill list.
- Parse JSON LLM responses into `contracts.PilotDecision`.
- Validate action values and selected skills against contract schemas and the skill registry.
- Add retry/adaptation behavior for malformed JSON or invalid decisions, without executing skills.
- Provide a mock/in-memory LLM client interface for deterministic tests.
- Add tests for valid decisions, malformed JSON, unknown skills, invalid actions, retry exhaustion,
  prompt determinism, and no ROS dependency.

## Out Of Scope

- Calling a real remote or local LLM provider.
- Choosing the production model, API key posture, network behavior, or Pi runtime secret handling.
- Running the pilot loop, executing skills, publishing ROS commands, safety validation enforcement,
  assertion computation, run logging, replay orchestration, or hardware motion.
- Defining new schemas in `pilot/` or changing contract schemas.
- Letting LLM output bypass validation or reach ROS/Brain directly.

## Acceptance

- `pilot` exposes an LLM decision adapter API that builds deterministic prompts from
  `PilotObservation`, recent trace/history text, safety constraints, and skill summaries.
- Prompt output includes every required section from `PILOT_MASTER_REQUIREMENTS.md`.
- Adapter parses valid JSON into `contracts.PilotDecision`.
- Adapter rejects malformed JSON, unknown actions, unknown skill names, and schema-invalid command
  parameters with clear errors.
- Adapter supports deterministic retry against an injected mock client and stops after a configured
  retry limit.
- Invalid LLM output never produces an executable command object.
- Tests cover valid continue/retry/stop/request-human decisions.
- Tests cover prompt determinism and JSON-serializable prompt payloads.
- Tests prove the adapter imports and runs without ROS packages or a real LLM provider.
- `make -C pilot test`, `make -C pilot lint`, root `make sync`, root `make test`, root
  `make validate`, and root `make lint` pass.

## Constraints

- The LLM is advisory until its output validates as `contracts.PilotDecision`.
- The adapter must be pure Python and provider-agnostic.
- No API keys, model provider SDKs, network calls, ROS imports, or hardware dependencies in this
  feature.
- Use `make sync`, not root `uv sync`, as the repo-level sync gate because this repo has per-vertical
  `pyproject.toml` files.
- Do not define schemas outside `contracts/`.

## Decisions

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| LDA-001 | closed | Implement the adapter in `pilot.decision`, separate from `pilot.observation` and `pilot.skills`. | Keeps prompt/parse behavior isolated from snapshot construction and registry metadata. | Folding adapter code into observation or skills modules. |
| LDA-002 | closed | Define a minimal provider protocol with an injected mock client for tests, but no real provider implementation. | Provider choice/key/network posture remains unresolved and out of scope; tests still need deterministic responses. | Adding OpenAI/Anthropic/local-model SDK dependencies now. |
| LDA-003 | closed | Build prompt payloads as deterministic JSON-compatible dictionaries, then render stable text/JSON for provider calls. | Repeatable prompts are easier to test and replay. | Free-form string concatenation only. |
| LDA-004 | closed | Parse and validate LLM output through `contracts.PilotDecision` and `TypeAdapter` for embedded skill commands. | Contracts own the decision/skill schema and invalid output must not reach execution. | Hand-parsing decisions into ad hoc dicts. |
| LDA-005 | closed | Treat retry as adapter-local parse/validation retry only; no loop-control retry or skill execution behavior. | The deterministic harness owns loop iteration and execution. | Implementing the pilot loop inside the adapter. |

## Open Questions

None for this feature draft. The unresolved production LLM runtime/key/network choice remains out of
scope and will be handled by a later provider/runtime feature.

## Approval Gate

Approved by 215eight on 2026-06-27. The feature is decomposed into runnable slices in
`.ai-sdd/features/llm-decision-adapter/pipeline.yaml` and
`.ai-sdd/features/llm-decision-adapter/slices/*.md`.
