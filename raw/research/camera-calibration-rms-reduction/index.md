---
topic: "how to reduce OpenCV camera calibration RMS reprojection error for IMX708 Wide on Raspberry Pi with ROS 2 — or alternative calibration methods"
slug: camera-calibration-rms-reduction
researched: 2026-06-26
sources: [./sources.md]
---

# Research: Reducing RMS Reprojection Error for IMX708 Wide Camera Calibration

> The primary cause of the 2.47px RMS error on VEXY's IMX708 Wide camera is almost certainly **continuous phase-detection autofocus (PDAF)** adjusting the focal length between calibration captures. OpenCV's `calibrateCamera` assumes a fixed camera matrix K across all frames; when focal length changes per-capture, no single K fits well and RMS inflates. **The fix is to lock focus before calibrating** by setting `AfMode=0` (manual) and an appropriate `LensPosition` via `ros2 param set` on the running camera node, or by editing the libcamera tuning file to disable the `rpi.af` algorithm. Secondary contributors are insufficient pose diversity and potentially a non-flat printed board. If after fixing autofocus the RMS is still high, switching from a plain checkerboard to a **ChArUco board** enables partial-view captures at image edges, which dramatically improves wide-angle distortion fitting.

## Research Questions

1. What causes RMS > 2px in OpenCV calibration on the IMX708 Wide, and what is the primary fix?
2. How can autofocus be reliably disabled on the IMX708 Wide / `camera_ros` for stable calibration?
3. What pose selection and coverage strategies reduce RMS from the capture side?
4. Should we switch from a plain checkerboard to ChArUco or another pattern?
5. What RMS thresholds are acceptable for AprilTag pose estimation at our scale?

## Current State (Codebase)

`robot/ros2-runtime/src/vexy_ros/camera_calibration_capture.py` implements `CheckerboardCalibrator` which:
- Subscribes to `/camera/image_raw` (5 fps, 640×480)
- Uses `cv2.findChessboardCorners` on an 8×6 inner-corner board (9×7 squares, 25mm)
- Captures on Enter keypress via a background stdin thread
- Calls `cv2.calibrateCamera` after 25 samples and writes `/home/vexy/calibration/imx708_wide_640x480.yaml`

The calibration run that produced RMS=2.4755 yielded:
- `fx=558.33, fy=557.27` (close together — reasonable)
- `cx=421.65` vs expected center 320 — **100px off-center**, indicating the solver is compensating for focal drift through the principal point [S1-inference]
- Three sample images show very low camera angle (robot is floor-level), all similar perspectives, with some captures at extreme foreshortening

The camera node is `camera_ros` (Christian Rauch's libcamera ROS 2 node), running as part of `vexy-ros-stack.service` with `AfMode` not explicitly set — meaning libcamera defaults to `AfModeContinuous` for the IMX708 [S2].

## Key Findings

### 1. IMX708 PDAF is the primary culprit [S2][S3][S4]

The IMX708 Wide camera (Pi Camera Module 3 Wide) has **Phase Detection AutoFocus (PDAF)** enabled in continuous mode by default. Libcamera's `AfModeContinuous` runs at all times unless explicitly overridden. Every few frames, the AF algorithm repositions the lens, changing the focal length (fx/fy in the K matrix). When calibration captures span multiple AF adjustments, OpenCV fits a single K that minimizes total error across all frames — but since the true focal length varies per-frame, no single K fits well. This is a well-known failure mode for calibration on cameras with continuous AF [S3][S4].

The `cx=421.65` result (100px off expected center for a 640-wide image) is a secondary symptom: when the solver cannot properly fit `fx` due to focal drift, it displaces the principal point to compensate.

### 2. How to lock focus on IMX708 Wide via camera_ros [S2][S5][S6]

`camera_ros` exposes libcamera controls as ROS parameters. Two controls are needed:

```bash
# Option A: runtime parameter set (camera_ros running, no restart needed)
ros2 param set /camera AfMode 0          # 0 = AfModeManual
ros2 param set /camera LensPosition 2.0  # diopters; 2.0 = ~50cm focus distance
```

**Critical**: `LensPosition` is **ignored** unless `AfMode` is already `AfModeManual` (value 0) [S5]. Set both, in that order. For calibration at ~50–80cm board distance, `LensPosition 1.5–2.0` is appropriate (formula: diopters = 1 / distance_m).

Option B — edit the tuning file to permanently disable AF for calibration:
```bash
# On the Pi, copy the wide tuning file and comment out rpi.af
sudo cp /usr/share/libcamera/ipa/rpi/vc4/imx708_wide.json /home/vexy/imx708_wide_naf.json
# Edit: rename "rpi.af" to "rpi.af.disabled" inside the file
LIBCAMERA_RPI_TUNING_FILE=/home/vexy/imx708_wide_naf.json <launch command>
```
Then use `v4l2-ctl --set-ctrl focus_absolute=<value>` to set a fixed hardware lens position [S3].

Option C — hardware: **disable the VCM driver entirely** via device tree:
```
dtoverlay=imx708,vcm=0
```
and remove `camera_auto_detect=1` from config. This prevents libcamera from ever driving the lens actuator [S6]. Most invasive but most reliable.

Option D (hardware): Arducam sells a fixed-focus IMX708 variant (no autofocus at all) [S7], which would permanently solve this class of issue.

### 3. Pose selection improvements [S8][S9][S10]

The ROS `camera_calibration cameracalibrator` progress bars track X, Y, tilt-X, and tilt-Y coverage — capturing across all four is necessary for accurate distortion estimation. Looking at the sample images from the failed run:
- All samples were taken from a very similar low-angle perspective (camera is floor-mounted)
- Few captures showed extreme tilt, and they were mostly in the lower half of the frame

Required for adequate coverage:
- **Frame position**: board must appear in all 4 quadrants of the image (upper-left, upper-right, lower-left, lower-right), not just center
- **Tilt**: left-leaning (left edge closer), right-leaning, top-leaning, bottom-leaning — each by 20–40°
- **Distance**: at least one "close" (board fills >50% of frame) and one "far" (board is ~25% of frame)
- **Face-on**: at least 5 near-frontal captures for conditioning the principal point

For VEXY's floor-mounted camera, taping the board to the ground at various positions and angles may work better than hand-holding.

### 4. ChArUco boards vs plain checkerboard [S11][S12][S13]

| Criteria | Plain Checkerboard | ChArUco Board |
|---|---|---|
| Corner accuracy | High (subpixel) | High (subpixel, from checkerboard part) |
| Partial view | No — full board required | Yes — each marker independently ID'd |
| Edge coverage | Hard: board must be fully visible | Easy: position board partially outside frame |
| Detection robustness | Fails under lighting variations | Better; ArUco part is more robust |
| Wide-angle calibration | Difficult at extreme angles | Better: can use partial captures |
| OpenCV API stability | Stable | Changed significantly in OpenCV 4.7+ |
| Implementation complexity | Low (current code) | Medium (CharucoDetector class) |
| Accuracy ranking | ≥ ChArUco | ≤ Checkerboard (slight disadvantage) |

**For the IMX708 Wide** (a wide-angle lens with significant peripheral distortion), ChArUco is advantageous specifically because it allows partial-view captures at image corners and edges — exactly where distortion is strongest and most important to constrain. With a plain checkerboard, the full board must be visible, making it hard to get calibration data from the image periphery [S11][S12].

The key limitation: ChArUco slightly underperforms plain checkerboard in raw corner localization accuracy, but this is outweighed by the ability to sample distortion at image edges. For the IMX708 Wide specifically, edge coverage is the bottleneck.

### 5. RMS thresholds for AprilTag pose estimation [S8][S14]

| RMS (px) | Quality | Suitability |
|---|---|---|
| < 0.5 | Excellent | Precise industrial/research use |
| 0.5–1.0 | Acceptable | Most robotics applications |
| 1.0–1.5 | Marginal | Simple presence detection; poor for pose |
| > 1.5 | Poor | AprilTag 6DoF pose will be unreliable |
| 2.47 (current) | Very poor | Expect 5–15% pose error; tag detection unstable |

For VEXY's use case (AprilTag 36h11 at 0.5–2m range for navigation), a target of **< 0.8px** is needed for reliable 6DoF pose estimation. Values around 0.3–0.5px are achievable on the IMX708 with fixed focus and good pose coverage.

### 6. Board flatness and print quality [S9]

A printed checkerboard on flimsy paper flexes when held, introducing non-planar 3D point errors. OpenCV's `calibrateCamera` assumes the board is perfectly flat (all Z=0 in object coordinates). Mounting the print on foam-core board, aluminum, or stiff cardboard glued flat eliminates this source of error. A warped board alone can add 0.3–0.7px to RMS.

## Constraints

- Camera is IMX708 Wide via `camera_ros` (libcamera RPi fork) — AF control must go through libcamera controls or device tree
- Camera runs as part of `vexy-ros-stack.service` — changing camera parameters requires `ros2 param set` to the running `/camera` node, or a service restart with new parameters
- Calibration script subscribes to `/camera/image_raw` — the camera must already be running
- Resolution must be fixed at 640×480 for calibration (matches runtime resolution)
- No display on Pi — Foxglove Studio at `ws://10.10.3.4:8765` is the live feedback channel

## Solution Comparison

| Criteria | Fix AF Only (Option A) | Fix AF + Pose Discipline | Switch to ChArUco |
|---|---|---|---|
| **Approach** | Set `AfMode=0, LensPosition=2.0` via param set, re-run existing calibration | Same AF fix + strict pose coverage protocol (quadrants + tilts) | Implement ChArUco board capture in `camera_calibration_capture.py` |
| **Expected RMS** | 0.5–1.5px | 0.3–0.8px | 0.3–0.7px |
| **Complexity** | 2 shell commands | 2 commands + board protocol | New code (~80 lines) + print new board |
| **Dependencies** | None | Rigid board backing | OpenCV aruco module (already in cv2) |
| **Codebase fit** | Drop-in | Drop-in | Requires new node or mode |
| **Risk** | `ros2 param set` may not persist after restart | Same; also depends on operator discipline | API churn in OpenCV 4.7+ |

## Recommendation

**Immediate (do now):** Lock focus before each calibration run.

```bash
# Step 0: lock focus BEFORE running calibration
sshpass -p 'vexytime' ssh vexy@10.10.3.4 \
  "source /opt/ros/jazzy/setup.bash && \
   ros2 param set /camera AfMode 0 && \
   sleep 0.5 && \
   ros2 param set /camera LensPosition 2.0"

# Step 1: run calibration as normal (Enter-to-capture)
# ... (existing command)
```

Expected result: RMS drops to 0.5–1.0px from focus-lock alone.

**Also do now:** Improve pose coverage during the capture session:
- Put the board on a flat surface (not hand-held) for at least some captures
- Tape the board at 4 corner positions of the robot's floor view
- Get at least 3 captures with significant tilt (>20°) left, right, toward, and away

**Short-term code improvement:** Add AF lock as a pre-flight step to the calibration script:

```python
# In main(), before starting the ROS spin:
node.get_logger().info("Locking camera focus for calibration...")
node.set_parameters([
    rclpy.parameter.Parameter("AfMode", value=0),
    rclpy.parameter.Parameter("LensPosition", value=2.0),
])
time.sleep(1.0)  # allow AF to settle
```

Note: this sets parameters on the *calibration* node itself, not `/camera`. The right approach is calling the `/camera` node's `set_parameters` service from within the calibration script, or using a `ros2 param set` subprocess call.

**Medium-term:** Switch to ChArUco for the Wide camera.
Implement a `--charuco` mode flag in `camera_calibration_capture.py` using `cv2.aruco.CharucoBoard` and `cv2.aruco.CharucoDetector` (OpenCV 4.7+ API). This enables partial-view captures at image edges, which is the most impactful remaining improvement for a wide-angle lens.

**Risks and mitigations:**
- `ros2 param set /camera AfMode 0` may fail if `camera_ros` doesn't expose this control as a settable parameter at runtime → mitigation: test with `ros2 param get /camera AfMode` first; fallback is the tuning file approach
- ChArUco API changed in OpenCV 4.7; old `CharucoBoard_create()` is deprecated → use `cv2.aruco.CharucoBoard((cols, rows), square_length, marker_length, dictionary)` and `cv2.aruco.CharucoDetector(board)`

## Next Steps

1. **Run focus-lock + recalibrate immediately** — expected to drop RMS to < 1.0px
2. **Verify `ros2 param get /camera AfMode`** to confirm the parameter is available on the running node
3. If RMS still > 1.0px after AF fix, add a flat rigid board backing and improve pose coverage
4. If still > 1.0px, implement ChArUco mode in the calibration script
5. After successful calibration, run full validation: `/camera/camera_info` K/D/P nonzero, `/camera/image_rect` at rate, AprilTag `/tf` poses plausible
6. Add RMS threshold gate to `calibrate_and_write()` — fail with exit code 1 if RMS > 1.0
