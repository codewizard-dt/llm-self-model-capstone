# Slice: pilot-scaffold-and-cache

| Field | Value |
|---|---|
| Feature | observation-builder |
| Stack | pilot |
| Depends on | - |

## What this slice delivers

The initial `pilot/` Python vertical scaffold plus ROS-free normalized cache/input types that later
observation-builder code can map into `contracts.PilotObservation`. This slice establishes package,
tooling, and input-shape foundations only; it does not implement the full snapshot builder.

## Files to create / change

```
pilot/
  pyproject.toml          NEW - uv project metadata and test/lint config
  Makefile                NEW - sync/test/validate/lint targets
  src/pilot/__init__.py   NEW - package exports
  src/pilot/observation.py NEW - normalized cache/input models and constants
  tests/test_observation_cache.py NEW - cache/input validation tests
Makefile                  CHANGE - delegate sync/test/validate/lint into pilot once the Makefile exists
```

## Requirements

- Use Python and pydantic-compatible patterns consistent with the repo; do not introduce a schema
  definition outside `contracts`.
- Define normalized, ROS-free input/cache models for task objective/phase, robot pose/localization,
  visible objects, visible tags, manipulator state, bridge health, last command/result, recent
  failures, and current assertions.
- Import and reuse contract models where appropriate, especially `PilotAssertion`, `PilotSkillCommand`,
  `PilotSkillResult`, and `PilotTaskPhase`.
- Provide deterministic helpers or ordering keys that a later builder can use for compaction.
- Add package-local tests covering cache construction, stale/missing inputs, and deterministic sort
  keys.
- Add root Makefile delegation for `pilot` targets so repo-level gates include the new vertical.

## Acceptance

- `pilot/` has a working uv project and Makefile.
- `make -C pilot test` and `make -C pilot lint` pass.
- Root `make test`, `make validate`, and `make lint` include the pilot vertical and pass.
- No ROS message class is imported or required by `pilot.observation`.
- No new schema is defined in `pilot/`; schema-bearing outputs remain imported from `contracts`.

## Out Of Scope

- Building the final `PilotObservation` snapshot.
- ROS subscription/live topic wiring.
- LLM prompting, skill registry, safety validation, execution, assertions computation, replay loop, or
  run logging.
