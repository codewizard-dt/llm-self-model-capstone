---
topic: what is AprilTags and how does it fit into this project
slug: apriltags
researched: 2026-06-16
---

# Primary Sources — AprilTags

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://april.eecs.umich.edu/software/apriltag | 2026-06-16 | Official definition: "visual fiducial system"; precise 3D position, orientation, identity from single image; C library with no external deps; robust to lighting/occlusion/view angle; tag families; ICRA 2011 origin |
| S2 | web | https://docs.wpilib.org/en/stable/docs/software/vision-processing/apriltag/apriltag-intro.html | 2026-06-16 | FRC/WPILib description: "low overhead, high accuracy localization"; per-tag 3D pose estimate from camera intrinsics; confirms tag36h11 as standard robotics family |
| S3 | web | https://april.eecs.umich.edu/papers/details.php?name=olson2011tags | 2026-06-16 | Original ICRA 2011 paper abstract: "full 6 DOF localization of features from a single image"; Hamming-distance coding system; stronger than ARTag; Edwin Olson, University of Michigan |
| S4 | codebase | `wiki/knowledge/sources/vision-vex-architecture.md` | 2026-06-16 | Pi vision stack: OpenCV + YOLO11n + `apriltag` library; `detector.detect(gray_frame)` returns tag ID + 3D pose; 8 FPS sufficient for capstone manipulation tasks; extends Task Telemetry Contract |
| S5 | codebase | `raw/research/vision-vex-architecture/index.md` | 2026-06-16 | Full vision architecture research: two-computer split; tag36h11 at 100mm×100mm; `vision_loop.py` pattern; extended contract JSON with `observed.pose`; spatial gap residuals `dx`, `dy`, `dtheta`; Hart/Scassellati lineage |
| S6 | codebase | `wiki/knowledge/concepts/task-telemetry-contract.md` | 2026-06-16 | Visual Observation Extension section: full extended contract JSON schema; AprilTag localization description; self-model capability layer additions (`camera_fov_deg`, `camera_mount_height_mm`, `visual_range_mm`) |
| S7 | codebase | `wiki/knowledge/entities/tools/vexcode.md` | 2026-06-16 | VEXcode V5 4.0 (late 2024): AI Vision Sensor now supports AprilTag detection + classroom/competition object classification natively via Smart Port |
| S8 | web | https://pypi.org/project/apriltag/ | 2026-06-16 | (cited in raw/research/vision-vex-architecture/sources.md S9) pip install apriltag; single-call API: `detector.detect(gray_frame)` returns id + 3D pose; tag36h11 family |
| S9 | web | https://pyimagesearch.com/2020/11/02/apriltag-with-python/ | 2026-06-16 | (cited in raw/research/vision-vex-architecture/sources.md S10) "pip-installable"; works with OpenCV-loaded images; real-time on Pi; confirms Python is first-class |
| S10 | web | https://github.com/masoug/apriltag-localization | 2026-06-16 | (cited in raw/research/vision-vex-architecture/sources.md S11) FRC 2023 used AprilTags for field localization; open-source soft-real-time implementation for Raspberry Pi; confirms production robotics use case |
| S11 | codebase | `wiki/knowledge/concepts/reality-gap.md` | 2026-06-16 | Lists "Fiducials/AprilTags + geometric alignment first, learned perception second" as primary mitigation for the reality gap |

---

## Excerpts

### S1 — APRIL Robotics Lab, University of Michigan
https://april.eecs.umich.edu/software/apriltag
> "AprilTag is a visual fiducial system, useful for a wide variety of tasks including augmented reality, robotics, and camera calibration. Targets can be created from an ordinary printer, and the AprilTag detection software computes the precise 3D position, orientation, and identity of the tags relative to the camera."
> "The AprilTag library is implemented in C with no external dependencies. It is designed to be easily included in other applications, as well as be portable to embedded devices. Real-time performance can be achieved even on cell-phone grade processors."

### S2 — FIRST Robotics Competition / WPILib AprilTag Intro
https://docs.wpilib.org/en/stable/docs/software/vision-processing/apriltag/apriltag-intro.html
> "AprilTags are a system of visual tags developed by researchers at the University of Michigan to provide low overhead, high accuracy localization for many different applications."
> "Using assumptions about how the camera's lens distorts the 3d world onto the 2d array of pixels in the camera, an estimate of the camera's position relative to the tag is calculated."

### S3 — ICRA 2011 Paper (Olson)
https://april.eecs.umich.edu/papers/details.php?name=olson2011tags
> "We describe a new visual fiducial system that uses a 2D bar code style 'tag', allowing full 6 DOF localization of features from a single image. Our system improves upon previous systems, incorporating a fast and robust line detection system, a stronger digital coding system, and greater robustness to occlusion, warping, and lens distortion."

### S4 — wiki/knowledge/sources/vision-vex-architecture.md (project wiki)
> "the `apriltag` Python library (`pip install apriltag`) for workspace localization — a single `detector.detect(gray_frame)` call returns tag ID + 3D pose. For the capstone's slow manipulation tasks, 8 FPS is more than sufficient."
> "vision extends the relates_to::[[task-telemetry-contract]] with `predicted.object_detected`, `observed.object_detected`, `observed.pose` fields — giving the relates_to::[[llm-authored-self-model]] a perception capability layer and enabling AprilTag-based spatial residuals in the gap model, directly paralleling the Hart/Scassellati visual self-observation lineage."

### S5 — raw/research/vision-vex-architecture/index.md (project research)
> "AprilTags for localization: `pip install apriltag` (wraps the official C library). Single call: `detector.detect(gray_frame)` returns tag id + 3D pose (translation + rotation). Place printed tags around the workspace; Pi detects and returns `{tag_id, x, y, z, heading}` in real time. Enables the robot to know *where it is in the workspace* without odometry calibration."
> "Predicted spatial outcome: `{x: 500, y: 0, heading: 0}` (self-model predicts robot pose after action). Observed spatial outcome: `{x: 487, y: -12, heading: 2}` (camera reads pose from AprilTag landmarks). Gap: `{dx: -13, dy: -12, dtheta: 2}` (residual that feeds next-generation self-model revision)"

### S6 — wiki/knowledge/concepts/task-telemetry-contract.md (project wiki)
> "AprilTag localization: printing tag36h11 family tags (100mm × 100mm) around the workspace lets the Pi compute the robot's pose (`{x, y, heading}`) from camera observations alone — no odometry calibration required. The LLM self-model predicts a pose after each action; the AprilTag observation is the ground-truth comparison. The `dx`, `dy`, `dtheta` residuals feed the next-generation self-model revision as spatial gap data, directly paralleling the Hart/Scassellati visual self-observation approach."

### S7 — wiki/knowledge/entities/tools/vexcode.md (project wiki)
> "AI Vision Sensor: AprilTag detection + classroom/competition object classification (VRC High Stakes 2024–25 game elements, balls, rings, cubes)"
