# Slice: registry-tests-and-exports

| Field | Value |
|---|---|
| Feature | skill-registry |
| Stack | pilot |
| Depends on | `registry-definitions` |

## What this slice delivers

Additional registry coverage and prompt-friendly export helpers that make the static registry usable
by later LLM decision adapter and safety-validator features without introducing execution behavior.

## Files to create / change

```
pilot/
  src/pilot/skills.py          CHANGE - serializable/prompt-friendly summary helpers if needed
  tests/test_skills.py         CHANGE - metadata bounds, no-ROS, and prompt summary tests
```

## Requirements

- Add a compact serializable representation for registry definitions suitable for future prompt
  construction and validator inspection.
- Prove duration and movement envelopes are present and bounded for every skill.
- Prove registry metadata reuses contract skill names and remains ROS-free.
- Prove command path/result source declarations use symbolic route names only.
- Keep executable precondition checks, safety validation, ROS publishing, and LLM prompting out of
  scope.

## Acceptance

- Tests cover bounded metadata for every skill.
- Tests cover prompt/serialization helper determinism.
- Tests cover no ROS dependency for `pilot.skills`.
- Tests cover symbolic command path/result source declarations.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- Skill execution, safety-validator enforcement, ROS route mapping, assertion computation, recipes,
  or run logging.
