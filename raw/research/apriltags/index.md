---
topic: what is AprilTags and how does it fit into this project
slug: apriltags
researched: 2026-06-16
sources: [./sources.md]
---

# Research: AprilTags — What They Are and How They Fit the Capstone

> AprilTags are printable fiducial markers (2D barcodes optimized for robotics) that a camera resolves into a precise 3D pose — position, orientation, and tag identity — from a single frame. In this capstone they serve as the **workspace localization layer** on the Raspberry Pi 5 coprocessor: printed tags taped to workspace walls let the Pi compute the robot's `{x, y, heading}` after each action, producing spatial residuals (`dx`, `dy`, `dtheta`) that flow into the Task Telemetry Contract's gap block and feed the LLM self-model's next-generation revision. The VEX V5 native AI Vision Sensor also supports AprilTag detection natively, but the Pi path is recommended for this capstone because it combines localization with YOLO object detection and LLM inference in one pipeline.

---

## Research Questions

1. What are AprilTags, technically — what problem do they solve and how do they work?
2. Where does AprilTag detection happen in the capstone architecture (Pi vs. V5 native)?
3. How do AprilTags integrate with the Task Telemetry Contract and self-model loop?
4. What is the practical implementation (library, tag family, detection call)?
5. What prior research in this project already covers AprilTags?

---

## Current State (Codebase)

No robot code exists yet. From the wiki and prior research:

- **`raw/research/vision-vex-architecture/index.md`** (2026-06-16): The canonical two-computer Pi + V5 architecture research. AprilTags are named explicitly as the workspace localization mechanism on the Pi, using `pip install apriltag` alongside OpenCV and YOLO11n.
- **`wiki/knowledge/concepts/task-telemetry-contract.md`**: The Visual Observation Extension section (added 2026-06-16) defines the full extended contract JSON including `predicted.pose`, `observed.pose`, and gap fields `dx`, `dy`, `dtheta` from AprilTag observations.
- **`wiki/knowledge/entities/tools/vex-v5.md`**: Documents the native AI Vision Sensor's AprilTag support (VEXcode V5 4.0, late 2024).
- **`wiki/knowledge/concepts/reality-gap.md`**: Lists "Fiducials/AprilTags + geometric alignment first, learned perception second" as the primary mitigation strategy.
- **`wiki/knowledge/entities/tools/raspberry-pi-5.md`**: Names `vision_loop.py` (capture → YOLO11n NCNN → `apriltag.detect()` → emit JSON) as the recommended vision loop pattern.

The project has already decided AprilTags belong in the architecture. This research report consolidates what they are and exactly how they plug in, for anyone new to the concept.

---

## Key Findings

### 1. What AprilTags Are [S1][S2][S3]

AprilTags are a visual fiducial system created by the APRIL Robotics Laboratory at the University of Michigan (Edwin Olson, ICRA 2011). They solve the same problem as a QR code — encode an ID in a printable pattern — but are designed specifically for robot localization:

- **2D barcode-style square tags** printed from any printer. Each tag encodes a small integer ID (e.g., tag ID 0–49) in a binary pattern surrounded by a solid black border.
- **6 DOF pose from a single image**: the detection algorithm returns not just "tag #7 is visible" but the camera's full 3D position and orientation relative to the tag (translation vector + rotation matrix). This is the key differentiator from a plain QR code.
- **Robust to adversity**: works at low resolution, under uneven lighting, at sharp view angles, with partial occlusion, and at distances where a QR code would fail.
- **Near-zero compute cost**: the C library has no external dependencies and runs real-time on cell-phone-grade processors. A Raspberry Pi 5 handles it effortlessly alongside YOLO inference.
- **Tag families**: `tag16h5` (small, fewer IDs), `tag25h9` (medium), `tag36h11` (36-bit payload, 11-bit Hamming distance, most commonly used and recommended for robotics).

The practical use case: print several tags, place them at known positions in the workspace. The camera sees the tags and computes the robot's pose relative to that known geometry — a plug-and-play indoor GPS.

### 2. Detection Paths in the Capstone [S4][S5][S7]

Two detection paths exist:

**Path A — Raspberry Pi 5 (recommended):**
- Library: `pip install apriltag` (wraps the official C library)
- Single detection call: `detector.detect(gray_frame)` returns a list of detections, each with `tag_id`, translation vector, rotation matrix, and center pixel
- Runs in `vision_loop.py` alongside YOLO11n NCNN detection
- Output emitted as JSON to `serial_bridge.py`: `{"tag_id": 5, "x": 487, "y": -12, "heading": 2}`
- Alternative: `cv2.aruco.detectMarkers()` (OpenCV ArUco module, built-in with OpenCV — no extra pip install)

**Path B — VEX V5 native AI Vision Sensor:**
- VEXcode V5 4.0 (late 2024) added built-in AprilTag detection via the AI Vision Smart Port sensor
- Very low latency (~20ms), no external hardware
- **Limitation**: only detects tags, no external ML models (no YOLO, no LLM). The Pi path is preferred because it bundles object detection, localization, and LLM inference in one pipeline.

For the Stage 1 demo (Jun 29 2026): use the Pi path with a USB webcam. The V5 native path is a fallback if Pi hardware is unavailable.

### 3. Integration with Task Telemetry Contract and Self-Model Loop [S5][S6]

AprilTags close the robot's **spatial feedback loop** — the equivalent of motor encoder readings, but for position in the workspace:

**Before AprilTags** (motor telemetry only):
```json
{
  "task": "pull",
  "predicted": { "distance_m": 0.5 },
  "observed":  { "distance_m": 0.48 },
  "gap":       { "distance_error_m": -0.02 }
}
```
The gap is a 1D scalar derived from encoder counts — accurate for the arm/wheel rotation but accumulates drift over longer paths.

**After AprilTags** (visual observation added):
```json
{
  "task": "pull",
  "predicted": { "distance_m": 0.5, "pose": {"x": 500, "y": 0, "heading": 0} },
  "observed":  { "distance_m": 0.48, "pose": {"x": 487, "y": -12, "heading": 2} },
  "gap":       { "distance_error_m": -0.02, "dx": -13, "dy": -12, "dtheta": 2 }
}
```
Now the gap block has a 3D spatial residual derived from the actual camera observation rather than integrated encoder counts. The LLM Generator can revise the self-model's predicted motion trajectory, not just its predicted force/torque.

This directly parallels the Hart/Scassellati visual self-observation lineage (`wiki/knowledge/entities/people/justin-hart.md`): the robot observes its own spatial outcome visually and uses that residual to correct its self-model — the core innovation of the capstone.

### 4. Practical Implementation [S8][S9][S10]

```python
# On Raspberry Pi 5
import apriltag, cv2

# Initialize
detector = apriltag.Detector()
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detections = detector.detect(gray)
    for d in detections:
        tag_id  = d.tag_id                 # integer ID
        center  = d.center                 # (x_px, y_px)
        pose    = d.pose_R, d.pose_t       # rotation matrix, translation vector
        # Convert pose to workspace (x_mm, y_mm, heading_deg) with known tag geometry
```

**Tag preparation**:
- Family: `tag36h11` (generate with the official apriltag Python library or online generators)
- Print at 100mm × 100mm on plain white paper, laminate if possible
- Tape to workspace walls at known, measured positions (acts as a coordinate frame anchor)
- At least 3 tags → unambiguous pose estimation from any robot position in the workspace

**OpenCV ArUco alternative** (no extra install):
```python
arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
corners, ids, _ = cv2.aruco.detectMarkers(gray, arucoDict)
```

### 5. Prior Research Coverage [S4][S5]

The `vision-vex-architecture` research report (2026-06-16) already provides the authoritative treatment of AprilTags in this project, including:
- The Pi vision stack (OpenCV → YOLO11n NCNN → `apriltag.detect()`)
- The `vision_loop.py` pattern
- The extended Task Telemetry Contract JSON schema
- Step-by-step implementation outline (including "Print AprilTags at 100mm × 100mm, tape to workspace walls")

The `task-telemetry-contract` wiki page has already been extended with the visual observation section. No new design decisions are needed — AprilTags are already committed in the architecture.

---

## Constraints

1. **Pi power supply**: The Pi 5 cannot draw power from the V5 battery. A USB-C PD power bank must be mounted on the robot.
2. **Camera calibration**: Accurate pose estimation from AprilTags requires camera intrinsic calibration (focal length, distortion coefficients). For the demo, use the `apriltag` library's built-in pose estimator with approximate camera parameters — sufficient for 5–10 cm accuracy at 30–80 cm range.
3. **Tag placement**: Tags must be at known positions in a stable coordinate frame. If the demo table moves, tags move with it and the coordinate frame shifts. Use a fixed anchor (floor or wall mount) for at least 1 tag.
4. **Lighting**: AprilTags are robust to low light but not to motion blur. For slow-moving manipulation tasks (the capstone's primary use case), this is not a problem.

---

## Recommendation

**AprilTags are already the committed localization technology for this project.** No decision remains to be made. The implementation path is:

1. `pip install apriltag` on the Raspberry Pi 5
2. Add `detector.detect(gray_frame)` call to `vision_loop.py` after YOLO inference
3. Convert detected pose to workspace `(x_mm, y_mm, heading_deg)` using known tag placement
4. Emit as JSON alongside YOLO detections over the serial bridge to V5 Brain
5. Merge into Task Telemetry Contract `observed.pose` field; compute `dx`, `dy`, `dtheta` gap
6. Print 3–5 `tag36h11` tags at 100mm × 100mm; tape to stable fixed points in the workspace

The key insight for newcomers: AprilTags are the capstone's **indoor GPS** — they give the robot's camera a ground-truth spatial reading after each action that the LLM self-model can compare against its prediction, producing the spatial gap residuals that drive next-generation self-model revision.

---

## Next Steps

- **Prior research already filed**: `/wiki-ingest raw/research/vision-vex-architecture/index.md` (if not already done) covers the full Pi + AprilTag architecture
- **Task to add**: `/task-add Implement vision_loop.py on Raspberry Pi 5: YOLO11n NCNN + apriltag.detect() + JSON serial bridge`
- **Task to add**: `/task-add Print and mount tag36h11 AprilTag set in demo workspace`
- **Decision already made**: Pi + USB webcam for Stage 1 demo (Jun 29 2026); upgrade to Pi Camera Module 3 Wide if latency matters
