# Slice: live-payload-mapping

| Field | Value |
|---|---|
| Feature | pm3-live-observation |
| Stack | pilot |
| Depends on | none |

## What this slice delivers

Add the ROS-free live observation mapping layer that converts compact live ROS JSON evidence into the
existing `pilot.observation.ObservationCache` and `contracts.PilotObservation` snapshot path. The
primary input is `/vision/agent_scene`; fallback inputs are normalized JSON payloads matching
`/vision/scene_map`, `/vision/object_tracks`, `/vex/telemetry`, `/vex/bridge_status`,
`/task_plan/current`, and `/operator/status`. This slice does not subscribe to ROS topics and does not
create a CLI; it is pure payload mapping with deterministic tests.

## Files to create / change

```text
pilot/src/pilot/live_observation.py   NEW - pure payload-to-observation mapping helpers
pilot/src/pilot/__init__.py           CHANGE - additive exports if appropriate
pilot/tests/test_live_observation.py  NEW - mapping and import-safety tests
```

## Requirements

- Provide a public API that accepts an agent-scene mapping plus optional fallback topic mappings,
  `objective`, `observed_ms`, and optional task phase, then returns a `PilotObservation`.
- Convert agent-scene robot pose fields from `yaw_rad` or `heading_deg` into contract `heading_rad`.
- Convert localization fields including source, confidence, and age from live payloads into
  `LocalizationState`.
- Convert visible object evidence into contract `VisibleObject` entries with stable IDs, labels,
  confidence, pose, uncertainty, age, reachability, and source metadata where available.
- Convert visible tag evidence into contract `VisibleTag` entries using tag id, family, confidence,
  pose, and age where available.
- Convert bridge/telemetry/operator health into contract `BridgeHealth` and `ManipulatorState`,
  surfacing stale or unknown values when source fields are missing.
- Preserve existing `build_observation_snapshot` sorting/truncation behavior.
- Do not import `rclpy`, ROS message classes, or `vexy_ros` at module import time.

## Acceptance

- Tests prove representative `/vision/agent_scene` payloads build contract-valid
  `PilotObservation` snapshots.
- Tests prove fallback payloads for scene map, object tracks, telemetry, bridge status, and operator
  status can build a contract-valid snapshot when agent scene is unavailable.
- Tests cover stale or missing bridge/telemetry/object/localization evidence without fabricated
  confidence.
- Tests cover required objective behavior: a missing or blank objective is rejected.
- Tests prove `pilot.live_observation` imports without ROS packages installed.
- Existing observation-builder tests remain green.

## Out of scope

- ROS node/subscription code, command-line argument parsing, output files, manual proof docs, command
  publishers, task-plan request publishers, skill execution, LLM decisions, or contract schema changes.
