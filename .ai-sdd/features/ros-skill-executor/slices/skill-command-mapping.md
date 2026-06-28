# Slice: skill-command-mapping

| Field | Value |
|---|---|
| Feature | ros-skill-executor |
| Stack | pilot |
| Depends on | executor-core-api |

## What this slice delivers

Deterministic mapping from the closed pilot skill vocabulary to executor payloads. This slice converts
validated skill commands into compact operator-command JSON payloads using registry metadata and
contract parameters, and handles non-motion verification skills without publishing robot motion.

## Files to create / change

```
pilot/
  src/pilot/executor.py        CHANGE - all MVP skill mappings and assertion-only paths
  tests/test_executor.py       CHANGE - mapping coverage for every PilotSkillName
```

## Requirements

- Provide an explicit mapping or explicit non-motion path for every `contracts.PilotSkillName`.
- Map movement and manipulator skills to the existing operator command surface, preserving the pilot
  `command_id` in the payload whenever possible.
- Use the approved `/operator/command` route first; reserve `/task_plan/request` only for skills whose
  registry route requires it.
- Derive payload parameters from validated command models rather than ad hoc dictionaries from LLM
  output.
- Implement `verify_grasp` and `verify_drop` as observation/assertion-only executor paths that do not
  publish transport payloads.
- Keep the mapping table aligned with `pilot.skills` registry metadata and fail tests if contract
  skill names are added without executor coverage.

## Acceptance

- Tests prove every MVP skill is mapped or explicitly assertion-only.
- Published payloads are JSON-compatible plain data and include route/action, command id, skill, and
  bounded parameters needed by the operator surface.
- `stop` maps to an operator/control halt request.
- `survey_scene`, facing/approach/centering/navigation, arm, and claw skills map to the expected
  operator actions or bounded control routes.
- Verification skills return deterministic observation/assertion results and publish nothing.

## Out Of Scope

- ROS node implementation or real topic publication.
- Rich fused assertion logic; `assertion-engine` owns that later.
- Safety checks beyond refusing non-accepted validation results.
