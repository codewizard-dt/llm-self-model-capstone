---
id: vex-3wire-port-spec
title: Research: VEX V5 3-Wire Port Spec — Connector, Pinout, and Servo Compatibility
updated: 2026-06-22
sources:
  - ../../raw/research/vex-3wire-port-spec/index.md
tags: [source, vex, hardware, connector, servo, 3wire]
---

# Research: VEX V5 3-Wire Port Spec — Connector, Pinout, and Servo Compatibility

Research conducted 2026-06-22. Full report: `raw/research/vex-3wire-port-spec/index.md`. Primary sources register: `raw/research/vex-3wire-port-spec/sources.md`.

## Connector Type

The V5 Brain's 8 × 3-wire ports (labeled A–H, opposite the battery port) use a **standard 2.54 mm (0.1") pitch, 3-pin connector** — the same TJC8/JR/Futaba-J family used on RC hobby servo leads. **The Brain-side ports have male pins**; all VEX 3-wire cables terminate in **female housings** (confirmed by "VEX connectors fit into a breadboard"). The ports are **keyed** so the cable inserts only one way.

VEX sells female-female 3-wire extension cables (276-1424) explicitly for "interfacing VEX components with other non-VEX systems."

## Pin Order and Electrical Spec

| Pin (left → right, facing Brain) | Wire colour | Function |
|----------------------------------|-------------|----------|
| 1 (outer) | Black | GND |
| 2 (centre) | Red / Orange | **+5 V regulated** |
| 3 (outer) | White | PWM Signal |

The **centre pin is always power** — the same polarity-safety convention used across all RC servo standards. Swapping the two outer pins (GND ↔ Signal) will not cause power damage; the servo simply won't respond.

Full electrical spec:

| Parameter | Value |
|-----------|-------|
| Power rail | 5 V regulated |
| **Total current** | **2 A shared across all 8 ports** |
| Signal protocol | RC PWM, ~50 Hz, 1–2 ms pulse width |
| Analog input | 0–5 V, 12-bit |
| Digital input High | 2.4–5.5 V |
| Digital output High | ≥ 2.9 V (high-Z load) |

The **2 A shared budget** is the binding constraint for multi-servo designs. A typical small hobby servo draws 200–600 mA under load; three or more under simultaneous load may exhaust the budget. Use an external 5 V BEC for high-draw configurations.

## Non-VEX RC Servo Compatibility

**Electrically fully compatible**: standard RC servos run 4.8–6 V and accept 1–2 ms PWM.

**Mechanically compatible with caveats**:
- **JR-style (unkeyed)** connectors fit directly into the keyed VEX port.
- **Futaba J** connectors have a polarising tab that may conflict with VEX keying — the tab may need to be removed.
- **Pin orientation must be verified** before powering up: insert the servo connector so Black=GND, Red=+5V, White=Signal. The safest path is using a 276-1424 female-female extension as a breadboard breakout to confirm orientation before closing the connector.

## Software

**VEXcode V5 Python** (VEX servo or any servo responding to 1–2 ms PWM):
```python
from vex import *
my_servo = Servo(brain.three_wire_port.a)
my_servo.set_position(90, DEGREES)   # VEX servo: 0–100° range
```

**VEXcode C++ / PROS (raw PWM for non-VEX servo)**:
```cpp
vex::pwm_out finger( Brain.ThreeWirePort.A );
```

The `Servo` class limits travel to 100° (VEX servo spec). Use `pwm_out` for non-VEX servos with wider travel (commonly 180°).

## Capstone Relevance

3-wire servos are appropriate for **non-telemetered auxiliary actuators** (camera pan/tilt, aesthetic articulations, latches). They cannot populate the relates_to::[[task-telemetry-contract]] `observed` block — use V5 Smart Motors for any self-model-loop axis. relates_to::[[aesthetic-vocabulary]] articulations are the primary use case in the capstone context.

derived_from::[[vex-3wire-port-spec]]
relates_to::[[vex-v5]]
relates_to::[[research-vexcode-v5]]
relates_to::[[task-telemetry-contract]]
relates_to::[[aesthetic-vocabulary]]
