---
topic: list of references of VEX V5 projects/github repos where they have opensourced their setup of autonomous robot that is controlled with rpi 5 with or without the camera module. also look for examples where they used telemetry as feedback. also look for examples where they used llms to model its behavior
slug: vex-v5-rpi-coprocessor-opensource
researched: 2026-06-17
---

# Primary Sources — VEX V5 + RPi Coprocessor Open-Source References

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://github.com/VEX-Robotics/VAIC_23_24 | 2026-06-17 | Official VAIC 23/24: Jetson Nano + V5 Brain via USB serial; V5SerialComms.py; AI_RECORD struct; GPS sensor fusion; Intel RealSense camera; web dashboard |
| S2 | web | https://github.com/VEX-Robotics/VAIC_24_25 | 2026-06-17 | Official VAIC 24/25: same architecture as 23/24, updated Jetson images |
| S3 | web | https://github.com/VEXU-GHOST/VEXU_GHOST | 2026-06-17 | UT Austin championship team: VEX V5 + Jetson running ROS2 Humble (Ubuntu 22.04); full production autonomy framework |
| S4 | web | https://github.com/UTAH-VEXU-Robotics/ros_lib | 2026-06-17 | rosserial bridge for V5 Brain on PROS 3.x; tested at 100 Hz over USB; compatible with any ROS Linux host (RPi-capable) |
| S5 | web | https://github.com/UTAH-VEXU-Robotics/rosserial | 2026-06-17 | Forked rosserial with rosserial_vex_v5 package; includes sensor and odometry example headers |
| S6 | web | https://github.com/RoBorregos/VEXU-Wiki | 2026-06-17 | ITESM VEXU 2022: ROS Melodic on Jetson Nano ↔ V5 Brain via rosserial at /dev/ttyACM1 115200; TF2, OpenCV-GPU, Nav Stack |
| S7 | web | https://github.com/Maotechh/VEX_communication | 2026-06-17 | RS-485 Smart Port communication tutorial; RS485-to-TTL wiring diagram; vexGenericSerial* API from PROS |
| S8 | web | https://github.com/Jordon-Notts/VEX-V5-Brain-External-Comm | 2026-06-17 | VEXU Over Under: Arduino/RPi → V5 Brain; tested PWM and string-based serial; string approach recommended |
| S9 | web | https://github.com/joshuaferrara/VEX-Robotics-Internet-Control-Server | 2026-06-17 | VEX Cortex + RPi web server; telemetry display (battery voltage, WiFi signal) via serial bridge |
| S10 | web | https://github.com/EvolvedAwesome/VEXSerial | 2026-06-17 | VEX Cortex + RPi UART packet library; pyserial on RPi GPIO; RobotC on Cortex |
| S11 | web | https://gftabor.github.io/project/autonomous-vex-robotics/ | 2026-06-17 | Griffin Tabor WPI: VEX hardware + RPi + planar lidar + ROS + PCL; $150 autonomy budget; WPI Provost Award; Google Cartographer SLAM |
| S12 | web | https://academicworks.cuny.edu/ny_pubs/1061/ | 2026-06-17 | CUNY paper: RPi replaces Cortex as sole controller of VEX EDR hardware; vision-based control; Linux enables advanced algorithms |
| S13 | web | https://github.com/vexide/vex-v5-serial | 2026-06-17 | Rust implementation of V5 serial protocol (USB + Bluetooth); documents full packet format for host-side V5 communication |
| S14 | web | https://github.com/SMARTlab-Purdue/SMART-LLM | 2026-06-17 | Purdue: multi-agent LLM task planning for robots (ICRA 2024); closest adjacent academic work to LLM robot control |
| S15 | web | https://plc.pd.vex.com/t/workshop-recap-robotics-applications-using-ai-large-language-models-with-vex-aim/2043 | 2026-06-17 | VEX AIM + LLM workshop (2025); only VEX-specific LLM event found; targets VEX AIM (not V5), educational not autonomous |
| S16 | web | https://www.raspberrypi.com/news/event-based-vision-comes-to-raspberry-pi-5-with-the-prophesee-genx320-starter-kit/ | 2026-06-17 | RPi5 AI/vision ecosystem; Hailo AI Kit available for RPi5; confirms RPi5 viable for edge vision tasks |
| S17 | web | https://advanced.onlinelibrary.wiley.com/doi/10.1002/adrr.202500072 | 2026-06-17 | BrainBody-LLM: closed-loop LLM with runtime state feedback for robot task planning; GPT-4 used; run-time error feedback improves correction |

---

## Excerpts

### S1 — VEX-Robotics/VAIC_23_24 (JetsonExample README)
https://github.com/VEX-Robotics/VAIC_23_24/blob/main/JetsonExample/README.md
> "the v5 object is a V5SerialComms class from V5Comm.py that handles serial communication to the V5 Brain. The v5Map object uses the MapPosition class to process the inferred objects from the 2D camera image into a projection onto 3D space to return the location of each object on the field."

### S3 — VEXU-GHOST/VEXU_GHOST (README)
https://github.com/VEXU-GHOST/VEXU_GHOST
> "Advanced robot software framework for a Vex V5 + Nvidia Jetson stack. This repository contains code intended to support VEXU and VEXAI teams interested in leveraging advanced programming techniques on their competition robots. Ubuntu 22.04."

### S4 — UTAH-VEXU-Robotics/ros_lib (README)
https://github.com/UTAH-VEXU-Robotics/ros_lib
> "This package contains everything needed to run rosserial on the VEX V5 Robot Brain, on the PROS 3.x.x tooling. Over microUSB, any message can stream at 100hz. Higher speeds (e.g. 500hz) are unstable right now."

### S6 — RoBorregos/VEXU-Wiki
https://github.com/RoBorregos/VEXU-Wiki
> "Dependencies installation (PROS, ROS-Melodic, Tensorflow 2, OpenCV - GPU, Ros-Navigation Stack, Rosserial) ROSMelodic-PROS connection (JetsonNano-VBrain) by using rosserial. Connection: rosrun rosserial_python serial_node.py _port:=/dev/ttyACM1 _baud:=115200"

### S7 — Maotechh/VEX_communication
https://github.com/Maotechh/VEX_communication
> "First of all, we need to buy an RS485 to TTL module in order to change the A and B lines of RS485 represented by the black and red lines of VEX to UART level. Black: RS485-A  Red: RS485-B  Green: GND  Yellow: Power(12V)"

### S8 — Jordon-Notts/VEX-V5-Brain-External-Comm
https://github.com/Jordon-Notts/VEX-V5-Brain-External-Comm
> "For example an Arduino Uno or a raspberry pi collecting information from a sensor, then sending the information to the V5 brain. ... The pulses of the system regularly had an error of about 5ms. ... by sending string data i can send 'x90,y100' or however i like."

### S9 — joshuaferrara/VEX-Robotics-Internet-Control-Server
https://github.com/joshuaferrara/VEX-Robotics-Internet-Control-Server
> "This is one part of a three part system used to control VEX robots over the internet. This part takes user input from a website and relays it to the robot via a serial connection from a Raspberry Pi to the VEX cortex. The website also displays various telemetry data from the robot (battery voltage, wifi signal, etc...)."

### S11 — Griffin Tabor Autonomous VEX Project
https://gftabor.github.io/project/autonomous-vex-robotics/
> "The autonomy elements were built on a 150$ budget using a simple planar lidar, raspberry pi and a set of encoders. The software stack was built using ROS and PCL. ... This project won the WPI Provost award in the Computer Science Department."

### S12 — CUNY Paper: RPi-Controlled VEX Robot
https://academicworks.cuny.edu/ny_pubs/1061/
> "This paper describes the development of a Raspberry PI-controlled VEX robot for an undergraduate robotic course. The Raspberry PI controls the mobile base built using the VEX robotics kit without using the Cortex micro-controller that comes with the kit. The aim is to create a physical robot that is manageable, easily replicable, and capable of performing advanced robotic control tasks such as vision-based control."

### S17 — BrainBody-LLM (Wiley)
https://advanced.onlinelibrary.wiley.com/doi/10.1002/adrr.202500072
> "GPT-4 improved on both these models by effectively utilizing run-time feedback errors for accurate task planning. The BrainBody-LLM framework is designed to enable direct autonomous planning across a broad spectrum of robotic tasks, both in simulation and real-world environments."
