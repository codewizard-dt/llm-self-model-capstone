---
topic: the vexcode api https://api.vex.com/v5/home/ before creating a local reference... do a thorough comparision of the python and C++ apis. Determine the pros and cons of each relative to the other and compare what can be done with both
slug: vexcode-python-vs-cpp
researched: 2026-06-20
---

# Primary Sources — VEXcode V5 Python vs C++ API Comparison

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://api.vex.com/v5/home/ | 2026-06-20 | Confirms the API splits into Blocks / Python / C++ / Tutorials; C++ = "classes, objects, constructors, member functions", Python = "methods, functions, parameters, return values" |
| S2 | web | https://api.vex.com/v5/home/python/ (Section Navigation, rendered) | 2026-06-20 | Full Python top-level section list + sub-page URLs (Drivetrain, Motion, Vision, Screen, Controller, Sensing, Inertial, 3-wire, Pneumatics, Brain, SDcard, VEXlink, Console, Logic, Arm, Magnet, Competition, MicroPython Libraries) |
| S3 | web | https://api.vex.com/v5/home/cpp/ (Section Navigation, rendered) | 2026-06-20 | Full C++ top-level section list + URLs (Drivetrain, Motors and Motor Controllers, Controller, Brain, Competition, Smart Port Devices, 3-Wire Devices, Console, Logic, VEXlink, CTE Workcell) |
| S4 | web | https://api.vex.com/v5/home/cpp/Motors_and_MotorControllers/motor_and_motor_group.html ("On this page", rendered) | 2026-06-20 | C++ Motor method inventory grouped Actions/Mutators/Getters (camelCase) |
| S5 | web | https://api.vex.com/v5/home/python/Motion/motor_and_motor_group.html (rendered anchors) | 2026-06-20 | Python Motor method inventory (snake_case) incl. reset_position/set_reversed/get_timeout; proves snake↔camel + per-page divergence |
| S6 | web | https://api.vex.com/v5/home/python/Micropython_libraries.html | 2026-06-20 | MicroPython 1.13 (Python 3.4 base); available modules list; references docs.micropython.org |
| S7 | web | https://roboticcoding.com/is-micropython-faster-than-c/ | 2026-06-20 | MicroPython too slow for tight loops/real-time; fast enough for high-level logic/sensor polling; ~200–300× slower on ESP32 for compute |
| S8 | web | https://medium.com/@okannamdar/c-vs-micropython-measuring-real-time-precision-in-a-low-latency-tracking-system-e23fbb2f905d | 2026-06-20 | Interpretation overhead accumulates across cycles, affecting loop stability/sensor synchrony/latency predictability |
| S9 | web | https://news.ycombinator.com/item?id=25861584 | 2026-06-20 | "MicroPython is also a lot slower than Arduino style C++. Like, a LOT." ~10× clock-equivalent gap anecdote |
| S10 | web | https://www.vexforum.com/t/pid-programming-python/110892 | 2026-06-20 | VEX-specific: PID in Python is hard/under-documented; "most people use c++" |
| S11 | web | https://api.vex.com/v5/home/cpp/Logic/Threads.html + https://api.vex.com/v5/home/python/Logic/Threads.html | 2026-06-20 | Both languages expose Threads/multitasking with the same description and stop() semantics |
| S12 | web | https://www.vexforum.com/t/how-to-use-vex-threads/100901 | 2026-06-20 | VEXcode threads are cooperative (scheduler author comment) |
| S13 | web | https://www.reddit.com/r/vex/comments/m9beg9/advice_needed_which_code_to_use/ | 2026-06-20 | Python easier syntax/reads like English; C++ is the competitive default; same sensor support |
| S14 | web | https://www.vexforum.com/t/python-or-c/71352 | 2026-06-20 | C++ harder for beginners (reason block options exist); PROS only after learning VEXcode C++ |
| S15 | codebase | `robot/v5-brain/pros_bridge/src/main.cpp` | 2026-06-20 | Brain code is PROS C++ (`pros/apix.h`, `pros::millis/delay`, `serctl(SERCTL_DISABLE_COBS)`, `initialize()`/`opcontrol()`), JSON-over-serial bridge |
| S16 | codebase | `robot/v5-brain/pros_bridge/README.md` | 2026-06-20 | Confirms V5 USB user/console serial bridge design; PROS stdin/stdout; SERCTL_DISABLE_COBS requirement |
| S17 | codebase | `raw/research/vexcode-v5/index.md` | 2026-06-20 | Prior research recommended VEXcode **Python** on Brain — the contradiction this report flags |

## Excerpts

### S1 — VEX V5 API home
https://api.vex.com/v5/home/
> "C++ - Learn about the C++ classes, objects, constructors, member functions, parameters, return values, and examples used in VEXcode V5." / "Python - Learn about the Python methods, functions, parameters, return values, and examples used in VEXcode V5."

### S4 — C++ Motor and Motor Group (On this page)
https://api.vex.com/v5/home/cpp/Motors_and_MotorControllers/motor_and_motor_group.html
> Actions: spin, spinFor, spinToPosition, stop. Mutators: setPosition, setVelocity, setStopping, setMaxTorque, setTimeout. Getters: isDone, isSpinning, position, velocity, current, power, torque, efficiency, temperature, voltage, direction, installed, count.

### S5 — Python Motor and Motor Group (anchors)
https://api.vex.com/v5/home/python/Motion/motor_and_motor_group.html
> #spin #spin-for #spin-to-position #stop #set-position #set-velocity #set-stopping #set-max-torque #set-timeout #reset-position #set-reversed #get-timeout #is-done #is-spinning #position #velocity #current #power #torque #efficiency #temperature #count

### S6 — MicroPython Libraries
https://api.vex.com/v5/home/python/Micropython_libraries.html
> "MicroPython 1.13, which is based on Python 3.4." Modules: "uasyncio, uarray, ubinascii, ucollections, uio, ujson, urandom, ure, uselect, ustruct, utime, math, cmath, sys, gc".

### S7 — Is MicroPython Faster Than C?
https://roboticcoding.com/is-micropython-faster-than-c/
> "For tight loops, bit-banging, or real-time control, MicroPython is too slow. But for high-level logic, sensor polling, and network communication, it's fast enough and much easier to work with." … "on ESP32, MicroPython is typically 200–300× slower for compute-heavy tasks due to its interpreted nature."

### S8 — C++ vs MicroPython: Real-Time Precision
https://medium.com/@okannamdar/c-vs-micropython-measuring-real-time-precision-in-a-low-latency-tracking-system-e23fbb2f905d
> "Although these numbers may seem tiny, across thousands of cycles per second, they accumulate, affecting loop stability, sensor synchrony, and latency predictability in closed-loop systems."

### S9 — Hacker News
https://news.ycombinator.com/item?id=25861584
> "MicroPython is also a lot slower than Arduino style C++. Like, a LOT." … "An 80MHz microcontroller running C can go about as fast as a 800MHz microcontroller running MicroPython."

### S10 — PID Programming Python (VEX Forum)
https://www.vexforum.com/t/pid-programming-python/110892
> "I have been trying to add PID into my auton, but I can't figure out how to add it with python programming. as far as I can see, most people use c++."

### S11 — Threads (Python & C++ API)
https://api.vex.com/v5/home/python/Logic/Threads.html
> "Threads allow a robot to run multiple tasks simultaneously within the same program. They enable multitasking, letting the robot perform independent actions at the same time." (Identical text appears on the C++ Threads page.)

### S12 — How to use VEX Threads (VEX Forum)
https://www.vexforum.com/t/how-to-use-vex-threads/100901
> "I find it useful for normal VEX programming, for example, separating the display of status on the V5 screen from code controlling motors. But then I wrote the scheduler that VEXcode uses so I'm biased."

### S13 — Advice needed, which code to use (r/vex)
https://www.reddit.com/r/vex/comments/m9beg9/advice_needed_which_code_to_use/
> "python is generally easier on syntax and reads more like plain english than C based languages, but C can be used in Vexcode pro."

### S15 — PROS Brain bridge (codebase)
`robot/v5-brain/pros_bridge/src/main.cpp`
> `#include "pros/apix.h"` … `serctl(SERCTL_DISABLE_COBS, nullptr);` … `void opcontrol() { ... int ch = std::getchar(); ... pros::delay(10); }` — PROS lifecycle + JSON-over-serial, not VEXcode.
