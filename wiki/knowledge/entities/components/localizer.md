---
id: localizer
title: localizer.py
aliases: [localizer, vexy localizer, pose localizer]
updated: 2026-06-22
sources:
  - ../../../raw/research/apriltag-larger-workspace-map/index.md
tags: [component, python, localization, dead-reckoning, apriltag, map]
---

# localizer.py

Proposed Python module at `robot/pi-runtime/src/vexy_system2/localizer.py`. Bridges the [[robot-workspace-map]] (static JSON config) and the runtime pose state (volatile, in-memory). Does not yet exist — this is the planned implementation.

planned_for::[[robot-workspace-map]]
runs_on::[[raspberry-pi-5]]
integrates_with::[[apriltag-library]]
feeds::[[task-telemetry-contract]]

---

## Four planned functions

| Function | Signature | Purpose |
|---|---|---|
| `load_map` | `(map_id: str) -> dict` | Read and validate `config/maps/<map_id>.json`; raise on schema error |
| `update_from_tag` | `(detection, map: dict, current_pose: dict) -> dict` | Absolute pose fix from a tag detection; resets `confidence` to 1.0 |
| `update_from_odometry` | `(encoder_delta: dict, current_pose: dict) -> dict` | Dead-reckoning step from V5 motor encoder ticks; decays `confidence` |
| `get_vector_to_waypoint` | `(name: str, map: dict, current_pose: dict) -> tuple` | Returns `(dx_mm, dy_mm, dheading_deg)` toward a named waypoint |

## Pose state schema

```python
pose = {
    "x_mm": float,
    "y_mm": float,
    "heading_deg": float,
    "confidence": float   # 1.0 = fresh tag fix; decays with distance traveled
}
```

The `landmarks` dict (keyed by tag ID string) is populated on first sighting each run and used by `update_from_tag` to compute absolute fixes on subsequent sightings.

## Integration points

- **`camera_broker.py`** — calls `update_from_tag()` whenever `detector.detect()` returns a hit
- **`planner_demo.py`** — calls `get_vector_to_waypoint()` to compute drive commands toward named positions
- **`state.py`** — `atomic_write_json` can persist pose for debugging; not required for runtime operation

## Drift characteristics

V5 motor encoder odometry on smooth floor: ~1–3 cm per meter. On carpet: 2–3× higher. For a 1.5 m round trip (grab + return), expect ±3–6 cm accumulated error before next tag re-fix. This is acceptable for approach drives; the final throw alignment always gets a fresh fix from tag 0 (bin) at ~1 m range.
