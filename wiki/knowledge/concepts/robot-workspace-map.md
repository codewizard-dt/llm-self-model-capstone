---
id: robot-workspace-map
title: Robot Workspace Map (Multi-Arena JSON Format)
aliases: [workspace map, VEXY_MAP, multi-arena map, AprilTag map]
updated: 2026-06-25
tags: [concept, map, localization, configuration, multi-arena, apriltag, dead-reckoning]
sources:
  - ../sources/apriltag-larger-workspace-map.md
  - ../sources/robot-apriltag-ball-delivery.md
---

# Robot Workspace Map (Multi-Arena JSON Format)

A workspace map is a JSON configuration file that defines the physical environment the robot operates in: arena dimensions, tag placements and roles, and named waypoints for the planner. Loading a different map file switches the robot to a new arena with no code changes.

derived_from::[[apriltag-larger-workspace-map]]
uses::[[apriltag-library]]
extends::[[apriltag-workspace-layout]]
feeds::[[task-telemetry-contract]]

---

## Map file schema

Maps live at `robot/pi-runtime/config/maps/<map-id>.json`. The active map is selected via the `VEXY_MAP=<map-id>` environment variable (follows the existing `VEXY_*` convention in `config/defaults`).

```json
{
  "map_id": "gen0-grab-toss-v1",
  "map_version": "1.0",
  "description": "150cm x 200cm floor arena, ball at west end, bin at east end",
  "arena": {
    "width_mm": 1500,
    "height_mm": 2000,
    "origin": "bottom-left",
    "shape": "rectangle"
  },
  "tag_family": "tag36h11",
  "tag_size_mm": 200,
  "tags": [
    {
      "id": 0,
      "role": "bin",
      "description": "Mounted on bin front face, facing west",
      "pose": {"x_mm": 1800, "y_mm": 750, "heading_deg": 180}
    },
    {
      "id": 1,
      "role": "ball_staging",
      "description": "Taped to table near ball start, facing east",
      "pose": {"x_mm": 200, "y_mm": 750, "heading_deg": 0}
    },
    {
      "id": 2,
      "role": "home",
      "description": "Back wall reference, facing inward",
      "pose": {"x_mm": 200, "y_mm": 200, "heading_deg": 45}
    }
  ],
  "waypoints": {
    "home":          {"x_mm": 250,  "y_mm": 250,  "heading_deg": 90},
    "ball_approach": {"x_mm": 600,  "y_mm": 750,  "heading_deg": 0},
    "ball_pickup":   {"x_mm": 350,  "y_mm": 750,  "heading_deg": 0},
    "throw_point":   {"x_mm": 1400, "y_mm": 750,  "heading_deg": 0}
  }
}
```

The `waypoints` block lets the planner reference named positions without hard-coding coordinates in code. The `arena.shape` field (`"rectangle"` initially) is the extension point for future L-shaped or irregular arenas — add a `"boundary_points"` array without breaking the loader.

---

## Pose memory and dead-reckoning

The map provides the *expected* world poses of each tag. At runtime the [[localizer]] module maintains volatile pose state:

```python
robot_state = {
    "pose": {
        "x_mm": float,
        "y_mm": float,
        "heading_deg": float,
        "confidence": float   # 1.0 = recent tag fix; decays with odometry distance
    },
    "landmarks": {            # populated on first sighting each run
        "0": {"x_mm": ..., "y_mm": ...},
        "1": {"x_mm": ..., "y_mm": ...},
        "2": {"x_mm": ..., "y_mm": ...}
    }
}
```

When a tag enters the camera frame, `update_from_tag()` computes an absolute pose fix and resets `confidence` to 1.0. Between fixes, `update_from_odometry()` integrates encoder ticks and decays confidence. Practical drift: ~1–3 cm per meter on smooth floor; ~2–3× higher on carpet.

---

## Multi-map directory layout

```
robot/pi-runtime/config/
  defaults                      ← VEXY_MAP=gen0-grab-toss-v1
  maps/
    gen0-grab-toss-v1.json     ← first arena (rectangle)
    hallway-test-v1.json        ← future
    l-shaped-arena-v1.json      ← future (add boundary_points array)
```

No code changes are needed to support a new arena — create the JSON file, set `VEXY_MAP`, restart.

## Current ROS 2 Runtime Location

> **Contradiction:** This page originally described maps under `robot/pi-runtime/config/maps/`. [Research: Robot AprilTag Ball Delivery](../sources/robot-apriltag-ball-delivery.md) and the current `vexy_ros` runtime place the active grab/toss maps under `robot/ros2-runtime/config/maps/`. The map shape and tag roles remain the same, but the active implementation location has moved with the ROS 2 runtime.

The delivery program depends on the same semantic map roles: `bin` is tag `0`, `ball_staging` is tag `1`, and `home` is tag `2`. `vexy_deliver_ball` currently uses those role IDs as CLI defaults while allowing overrides for field calibration or alternate arena layouts. relates_to::[[vexy_ros ROS 2 Runtime]]

---

## Industry precedent

The FRC/FTC robotics ecosystem uses identical architecture: Limelight `.fmap` files and WPILib field layout JSONs store tag world poses and are loaded at runtime to localize the robot globally. The capstone simplifies the 3D transform matrix (4×4 homogeneous) to a 2D pose `{x_mm, y_mm, heading_deg}` since the robot operates on a flat floor.
