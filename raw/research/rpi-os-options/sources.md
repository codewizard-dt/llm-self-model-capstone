---
topic: "Changing the OS setup on the RPi: Bookworm vs Ubuntu 24.04/ROS 2 Jazzy vs Trixie/Hailo"
slug: rpi-os-options
researched: 2026-06-23
---

# Primary Sources — RPi OS Options

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://github.com/raspberrypi/picamera2 | 2026-06-23 | picamera2 is officially "only supported on Raspberry Pi OS Bullseye (or later)" — explicitly not Ubuntu |
| S2 | web | https://github.com/raspberrypi/picamera2/issues/1337 | 2026-06-23 | Community issue confirming picamera2 on Ubuntu 24.04 Pi 5 requires workaround |
| S3 | web | https://www.reddit.com/r/Ubuntu/comments/1ddpnto/ | 2026-06-23 | Reddit: "build libcamera and camera_ros in your ROS2 workspace" is the workaround for PiCam3 on Ubuntu+ROS2 |
| S4 | web | https://robocre8.gitbook.io/robocre8/tutorials/how-to-install-ros2-jazzy-base-on-raspberry-pi-4-or-5-full-install | 2026-06-23 | Step-by-step ROS 2 Jazzy install on Ubuntu 24.04 Pi 4/5 — confirmed it works with correct apt repo config |
| S5 | web | https://index.ros.org/p/rosserial_vex_v5/ | 2026-06-23 | rosserial_vex_v5 has "No version for distro jazzy" — VEX V5 serial bridge must be custom on Jazzy |
| S6 | codebase | `wiki/knowledge/concepts/camera-module-3-setup.md` | 2026-06-23 | Current Pi 5 setup: Bookworm, picamera2, YOLO11n ~8–10 FPS, AprilTag |
| S7 | codebase | `wiki/knowledge/entities/tools/vaic-reference-architecture.md` | 2026-06-23 | VAIC reference: Bookworm-based, pyserial at /dev/ttyACM0, 115200 baud — directly portable to capstone |
| S8 | web | https://www.reddit.com/r/ROS/comments/1q8pqw1/ | 2026-06-23 | ROS Jazzy packages require `noble-updates` apt repo, not just base noble — common install failure point |
| S9 | web | https://discourse.openrobotics.org/t/real-time-raspberry-pi-ros-2-image-updated-for-jazzy-and-24-04/45047 | 2026-06-23 | Real-time Jazzy + Ubuntu 24.04 image exists for Pi 3/4/5 (ros-realtime project) |
| S10 | web | https://zbotic.in/raspberry-pi-ros2-ubuntu-vs-raspbian/ | 2026-06-23 | "Robot with camera pipeline (Pi Camera Module 3): Use Raspberry Pi OS Bookworm + Docker ROS2" — Zbotic recommendation against Ubuntu+PiCam3 |
| S11 | web | https://blog.roboflow.com/raspberry-pi-luxonis-oak-computer-vision/ | 2026-06-23 | OAK-D + RPi integration via DepthAI SDK; USB connection; `pip install depthai` |
| S12 | web | https://medium.com/@zlodeibaal/luxonis-oak-d-4d-a-closer-look-at-the-next-gen-smart-3d-camera-c22c87f6a5f2 | 2026-06-23 | OAK-D combined inference latency 80–100 ms; NPU offloads host; LLM/VLM still gaps vs Jetson |
| S13 | web | https://discuss.luxonis.com/blog/6392-depthai-ros-release-30 | 2026-06-23 | depthai-ros Jazzy: need to build depthai-core from source (kilted branch), not apt binary yet |
| S14 | web | https://www.hackster.io/news/raspberry-pi-os-trixie-gets-hailo-based-ai-kit-ai-hat-support-and-a-new-ai-camera-feature-5e8523191150 | 2026-06-23 | Hailo AI HAT+ support re-added to Trixie after being missing at launch (July 2025); install: `sudo apt install dkms hailo-all` |
| S15 | web | https://www.raspberrypi.com/news/software-updates-for-raspberry-pi-ai-products/ | 2026-06-23 | Official RPi news: "AI HAT+ and AI Kit both based on Hailo accelerators are now fully supported on the Trixie version of Raspberry Pi OS" |
| S16 | web | https://www.raspberrypi.com/news/introducing-the-raspberry-pi-ai-hat-plus-2-generative-ai-on-raspberry-pi-5/ | 2026-06-23 | AI HAT+ 13 TOPS = $70, 26 TOPS = $110; AI HAT+ 2 (Hailo-10H, 40 TOPS, 8 GB RAM) = $130 |
| S17 | web | https://jrattechworks.com/raspberry-pi-ai-hat-2/ | 2026-06-23 | Trixie Python 3.13: Open WebUI not compatible; RPi recommends Docker for LLM interfaces |
| S18 | web | https://forums.raspberrypi.com/viewtopic.php?t=392639 | 2026-06-23 | Early Trixie camera bug (cameras not working); fixed in later updates ~Oct 2025 |
| S19 | web | https://pidiylab.com/raspberry-pi-os-vs-ubuntu-server/ | 2026-06-23 | 64-bit Bookworm is "recommended default for Pi 4 and Pi 5 since Oct 2023, fully stable" |
| S20 | web | https://www.raspberrypi.com/news/trixie-the-new-version-of-raspberry-pi-os/ | 2026-06-23 | Official Trixie announcement; user comment: "Hailo AI HAT only work with Bookworm not with Trixie [at launch]" — later resolved |

---

## Excerpts

### S1 — picamera2 GitHub README
https://github.com/raspberrypi/picamera2
> "Picamera2 is only supported on Raspberry Pi OS Bullseye (or later) images, both 32 and 64-bit."

### S3 — Reddit r/Ubuntu: Pi Camera 3 on Ubuntu 24.04 with ROS 2
https://www.reddit.com/r/Ubuntu/comments/1ddpnto/raspberry_pi_5_running_2404_with_a_pi_camera_3/
> "If you intend to use camera_ros to get camera stream support on ROS2, the ideal solution is to build libcamera and camera_ros in your ROS2 workspace."

### S5 — ROS index: rosserial_vex_v5
https://index.ros.org/p/rosserial_vex_v5/
> "No version for distro jazzy showing lunar. Known supported distros are highlighted in the buttons above."

### S8 — Reddit r/ROS: ROS 2 Jazzy install failure on Ubuntu Server
https://www.reddit.com/r/ROS/comments/1q8pqw1/
> "Jazzy packages were built against updated library versions that are only available in the noble-updates repository, not the base noble release."

### S10 — Zbotic: Ubuntu vs Raspberry Pi OS for ROS2
https://zbotic.in/raspberry-pi-ros2-ubuntu-vs-raspbian/
> "Robot with camera pipeline (Pi Camera Module 3): Use Raspberry Pi OS Bookworm + Docker ROS2."

### S12 — Medium: OAK-D 4D latency
https://medium.com/@zlodeibaal/luxonis-oak-d-4d-a-closer-look-at-the-next-gen-smart-3d-camera-c22c87f6a5f2
> "For most robotics applications, the combined inference latency (including depth estimation) of 80–100 ms is acceptable, though not ideal for high-speed control loops."

### S13 — Luxonis forum: depthai-ros 3.0 on Jazzy
https://discuss.luxonis.com/blog/6392-depthai-ros-release-30
> "Building depthai-core from source (from the kilted branch) instead of using install_dependencies.sh worked for me. Then the depthai-ros kilted branch builds and runs correctly for Jazzy."

### S14 — Hackster.io: Trixie Hailo support
https://www.hackster.io/news/raspberry-pi-os-trixie-gets-hailo-based-ai-kit-ai-hat-support-and-a-new-ai-camera-feature-5e8523191150
> "Raspberry Pi OS users with a Raspberry Pi AI Kit or Raspberry Pi AI HAT+ can install the new software with the command sudo apt update && sudo apt install dkms && sudo apt install hailo-all"

### S16 — Raspberry Pi AI HAT+ 2 announcement
https://www.raspberrypi.com/news/introducing-the-raspberry-pi-ai-hat-plus-2-generative-ai-on-raspberry-pi-5/
> "Unlock large language models (LLMs) and vision-language models (VLMs) on Raspberry Pi 5 with the Raspberry Pi AI HAT+ 2: on sale now at $130."

### S17 — jrattechworks: AI HAT+ 2 Trixie Python 3.13 issue
https://jrattechworks.com/raspberry-pi-ai-hat-2/
> "Raspberry Pi recommends running it in Docker, because Open WebUI is not currently compatible with the system Python (Python 3.13) shipped with Raspberry Pi OS 'Trixie'."
