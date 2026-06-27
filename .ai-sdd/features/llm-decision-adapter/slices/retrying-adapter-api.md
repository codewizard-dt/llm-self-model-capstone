# Slice: retrying-adapter-api

| Field | Value |
|---|---|
| Feature | llm-decision-adapter |
| Stack | pilot |
| Depends on | `decision-parser-validation` |

## What this slice delivers

The public adapter API that combines deterministic prompt construction, an injected provider protocol,
response parsing, and bounded retry-on-invalid-output behavior. It includes an in-memory/mock client
for tests, but no real LLM provider implementation.

## Files to create / change

```
pilot/
  src/pilot/decision.py              CHANGE - provider protocol, adapter orchestration, retry policy
  src/pilot/__init__.py              CHANGE - additive exports for adapter API if useful
  tests/test_decision_adapter.py     NEW - retry, exhaustion, mock client, no-provider tests
```

## Requirements

- Define a minimal provider/client protocol for submitting rendered prompts and receiving raw text.
- Provide an in-memory/mock client implementation or test helper for deterministic tests.
- Add an adapter function/class that builds the prompt, invokes the injected client, parses and
  validates the response, and retries malformed or invalid output up to a configured limit.
- Include parse/validation failure context in retry attempts without expanding scope into loop-control
  retry or skill execution.
- Stop after the configured retry limit with a clear adapter error and no executable command object.
- Keep real provider choice, API key handling, network behavior, ROS imports, skill execution, and
  safety validation out of scope.

## Acceptance

- Tests cover successful first-attempt decision adaptation.
- Tests cover malformed JSON followed by a valid retry.
- Tests cover unknown skill or invalid action followed by a valid retry.
- Tests cover retry exhaustion and prove no executable decision object is returned.
- Tests cover deterministic mock/in-memory client behavior.
- Tests prove `pilot.decision` remains ROS-free and provider-SDK-free.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- Real remote or local LLM provider implementation.
- Pilot loop ownership, skill execution, ROS publishing, safety-validator enforcement, assertion
  computation, run logging, replay loop orchestration, recipes, or hardware motion.
