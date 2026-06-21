---
topic: V5 Brain program language choice — VEXcode Python (MicroPython) thin executor vs PROS C++ thin executor vs PROS C++ smart brain (LemLib trajectory)
slug: v5-brain-python-vs-pros
researched: 2026-06-21
---

# Primary Sources — V5 Brain Python vs PROS C++

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/pi-runtime/docs/ARCHITECTURE.md` | 2026-06-21 | Defines thin-executor role split: Pi owns vision/planning, Brain owns motors/safety |
| S2 | codebase | `robot/v5-brain/pros_bridge/src/main.cpp` | 2026-06-21 | Current PROS C++ starter: SERCTL_DISABLE_COBS, getchar() loop, 250ms watchdog, TODOs for motor ports |
| S3 | codebase | `robot/pi-runtime/docs/PROTOCOL.md` | 2026-06-21 | Wire format spec: newline JSON, v/seq/type/cmd/ttl_ms, max 1000ms TTL, response fields |
| S4 | codebase | `robot/pi-runtime/src/vexy_system2/protocol.py` | 2026-06-21 | Pi-side protocol implementation: clamping, validation, encode/decode |
| S5 | web | https://api.vex.com/v5/home/python/Logic/Threads.html | 2026-06-21 | VEXcode Python Thread class; cooperative scheduler; wait() calls yield |
| S6 | web | https://www.vexforum.com/t/std-cin-or-scanf-support-in-vex-vscode/131665 | 2026-06-21 | "The brain supports it but I suspect the VEXcode console does not" — stdin interception concern |
| S7 | web | https://github.com/orgs/micropython/discussions/11448 | 2026-06-21 | MicroPython sys.stdin.read(1) blocks; uselect.poll(0) pattern for non-blocking check |
| S8 | web | https://stackoverflow.com/questions/21791621/taking-input-from-sys-stdin-non-blocking | 2026-06-21 | "By turning blocking off you can only read a character at a time. No way to get readline() to work in a non-blocking context." |
| S9 | web | https://www.vexforum.com/t/reading-vex-v5-serial-port-using-python/84699 | 2026-06-21 | RPi+V5 USB serial setup question — all Python in answers is Pi-side, not Brain-side |
| S10 | web | https://www.vexforum.com/t/rapsberry-pi-to-vex-bidirectional-communication/85696 | 2026-06-21 | Bidirectional RPi↔V5 — no working Brain-side Python stdin example found |
| S11 | web | https://www.vexforum.com/t/how-to-use-webserver/123135 | 2026-06-21 | "Here is a simple python user program that allows you to read and write data to the user port from your brain" — but context clarifies pyserial runs on the computer, not Brain |
| S12 | web | https://docs.micropython.org/en/v1.15/library/uselect.html | 2026-06-21 | uselect module in standard MicroPython 1.15 — availability on VEX's custom port unconfirmed |
| S13 | web | https://www.aadishv.dev/robotics-5 | 2026-06-21 | Real VEX AI team: PROS + SERCTL_DISABLE_COBS confirmed; single-task deadlock; two-task split (send/receive) required |
| S14 | web | https://www.vexforum.com/t/v5-brain-to-raspberry-pi-communication/124407 | 2026-06-21 | PROS C++ two-task pattern: sendDataToRPI task + receiveDataFromRPI task with fgets(stdin) |
| S15 | web | https://pros.cs.purdue.edu/v5/tutorials/topical/multitasking.html | 2026-06-21 | "PROS task scheduler is a preemptive, priority-based, round-robin scheduler. Tasks are preempted every millisecond." |
| S16 | web | https://github.com/VEX-Robotics/VAIC_23_24/blob/main/JetsonExample/README.md | 2026-06-21 | VAIC official reference: PROS C++ on Brain, V5SerialComms class on Jetson — architecture mirror of capstone |
| S17 | web | https://github.com/LemLib/LemLib | 2026-06-21 | LemLib is a PROS-only template; requires IMU + odometry config; adds pose-level trajectory PID |
| S18 | web | https://lemlib.readthedocs.io/en/stable/tutorials/2_configuration.html | 2026-06-21 | LemLib configuration: drivetrain + IMU + odometry required; track width, wheel diameter, rpm tuning |
| S19 | web | https://www.reddit.com/r/vex/comments/1gdm8vn/clarification_on_the_state_of_vex_sdk_and_its/ | 2026-06-21 | "VEXos utilizes a cooperative scheduler whereas FreeRTOS uses a preemptive scheduler" — confirms the scheduling difference |
| S20 | codebase | `robot/pi-runtime/docs/TOMORROW_BRINGUP.md` | 2026-06-21 | Language-agnostic Brain requirements; physical bringup sequence documented |

---

## Excerpts

### S6 — std::cin or scanf() support in VEX VScode (VEX Forum)
https://www.vexforum.com/t/std-cin-or-scanf-support-in-vex-vscode/131665
> "I'm trying to utilize std::cin / scanf() to aid with building my autonomous, when I try to enter a value into the console, it does not accept any inputs... Are there any plans to add this feature?"
> Response: "The brain supports it but I suspect the VEXcode console does not."

### S7 — MicroPython Discussion: Non-blocking read
https://github.com/orgs/micropython/discussions/11448
> "sys.stdin.read(1) will read that byte and block (potentially forever) on waiting for the next byte... When we call spoll.poll(0), the 0 parameter specifies a milliseconds timeout value of 0, which means that the poll() method will return immediately with a list of file descriptors that have events to process, or an empty list if no events are ready to be processed."

### S13 — aadishv.dev: VEX AI serial implementation at Worlds
https://www.aadishv.dev/robotics-5
> "We use the PROS framework instead of VEXcode for our programming on the V5 side. PROS uses an encoding scheme known as COBS to ensure that packet delimiters do not include as part of message content... this is not good for our VEX AI code, because our Jetson serial layer does not handle COBS decoding. Because of this, we actually disable the COBS layer on the V5 side."
> "It isn't super obvious at first why we need two separate tasks for sending and receiving packets. After all, we know that the Jetson only sends us a packet after we've sent it one packet. This is what we thought too, at first, so we implemented it as a single task... [but we needed to split them]."

### S14 — V5 Brain to Raspberry Pi Communication (VEX Forum)
https://www.vexforum.com/t/v5-brain-to-raspberry-pi-communication/124407
> "void receiveDataFromRPI(void* param) { char buffer[256]; while (true) { if (fgets(buffer, sizeof(buffer), stdin) != NULL) { printf(\"Received from RPi: %s\", buffer); } pros::delay(20); } }"

### S15 — PROS Multitasking documentation
https://pros.cs.purdue.edu/v5/tutorials/topical/multitasking.html
> "The PROS task scheduler is a preemptive, priority-based, round-robin scheduler. This means that tasks are preempted (interrupted) every millisecond to determine if another task ought to run."

### S19 — Reddit: VEXos vs FreeRTOS scheduler
https://www.reddit.com/r/vex/comments/1gdm8vn/clarification_on_the_state_of_vex_sdk_and_its/
> "VEXos utilizes a cooperative scheduler whereas FreeRTOS uses a preemptive scheduler. It's not clear whether VEXos is based on another OS or completely developed from the ground up. It doesn't matter that much for user code though since VEXos and user code run on separate cores within the V5 brain."
