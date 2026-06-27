# Slice: prompt-builder

| Field | Value |
|---|---|
| Feature | llm-decision-adapter |
| Stack | pilot |
| Depends on | - |

## What this slice delivers

The deterministic prompt construction layer for LLM decision requests. It turns a
`contracts.PilotObservation`, recent history text, safety constraints, and prompt-friendly
`pilot.skills` registry summaries into a compact JSON-compatible payload and stable rendered prompt
without importing ROS or calling a model provider.

## Files to create / change

```
pilot/
  src/pilot/decision.py              NEW - prompt payload models/helpers and stable rendering
  src/pilot/__init__.py              CHANGE - additive exports for prompt helper API if useful
  tests/test_decision_prompt.py      NEW - prompt sections, determinism, serializability, no-ROS tests
```

## Requirements

- Add a `pilot.decision` module for LLM decision adapter code.
- Build prompt payloads from `contracts.PilotObservation`, recent trace/history text, safety
  constraints, and allowed skill summaries from `pilot.skills`.
- Include objective, current phase, observation snapshot, assertions, last skill/result, recent
  history, allowed skills, safety constraints, and output schema sections.
- Produce JSON-compatible prompt payloads with deterministic key ordering and deterministic rendered
  text.
- Preserve contract field names closely enough that prompt content can be replayed and inspected.
- Keep the module provider-agnostic and ROS-free.
- Do not parse model output, retry invalid responses, execute skills, or validate safety policy in
  this slice.

## Acceptance

- Tests prove every required prompt section is present.
- Tests prove prompt payloads are JSON-serializable.
- Tests prove repeated prompt rendering for the same input is byte-for-byte deterministic.
- Tests prove allowed skills come from the registry summary API.
- Tests prove `pilot.decision` imports without ROS packages or provider SDKs.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- Real LLM provider integration.
- Parsing LLM responses, retry behavior, skill execution, safety validation, assertion computation,
  recipes, run logging, or replay loop orchestration.
