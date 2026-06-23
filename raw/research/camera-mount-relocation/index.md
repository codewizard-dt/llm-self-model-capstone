---
topic: "Camera mount relocation for VEX V5 Clawbot: RPi Camera Module 3 currently has angle/visibility issues for the object in front of the scoop/claw; robot is 10\"×10\" base, Pi on back, 30cm ribbon incoming; suggest best new or existing mount location"
slug: camera-mount-relocation
researched: 2026-06-23
sources: [./sources.md]
---

# Research: Camera Mount Relocation for VEX V5 Clawbot

> The camera is currently at roughly body height on the rear of the robot, producing a horizontal viewing angle that misses objects near floor level directly in front of the claw. The **best existing spot** is the top of the stationary arm-pivot tower (~8–9" height, center-rear of robot), camera tilted 30° below horizontal — this covers the entire grab/scoop zone (5–15" in front) with a straight ribbon path of ~25–28 cm from the Pi CSI connector. If ribbon routing turns out to be tight, a **plywood I-beam rear mast** (~10–12" tall, bolted to the existing back C-channel holes) achieves the same geometry with only 5–8 cm of ribbon while keeping the camera well clear of the swinging arm. Both options require tilting the camera module ~30° downward before securing it.

---

## Research Questions

1. What is the current camera placement geometry and why does it fail to see the target object?
2. What existing structural points on the Clawbot offer a high, forward-facing mounting location?
3. How does the 30 cm ribbon constraint change which locations are reachable from the rear-mounted Pi?
4. What viewing angle / height produces reliable YOLO object detection for a ground-level object 5–15" in front of the robot?
5. Is a new plywood mast structure necessary, or can an existing point meet the requirements?

---

## Current State

From the design photos (`raw/design/`) and the wiki:

| Fact | Source |
|------|--------|
| Robot base: **10" × 10"** (25.4 cm × 25.4 cm) | Photos + user measurement |
| Robot height at arm tower top: **~8–9"** | Photo PXL_20260623_003559372 (tape measure) |
| Pi mounted on **rear** of robot, CSI connector ~3" from back edge of frame | Wiki: `rpi-complete-kits-mobile-power` |
| Incoming ribbon length: **30 cm (≈ 11.8")** replacing the current 11" ribbon | User note |
| Camera Module 3 FOV: **75° H × 56° V** (standard) or **120° diagonal** (Wide) | Wiki: `vision-vex-architecture` |
| Arm: pivots from stationary C-channel tower near center-rear; arm tip swings forward and down | Wiki: `vex-v5-clawbot-build-instructions` |
| End-effector: scoop (passive) — object picked up at floor level, ~8–15" in front of robot | Wiki: `clawbot-scoop-replacement` |

### Why the current placement fails

The Pi CSI connector sits ~3" from the back edge of the 10" base. The current 11" ribbon exits ~3" into the robot body, giving ~8" of reach — barely enough to reach the front face of the chassis, and only at body height (~4–5"). A **horizontal** camera at 4–5" height looking forward can see the workspace 2–3 ft out, but objects **close to the floor directly in front** (within 0–10") fall **below the camera's downward FOV limit** unless the camera is tilted steeply downward — which the current mount apparently does not do.

Additionally, the arm itself can occlude the forward view from a rear-body-height camera when the arm is extended forward and down for a grab.

---

## Ribbon Reach Geometry

**Pi CSI connector position:** ~3" from back edge of 10" base → **7" from front face**.

**30 cm = 11.8" total ribbon.** After accounting for gentle bends (no kinking allowed on FPC cables), usable reach ≈ **25–27 cm from the connector**.

| Destination | Straight-line distance from Pi connector | Fits 30 cm ribbon? |
|---|---|---|
| Front chassis rail (horizontal) | 7" = 17.8 cm | ✓ easily |
| Front chassis rail, routed over top | ~10" = 25.4 cm | ✓ with care |
| Arm tower top (~5" forward, ~8" up from chassis) | √(5²+8²) = 9.4" minimum; routed: ~13" = 33 cm | **⚠ tight — may need routing tricks** |
| Rear plywood mast (~10-12" tall, at back) | ~10–12" = 25–30 cm (straight up) | ✓ just fits |
| Center-top of robot (~5" forward, ~4" up) | ~6.4" = 16 cm | ✓ easily |

---

## Key Findings

**F1 — Industry standard for pick-and-place: camera high + angled down [S3]**
Best practices for manipulation robots recommend cameras at 150 cm height, 45° downward, or at ~50 cm facing forward with a slight downward angle. The standard pattern is "overhead static camera for approach, wrist-mounted camera for fine-grab." For this capstone (single camera), a fixed elevated camera angled ~30–45° down achieves the best single-camera coverage of the grab zone.

**F2 — Arm pivot tower is the highest FIXED existing point [S1, S2]**
The stationary C-channel arm tower (84T gear is attached here; it does NOT move with the arm) reaches ~8–9" height. The arm itself pivots from this tower and swings from horizontal-forward (grab position) to roughly 45° upward (raised position). The camera can safely sit on the FRONT FACE of the tower top — the arm swings below and in front of this point, not over it. This is the best existing mounting point.

**F3 — Arm tower ribbon path: borderline at 30 cm [S1, S2]**
From the Pi connector (3" from back) to the top of the arm tower (~5" forward, ~8–9" up from chassis top):
- Minimum path: straight-line ~9.4" (24 cm) — theoretically fits
- Realistic routed path: 13–15" (33–38 cm) — **exceeds 30 cm if routed around structure**
- Mitigation: if the Pi's CSI connector edge faces inward (toward the tower), the ribbon can go up the inner face of the arm tower directly — reducing the routed path to ~10–12" (25–30 cm), which just fits with careful management

**F4 — Front chassis rail is the easiest existing spot [S1]**
The front rail of the chassis is at ~4–5" height, 7" forward from the Pi connector (17.8 cm). A 30 cm ribbon reaches it with 12+ cm to spare. The downside: lower height means the camera must tilt steeply (45–50°) and objects within 3–4" of the robot nose will be in the close-range blind spot. For a scoop approach where the robot drives forward, the object is typically 6–12" ahead — borderline visible at 45° tilt from 4.5" height.

**F5 — Camera Module 3 viewing angle at candidate heights [inference]**

| Camera height | Tilt below horizontal | Center of view hits ground at | Near/far edge of 56° V FOV on ground |
|---|---|---|---|
| 4.5" (front rail) | 45° | 4.5" in front | ~2" to ~12" |
| 4.5" (front rail) | 30° | 7.8" in front | ~4" to ~28" |
| 8.5" (arm tower top) | 30° | 14.7" in front | ~7" to far field |
| 8.5" (arm tower top) | 45° | 8.5" in front | ~4" to ~25" |
| 11" (mast) | 40° | 13" in front | ~6" to far field |

For a scoop that grabs at 8–15" in front, the arm tower (8.5", tilted 30–40°) gives the best coverage. The front rail at 45° tilt covers the same zone but from lower, giving less margin.

**F6 — Plywood mast at rear is the cleanest new-structure option [S3, inference]**
A plywood I-beam column (two ¼" plywood flanges + ½" web, 1" wide) bolted to the existing holes in the rear top C-channel rail with #8-32 screws (the same hardware already in the kit). At 10–12" tall, camera at top tilted 40° forward-down, ribbon path is straight up from the Pi = 10–12" = 25–30 cm — barely within the 30 cm budget. This gives the same geometry as the arm tower mount but with a guaranteed ribbon path and no risk of arm contact.

---

## Constraints

- **30 cm ribbon is the hard limit** — no extension possible; routing must stay under ~27 cm of actual cable path
- **Pi is on the rear** — all ribbon paths go forward and/or up from there
- **Arm sweeps** from horizontal-forward (grab) to ~45° raised; camera must not be in the arm's sweep arc
- **Arm tower option requires careful routing** — the ribbon path to the tower top is ~10–13" depending on how the Pi is oriented; must be managed with cable clips rather than free-hanging
- **Camera Module 3 FPC cable cannot be kinked** — bends must be gentle (radius > ~5 mm)
- **Existing VEX holes** are on 0.5" grid, #8-32 screws — any new plywood structure must bolt to these

---

## Solution Comparison

| Criteria | A: Arm Tower Top (existing) | B: Front Chassis Rail (existing) | C: Rear Plywood Mast (new) | D: Forward I-Beam Arch (new) |
|---|---|---|---|---|
| **Height** | ~8–9" | ~4–5" | 10–12" | 10–14" |
| **Ribbon path** | ~25–33 cm (⚠ tight) | ~17–22 cm (✓ easy) | ~25–30 cm (✓ just fits) | ~20–25 cm (✓) |
| **View of grab zone** | Excellent (8–15" in front) | Good (4–12" in front) | Excellent (8–15" in front) | Excellent |
| **Arm clearance** | Good (arm swings below) | Excellent (arm passes above) | Excellent (arm never reaches rear mast) | Good |
| **New build required** | None | None | Simple plywood mast | Complex arch |
| **Tilt needed** | 30–40° | 45–50° | 35–45° | 0–10° (near-nadir) |
| **Complexity** | Low | Very Low | Low-Medium | Medium |
| **Overall** | ★★★★★ | ★★★ | ★★★★ | ★★★ |

---

## Recommendation

### First choice: Arm tower top, camera angled 30–35° downward

Mount the Camera Module 3 on the **front face of the arm pivot tower**, at the top — the same C-channel face where the 84T gear sits, approximately 8–9" above the floor. Tilt the camera **30–35° below horizontal**, facing forward.

**How to mount:**
1. Velcro the camera to the front face of the upper C-channel arm tower, or use a 3D-printed/cardboard bracket with two #8-32 screws through existing VEX holes
2. Tilt the module forward 30–35° (can be shimmed with a folded piece of cardboard or foam behind the camera PCB before securing with velcro)
3. Route the 30 cm ribbon: from Pi CSI connector → run UP along the inside face of the arm tower (cable-clip or zip-tie to the tower C-channel every 2–3"), keeping bends gentle → connect to camera at top. Keep the Pi's connector edge oriented toward the tower to minimize routing distance.

**What this achieves:**
- Camera at 8–9" height → sees ground from ~5" to ~20" in front (the entire scoop approach zone)
- Arm is below and forward of camera when in grab position — no occlusion
- Fixed geometry: camera position never changes regardless of arm angle

**Fallback if 30 cm is too tight after routing:** proceed to Option C.

### Second choice (if ribbon is tight): Rear plywood I-beam mast

Build a **10–12" tall plywood I-beam column** and bolt it to the rear top C-channel with two #8-32 screws through existing holes. Mount the camera at the top of the mast, tilted ~40° forward-down.

**Mast construction:**
- Material: ¼" (6mm) plywood or craft-grade hardboard
- Cross-section: two ¾"-wide flanges + ¼"-thick web = I-beam = ~1" total width
- Height: 10–11" keeps the ribbon path at exactly 30 cm
- Attachment: two existing 0.5"-grid holes on the rear C-channel; #8-32 bolts from the kit
- Camera mount: small platform at top, camera velcroed or screwed face-forward with ~40° downward tilt built into the platform angle

**Ribbon path:** Pi CSI connector (3" from back edge) → ribbon goes straight up the mast = 10–11" = 25–28 cm → comfortably within 30 cm.

### Do not use: Front chassis rail alone

The 4–5" height requires a 45–50° downward tilt. At that angle, objects within 3" of the robot nose are below the FOV, and the working distance is compressed. Use this spot only if both Options A and C prove impractical.

---

## Verification

After mounting (whichever option):
1. **Cable check:** ribbon lies flat with gentle curves, no kinks
2. **Power check:** `rpicam-hello --timeout 5000` shows live image on Pi monitor
3. **Frame check:** `cam.capture_array().shape == (480, 640, 3)`
4. **Object visibility test:** place a ball or disc on the floor at 6", 10", 14" in front of robot. In the live YOLO preview, confirm the object is in frame at all three distances with the arm in the lowered (grab) position.
5. **Arm occlusion check:** raise and lower arm through full range while watching the live feed — confirm camera never goes dark or blocked.

---

## Next Steps

- **To proceed with Option A:** velcro/bracket + 30 cm ribbon when it arrives; angle ~32° down
- **To proceed with Option C:** cut two plywood pieces, form the I-beam, bolt to rear C-channel rail
- **To create a task:** `/task-add Relocate Camera Module 3 to arm tower top and re-verify YOLO object detection`
- **To ingest into wiki:** `/wiki-ingest raw/research/camera-mount-relocation/index.md`
