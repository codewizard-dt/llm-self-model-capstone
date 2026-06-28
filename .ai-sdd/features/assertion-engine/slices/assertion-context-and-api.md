# Slice: assertion-context-and-api

| Field | Value |
|---|---|
| Feature | assertion-engine |
| Stack | pilot |
| Depends on | - |

## What this slice delivers

The ROS-free assertion-engine foundation: immutable pilot-local context/configuration types, the public
assertion id vocabulary, helper construction for contract-valid `PilotAssertion` records, and a small
public API skeleton that downstream evaluator slices can fill in without defining schemas in `pilot`.

## Files to create / change

```
pilot/
  src/pilot/assertions.py       NEW - assertion context, ids, helpers, and public API foundation
  src/pilot/__init__.py         CHANGE - additive exports for assertion engine API
  tests/test_assertions.py      NEW - context/defaults, helper validation, no-ROS tests
```

## Requirements

- Define immutable pilot-local context/configuration for target ball selection, destination selection,
  confidence thresholds, localization age limits, reachability distance, and image-center tolerance.
- Define the required MVP assertion ids exactly: `target_ball_visible`, `robot_pose_reliable`,
  `ball_reachable`, `ball_centered_for_grasp`, `grasp_likely`, `carrying_ball`, `at_destination`,
  `drop_likely`, and `ball_at_destination`.
- Provide helper functions or internal builders that create contract-valid `contracts.PilotAssertion`
  records with evidence, confidence, observed time or age metadata, and optional recovery hints.
- Expose a public entrypoint such as `evaluate_assertions(observation, context)` that accepts
  `contracts.PilotObservation` and returns a stable tuple/list of `contracts.PilotAssertion`.
- Keep evaluator logic minimal in this slice; unknown placeholders for all required ids are acceptable
  only as foundation behavior until the evaluator slice replaces them.
- Keep the module pure Python and ROS-free.

## Acceptance

- Tests prove defaults and explicit context values are immutable, deterministic, and task-configurable.
- Tests prove every required assertion id is present exactly once and in stable order.
- Tests prove helper-created assertions validate through `contracts.PilotAssertion`.
- Tests prove the public entrypoint accepts a `contracts.PilotObservation` and returns contract-valid
  placeholder assertions for all required ids.
- Tests prove `pilot.assertions` can be imported without `rclpy`, ROS message packages, or ROS topic
  classes installed.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- Final true/false evaluator heuristics for object visibility, reachability, grasp, carry, arrival,
  drop, or final delivery success.
- ROS live topic wiring, safety validation, command execution, run logging, replay orchestration, or
  hardware behavior.
- Contract schema changes or pilot-local pydantic schemas.
