---
id: apriltag-larger-workspace-map
title: "Research: AprilTag Larger Workspace & Map Format"
updated: 2026-06-22
sources:
  - ../../raw/research/apriltag-larger-workspace-map/index.md
tags: [source, research, apriltag, workspace, localization, map, dead-reckoning]
---

# Research: AprilTag Larger Workspace & Map Format

Research report (2026-06-22) correcting the initial 80 cm × 80 cm arena recommendation and specifying the map format for multi-environment support. Supersedes the workspace-size and tag-size claims in the initial AprilTag research.

supersedes::[[apriltag-workspace-layout]] (workspace size and tag size sections only)
derived_from::[[apriltags]]
extends::[[apriltag-library]]
extends::[[vex-coprocessor-pattern]]

**The 80 cm × 80 cm arena is too small.** The Clawbot is 50 cm from tail to claw — an 80 cm arena leaves only 30 cm of free space per axis, which is insufficient to turn, align, or maneuver. **Correct arena: 150 cm × 200 cm** (≈5 ft × 6.5 ft), providing 3× the robot body length in the short axis. An 8-foot folding table (76 cm wide) is also too narrow — use the floor or a taped rectangle.

**Detection range scales linearly with tag size.** At 640×480, 100 mm tags detect reliably at 30–80 cm. Extrapolating: 150 mm → 45–120 cm; **200 mm → 60–160 cm** (practical ~1.5 m); 250 mm → 75–200 cm. The theoretical max for 200 mm at 640×480 with focal length ≈554 px and minimum ~60 px tag width = `(200 × 554) / 60 ≈ 1847 mm`. **Print at 200 mm on A4/Letter paper** (210 mm wide; 5 mm margin fits exactly).

**Checkpoint re-fix pattern removes the continuous-visibility requirement.** The robot stores each landmark's world position on first sighting, then dead-reckons via V5 motor encoder odometry (~1–3 cm drift per meter on smooth floor). A fresh pose fix happens automatically whenever a tag re-enters frame — which is engineered to occur just before each precision maneuver (approach to ball, final throw alignment). The robot does not need a tag continuously visible.

**Map format: simplified 2D JSON.** The FRC/FTC ecosystem uses Limelight `.fmap` and WPILib field layout JSON (4×4 transform matrices). For the capstone's 2D floor task, a simpler format suffices: `map_id`, `arena` (width/height/shape/origin), `tag_family`, `tag_size_mm`, `tags[]` (id + role + world pose `{x_mm, y_mm, heading_deg}`), and `waypoints{}` (named positions for the planner). The `arena.shape` field (`"rectangle"` initially) is the extension point for future L-shaped or irregular arenas.

**Multi-map support via `VEXY_MAP` env var.** Maps live in `robot/pi-runtime/config/maps/<map-id>.json`. The `VEXY_MAP=<map-id>` env var (matching the existing `VEXY_*` convention in `config/defaults`) selects the active map at runtime. New arenas require only a new JSON file — no code changes. A new `localizer.py` module (4 functions: `load_map`, `update_from_tag`, `update_from_odometry`, `get_vector_to_waypoint`) is the sole new code artifact.
