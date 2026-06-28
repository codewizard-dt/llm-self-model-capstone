# Slice: assertion-evaluators

| Field | Value |
|---|---|
| Feature | assertion-engine |
| Stack | pilot |
| Depends on | `assertion-context-and-api` |

## What this slice delivers

The deterministic assertion evaluators for the first delivery task. This slice replaces foundation
placeholder outcomes with fused evidence heuristics for visibility, localization reliability,
reachability, centering, grasp, carry, destination arrival, drop likelihood, and final ball-at-
destination classification.

## Files to create / change

```
pilot/
  src/pilot/assertions.py       CHANGE - evaluator heuristics and evidence fusion
  tests/test_assertions.py      CHANGE - true/false/unknown evaluator coverage
```

## Requirements

- Evaluate `target_ball_visible` using target id/label and confidence thresholds from context.
- Evaluate `robot_pose_reliable` using pose presence, localization confidence, localization age, and
  bridge fault/stale state.
- Evaluate `ball_reachable` and `ball_centered_for_grasp` using available object bbox/pose evidence,
  reachability thresholds, and image-center/grasp corridor tolerance.
- Evaluate `grasp_likely` and `carrying_ball` using at least two evidence classes: manipulator or
  skill-result evidence plus vision/object state or held-object state.
- Evaluate `at_destination`, `drop_likely`, and `ball_at_destination` using destination context,
  localization/tag evidence, manipulator state, last skill result, and visible object evidence.
- Return `unknown` with clear recovery hints when evidence is missing, stale, unsafe, or contradictory.
- Do not call the LLM, publish commands, execute stops, or import ROS packages.

## Acceptance

- Tests cover true, false, and unknown outcomes for `target_ball_visible`, `robot_pose_reliable`,
  `grasp_likely`, `carrying_ball`, `drop_likely`, and `ball_at_destination`.
- Tests cover reachable and centered ball outcomes when bbox or pose evidence is available, and
  `unknown` when required evidence is absent.
- Tests cover destination arrival using configured destination pose or tag-relative context.
- Tests prove conflicting grasp/drop evidence returns `unknown`, not confident success.
- Tests prove all evaluator outputs include meaningful evidence entries and bounded confidence.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- LLM judging of ambiguous assertions.
- Skill baseline capture, delivery recipe orchestration, replay loop, run logging, safety validation,
  executor route mapping, or hardware verification.
- New contract fields or schema changes.
