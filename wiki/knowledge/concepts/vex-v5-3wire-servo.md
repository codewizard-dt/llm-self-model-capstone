---
id: vex-v5-3wire-servo
title: VEX V5 3-Wire Servo Port — Connector, Pinout, and Non-VEX Servo Use
updated: 2026-06-22
sources:
  - ../../raw/research/vex-3wire-port-spec/index.md
tags: [vex, hardware, servo, connector, 3wire, capstone]
---

# VEX V5 3-Wire Servo Port — Connector, Pinout, and Non-VEX Servo Use

The V5 Brain has 8 × 3-wire ports (A–H) that output standard RC PWM and supply regulated 5 V. They are the correct interface for position-controlled servos, analog/digital sensors, and LED indicators. They are **not** appropriate for any axis requiring encoder feedback (use Smart Motors for those).

## Physical Connector

| Property | Value |
|----------|-------|
| Pin pitch | 2.54 mm (0.1") |
| Brain-side | **Male pins** in a keyed housing |
| Cable-side | **Female housing** (same as RC servo leads) |
| Keying | Yes — one insertion orientation only |
| Compatible families | JR (unkeyed, direct fit), Futaba J (tab may need removal) |

The connector is industry-standard TJC8 / "RC servo connector." VEX cables fit breadboard male header pins, confirming female cable contacts.

## Pinout

Looking at the Brain face-on with the 3-wire port facing you:

```
[ GND ] [ +5V ] [ SIG ]
  blk     red    wht
  (left)  (ctr) (right)
```

**Power is always the centre pin** — the same polarity-safety convention used in all RC servo standards. Even if GND and SIG are swapped, no power-reversal damage occurs; the servo just won't respond.

## Electrical Budget

**5 V @ 2 A total shared across all 8 ports.** This is the hardest constraint for multi-servo designs:

| Servo count | Typical draw | Budget headroom |
|-------------|-------------|-----------------|
| 1 small servo (SG90) | ~200–400 mA | Comfortable |
| 2–3 small servos | ~600 mA–1.2 A | Tight |
| 4+ or any standard-size servo | 1 A–2.5 A | May exceed budget |

Use an external 5 V BEC fed from the V5 battery (12.8 V) if the budget is tight. Signal wire still connects to Brain 3-wire port; only power and ground go to the BEC.

## Non-VEX Servo Compatibility

1. **Electrical**: fully compatible. Standard RC servos run 4.8–6 V and accept 1–2 ms PWM.
2. **Connector**: JR-style (most generic hobby servos, TowerPro SG90/SG92R, etc.) plug directly into Brain 3-wire ports.
3. **Pin order check**: verify Black=GND, Red=+5V, White=Signal before powering. Use VEX 276-1424 female-female extension as a breadboard breakout to confirm orientation safely.
4. **Futaba J**: has a polarising tab — may need to be trimmed to fit VEX's keyed port.

## API

**VEXcode V5 Python** (VEX servo, or any servo responding to 1–2 ms PWM):
```python
from vex import *
cam_tilt = Servo(brain.three_wire_port.b)
cam_tilt.set_position(45, DEGREES)   # 0–100° range on VEX 276-2162 servo
```

**For non-VEX servos** (wider travel, e.g. 180°) use raw PWM:
```cpp
// VEXcode C++
vex::pwm_out finger( Brain.ThreeWirePort.A );
```

**PROS C++** (ADI API):
```cpp
pros::adi_port_config_e_t type = pros::E_ADI_LEGACY_PWM;
pros::c::adi_port_set_config('A', type);
pros::c::adi_port_set_value('A', 127);  // 0–255 maps to PWM range
```

## Capstone Use Cases

| Use case | Suitable? | Notes |
|----------|-----------|-------|
| Camera pan/tilt | ✓ | Auxiliary; no telemetry needed |
| Aesthetic articulation (flair) | ✓ | See relates_to::[[aesthetic-vocabulary]] |
| Door latch / slip-release trigger | ✓ | One-shot; no feedback required |
| Self-model loop axis (grab, pull, throw) | ✗ | Use V5 Smart Motor — needs encoder telemetry |

derived_from::[[vex-3wire-port-spec]]
relates_to::[[vex-v5]]
relates_to::[[task-telemetry-contract]]
relates_to::[[aesthetic-vocabulary]]
relates_to::[[research-vexcode-v5]]
