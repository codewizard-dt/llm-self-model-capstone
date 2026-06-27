# Slice: skill-safety-rules

| Field | Value |
|---|---|
| Feature | safety-validator |
| Stack | pilot |
| Depends on | validator-api-and-policy |

## What this slice delivers

Concrete safety rules for the closed MVP skill vocabulary. This slice extends the validator so each
movement or evidence-dependent skill is checked against registry metadata, current observation
freshness, target/destination availability, and per-skill numeric envelopes before it can reach the
future ROS skill executor.

## Files to create / change

```
pilot/
  src/pilot/safety.py          CHANGE - skill-specific evidence and envelope validation rules
  tests/test_safety.py         CHANGE - add focused rule coverage
```

## Requirements

- Validate every command against its registry definition before applying safety rules.
- Reject unknown or missing registry definitions with stable reason codes.
- Enforce the stricter of contract-owned numeric bounds and registry metadata for max duration,
  drive speed, turn rate, arm angle/velocity, claw force, and no-motion verification skills.
- Prefer rejection over silent clamping for user/LLM-provided oversized numeric values.
- Require target or destination evidence for `face_target`, `approach_target`,
  `center_object_in_gripper`, and `go_to_destination` when the skill depends on an observed object,
  tag, destination id, or coordinate target.
- Reject stale localization for navigation or approach rules that require reliable robot pose.
- Keep verification skills ROS-free and limited to observation/assertion/manipulator evidence checks.
- Preserve replay-mode support without requiring live hardware supervision.

## Acceptance

- Each `contracts.PilotSkillName` value has a validation path.
- Oversized duration/speed/turn/arm/claw requests reject with deterministic reason codes.
- Target-dependent skills reject missing or stale target/destination evidence.
- Navigation rejects stale or low-confidence localization when coordinates are used.
- Verification skills never request movement and reject stale or insufficient evidence where required.
- Tests cover representative accepted and rejected cases for all skill families.

## Out Of Scope

- Computing fused task assertions; semantic grasp/drop classification remains owned by
  `assertion-engine`.
- ROS command mapping and execution.
- Changing contract schemas or registry vocabulary.
