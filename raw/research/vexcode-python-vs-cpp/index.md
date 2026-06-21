---
topic: the vexcode api https://api.vex.com/v5/home/ before creating a local reference... do a thorough comparision of the python and C++ apis. Determine the pros and cons of each relative to the other and compare what can be done with both
slug: vexcode-python-vs-cpp
researched: 2026-06-20
sources: [./sources.md]
---

# Research: VEXcode V5 Python vs C++ API — Thorough Comparison + Local Reference

> The VEXcode V5 Python and C++ APIs are **two language bindings over one identical underlying VEX V5 SDK**: every device, sensor, and control primitive exposed to one is exposed to the other, so functional parity is essentially complete. They differ in three ways that matter: (1) **surface syntax** — Python uses `snake_case` and MicroPython idioms, C++ uses `camelCase`, typed declarations, and explicit `vex::` namespacing; (2) **documentation taxonomy** — the same devices are filed under different section trees (Python splits sensors into many top-level pages; C++ groups them under "Smart Port Devices" and the industrial devices under "CTE Workcell"); and (3) **runtime execution** — Python runs interpreted as **MicroPython 1.13** (≈10–300× slower for compute-heavy/tight loops), while C++ is **compiled to native ARM Cortex-A9** with deterministic timing. Both share the **same cooperative thread scheduler** (`Logic/Threads`) and the same Competition template model. **Recommendation: C++ for the on-Brain control layer** (it is faster, what the codebase already uses via PROS, and the competition norm for PID/real-time), **Python only where ease-of-iteration on non-time-critical logic outweighs speed** — but note the heavy on-Brain compute belongs on the external Pi regardless of language. This report builds on and does not repeat [../vexcode-v5/index.md](../vexcode-v5/index.md) (general VEXcode landscape, install, Brain hardware, serial pipeline); it adds the method-level Python↔C++ comparison and a complete linked local reference of both API trees.

---

## Research Questions

1. What is the complete top-level structure of the VEXcode V5 **Python** API vs the **C++** API, and how do the two doc trees map onto each other? (the "complete local reference with links")
2. At the method level, how close is functional parity between the two? Where do they actually diverge?
3. What are the **runtime / performance / concurrency** differences (interpreted MicroPython vs compiled C++) and what do they mean for real robot code (PID, sensor polling, multitasking)?
4. What are the **pros and cons of each relative to the other** for the capstone's use case?
5. Given the codebase already has a **PROS C++** Brain bridge, how do VEXcode C++ and PROS relate, and which language/toolchain should the on-Brain layer use?

---

## Current State (Codebase)

- **The robot-side code is already C++, via PROS — not VEXcode.** `robot/v5-brain/pros_bridge/src/main.cpp` is a PROS sketch: it `#include "pros/apix.h"`, calls `pros::millis()` / `pros::delay()` / `serctl(SERCTL_DISABLE_COBS, ...)`, and implements `initialize()` / `opcontrol()` (PROS lifecycle entry points, **not** VEXcode's `int main()` / `vex::competition`). It reads newline-delimited JSON from the V5 user/console USB serial port and acks over `stdout`. This is the Brain end of the telemetry pipeline documented in the memory `project-telemetry-pipeline`.
- **This contradicts the prior research's recommendation.** [../vexcode-v5/index.md](../vexcode-v5/index.md) recommended "VEXcode V5 **Python** on the V5 Brain for all robot-side code." The codebase chose **PROS C++** instead. That is a defensible reversal (see Recommendation), but it should be recorded as a decision rather than left as silent drift.
- **`robot/v5-brain/pros_bridge/README.md`** confirms the intended integration: Pi speaks newline-delimited JSON over the V5 USB user/console serial port; PROS interacts with serial via file-style `stdin`/`stdout`; `SERCTL_DISABLE_COBS` is required when reading serial directly instead of via `pros terminal`.
- Prior VEXcode research lives at `raw/research/vexcode-v5/` and the entity stub at `wiki/knowledge/entities/tools/vexcode.md`.

> **Scope note:** "VEXcode C++" (the API at api.vex.com, `vex::` namespace, cooperative scheduler) and "PROS C++" (Purdue, `pros::` namespace, FreeRTOS preemptive scheduler) are **different C++ toolchains for the same Brain**. This report's API comparison is Python-vs-C++ *within VEXcode*; the codebase's `pros::` code is a third option covered in the Recommendation and in [../vexcode-v5/index.md](../vexcode-v5/index.md).

---

## Complete Local Reference (links to the docs)

Home: <https://api.vex.com/v5/home/> · Python root: <https://api.vex.com/v5/home/python/index.html> · C++ root: <https://api.vex.com/v5/home/cpp/index.html>

### Python API — top-level sections [S2]

| Section | Doc link | Notes |
|---|---|---|
| Drivetrain | `python/Drivetrain.html` | 2-/4-motor drive abstraction |
| Motion | `python/Motion/index.html` | Motor & Motor Group, MC55, Motor 393, Victor 883, Servo |
| Vision | `python/Vision/index.html` | Vision + AI Vision sensor |
| Screen | `python/Screen.html` | Brain touchscreen draw/print (top-level in Python) |
| Controller | `python/Controller.html` | Joysticks, buttons, rumble |
| Sensing | `python/Sensing/index.html` | Distance, Optical, Rotation, GPS, bumper, etc. |
| Inertial | `python/Inertial.html` | IMU (top-level in Python) |
| 3-Wire Devices | `python/3-wire/index.html` | Legacy 3-wire analog/digital |
| Pneumatics | `python/Pneumatics/index.html` | Solenoid/cylinder control |
| Brain | `python/Brain.html` | `battery`, `screen`, `sdcard`, `timer`, `three_wire_port`, `program_stop()` |
| SD Card | `python/SDcard.html` | File I/O (top-level in Python) |
| VEXlink | `python/VEXlink/index.html` | Robot-to-robot radio link |
| Console | `python/Console.html` | `print()` to USB user port |
| Logic | `python/Logic/index.html` | **Threads/multitasking**, events, timers, control flow |
| 6-Axis Arm | `python/Arm.html` | CTE workcell arm (top-level in Python) |
| Magnet | `python/Magnet.html` | CTE workcell electromagnet (top-level in Python) |
| Competition | `python/Competition.html` | Driver/autonomous competition template |
| MicroPython Libraries | `python/Micropython_libraries.html` | **Python-only** — see runtime note below |

Full path prefix: `https://api.vex.com/v5/home/<link>`.

### C++ API — top-level sections [S3]

| Section | Doc link | Notes |
|---|---|---|
| Drivetrain | `cpp/Drivetrain/index.html` | incl. `smartdrive` |
| Motors and Motor Controllers | `cpp/Motors_and_MotorControllers/index.html` | Motor & Motor Group (`motor_and_motor_group.html`), MC55 (`mc55.html`), Motor 393, Victor 883, Servo |
| Controller | `cpp/Controller/index.html` | Joysticks, buttons, rumble |
| Brain | `cpp/Brain/index.html` | **groups** screen, SD card, battery, timer, 3-wire port |
| Competition | `cpp/Competition.html` | Competition template |
| Smart Port Devices | `cpp/Smart_Port_Devices/index.html` | **groups** Inertial, Rotation, Distance, Optical, GPS, AI Vision, Vision |
| 3-Wire Devices | `cpp/3-Wire_Devices/index.html` | Legacy 3-wire analog/digital |
| Console | `cpp/Console.html` | `printf` to USB user port |
| Logic | `cpp/Logic/index.html` | **Threads/multitasking** (`cpp/Logic/Threads.html`), events, control flow |
| VEXlink | `cpp/VEXlink/index.html` | Robot-to-robot radio link |
| CTE Workcell | `cpp/CTE_Workcell/index.html` | **groups** 6-Axis Arm, Object Sensor, Pneumatics, Signal Tower |

Full path prefix: `https://api.vex.com/v5/home/<link>`.

### Doc-tree mapping (same devices, different filing)

| Capability | Python location | C++ location |
|---|---|---|
| Smart motors | `Motion/` | `Motors_and_MotorControllers/` |
| IMU / inertial | `Inertial.html` (top-level) | under `Smart_Port_Devices/` |
| Vision / AI Vision | `Vision/` (top-level) | under `Smart_Port_Devices/` |
| Distance/Optical/Rotation/GPS | `Sensing/` (top-level) | under `Smart_Port_Devices/` |
| Brain screen | `Screen.html` (top-level) | under `Brain/` |
| SD card | `SDcard.html` (top-level) | under `Brain/` |
| 6-axis arm / pneumatics / magnet | `Arm.html`, `Pneumatics/`, `Magnet.html` (top-level) | under `CTE_Workcell/` (Arm, Pneumatics, Object Sensor, Signal Tower) |
| Std-library reference | `Micropython_libraries.html` | *(none — uses pre-loaded C++ standard library)* |

**Takeaway:** the C++ tree is flatter/grouped by *connector* (Smart Port, 3-Wire, Brain-internal, CTE); the Python tree is wider, listing many devices at top level. Same hardware coverage either way.

---

## Key Findings

### 1. Functional parity is ~complete; both wrap the identical SDK [S1][S4][S5]
The Motor/Motor Group page proves it concretely. C++ exposes (Actions/Mutators/Getters): `spin`, `spinFor`, `spinToPosition`, `stop`; `setPosition`, `setVelocity`, `setStopping`, `setMaxTorque`, `setTimeout`; `isDone`, `isSpinning`, `position`, `velocity`, `current`, `power`, `torque`, `efficiency`, `temperature`, `voltage`, `direction`, `installed`, `count` [S4]. Python exposes the same set in `snake_case`: `spin`, `spin_for`, `spin_to_position`, `stop`; `set_position`, `set_velocity`, `set_stopping`, `set_max_torque`, `set_timeout`; `is_done`, `is_spinning`, `position`, `velocity`, `current`, `power`, `torque`, `efficiency`, `temperature`, `count`, plus `reset_position`, `set_reversed`, `get_timeout` [S5]. Telemetry the capstone cares about — **position, velocity, current, torque, efficiency, temperature** — is present in **both**.

### 2. The divergences are small and per-page, not architectural [S4][S5]
The two surfaces are **independently documented**, not auto-generated mirrors, so they drift slightly: the C++ motor page surfaces `voltage` / `direction` / `installed` getters; the Python motor page instead surfaces `reset_position` / `set_reversed` / `get_timeout`. These reflect documentation organization more than capability gaps (most such methods exist in both, filed differently), but **do not assume a method name exists in the other language by mechanical case-conversion — verify on the per-device page.**

### 3. Naming/idiom translation rules (Python ↔ C++) [S2][S3][S4][S5]
- Methods: `snake_case` (Py) ↔ `camelCase` (C++): `spin_to_position` ↔ `spinToPosition`.
- Construction: Python `motor_1 = Motor(PORT1)` ↔ C++ `vex::motor motor1 = vex::motor(PORT1);` (typed, namespaced).
- Enums/units: Python `FORWARD`, `DEGREES`, `RPM` (from `vex import *`) ↔ C++ `vex::directionType::fwd`, `vex::rotationUnits::deg`, `vex::velocityUnits::rpm`.
- Entry point: Python is top-to-bottom script with auto-instantiated `Brain` ↔ C++ has `int main()` + `vex::competition`.

### 4. Runtime: interpreted MicroPython vs compiled native [S6][S7][S8][S9]
- Python on the Brain is **MicroPython 1.13 (Python 3.4 base)**, interpreted [S6]. Available modules: `uasyncio, uarray, ubinascii, ucollections, uio, ujson, urandom, ure, uselect, ustruct, utime, math, cmath, sys, gc` — **no pip, no NumPy/CPython C-extensions** [S6].
- C++ is compiled to native ARM Cortex-A9. General embedded benchmarks put MicroPython **~10–300× slower than C for compute-heavy/tight loops** [S7][S9]; "for tight loops, bit-banging, or real-time control, MicroPython is too slow… for high-level logic, sensor polling, and network communication, it's fast enough" [S7]. Real-time precision: interpretation overhead accumulates across thousands of cycles/sec, hurting "loop stability, sensor synchrony, and latency predictability in closed-loop systems" [S8].
- Practical VEX consequence: **PID/odometry/tight control loops are the C++ norm**; "most people use c++" for PID, and Python PID is comparatively under-documented and harder [S10]. Python is fine for sensor reads, state logic, screen UI, and orchestration.

### 5. Concurrency model is shared, not different [S11][S12]
Both languages expose multitasking under `Logic/Threads` — Python `Thread` ↔ C++ `thread`/`task` — running on the **same cooperative VEXcode scheduler** (the scheduler's author confirms VEXcode threads are cooperative, single-core time-sliced) [S11][S12]. So concurrency *capability* is equal; what differs is that a long-running C++ thread yields predictably and cheaply, whereas a compute-heavy Python thread holds the interpreter longer per slice. (Contrast: **PROS** uses preemptive FreeRTOS — a reason the codebase's `pros::` choice gives stronger real-time guarantees than either VEXcode language — see [../vexcode-v5/index.md](../vexcode-v5/index.md).)

### 6. Ecosystem / learning [S13][S14]
Python reads closer to plain English and is the common beginner on-ramp after Blocks; C++ is harder to learn but is the competitive default and what most VRC PID/autonomous tutorials target [S13][S14]. Both have first-class VEX support, identical sensor coverage, and a Competition template.

---

## Constraints

Any choice must account for:
1. **Same hardware coverage either way** — language choice does not unlock or lock out any V5 device.
2. **MicroPython library ceiling** — no third-party Python packages on the Brain; heavy compute (ML, NumPy, the LLM/self-model) must live on the external Pi regardless of on-Brain language (matches `project-telemetry-pipeline`).
3. **Real-time** — for PID and tight loops, compiled C++ (VEXcode or PROS) is materially safer than MicroPython.
4. **Existing investment** — the Brain bridge is already PROS C++ (`pros::` API), which is *neither* VEXcode C++ *nor* VEXcode Python; switching to a VEXcode language would mean rewriting `main.cpp` against a different SDK and scheduler.
5. **Cooperative scheduler (VEXcode, both languages)** — long-blocking code starves other tasks; PROS's FreeRTOS avoids this.
6. **Doc-tree divergence** — verify method names per-device page; don't assume mechanical snake↔camel equivalence.

---

## Solution Comparison

| Criteria | VEXcode **Python** (MicroPython) | VEXcode **C++** | PROS **C++** *(what the codebase uses)* |
|---|---|---|---|
| **Device/API coverage** | Full V5 SDK | Full V5 SDK | Full V5 SDK (+ low-level `apix`) |
| **Syntax** | `snake_case`, dynamic, scripty | `camelCase`, typed, `vex::` namespace | `pros::` namespace, typed |
| **Runtime** | Interpreted MicroPython 1.13 | Compiled native ARM | Compiled native ARM |
| **Speed (tight loops)** | ~10–300× slower [S7][S9] | Native | Native |
| **Scheduler** | Cooperative | Cooperative | **Preemptive (FreeRTOS)** |
| **PID / real-time fit** | Weak (under-documented) [S10] | Strong (competition norm) | Strongest |
| **Ease of learning** | Easiest text option [S13] | Harder | Hardest |
| **3rd-party libs on Brain** | None (no pip) | Pre-loaded C++ stdlib | C/C++ headers |
| **Serial JSON bridge** | `print()` / `sys.stdin` | `printf` / `getchar` | `getchar`/`printf` + `SERCTL_DISABLE_COBS` *(in `main.cpp`)* |
| **Codebase fit** | Would require rewrite | Would require rewrite | **Already implemented** |
| **Maintenance** | VEX (active) | VEX (active) | Community/Purdue (active) |

---

## Recommendation

**For the capstone's on-Brain control layer: stay with compiled C++, and keep the existing PROS bridge** — do not migrate the Brain code to VEXcode Python. Rationale:
1. The Brain layer's job is low-level, time-sensitive motor/serial handling (watchdog at 250 ms, 10 ms loop in `opcontrol()`); compiled C++ gives the deterministic timing MicroPython cannot, and PROS's preemptive scheduler is the strongest fit of the three.
2. The bridge is **already written in PROS C++** and matches the Pi-side JSON serial design; rewriting it in Python would trade performance down and re-introduce the cooperative-scheduler constraint for no gain.
3. The heavy intelligence (LLM, self-model, ML) lives on the **Pi in CPython** anyway, so the language richness Python would offer on the Brain is unnecessary there — it's available where it matters, off-Brain.

**Where Python is still the right tool:** the **Pi side** (full CPython, NumPy, the LLM toolchain) and any quick on-Brain experiments / demos where iteration speed beats loop performance and you're not running PID. If the team wants a *single* on-Brain language for pedagogy and is willing to accept cooperative scheduling, **VEXcode C++** (not Python) is the closest official analog to the current PROS code.

**Implementation outline (record the decision, don't re-architect):**
1. File a `/decision-create` capturing "on-Brain layer = PROS C++; Pi layer = CPython" and explicitly superseding the Python-on-Brain suggestion in `vexcode-v5` research.
2. Keep `main.cpp` as the Brain contract; treat api.vex.com C++ pages as the device-method reference and the local reference table above for navigation.
3. Use the Motor getter set (`position/velocity/current/torque/efficiency/temperature`) as the telemetry schema crossing the serial link.

**Risks & mitigations:**
- *PROS ≠ VEXcode C++ API*: method names/namespaces differ (`pros::` vs `vex::`). When reading api.vex.com C++ docs, translate to PROS equivalents; don't paste VEXcode snippets into the PROS project verbatim.
- *Cooperative vs preemptive confusion*: the api.vex.com docs describe VEXcode's cooperative threads; the codebase's FreeRTOS behavior differs — note this when consulting `Logic/Threads`.
- *Doc drift*: verify any method on its per-device page before relying on it.

**Alternative if constraints change:** if the team abandons PROS for the official toolchain, adopt **VEXcode C++** for parity with the docs and the cooperative model; reserve **VEXcode Python** for Blocks→text teaching and non-time-critical scripts only.

---

## Next Steps

- Run `/wiki-ingest raw/research/vexcode-python-vs-cpp/index.md` to synthesize this into the knowledge base (update `wiki/knowledge/entities/tools/vexcode.md`; consider a new concept page "VEXcode Python vs C++ parity").
- `/decision-create Choose on-Brain language/toolchain: PROS C++ (current) vs VEXcode C++ vs VEXcode Python` — to resolve the contradiction between this codebase's PROS choice and the prior `vexcode-v5` Python recommendation.
- Optional `/task-add Document Python↔C++ (and PROS↔VEXcode) method-name translation cheatsheet for the telemetry schema`.
