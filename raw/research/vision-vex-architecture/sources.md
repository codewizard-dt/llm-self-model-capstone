---
topic: How to include vision into a VEX V5 architecture (Raspberry Pi + webcam)
slug: vision-vex-architecture
researched: 2026-06-16
---

# Primary Sources — Vision into VEX V5 Architecture

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://chatgpt.com/share/6a31d448-7b80-83e8-ad7e-44000efe8e07 | 2026-06-16 | Two-computer architecture (Pi + V5), physical mounting options (standoffs + 3D print), webcam choices, JSON serial protocol, CV stack (Python+OpenCV+YOLO), AprilTag recommendation |
| S2 | web | https://www.vexforum.com/t/v5-brain-to-raspberry-pi-communication/124407 | 2026-06-16 | Confirmed microUSB → USB-A connection; Pi sees /dev/ttyACM0 and /dev/ttyACM1; udev rules for consistent naming |
| S3 | web | https://www.reddit.com/r/vex/comments/qf1tdi/how_to_get_raspberry_pi_communicating_with_vex_v5/ | 2026-06-16 | Confirmed USB serial and RS-485 Smart Port as two valid channels; noted competition rule R16a prohibiting Pi on competition robots |
| S4 | web | https://www.vexforum.com/t/serial-comunication-vex5/123519 | 2026-06-16 | VEXcode V5 Python serial output pattern; brain.screen.print() goes to USB user serial port |
| S5 | web | https://learnopencv.com/yolo11-on-raspberry-pi/ | 2026-06-16 | YOLO11n on Pi 5: 8-10 FPS at standard resolution; 25+ FPS at 240×240 with NCNN + INT8 quantization |
| S6 | web | https://www.ejtech.io/learn/yolo-on-raspberry-pi | 2026-06-16 | Pi 5 CPU: ~8 FPS with YOLO11n NCNN off-the-shelf; step-by-step install and inference code |
| S7 | web | https://docs.ultralytics.com/guides/raspberry-pi | 2026-06-16 | YOLO26n (hardware-aware) achieves 7.79 FPS at 640×640 ONNX on Pi 5; ~15% faster than YOLO11n |
| S8 | web | https://forums.raspberrypi.com/viewtopic.php?t=373669 | 2026-06-16 | Hailo AI Kit benchmark: Pi 5 CPU 2 FPS vs Hailo PCIe gen2 41 FPS (YOLOv8s 640×640) |
| S9 | web | https://pypi.org/project/apriltag/ | 2026-06-16 | pip install apriltag; single-call API: detector.detect(gray_frame) returns id + 3D pose; tag36h11 family |
| S10 | web | https://pyimagesearch.com/2020/11/02/apriltag-with-python/ | 2026-06-16 | AprilTags = fiducial markers; pip-installable Python library; works with OpenCV loaded images; real-time on Pi |
| S11 | web | https://github.com/masoug/apriltag-localization | 2026-06-16 | Open-source soft-real-time AprilTag localization for Raspberry Pi; used in FRC 2023 robotics competition |
| S12 | codebase | `capstone-experiment.flowchart.md` | 2026-06-16 | Current architecture: no perception layer; Task Execution only logs motor telemetry |
| S13 | codebase | `raw/research/vex-v5-advanced-toolchains/index.md` | 2026-06-16 | USB serial user port is the LLM integration path; PROS Smart Port RS-485 is Stage 2 option |
| S14 | codebase | `wiki/index.md::task-telemetry-contract` | 2026-06-16 | Task Telemetry Contract currently motor-only (torque, current, velocity, position) for grab/pull/throw |
| S15 | web | https://www.raspberrypi.com/products/camera-module-3/ | 2026-06-16 | Official specs: 12MP Sony IMX708, PDAF autofocus, 75°/120° FOV, 1080p50 video, $25, 25×24mm PCB, 200mm ribbon cable, in production until Jan 2030; Picamera2 Python library |

---

## Excerpts

### S1 — ChatGPT: VEX V5 Raspberry Pi Mounting (shared conversation)
https://chatgpt.com/share/6a31d448-7b80-83e8-ad7e-44000efe8e07

> "Yes. In fact, for your capstone idea, I would strongly recommend treating the VEX V5 brain as a motor/sensor controller and putting all AI/computer vision on a Raspberry Pi."

> Architecture:
> ```
> USB Webcam → Raspberry Pi 5 (OpenCV, YOLO, LLM, telemetry) → USB/Serial → VEX V5 Brain (Motors, Encoders, Sensors) → Robot Chassis
> ```

> "Pi sends commands. V5 executes motor actions."
> Protocol: `{"forward": 0.4, "turn": -0.1}`

> "For your project I'd start with: Python, OpenCV, Ultralytics YOLO"

> "Instead of asking an LLM 'Where am I?' Place AprilTags around the room. For an autonomous robot project this is one of the highest leverage things you can do."

### S2 — VEX Forum: V5 Brain to Raspberry Pi Communication
https://www.vexforum.com/t/v5-brain-to-raspberry-pi-communication/124407

> "Connect the VEX V5 Brain to one of the USB ports on the Raspberry Pi using a USB cable from the microUSB port on the V5 Brain to the USB port on the Raspberry Pi."

> "Modify udev Rules (if necessary): Sometimes, to ensure consistent device naming and permissions, you might need to add udev rules. Create a file in /etc/udev/rules.d/ (e.g., 99-vex.rules)"

### S5 — LearnOpenCV: YOLO11 on Raspberry Pi
https://learnopencv.com/yolo11-on-raspberry-pi/

> "Speed & Efficiency: When optimized for Raspberry Pi using techniques like NCNN model conversion and hardware-aware quantization, YOLO11 can achieve millisecond-level latency and handle up to 25+ FPS on 240×240 resolution frames."

> "in your experiments across all the formats, we got an average FPS of about 8 – 10"

### S6 — EJ Technology: YOLO on Raspberry Pi
https://www.ejtech.io/learn/yolo-on-raspberry-pi

> "On our Raspberry Pi 5, we achieved about 8 FPS running the off-the-shelf YOLO11n NCNN model."

### S7 — Ultralytics Docs: Raspberry Pi Quick Start
https://docs.ultralytics.com/guides/raspberry-pi

> "YOLO26 is specifically designed to run on hardware-constrained devices such as the Raspberry Pi 5. Compared to YOLO11n, YOLO26n achieves a ~15% increase in FPS (6.79 → 7.79) while also delivering higher mAP (40.1 vs 39.5) at 640 input size with ONNX-exported models on the Raspberry Pi 5."

### S8 — Raspberry Pi Forums: AI Kit Necessity for YOLO
https://forums.raspberrypi.com/viewtopic.php?t=373669

> "We've tested YoloV8s object detection demo. 120fps video input. 640×640. Pi5 8GB without Hailo 2fps; Pi5 8GB with hailo PCIe gen2 41fps; Pi5 8GB with hailo PCIe gen3 82fps."

### S10 — PyImageSearch: AprilTags with Python
https://pyimagesearch.com/2020/11/02/apriltag-with-python/

> "The library we'll be using is apriltag, which, lucky for us, is pip-installable."
> "Libraries exist to detect AprilTags and ArUco tags in nearly any programming language used to perform computer vision, including Python, Java, C++, etc."

### S11 — GitHub: AprilTag Localization (masoug)
https://github.com/masoug/apriltag-localization

> "The 2023 FIRST FRC season introduced AprilTag fiducial markers on the field for robots to localize themselves on the competition field. This repo is an open-source implementation of a soft-real-time AprilTag localization algorithm for use on an embedded target like a Raspberry Pi."

### S15 — Raspberry Pi Camera Module 3 Product Page
https://www.raspberrypi.com/products/camera-module-3/

> "Resolution: 11.9 megapixels"
> "Pixel size: 1.4μm × 1.4μm"
> "Horizontal/vertical: 4608 × 2592 pixels"
> "Diagonal field of view: 75 degrees (Camera Module 3, Camera Module 3 NoIR), 120 degrees (Camera Module 3 Wide, Camera Module 3 NoIR Wide)"
> "Common video modes: 1080p50, 720p120"
> "Dimensions: 25 × 24 × 11.5mm"
> "Ribbon cable length: 200mm"
> "Available from $25 with your choice of standard and wide lenses, with or without an infrared filter"
> "Raspberry Pi Camera Module 3 will remain in production until at least January 2030"
> "Camera Module 3 features ultra-fast auto focus as standard."
> "The latest version of Raspberry Pi OS comes pre-installed with a beta of Picamera2, a Python library developed here at Raspberry Pi in Cambridge."
