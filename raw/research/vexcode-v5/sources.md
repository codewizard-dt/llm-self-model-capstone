---
topic: VEXcode V5 — functionality, implementation, and limitations (install/v5 page)
slug: vexcode-v5
researched: 2026-06-16
---

# Primary Sources — VEXcode V5

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://apps.apple.com/us/app/vexcode-v5/id1516887593 | 2026-06-16 | Blocks/Python/C++ mode list; AI Vision AprilTag support; Switch blocks; Read Blocks Aloud; random-number bug fix note |
| S2 | web | https://kb.vex.com/hc/en-us/articles/360047130071-Coding-with-VEXcode-V5 | 2026-06-16 | New project defaults to V5 Brain only; multi-device article links |
| S3 | web | https://en.wikipedia.org/wiki/VEX_Robotics | 2026-06-16 | VEXcode is Scratch-based; consistent across VEX 123/GO/IQ/V5; C++ header file for sensor/drivetrain; PROS context |
| S4 | web | https://motors.vex.com/vexcode/install/v5 | 2026-06-16 | Platform availability: web (Chrome), desktop (Win/Mac), mobile (iPad/Android/Fire); Chrome App EOL July 2025; Windows ARM support |
| S5 | web | https://kb.vex.com/hc/en-us/articles/360035954211-Installing-VEXcode-V5-on-Chromebook | 2026-06-16 | Chrome App becoming unusable after Google discontinues Chrome Apps; recommendation to switch to web-based VEXcode V5 |
| S6 | web | https://kb.vex.com/hc/en-us/articles/29373428548372-New-Features-in-VEXcode-V5-4-0 | 2026-06-16 | VEXcode 4.0 features: AI Vision Sensor object classification, Read Blocks Aloud, Switch blocks, enhanced stop command, API doc link |
| S7 | web | https://kb.vex.com/hc/en-us/articles/360045052352-Starting-Downloading-and-Running-a-Python-Project-in-VEXcode-V5 | 2026-06-16 | 8 Brain slots; download→slot→run workflow; Clawbot template usage |
| S8 | web | https://api.vex.com/v5/home/python/Brain.html | 2026-06-16 | Brain object auto-created at project start; constructor for manual Brain config |
| S9 | web | https://kb.vex.com/hc/en-us/articles/20676091646100-Data-Logging-with-a-VEX-Brain-and-Sensors-Using-Python | 2026-06-16 | Data logging CSV to SD card via Python; standard file I/O available |
| S10 | web | https://vexide.dev/blog/posts/serial-deep-dive/ | 2026-06-16 | V5 Serial Protocol: system port (upload/control) vs user port (stdio debug); Controller connection has one port; Bluetooth via V5 Radio |
| S11 | web | https://kb.vex.com/hc/en-us/articles/360049619171-Coding-the-VEX-AI-Robot | 2026-06-16 | VEX AI demo: Jetson Nano → V5 Brain via USB serial; data displayed on Brain screen; VEXlink robot-to-robot comms |
| S12 | web | https://snikolaj.com/2023/02/25/vex-robotics-v5-brain-analysis/ | 2026-06-16 | V5 Brain SoC: Xilinx ZYNQ XC7Z010 (dual Cortex-A9 + FPGA); RAM externally mounted; high quiescent current |
| S13 | web | https://github.com/vexide/vex-v5-qemu | 2026-06-16 | CPU1 runs user code; VEXcode uses undocumented SDK for cooperative scheduler; C++ stdlib pre-loaded in Brain memory; QEMU emulation runs vexide + PROS |
| S14 | web | https://www.vexforum.com/t/how-do-i-download-modules-to-the-brain/123402 | 2026-06-16 | VEXcode Python VM is MicroPython; v2.0.7 uses MicroPython 1.13 (up from 1.12); improved file IO |
| S15 | web | https://vexide.dev/blog/posts/serial-deep-dive/ | 2026-06-16 | Serial connection types: direct USB (two ports), controller/VEXnet, Bluetooth |
| S16 | web | https://kb.vex.com/hc/en-us/articles/360037858231-VEXcode-Pro-V5-Overview | 2026-06-16 | VEXcode Pro V5 is EOL; replaced by VS Code Extension; 8 Brain slots in Pro also |
| S17 | web | https://www.vexrobotics.com/vexcode/vscode-extension | 2026-06-16 | VS Code Extension replaces Pro V5; supports V5/IQ2/EXP/CTE/AIM/AIR; Python + C++; recommended for pro-track students |
| S18 | web | https://www.vexforum.com/t/pros-vs-vexcode/58740 | 2026-06-16 | PROS vs VEXcode comparison: PROS better documented (at time of post); VEXcode fixed multi-file, keyboard shortcuts, format issues from VCS era |
| S19 | web | https://www.vexforum.com/t/external-libraries-in-vexcode-v5-with-python/126115 | 2026-06-16 | External library limitation: math module (cos/sin/atan2) availability questioned; competition legality of importing standard Python math questioned |

---

## Excerpts

### S1 — VEXcode V5 App Store Listing
https://apps.apple.com/us/app/vexcode-v5/id1516887593
> "Added Switch block functionality to the VEXcode V5 interface — The AI Vision sensor can now be used to detect AprilTags as well as game objects from the 2025 High Stakes game or other classroom objects — New stop project command provides enhanced control over program execution"
> "From elementary school through college, VEXcode is a coding environment that meets students at their level."

### S4 — motors.vex.com install page (mirror of vexrobotics.com/vexcode/install/v5)
https://motors.vex.com/vexcode/install/v5
> "Available on Chrome-based browser on Chromebook, Mac, and Window devices. No installation needed. Always up-to-date. Available as a desktop app for Windows and Mac devices. Available as a mobile app for iPad, Android, and Amazon Fire tablets. ... Google has decided to discontinue all Chrome Apps effective July 2025."

### S10 — vexide Serial Deep Dive
https://vexide.dev/blog/posts/serial-deep-dive/
> "Direct wired connection: A USB connection directly from your computer and into the Brain. This is by far the fastest connection type. This type of connection has 2 separate serial ports. These serial ports are named system and user. The system port is used for communicating with the Brain over the serial protocol, and the user port is used for viewing user program stdio output (this is often called the debug terminal)."

### S11 — Coding the VEX AI Robot
https://kb.vex.com/hc/en-us/articles/360049619171-Coding-the-VEX-AI-Robot
> "This demo project collects data from the Jetson processor via USB serial connection. Once the data is received it is displayed on the V5 Brain's screen and also transmitted to a partner V5 robot that is connected via VEXlink."

### S12 — V5 Brain Hardware Analysis
https://snikolaj.com/2023/02/25/vex-robotics-v5-brain-analysis/
> "The dual Cortex A9 + FPGA combination immediately made me think that they're using a (AMD) Xilinx Zynq SoC, and indeed they are – specifically, an XC7Z010."
> "Our battery during the competition drained extremely fast even when the robot was doing nothing, and the Zynq's datasheet states the quite large quiescent current consumption."

### S13 — vexide/vex-v5-qemu GitHub
https://github.com/vexide/vex-v5-qemu
> "VEXcode heavily relies on undocumented parts of the proprietary SDK for its cooperative task scheduler. Also, a portion of each VEXcode program is effectively missing since the C++ standard library it uses comes pre-loaded into the Brain's memory."
> "The V5 brain runs off two Cortex-A9 cores in it's main SOC (the Xilinx ZYNQ zc7020). We are emulating the core responsible for running user code on the brain (also known as CPU1)."

### S14 — VEX Forum: Python module downloads
https://www.vexforum.com/t/how-do-i-download-modules-to-the-brain/123402
> "The latest VEXcode release (2.0.7) did include an updated Python VM with a few new features. 1 - This release is based on micropython V1.13 we previously used 1.12, so several months worth of bug fixes to the core of the Python VM. 2 - improved file support you can now use standard Python file IO."

### S19 — VEX Forum: External libraries in VEXcode V5 Python
https://www.vexforum.com/t/external-libraries-in-vexcode-v5-with-python/126115
> "I am trying to use math such as cos, sin, or atan2. But unfortunately, these functions are only available in the math python library. Will importing math into my VEXcode program work, and if so, is it legal?"
