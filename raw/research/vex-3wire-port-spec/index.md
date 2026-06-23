---
topic: VEX 3-wire port spec including connector types
slug: vex-3wire-port-spec
researched: 2026-06-22
sources: [./sources.md]
---

# Research: VEX V5 3-Wire Port Spec — Connector, Pinout, and Servo Compatibility

> The V5 Brain's 8 × 3-wire ports (A–H) use a standard 2.54 mm (0.1") pitch, keyed, 3-pin connector identical in form factor to RC hobby servo cables. The Brain-side ports expose **male pins**; all VEX 3-wire cables terminate in **female** housings. The pin order is **GND → +5 V → Signal** (left to right when facing the port). Power rail is a regulated **5 V at a shared 2 A budget** across all eight ports. Signal protocol is standard RC PWM (1–2 ms pulse width, ~50 Hz). Non-VEX hobby servos are electrically and mechanically compatible with caveats about keying and pin orientation described below.

---

## Research Questions

1. What physical connector type do the V5 Brain's 3-wire ports use (pitch, gender, housing style)?
2. What is the pin order (GND / power / signal)?
3. What voltage and current does the power rail supply?
4. Are standard RC hobby servos (JR / Futaba J) directly plug-compatible without an adapter?
5. How do you control a servo in VEXcode V5 Python and PROS C++?

---

## Current State (Codebase)

The capstone codebase (`robot/v5-brain/`) uses PROS C++ and has no existing 3-wire servo code. The wiki entity at `wiki/knowledge/entities/tools/vex-v5.md` records "21 Smart Ports + 8 3-wire ports" but has no connector-level detail. This research fills that gap.

---

## Key Findings

### 1. Physical Connector — 2.54 mm (0.1") Pitch, Female-on-Cable

The 3-wire connector is a **standard 3-pin, 2.54 mm pitch** header identical in form factor to hobby RC servo connectors (JR / Futaba J / TJC8 family). [S6, S7]

- **Brain-side**: keyed male-pin receptacle (ports labeled A–H on the side opposite the battery). "The ports are keyed so you can only plug the cable in one way." [S2]
- **Cable-side**: female housing (same plastic housing found on RC servo leads). "The VEX connectors fit into a breadboard" — breadboards accept male pins, confirming the cable end is female. [S5]
- VEX sells **female-female** 3-wire extension cables (276-1424) explicitly described as useful "for interfacing VEX components with other non-VEX systems." [S8]

### 2. Pin Order — GND · +5 V · Signal

| Pin (left → right, facing Brain) | Wire colour | Function |
|----------------------------------|-------------|----------|
| 1 (outer) | Black | Ground (GND) |
| 2 (centre) | Red / Orange | +5 V regulated power |
| 3 (outer) | White | PWM Signal |

Confirmed by VEX forum community ("GND, 5V, and signal from left to right… this is according to the ADI wire colours: black, red and white") [S5] and cross-checked against the VEX LED Indicator article which explicitly calls the centre wire the "+5V wire." [S4]

The **centre pin is always power** — the same polarity-safety convention used across all RC servo standards. Even if the outer pins are swapped, the servo will not receive reversed polarity (it just won't respond to signals). [S6]

### 3. Electrical Specification

| Parameter | Value | Source |
|-----------|-------|--------|
| Power rail | 5 V regulated | [S3], [S4] |
| Total current budget | **2 A shared across all 8 ports** | [S3] |
| Signal protocol | RC PWM, ~50 Hz, 1–2 ms pulse width | [S1], [S9] |
| Analog input range | 0–5 V, 12-bit resolution | [S3] |
| Digital input high | 2.4–5.5 V | [S3] |
| Digital output high | ≥ 2.9 V (high-impedance load) | [S3] |

The 2 A shared budget is the critical constraint for multiple servos. A typical small hobby servo draws ~200–600 mA under load; if three or more heavy servos are connected, the shared budget may be exhausted. An external 5 V BEC is the mitigation for high-draw loads.

### 4. Non-VEX RC Servo Compatibility

**Electrically**: fully compatible. Standard RC servos run on 4.8–6 V and accept 1–2 ms PWM — an exact match for V5 3-wire output. [S6, S9]

**Mechanically**: physically compatible with caveats:
- VEX ports are **keyed** (Futaba J-style tab); the female JR connector (unkeyed) **will** slide into a keyed VEX port because the JR housing is smaller and lacks the blocking tab.
- Futaba J connectors (with a tab on the housing) may not fit without removing the tab, because the VEX port key is oriented differently.
- **Pin orientation check required**: standard JR convention places Signal on the opposite outer pin compared to VEX (some brands have Signal on the same side, others on the opposite side). Because VEX ports are keyed you can only insert the connector one way — verify wire colours against VEX's order (Black=GND, Red=+5V, White=Signal) *before* powering up. Swapping GND and Signal will not damage anything (power centre pin is safe) but the servo will not respond.
- Safest path: use a VEX 3-wire female-female extension cable (276-1424) as a breakout, expose the pins on a breadboard, and insert the servo wires in the correct GND/+5V/Signal order.

### 5. Software — VEXcode V5 Python and PROS C++

**VEXcode V5 Python** (uses `Servo` class from VEX API):
```python
from vex import *
my_servo = Servo(brain.three_wire_port.a)      # port A
my_servo.set_position(50, PERCENT)             # 0–100% of 100° range
# OR
my_servo.set_position(90, DEGREES)             # absolute degrees (VEX servo: 0–100°)
```

The VEX servo supports 100° of motion. For a non-VEX servo with a wider range, use `pwm_out` to emit raw PWM instead:

**PROS C++ (raw PWM for non-VEX servo)**:
```cpp
// VEXcode C++
vex::pwm_out finger( Brain.ThreeWirePort.A );
// or PROS ADI:
pros::ADIDigitalOut pwm_port('A');  // configure as PWM output in PROS
```

The VEXcode V5 Python API lists the `Servo` class under **Motion → 3-Wire Devices**; the same class is available in C++. [S1]

---

## Constraints

- **2 A shared cap** across all 8 ports — budget carefully with multiple servos.
- **VEX servo API limits rotation to 100°** (VEX's own servo spec). If using a non-VEX servo via `pwm_out`, the full travel of the servo (commonly 180°) is accessible.
- **No encoder feedback**: 3-wire servos have no positional readback to the Brain — they cannot populate the Task Telemetry Contract's `observed` block. Use Smart Motors for any axis requiring telemetry.
- **Power (+5V) is Brain-regulated**, not direct battery voltage — servos must be rated for 5 V operation.
- **Keyed ports**: only VEX 3-wire cables and JR-style (unkeyed) connectors can be inserted correctly. Futaba J connectors need the polarising tab removed.

---

## Recommendation

For non-critical, non-telemetered actuators (camera pan/tilt, aesthetic articulations, a latch):
1. Use a VEX 3-wire extension cable (276-1424, female-female) to adapt the non-VEX servo.
2. Verify pin order on the breadboard before closing the connector.
3. Configure the Brain-side port as `pwm_out` if using a non-VEX servo, or `Servo` if using the VEX 276-2162 servo.
4. Keep total 3-wire servo current under 1.5 A if other 3-wire devices are also in use.

For any axis in the self-model loop (where you need `observed` telemetry), use a V5 Smart Motor, not a 3-wire servo.

---

## Next Steps

- `/wiki-ingest raw/research/vex-3wire-port-spec/index.md` to add this to the knowledge base.
- Consider filing a concept page: `wiki/knowledge/concepts/vex-v5-3wire-servo.md` combining this research with the prior servo wiki-query answer.
