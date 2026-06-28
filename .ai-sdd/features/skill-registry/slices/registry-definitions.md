# Slice: registry-definitions

| Field | Value |
|---|---|
| Feature | skill-registry |
| Stack | pilot |
| Depends on | - |

## What this slice delivers

The static ROS-free skill registry module for the MVP pilot skill vocabulary. It defines immutable
metadata for each bounded skill and a small public API to list and retrieve definitions. This slice
focuses on the registry implementation and core completeness tests.

## Files to create / change

```
pilot/
  src/pilot/skills.py          NEW - immutable skill definitions and lookup/list API
  src/pilot/__init__.py        CHANGE - additive exports for registry API
  tests/test_skills.py         NEW - completeness, deterministic ordering, and lookup tests
```

## Requirements

- Implement immutable dataclasses for skill definitions and static metadata.
- Key definitions by `contracts.PilotSkillName`.
- Cover every MVP skill exactly once.
- Include inputs/defaults, preconditions, max duration, max movement envelope, command path, expected
  result source, success assertion, failure reasons, and recovery hints.
- Use symbolic command paths/result sources only; do not import ROS packages or message classes.
- Provide deterministic `list_skill_definitions()` and strict `get_skill_definition()` APIs.
- Do not perform runtime safety validation or command execution.

## Acceptance

- Every `contracts.PilotSkillName` enum value has exactly one definition.
- Registry listing order is deterministic.
- Unknown lookup raises a clear exception.
- Each definition includes non-empty preconditions, failure reasons, recovery hints, command path,
  expected result source, and success assertion metadata.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- Runtime clamping/enforcement, safety validation, ROS execution, LLM prompt rendering, recipes, run
  logging, and replay loop orchestration.
