# Slice: decision-parser-validation

| Field | Value |
|---|---|
| Feature | llm-decision-adapter |
| Stack | pilot |
| Depends on | `prompt-builder` |

## What this slice delivers

The response parsing and schema validation layer for LLM decisions. It accepts raw model text, extracts
strict JSON, validates it as `contracts.PilotDecision`, rejects unknown actions or skills, and returns
clear errors instead of executable command objects when output is malformed or schema-invalid.

## Files to create / change

```
pilot/
  src/pilot/decision.py              CHANGE - response parser, validation result/errors
  tests/test_decision_parser.py      NEW - valid/invalid decision parsing tests
```

## Requirements

- Parse raw LLM response text as JSON and reject malformed or non-object responses.
- Validate parsed data through `contracts.PilotDecision`.
- Validate selected skill names against the `pilot.skills` registry.
- Validate embedded skill command/action payloads through contract-owned schemas or pydantic
  adapters; do not hand-accept ad hoc command dictionaries.
- Return clear structured errors for malformed JSON, unknown actions, unknown skills, and
  schema-invalid command parameters.
- Ensure invalid output never returns a `PilotDecision` or other executable command object.
- Keep parsing provider-agnostic and ROS-free.
- Do not implement retry loops or model invocation in this slice.

## Acceptance

- Tests cover valid `continue`, `retry`, `stop`, and `request_human` decisions.
- Tests cover malformed JSON, non-object JSON, unknown actions, unknown skill names, and invalid
  command parameters.
- Tests prove validation errors are clear enough for a retry prompt.
- Tests prove invalid LLM output never produces an executable decision object.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- Provider SDKs, network calls, retry behavior, loop execution, safety validation, ROS publishing,
  assertion computation, recipes, run logging, or replay loop orchestration.
