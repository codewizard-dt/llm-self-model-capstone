---
topic: How to use PROS CLI to build/upload, and exactly what C++ program the Brain needs to receive Python commands from the RPi over serial and translate them to V5 motor commands
slug: pros-cli-brain-bridge
researched: 2026-06-21
sources: [./sources.md]
---

# Research: PROS CLI Workflow + The Exact Brain-Side C++ Bridge Program

> **The Brain program is a serial command interpreter, not robot logic.** Its entire job: read newline-delimited JSON from the USB user port (sent by the Pi's Python), translate each command into a PROS motor call (`motor.move_velocity()` etc.), send back a JSON ack, and stop the motors if commands stop arriving. The PROS CLI workflow is four commands: `pros conduct new-project`, `pros make`, `pros upload --slot N`, `pros terminal`. The robust program architecture is **two FreeRTOS tasks** — one receiving commands, one enforcing a safety watchdog — exploiting PROS's preemptive scheduler so a blocked read can never disable the watchdog. This report gives the complete CLI command set and a full, annotated reference implementation that extends the existing `main.cpp` sketch.

---

## Research Questions

1. What are the exact PROS CLI commands to install, create a project, build, upload to a slot, and open a serial terminal?
2. What is the minimal-but-correct C++ program structure for a Pi→Brain command bridge?
3. Which PROS motor API calls translate "drive at velocity vx" into actual V5 Smart Motor commands?
4. How do you read serial from the Pi in PROS without the read blocking the safety watchdog?
5. How should JSON be parsed on the Brain (hand-rolled vs library)?

---

## Current State (Codebase)

`robot/v5-brain/pros_bridge/src/main.cpp` is a single-loop starter sketch [S-code]:
- `initialize()`: `serctl(SERCTL_DISABLE_COBS, nullptr)`
- `opcontrol()`: one `while(true)` loop — `getchar()` char-by-char into a 512-byte line buffer, dispatch on `'\n'`, `pros::delay(10)` each iteration
- Handles `heartbeat`, `stop` (sets estop), `drive` (TODO: parse vx/omega, command motors)
- Watchdog: `pros::millis() - last_packet_ms > 250` → `stop_drive()`
- Motor ports unwired (all TODOs)

The Pi side (`robot/pi-runtime/`) already speaks the wire format: newline-delimited JSON, `v/seq/type/cmd/ttl_ms`, commands `heartbeat/stop/drive/turn/set_goal`, clamps to ±0.35 linear / ±0.60 omega [S-code]. The Clawbot port map (from the entity page): **ports 1 & 10 drive, port 3 claw, port 8 arm.**

---

## Key Findings

### Part 1 — PROS CLI Workflow

**Install** (macOS/Linux dev machine — NOT the Pi; the Pi never builds C++): [S1, S2]
```bash
pip3 install pros-cli            # Python 3.6+; installs the `pros` command
pros --version                   # verify
# Linux only: add yourself to dialout group for USB upload permission
sudo usermod -a -G dialout $USER   # then log out/in
```
The official installer for macOS/Windows bundles the CLI + ARM toolchain; pip install is the "advanced user" path and needs the `arm-none-eabi-gcc` toolchain present. [S2]

**Create a project:** [S3, S4]
```bash
pros conduct new-project ./vexy-brain        # creates project with latest kernel
# (older alias: `prosv5 conduct new-project`; `pros` and `prosv5` are equivalent)
```
A project is just user files + a target platform + a list of installed templates. `project.pros` records the kernel version and `upload_options` (including a default `slot`). [S3, S5]

**Build:** [S4, S6]
```bash
pros make                # compiles to bin/monolith.bin
```

**Upload to a Brain slot (1–8):** [S6, S7]
```bash
pros upload --slot 1            # build output → slot 1 on the Brain
pros mu --slot 1                # "make + upload" in one command (most common)
pros mu                         # no --slot → defaults to slot 1
```
You can also pin the slot in `project.pros` under `upload_options: {"slot": 1}` so a bare `pros mu` always targets it. [S7]

**Open the serial terminal (the user port — see live `printf` output):** [S6]
```bash
pros terminal                  # opens the user/debug port; shows stdout from the program
```
⚠️ **Critical for the capstone:** `pros terminal` (and the VS Code "Integrated Terminal") **opens and holds the user serial port**. If it's open, the Pi's pyserial cannot also open that port. Close the PROS terminal before running the Pi bridge. [S8, prior research]

**Add a template (e.g. LemLib later):** [S3]
```bash
pros conduct fetch LemLib@<version>     # into local depot
pros conduct apply LemLib               # into this project
```

**One-shot dev loop:** edit `main.cpp` → `pros mu --slot 1` → tap slot on Brain (or it auto-runs after upload if "run after download" is on).

### Part 2 — The Motor Translation Layer (the heart of the program)

A V5 Smart Motor runs its own hardware PID. The Brain program does **not** compute voltages — it hands the motor a **setpoint** via one of these PROS calls: [S9, S10]

| PROS C++ call | What it commands | Range |
|---|---|---|
| `motor.move_velocity(rpm)` | Closed-loop target velocity (hardware PID holds it) | ±100 (36:1), ±200 (18:1), ±600 (6:1) |
| `motor.move(value)` | Open-loop "voltage" like a joystick | −127…127 |
| `motor.move_voltage(mV)` | Direct voltage | −12000…12000 mV |
| `motor.brake()` | Stop per brake mode | — |
| `motor.set_brake_mode(E_MOTOR_BRAKE_BRAKE)` | Coast/brake/hold on zero | — |

**For the capstone's `drive` command, `move_velocity` is correct** — it uses the motor's internal PID so "go this fast" actually holds that speed, and the achieved velocity is what telemetry reads back. The Clawbot 18:1 drive cartridge caps at ±200 RPM, so map the Pi's normalized `vx` (−0.35…0.35) onto RPM:

```cpp
// vx is a normalized linear command from the Pi; MAX_RPM is the cartridge cap
int16_t rpm = (int16_t)(vx / MAX_LINEAR * 200);   // 18:1 → 200 RPM
left.move_velocity(rpm + turn_term);
right.move_velocity(rpm - turn_term);
```

### Part 3 — Reading Serial Without Starving the Watchdog

The danger (from prior research): a blocking read holds the loop; if the Pi disconnects mid-read, the watchdog never fires. PROS solves this because its scheduler is **preemptive** — a separate task always runs. [S11, prior research]

**Recommended architecture — two tasks:** [S11, S12]
- **Receive task**: blocks on reading stdin, assembles lines, parses, commands motors, updates `last_packet_ms` (a shared `std::atomic` or mutex-guarded).
- **Safety/watchdog task**: independent loop, every 10–20 ms checks `pros::millis() - last_packet_ms`; if over the TTL/watchdog threshold, force motors to brake. Because it's a separate FreeRTOS task, it runs even if the receive task is blocked.

This is the structural upgrade over the current single-loop sketch. The VEX forum community confirms `printf()` to send and `getchar()`/`fgets()`/`scanf()` to receive over the USB link. [S12]

### Part 4 — JSON Parsing on the Brain

Two viable options: [S13, S14]
- **Hand-rolled field extraction** (what the sketch does with `line.find("\"cmd\":\"drive\"")`): zero dependencies, but fragile and tedious for numeric fields like `vx`. Fine for command-type dispatch; painful for floats.
- **ArduinoJson** (header-only, embedded-grade, `StaticJsonDocument<N>` stack allocation): drops into a PROS `include/` directory, no heap fragmentation if you use the static document. Recommended for parsing the numeric command fields cleanly. [S13]

For ~300-byte command packets a `StaticJsonDocument<256>` is plenty. Keep it stack-allocated to avoid heap churn at 50 Hz.

---

## The Complete Reference Program

This is the full Brain-side bridge — extends the existing sketch with the two-task pattern, motor wiring, and clean parsing. Drop ArduinoJson's single header into `include/`.

```cpp
#include "main.h"
#include "pros/apix.h"
#include "ArduinoJson.h"     // header-only, in include/
#include <atomic>
#include <string>

// ---- Clawbot port map (from build instructions) ----
constexpr int LEFT_PORT = 1, RIGHT_PORT = 10, CLAW_PORT = 3, ARM_PORT = 8;
constexpr int WATCHDOG_MS = 250;
constexpr double MAX_LINEAR = 0.35, MAX_OMEGA = 0.60;
constexpr int DRIVE_MAX_RPM = 200;          // 18:1 cartridge

pros::Motor left_drive(LEFT_PORT);
pros::Motor right_drive(RIGHT_PORT, true);  // reversed
pros::Motor claw(CLAW_PORT);
pros::Motor arm(ARM_PORT);

std::atomic<uint32_t> last_packet_ms{0};
std::atomic<bool> estop{false};

void all_stop() {
  left_drive.brake(); right_drive.brake();
  claw.brake(); arm.brake();
}

void ack(int seq, const char* state, const char* fault = "null") {
  // telemetry piggybacks on the ack: report what the motors actually achieved
  printf("{\"v\":1,\"ack\":%d,\"type\":\"ack\",\"state\":\"%s\","
         "\"recv_ms\":%lu,\"fault\":%s,"
         "\"left_rpm\":%.1f,\"right_rpm\":%.1f,"
         "\"left_temp\":%.0f,\"left_current\":%d}\n",
         seq, state, (unsigned long)pros::millis(), fault,
         left_drive.get_actual_velocity(), right_drive.get_actual_velocity(),
         left_drive.get_temperature(), left_drive.get_current_draw());
  fflush(stdout);
}

void handle(const std::string& line) {
  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, line)) { return; }      // malformed → ignore
  last_packet_ms = pros::millis();
  int seq = doc["seq"] | -1;
  const char* type = doc["type"] | "";
  const char* cmd  = doc["cmd"]  | "";

  if (!strcmp(type, "heartbeat")) { ack(seq, "ok"); return; }
  if (!strcmp(cmd, "stop")) {
    estop = (strcmp(doc["reason"] | "", "operator_estop") == 0);
    all_stop(); ack(seq, "ok"); return;
  }
  if (!strcmp(cmd, "drive")) {
    if (estop) { all_stop(); ack(seq, "rejected", "\"estop_latched\""); return; }
    double vx    = doc["vx"]    | 0.0;
    double omega = doc["omega"] | 0.0;
    // clamp defensively (Pi already clamps, but never trust the wire)
    vx    = vx    < -MAX_LINEAR ? -MAX_LINEAR : (vx    > MAX_LINEAR ? MAX_LINEAR : vx);
    omega = omega < -MAX_OMEGA  ? -MAX_OMEGA  : (omega > MAX_OMEGA  ? MAX_OMEGA  : omega);
    int16_t base = (int16_t)(vx / MAX_LINEAR * DRIVE_MAX_RPM);
    int16_t turn = (int16_t)(omega / MAX_OMEGA * DRIVE_MAX_RPM);
    left_drive.move_velocity(base + turn);
    right_drive.move_velocity(base - turn);
    ack(seq, "ok"); return;
  }
  all_stop(); ack(seq, "rejected", "\"unknown_command\"");
}

// ---- Task 1: receive loop ----
void receive_task(void*) {
  std::string line;
  while (true) {
    int ch = getchar();                 // next byte from user port, or EOF if none
    if (ch != EOF) {
      if (ch == '\n') { handle(line); line.clear(); }
      else if (line.size() < 512) line.push_back((char)ch);
      else line.clear();                // oversized → drop
    } else {
      pros::delay(2);                   // nothing waiting; yield briefly
    }
  }
}

// ---- Task 2: independent safety watchdog ----
void watchdog_task(void*) {
  while (true) {
    if (pros::millis() - last_packet_ms > WATCHDOG_MS) all_stop();
    pros::delay(10);
  }
}

void initialize() {
  serctl(SERCTL_DISABLE_COBS, nullptr);   // plain stdout for pyserial
  left_drive.set_brake_mode(pros::E_MOTOR_BRAKE_BRAKE);
  right_drive.set_brake_mode(pros::E_MOTOR_BRAKE_BRAKE);
  last_packet_ms = pros::millis();
}

void opcontrol() {
  // No competition switch → opcontrol runs immediately after initialize().
  pros::Task r(receive_task,  nullptr, "rx");
  pros::Task w(watchdog_task, nullptr, "watchdog");
  while (true) pros::delay(1000);          // tasks do the work
}
```

**Why this shape:**
- `initialize()` disables COBS and sets brake modes once.
- `opcontrol()` spawns the two tasks and idles — the preemptive scheduler runs both [S11].
- The watchdog is a *separate task*, so even if `getchar()` blocks, motors still stop on Pi silence.
- `move_velocity()` feeds the motor's inner PID; `get_actual_velocity()`/`get_temperature()`/`get_current_draw()` ride back on the ack as telemetry [S9, S10].
- Defensive clamping repeats the Pi-side clamp — the Brain is the last safety layer (per `ARCHITECTURE.md`).

---

## Constraints

1. Build/upload happens on a laptop, not the Pi — the Pi only runs Python + pyserial against the user port.
2. `pros terminal` and the Pi bridge cannot hold the user port simultaneously — close one.
3. The program must run from a slot (tap on Brain, or auto-run after upload) before the Pi connects.
4. Motor ports must match the physical wiring (1/10 drive, 3 claw, 8 arm for the Clawbot).
5. ArduinoJson header must be vendored into `include/` (no pip/package manager on the Brain).
6. `move_velocity` RPM ceiling depends on the installed cartridge (200 for the stock 18:1).

---

## Recommendation

**Adopt the two-task structure now**, even before hardware arrives — it's the difference between a demo-safe watchdog and a latent runaway bug. Concretely:
1. `pip3 install pros-cli`; convert `robot/v5-brain/pros_bridge/` into a real PROS project (`pros conduct new-project`) if it isn't one yet, or confirm `project.pros` exists.
2. Vendor `ArduinoJson.h` into `include/`.
3. Replace the single `opcontrol()` loop with the receive-task / watchdog-task pair above.
4. Wire the Clawbot port map and the `vx/omega → RPM` mapping.
5. `pros mu --slot 1`, tap slot 1, run the Pi `serial_ping_test.sh`.

**Risks & mitigations:**
- *`getchar()` blocking semantics on V5 are unverified* → the watchdog task makes this safe regardless; verify empirically with the first bringup (prior research's 10-line echo test).
- *RPM mapping is morphology-specific* → keep `DRIVE_MAX_RPM` and the port map as named constants for easy retune when the cartridge or build changes.
- *Heap fragmentation at 50 Hz* → use `StaticJsonDocument` (stack), never `DynamicJsonDocument`.

**Alternative if Python-on-Brain turns out viable** (the unresolved stdin question): the same two-layer logic ports to VEXcode Python with `ujson` + a `Thread` watchdog — but only if VEX's cooperative scheduler runs the watchdog thread during a blocked read, which is exactly the doubt PROS sidesteps. See [[v5-brain-python-vs-pros]].

---

## Next Steps

- `/task-add Convert pros_bridge to two-task PROS program — wire Clawbot ports, vx/omega→RPM, ArduinoJson parsing`
- Verify the project is a valid PROS project (`project.pros` present); if not, scaffold it
- Decide the canonical slot (recommend slot 1) and pin it in `project.pros`
- On first hardware bringup: run the prior-research stdin echo test, then this bridge, robot on blocks
