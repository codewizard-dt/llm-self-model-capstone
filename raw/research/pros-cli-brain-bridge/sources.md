---
topic: How to use PROS CLI to build/upload, and exactly what C++ program the Brain needs to receive Python commands from the RPi over serial and translate them to V5 motor commands
slug: pros-cli-brain-bridge
researched: 2026-06-21
---

# Primary Sources — PROS CLI + Brain Bridge Program

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S-code | codebase | `robot/v5-brain/pros_bridge/src/main.cpp` + `robot/pi-runtime/src/vexy_system2/protocol.py` | 2026-06-21 | Current single-loop sketch; wire format; clamp values; port map reference |
| S1 | web | https://github.com/Jerrylum/cmapi-cli | 2026-06-21 | `pip3 install pros-cli`; Linux requires adding user to dialout group for upload |
| S2 | web | https://pros.cs.purdue.edu/v5/getting-started/macos.html | 2026-06-21 | Official macOS installer bundles CLI+toolchain; pip is the advanced path; .whl install option |
| S3 | web | https://pros.cs.purdue.edu/v5/cli/conductor.html | 2026-06-21 | Conductor model: project = files + platform + templates; `pros conduct fetch` then `apply` for custom templates |
| S4 | web | https://pros.cs.purdue.edu/v5/pros-4/clawbot.html | 2026-06-21 | `prosv5 mu` builds+uploads; project creation via CLI |
| S5 | web | https://github.com/purduesigbots/pros-cli/issues/110 | 2026-06-21 | `project.pros` has `upload_options` with `slot`; default upload is slot 1 |
| S6 | web | https://tustincode.com/common-pros-and-terminal-commands/ | 2026-06-21 | `prosv5 upload --slot N` (1-8); `prosv5 mu` = make+upload; no slot defaults to slot 1 |
| S7 | web | https://github.com/purduesigbots/pros-cli | 2026-06-21 | CLI is Python 3.6 based; conductor handles project management |
| S8 | web | https://www.vexforum.com/t/how-to-use-webserver/123135 | 2026-06-21 | If VEX/PROS terminal is open it controls the serial port; must close it to open the user port in another app |
| S9 | context7 | /websites/pros_cs_purdue_edu_v5 — "Motor move_velocity move_voltage brake API" | 2026-06-21 | `motor.move_velocity(rpm)` uses PID; RPM caps 100/200/600 by gearset; `move()` ±127; `get_actual_velocity()` returns RPM |
| S10 | context7 | /websites/pros_cs_purdue_edu_v5 — "Motor velocity control gearset" | 2026-06-21 | move_velocity holds speed via internal PID; gearset determines max (100=36:1, 200=18:1, 600=6:1) |
| S11 | context7 | /websites/pros_cs_purdue_edu_v5 — "pros::Task create background task" | 2026-06-21 | `pros::Task(fn, param, name)` creates a background task; tasks need a delay() to avoid starvation; preemptive |
| S12 | web | https://www.vexforum.com/t/v5-brain-to-raspberry-pi-communication/124407 | 2026-06-21 | PROS: printf() to send, getchar()/scanf()/fgets() to receive over USB; two-task send/receive pattern |
| S13 | web | https://arduinojson.org/ | 2026-06-21 | ArduinoJson header-only embedded JSON; StaticJsonDocument stack allocation avoids heap fragmentation |
| S14 | context7 | /websites/pros_cs_purdue_edu_v5 — "SERCTL_DISABLE_COBS serial read" | 2026-06-21 | serctl(SERCTL_DISABLE_COBS) disables COBS so you can read serial yourself instead of `pros terminal`; get_read_avail() for non-blocking checks |

---

## Excerpts

### S6 — Common PROS and Terminal Commands (Tustin Code)
https://tustincode.com/common-pros-and-terminal-commands/
> "type prosv5 upload --slot <SLOT NUM>. <SLOT NUM> is any number between 1 through 8 as the V5 Brain can hold up 8 programs at a time... If you simply type prosv5 upload with no slot specified, it will automatically upload to program slot 1... If you type prosv5 mu it will first make the project and then upload the project all in this one command."

### S9 — PROS Motor velocity control (Context7 / pros_cs_purdue_edu_v5)
/websites/pros_cs_purdue_edu_v5
> "motor_move_velocity ... The velocity is held with PID control. The actual speed depends on the motor's gearset (100 for 36:1, 200 for 18:1, 600 for 6:1). Returns PROS_ERR on failure."

### S11 — PROS Task creation (Context7 / pros_cs_purdue_edu_v5)
/websites/pros_cs_purdue_edu_v5
> "Tasks are functions executed asynchronously. Ensure task functions include a delay() to prevent processor starvation. ... pros::Task my_task(task_fn, (void*)\"PROS\", \"My Task\");"

### S12 — V5 Brain to Raspberry Pi Communication (VEX Forum)
https://www.vexforum.com/t/v5-brain-to-raspberry-pi-communication/124407
> "Writing to Serial: Use printf() for sending data, which writes to the standard output (connected to the Raspberry Pi via USB in your setup). Reading from Serial: Use scanf(), getchar(), or similar functions to read incoming data from the standard input."

### S14 — PROS Filesystem/Serial (Context7 / pros_cs_purdue_edu_v5)
/websites/pros_cs_purdue_edu_v5
> "These methods can be accessed through the serctl() function. At the moment two actions are supported - activating/deactivating the streams, and enabling/disabling COBS. If you want to read the serial comms yourself (without using pros terminal), then you'll want to disable COBS."

### S1 — cmapi-cli (GitHub, Jerrylum)
https://github.com/Jerrylum/cmapi-cli
> "It is recommended to install the PROS-CLI manually using pip. pip3 install pros-cli ... On Linux, you also need to add yourself to the dialout group before you can upload to the V5 Brain."

### S8 — How to use webserver (VEX Forum)
https://www.vexforum.com/t/how-to-use-webserver/123135
> "if using VEXcode or VSCode with the vex extension make sure the user terminal is closed otherwise that will control the serial port."

### S3 — PROS Conductor User Guide
https://pros.cs.purdue.edu/v5/cli/conductor.html
> "They must download the zip archive, pros conduct fetch it into their local depot, then pros conduct apply it to a project."
