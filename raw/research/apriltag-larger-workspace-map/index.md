---
topic: "AprilTag workspace design for larger arenas: tag sizing, detection range, pose memory, and multi-map file format"
slug: apriltag-larger-workspace-map
researched: 2026-06-22
sources: [./sources.md]
---

# Research: AprilTag Larger Workspace & Map Format

> The 80 cm × 80 cm arena recommended in prior research is too small for a Clawbot (50 cm nose-to-tail). The right answer is a **1.5 m × 2 m floor arena** with **200 mm printed tags**, using a checkpoint re-fix pattern so the robot does not need a tag in frame continuously. Maps should be stored as JSON files in `robot/pi-runtime/config/maps/<map-id>.json`, selected at runtime via `VEXY_MAP` env var — the same naming pattern already used in `config/defaults`. Multi-map support requires no code architecture change, only a map-loader module.

---

## Research Questions

1. What workspace size is appropriate for a Clawbot doing grab-and-toss?
2. How does tag size affect detection range, and what tag size is needed for a 1.5–2 m arena?
3. How does pose memory + dead-reckoning work to extend the effective workspace beyond the tag's visual range?
4. What JSON format should workspace maps use, and what fields are needed?
5. How should multi-map support be structured for future arenas of different shapes?

---

## Current State (Codebase)

- **`robot/pi-runtime/config/defaults`**: env file with `VEXY_*` vars. Currently has camera, bridge, serial, and state-dir settings. No map concept yet. [S1]
- **`robot/pi-runtime/src/vexy_system2/state.py`**: provides `atomic_write_json` / `read_json` — the existing pattern for persistent JSON state. Ready to store pose state. [S1]
- **`robot/pi-runtime/src/vexy_system2/camera_broker.py`**: vision pipeline entry point. No localization layer yet. [S1]
- **`robot/pi-runtime/src/vexy_system2/protocol.py`**: defines `MAX_LINEAR`, `MAX_OMEGA`, TTL — the command layer. No map awareness. [S1]
- No `maps/` directory exists yet under `config/`. [S1]

---

## Key Findings

### 1. Workspace size

The Clawbot is 19 in (≈50 cm) from tail to claw. An 80 cm × 80 cm arena leaves only 30 cm of free space per axis after the robot body occupies its own length — insufficient to turn, approach, or maneuver [S2].

**Recommended arena: 150 cm × 200 cm** (roughly 5 ft × 6.5 ft). This gives 3× the robot body length in the short axis and 4× in the long axis — enough to:
- Turn in place without hitting walls (robot width ≈ 30 cm; clearance ≈ 60 cm per side at center)
- Approach the ball from behind and align
- Travel the full grab→toss distance without tag visibility gaps exceeding 1–1.5 m

A standard 8-foot folding table (76 cm × 244 cm) is NOT wide enough at 76 cm. Use the floor, a 6-foot table end-to-end (183 cm) with the robot traveling along the length, or tape out a floor rectangle.

### 2. Tag size → detection range (linear scaling rule)

Detection range scales linearly with physical tag size for a given camera resolution [S3][S4]. The prior wiki entry established 100 mm tags at 640×480 → reliable at 30–80 cm. Extrapolating linearly:

| Tag size (mm) | Reliable detection range | Pose accuracy |
|---|---|---|
| 100 | 30–80 cm | ±3–5 mm at 50 cm |
| 150 | 45–120 cm | good for approach |
| **200** | **60–160 cm** | **recommended for 1.5 m arena** |
| 250 | 75–200 cm | needed for 2 m+ diagonal views |

The formula from the Aerial Robotics Competition reference: "A tag must occupy a sufficient number of pixels in the image for its internal code to be decoded." Tag36h11 requires approximately 10 px per bit-row; the 6-bit interior means a minimum of ~60 px tag width in frame. [S4]

For a 640×480 camera at roughly 60° HFOV (focal length ≈ 554 px):
```
max_detection_range_mm = (tag_size_mm × focal_length_px) / min_px
                       = (200 × 554) / 60
                       ≈ 1847 mm ≈ 1.85 m
```
So 200 mm tags at 640×480 → theoretical max ~1.85 m; practical reliable range ~1.5 m. **Use 200 mm for a 1.5 m × 2 m arena.** Print on A4/Letter paper (210 mm wide) — 200 mm tag with 5 mm margin fits exactly.

### 3. Pose memory + dead-reckoning pattern

The CMU underwater SLAM paper and Duckietown localization project both describe the same hybrid pattern [S5][S6]:

1. **Detect tag → absolute pose fix**: when a tag is in frame, compute `robot_world_pose = f(camera_pose, tag_world_pose)`. Store it as the current best estimate.
2. **Between fixes → odometry integration**: V5 motor encoder ticks → wheel displacement → `Δx, Δy, Δheading`. Accumulate onto the last known pose.
3. **Re-fix on re-entry**: whenever any tag re-enters frame, fuse the new absolute measurement with the odometric estimate (simple override for demo; EKF for production).

Practical drift rate for VEX V5 encoder-only odometry: **~1–3 cm per meter traveled** on smooth floor, more on carpet. For a 1.5 m round trip (grab and return), expect ±3–6 cm accumulated error before re-fix — acceptable for driving to the general bin area. The final throw alignment gets a fresh pose fix when the bin tag (ID 0) enters frame at ≈1 m out. [S5]

**Pose memory data structure** (stored in Pi volatile state, not persisted to disk):
```python
robot_state = {
    "pose": {
        "x_mm": float,      # current best estimate
        "y_mm": float,
        "heading_deg": float,
        "confidence": float  # 1.0 = recent tag fix; decays with distance traveled
    },
    "landmarks": {           # populated on first sight each run
        "0": {"x_mm": ..., "y_mm": ...},  # bin
        "1": {"x_mm": ..., "y_mm": ...},  # ball staging
        "2": {"x_mm": ..., "y_mm": ...}   # home
    }
}
```

### 4. Map file format

The FRC/FTC ecosystem has converged on a JSON "field map" format. Limelight calls it `.fmap`; WPILib publishes official field layout JSONs; PhotonVision and Limelight both consume the same schema [S7][S8]. The 3D transform format (`4×4 homogeneous matrix`) is overkill for a 2D floor task. **Use a simplified 2D capstone format**:

```json
{
  "map_id": "table-grab-toss-v1",
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

The `waypoints` block is the key addition beyond the tag list — it lets the planner reference named positions without hard-coding coordinates in code.

### 5. Multi-map support structure

**Directory layout** (follows existing `VEXY_*` config pattern):
```
robot/pi-runtime/config/
  defaults                         ← add: VEXY_MAP=table-grab-toss-v1
  maps/
    table-grab-toss-v1.json        ← first map
    hallway-test-v1.json           ← second map (future)
    l-shaped-arena-v1.json         ← irregular shape (future)
```

**Env var selection** (consistent with existing `VEXY_BRIDGE_MODE`, `VEXY_SERIAL_PORT` etc.):
```bash
VEXY_MAP=table-grab-toss-v1   # loads config/maps/table-grab-toss-v1.json
```

**New module**: `robot/pi-runtime/src/vexy_system2/localizer.py`
- `load_map(map_id: str) -> dict` — reads and validates JSON from `config/maps/`
- `update_from_tag(detection, map: dict) -> pose` — absolute fix when tag detected
- `update_from_odometry(encoder_delta, current_pose) -> pose` — dead-reckoning step
- `get_vector_to_waypoint(waypoint_name: str, map: dict, current_pose) -> (dx, dy, dheading)` — navigation helper

**Future shape support**: the `arena.shape` field in the JSON allows shapes beyond `"rectangle"`. An `"l-shape"` or `"custom-polygon"` variant can be supported later by adding a `"boundary_points"` array — no schema change needed for the map-loading layer.

---

## Constraints

- V5 motor encoders are the only dead-reckoning sensor available in Stage 1 (no IMU, no LemLib tracking wheels yet). Odometry error will accumulate faster than a tracked-wheel setup.
- The Pi's camera resolution is 640×480 in the current config (`VEXY_CAMERA_WIDTH=640`). Do not reduce resolution below 480×360 or tag detection will degrade at longer ranges.
- Tags must be on rigid, non-moving surfaces. The ball cannot carry a tag — use YOLO for ball detection.
- The `config/defaults` env file uses bare `KEY=VALUE` format (no `export`, no quotes) — match that pattern for `VEXY_MAP`.

---

## Recommendation

**Workspace**: 150 cm × 200 cm floor rectangle, minimum. Mark corners with tape. Robot travels lengthwise (ball at one end, bin at the other).

**Tag size**: Print at **200 mm × 200 mm** (fits A4/Letter with 5 mm margin). This gives reliable detection up to ~1.5 m.

**Tag count**: 3 tags minimum (ID 0 = bin, ID 1 = ball staging, ID 2 = home corner). A 4th tag (ID 3) at the opposite home corner helps when the robot turns away from tag 2.

**Map format**: The simplified 2D JSON schema above. One file per arena configuration. Filename = `map_id` field value + `.json`.

**Multi-map**: `VEXY_MAP` env var selects from `config/maps/`. Add one new map file per new arena — no code changes needed for new environments, only config.

**New code**: One new module `localizer.py` with 4 functions (load, tag-fix, odometry-step, waypoint-vector). Integrates into `camera_broker.py` for the tag-fix path and into the planner for the waypoint path.

**Risks**:
- Carpet floors increase odometry error 2–3×. Demo on smooth floor or low-pile mat.
- Tag pose accuracy degrades at oblique angles (>45°). Mount tags facing the robot's approach direction, not perpendicular to it.
- Larger tags (200 mm) need more white border area — ensure 10 mm quiet zone around the tag border or decoding reliability drops.

---

## Next Steps

- `/task-add` — Implement `localizer.py` with load_map, tag-fix, odometry-step, waypoint-vector
- `/task-add` — Create `config/maps/table-grab-toss-v1.json` first map file and add `VEXY_MAP` to `config/defaults`
- Print 4× tag36h11 tags (IDs 0–3) at 200 mm on matte paper; laminate recommended
- Measure and tape out a 150 cm × 200 cm rectangle on the demo floor
- `/wiki-ingest raw/research/apriltag-larger-workspace-map/index.md` to add this to the knowledge base
