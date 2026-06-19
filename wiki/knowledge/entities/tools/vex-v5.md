---
id: vex-v5
title: VEX V5
aliases: [VEX V5, VEX]
updated: 2026-06-16
sources:
  - ../../../raw/Feasibility of a Human-Built Generational Robot Software Factory.pdf
  - ../../../raw/Feasibility of a Software-Factory Approach to Learning Robots That Assemble Additional Robots from M.pdf
  - ../../../raw/research/vex-v5-classroom-starter-kit/index.md
  - ../../../raw/276-6009-750-Rev6.pdf
tags: [tool, hardware, vex, platform, robotics]
---

# VEX V5

A robotics platform recommended as the **Stage-2 base** for a physical-robot factory — the step where the loop "starts to feel industrial rather than educational." Classroom Starter Kit ~$849.49; Brain ~$384.99. 21 Smart Ports + 8 3-wire ports, smart motors, inertial/optical/distance sensors, GPS, **native AI Vision Sensor** (color, AprilTags, selected object detection), 8 stored program slots; programmable in Blocks, Python, C++ (cloud or local compile).

## Why Stage 2

Best mid-range choice when you want **deterministic mechanics, stronger structures, clearer typed device APIs, and a built-in vision story.** Smart ports auto-detect devices; the Brain exposes diagnostics; web/desktop workflows make commissioning and reruns more disciplined than a tablet-centric kit. Stronger for insertion-heavy, repeatable assembly than friction-fit LEGO. Caveats: pneumatics run at 100 psi and distance sensing uses a Class 1 laser (safety-envelope considerations).

## Classroom Starter Kit (276-7010)

Product research (2026-06-16) on the entry-level kit — see derived_from::[[vex-v5-classroom-starter-kit]]:

- **$849.49**, 10.6 lbs (4.8 kg), grades 9–12, 2–3 students per kit; supersedes the older 276-6500.
- Builds the **V5 Clawbot**; wraps one **V5 System Bundle** (276-7000, $779.49, electronics-only) plus structural steel, motion parts, and hardware.
- Electronics: V5 Brain, Controller, Radio, 1100mAh Li-Ion battery + charger, **(4) Smart Motors**, **(2) Bumper Switch v2**.
- **Classroom family** (scaling up): Starter Kit → Super Kit (adds motion kits) → Starter Bundle (276-7070, 6×, 12–18 students) → Super Bundle (276-7080, 6×, full classroom).
- Programmed via relates_to::[[vexcode]]; pairs with the free, standards-aligned relates_to::[[stem-labs]] curriculum. Optional add-ons: VEX PD+ licence (210-8353, $999/yr), VEXcare warranty (1-yr $89.49 / 2-yr $145.99).
- VEX Robotics is a subsidiary of [[innovation-first]].

## Configuration Space (from [[vex-v5-starter-kit-configurations]])

The Starter Kit officially produces **two base topologies**: the [[speedbot]] (2-motor drivetrain only) and the Clawbot (Speedbot + arm + claw). VEX STEM Labs states: "The VEX V5 Clawbot is an extension of the VEX Speedbot." The Advanced TrainingBot (arm on faster TrainingBot chassis) requires a **Competition or Super Kit** — not the Classroom Starter Kit.

**~15–30 valid configurations** exist across 6 free parameters: motor allocation, arm position, end-effector, wheel type, arm gear ratio, cartridge speed. All structural steel is consumed by the Clawbot; different shapes require cutting. What is NOT possible with base kit: tank treads, pneumatics, 4-bar linkage, scissor lift, flywheel shooter, AI vision.

For the capstone: **Speedbot = Gen 0, Clawbot = Gen 1**, then mutations (Gen 2–5) exhaust the meaningful design space — the small grammar is an asset.

## V5 Clawbot — Gen 0 Reference Morphology (from 276-6009-750 Rev6)

The **V5 Clawbot** is the canonical starter build bundled with every Classroom Starter Kit. It is the ground-truth "Gen 0" morphology the LLM self-model loop would start from. Full detail in the source page: derived_from::[[vex-v5-clawbot-build-instructions]].

**Configuration summary** (41-step build, ©2023):

| Subsystem | Parts | Motor |
|-----------|-------|-------|
| Drive (left) | 4" standard wheel × 1 | Smart Motor 11W, direct |
| Drive (right) | 4" standard wheel × 1 | Smart Motor 11W, direct |
| Front (passive) | 4" Omni-Directional wheel × 2 | — |
| Lift arm | 84T:12T = 7:1 gear reduction | Smart Motor 11W |
| Claw | 12T gear + rubber-band return | Smart Motor 11W |

**Port assignments** (from wiring diagram, steps 22 + 41):
- Ports 1 & 10: drive motors (300mm cable)
- Port 3: claw motor (600mm cable)
- Port 8: arm motor (900mm cable)

**Structure**: steel C-channels (15-hole and 25-hole), U-channels (20-hole), angles; all #8-32 star drive fasteners. One channel requires hacksaw cut — generation manifest should encode `constraints.requires_cutting: true`.

**Key kinematic parameters for the self-model's capability layer**:
- 7:1 arm reduction → higher torque, lower speed
- 4" wheels → ~12.6" circumference per motor revolution
- 2× Omni front wheels → no steering resistance in tank turns
- Claw rubber-band return → passive close force, active open

**Claw autonomy (from [[vex-v5-clawbot-claw-autonomy]])**: The claw has **no hardware sensing** — no bumper switch, limit switch, or force sensor is part of the standard 41-step build. The Starter Kit's included bumper switches are for a separate curriculum module. The official curriculum programs the claw with `spin_for(N, DEGREES)` + `set_timeout()` only — pure degree-based, manually tuned. The VEXcode V5 API has no `is_stalled()` or `spin_until_stall()`. Recommended autonomous grip pattern for the capstone: `set_max_torque(30, PERCENT)` + `spin_for(720, DEGREES)` + `set_timeout(3, SECONDS)` — the motor soft-stops on contact; `position()` after gives object-size proxy (0.02° accuracy); `current()`/`torque()` give grip-force signal. The 2.5 A hardware stall cap makes sustained grip safe.

**Typed parts vocabulary** (seed for `vex_v5_catalog.json`): see [[vex-v5-clawbot-build-instructions]] for full SKU table.

**Clawbot as the branching point**: the Clawbot is a *fixed* single build in the instructions, but the underlying VEX V5 kit is reconfigurable. The typed grammar branching points are: wheel type (standard vs. omni, diameter), motor count and port assignment, gear ratio (swap 84T:12T for other combos), channel length (hacksaw), arm vs. no arm, claw vs. alternative end-effector, sensor additions (AI Vision, GPS, distance, optical). Each is a node mutation in the [[llm-authored-self-model]]'s structural self-model.

## Grab / Pull / Throw Capability (from [[vex-v5-customization-grab-pull-throw]])

All three task primitives are achievable with the base Starter Kit. Key capability envelope (motor stall torque 2.1 Nm, continuous ≤ 0.735 Nm):

| Task | Mechanism | Max force / speed | Base kit? |
|------|-----------|------------------|-----------|
| **Grab** | 12T claw motor | ~42 N stall, ~14.7 N continuous | ✓ |
| **Pull** | 2× drive motors on 4" wheels | ~83 N stall, ~29 N continuous | ✓ |
| **Throw (slow)** | Arm motor 7:1 + #32 rubber bands | 0.45 m/s release, ~0.5 m range | ✓ |
| **Throw (fast)** | Flywheel with 6:1 cartridge | ~22 m/s rim speed | + $20 cartridge |

**Motor Python telemetry API** (every V5 Smart Motor, readable at runtime):
```python
motor.torque(Nm)          # 0.0–2.1 Nm
motor.current(AMP)        # 0–2.5 A
motor.velocity(RPM)       # actual RPM
motor.position(DEGREES)   # cumulative degrees
motor.power(WATT)         # 0–12.75 W
motor.temperature(PERCENT)
motor.set_max_torque(50, PERCENT)
```

Three swappable gear cartridges: **6:1 (600 RPM)**, **18:1 (200 RPM, default — included)**, **36:1 (100 RPM)**. Brain has 21 Smart Ports; Clawbot uses 4, leaving 17 free. Kit is explicitly scalable to add motors, sensors, aluminum, pneumatics.

Task contracts (predicted + observed + gap JSON) for each task primitive: see [[task-telemetry-contract]].

## Booster Kit (276-2232) — Morphology Search Space Expansion

Product research (2026-06-16) — see derived_from::[[vex-v5-booster-kit]]:

- **$214.49**, ~600 pieces, **no electronics** (zero motors, brain, sensors, battery). "Top Recommended Add-On Kit" per VEX; confirmed compatible with V5.
- **New typed primitives** the Starter Kit lacks:

| Part | Qty | New node type |
|---|---|---|
| 19T Rack Gear (276-1957) | 4 | `linear_actuator` (rack-and-pinion linear pull) |
| Gear Kit assortment (276-2169) | 1 | More `gear_ratio` choices |
| 12.00" Shaft (276-1149) | 4 | `long_arm` (higher throw release velocity `v = ω × arm_length`) |
| Intake Roller (276-1499) | 4 | `intake` (roller-based grab) |
| Motor Clutch (276-1098) | 3 | `slip_release` (catapult + overload protection) |

- **Structural bulk**: 8× 1×1×25 Steel Bars, 4× 2×1×25 Rails, 2× each of C-Channels, Plates, Angles, Gussets, plus ~160 screws, ~130 Keps Nuts, 26 Flat Bearings, 50 Bearing Attachment Rivets, assorted standoffs and shafts.
- **Motor bottleneck unchanged** — actuation still capped at 4 Smart Motors. Pair with 2–4 additional Smart Motors (~$53 each) to lift the real constraint.
- **EDR-era caveat**: Motor Clutch and Intake Roller designed for legacy 3-wire motors; verify V5 Smart Motor mounting on receipt before relying on those two parts.

## CAD Ecosystem (from [[vex-v5-cad-designs]])

**Official per-part STEP:** Every VEX V5 part has a downloadable `.step` file on its vexrobotics.com product listing — the authoritative geometry source, compatible with SolidWorks, Inventor, Fusion 360, Onshape, and Solid Edge.

**Onshape VEX V5 Parts Library** (relates_to::[[onshape]]): 100+ V5 parts with correct appearances, materials, weights, and part numbers. Free for educators. Parts placed 500,000+ times. Best starting point for building any configuration as an editable assembly. Access: Onshape Education account → App Store → "VEX Library".

**GrabCAD community libraries:**
- [VEX Robotics V5 Clawbot](https://grabcad.com/library/vex-robotics-v5-clawbot-1) (Michael Mohn, 2018) — 61 SolidWorks files from official STEP, fully mated for motion; 1,537 downloads
- [Vex Super Kit CAD Files](https://grabcad.com/library/vex-super-kit-cad-files-1) (Erdem Karayel, 2020) — 120 files, Competition + Classroom Super Kit parts
- [RBE1001 VEX V5](https://grabcad.com/library/rbe1001-vex-v5-1) (WPI, 2022) — 262 files, robot + field

**SJTU VEX Open Source** (`sjtu-vex.github.io/open-source/`): SolidWorks 2020+ library updated through May 2026, covering V5RC parts, VEX PRO, pneumatics, and field elements.

**No full-assembly Hero Bot CAD is published by VEX.** To get a Hero Bot as editable CAD: reconstruct it in Onshape from its `instructions.online` 3D build + Parts List. All Hero Bots (Flex, Dex, Axel, Striker, Disco, Moby…) require the Competition Starter Kit — they are outside the Classroom Starter Kit grammar.

**3D printable integration spec:** 0.500" hole spacing / #8-32 screws (shared by all V5, IQ, EDR structural parts). Community printable parts on Thingiverse (claw kits, part replicas) and Printables (vectored intake wheels `model/1293156`, rover wheel `model/698733`, hub inserts `model/1303938`). Fully legal for capstone use; banned in VRC competition (allowed in VEX U).

derives_from::[[vex-v5-cad-designs]]

## External AI Integration via USB Serial

The V5 Brain exposes two USB serial ports when connected to a host computer. The *user port* (stdio) lets user programs emit telemetry and receive commands from an external process — this is the integration path for the LLM self-model loop. VEX's official VEX AI demo uses a Jetson Nano connected via USB serial to a V5 Brain for exactly this purpose.

**Recommended capstone pattern**: a lightweight Python stub on the Brain emits JSON motor telemetry over the user port; the LLM + self-model runs on a host machine with full CPython and library access. See derived_from::[[research-vexcode-v5]].

## PROS Smart Port RS-485 — Second Coprocessor Channel

With relates_to::[[pros]], any V5 Smart Port can be configured as a generic RS-485 serial device via `pros::Serial(port, baud)` (up to ~921600 baud). This creates a coprocessor link **independent of the USB connection**:

- During a demo: USB stays connected for monitoring/debug while the AI pipeline SBC communicates over Smart Port RS-485.
- Enables ROS 2 integration via rosserial over the Smart Port channel.
- Requires an RS-485 transceiver chip (~$5) between the Smart Port and the external device.

**Stage 2 integration path**: relates_to::[[pros]] C++ + relates_to::[[lemlib]] — pose telemetry `{x, y, heading}` over USB serial user port; FreeRTOS preemptive scheduling keeps telemetry streaming concurrent with motor PID. See derived_from::[[research-vex-v5-advanced-toolchains]].

## Platform Comparison vs Consumer Kits (from [[picobricks-rex-vs-vex-v5]])

The cheaper [[picobricks-rex-evolution]] ($164.99, ESP32E) was evaluated as a Stage-2 alternative to VEX V5 and **rejected**. Consumer/education kits like the REX lack motor encoders and per-actuator telemetry — their DC motors are open-loop and their servos are standard RC servos with no feedback bus, so they cannot populate the [[task-telemetry-contract]]'s `observed` block, which the project's self-model loop depends on. **The V5 Smart Motor (Cortex M0 + optical encoder, ±0.02°, full torque/current/velocity/position API) is the differentiator** that makes the platform decision unambiguous; REX's only edges (price, WiFi-native LLM calls) do not close the telemetry gap. compared_in::[[picobricks-rex-vs-vex-v5]].

## Real-World Reference: UT Austin GHOST VEX U Team (2025)

The GHOST team (relates_to::[[ut-ieee-ras]]) won the **2025 VEX AI World Championship** running a VEX V5 Brain + Nvidia Jetson stack — demonstrating that VEX V5 scales beyond classroom use to fully-autonomous competitive robotics. Their tech stack (LIDAR, Intel Realsense, ROS, C++ framework) confirms VEX V5 as a viable autonomous research platform, not just an educational toy. Two PhD students (ASE) are on the team and are outreach targets for supervised hardware access. See derived_from::[[ut-vexu-team]].

## Raspberry Pi 5 Vision Integration (from [[vision-vex-architecture]])

The recommended architecture for adding computer vision and AI inference to the VEX V5 robot for the capstone:

```
USB Webcam / Pi Camera Module 3
│
▼
Raspberry Pi 5  (OpenCV, YOLO11n, AprilTags, LLM, telemetry aggregation)
│
microUSB → USB-A cable (115200 baud, JSON)
│
▼
VEX V5 Brain  (VEXcode V5 Python: motors, encoders, gyros, safety stops)
```

**Pi handles**: object detection (~8–10 FPS YOLO11n NCNN at 640×480), AprilTag localization (workspace pose from printed tags), LLM API calls, telemetry log merging.  
**V5 handles**: motor commands from Pi, encoder reads, gyro, bumpers, safety stops.

**Connection**: microUSB on V5 user port → USB-A on Pi. Pi sees `/dev/ttyACM0`; udev rule: `ATTRS{idVendor}=="2888", SYMLINK+="vex_brain"`. Baud fixed at 115200 by V5 firmware.

**V5 Python serial output**: `brain.screen.print()` goes to USB serial user port by default in VEXcode Python; use explicit `sys.stdout.write()` for cleaner serial-only output (avoids Screen display side-effect).

**Power constraint**: Pi 5 draws up to 5A at 5V — cannot be powered from V5 1100mAh Li-Ion battery. A separate 65W USB-C PD power bank must be mounted on the robot frame.

**Physical mounting**: bolt [[raspberry-pi-5]] to a VEX metal plate with M2.5 standoffs (Pi 5 hole pattern: 56mm × 85mm). Attach USB webcam or [[pi-camera-module-3]] to a VEX angle bracket at the robot front. Use right-angle microUSB cable for the V5 link and zip-tie it to the frame (the V5 microUSB port is fragile).

derived_from::[[vision-vex-architecture]]

used_by::[[physical-robot-software-factory]]  
derived_from::[[vex-v5-clawbot-build-instructions]]  
relates_to::[[lego-spike-prime]]  
relates_to::[[feasibility-human-built-generational-factory]]  
relates_to::[[typed-assembly-grammar]]  
relates_to::[[vexcode]]  
relates_to::[[stem-labs]]  
relates_to::[[research-vexcode-v5]]
relates_to::[[raspberry-pi-5]]
relates_to::[[pi-camera-module-3]]

## Rubber Bands — Passive Elastic Components (from [[vex-rubber-band-sizes]])

VEX sells rubber bands in two standard sizes — both legal for VRC competition and for the capstone:

| Size | Dimensions | Primary role |
|------|-----------|-------------|
| **#32** | 3" × 1/8" (76 × 3.2 mm) | Precision: triggers, latches, light return springs |
| **#64** | 3.5" × 1/4" (89 × 6.4 mm) | Power: lift assist, catapults, intake rollers |

Three material variants: **Synthetic/EPDM** for energy storage (high elongation); **Silicone** for intake rollers (higher friction against plastic → grips game pieces). The Clawbot Gen 0 already uses a rubber-band claw return (passive-close force, port 3 motor does active-open only). The slow-catapult throw primitive uses `#32 rubber bands + arm motor 7:1`.

Well-tuned rubber band counterbalancing reduces motor load ~30% — enabling a 1-motor lift to compete with a naive 2-motor design. Adding #64 bands to the arm is a likely Gen 1→2 mutation in the self-model evolution loop.

See relates_to::[[rubber-band-mechanisms]] for full mechanism taxonomy.
