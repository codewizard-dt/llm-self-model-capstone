---
topic: "compare the jetson nano and NVIDIA JetPack to rpi 5 and our suggested architecture"
slug: jetson-nano-vs-rpi5
researched: 2026-06-17
---

# Primary Sources — Jetson Nano / JetPack vs Raspberry Pi 5

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://forums.developer.nvidia.com/t/jetson-nano-developer-kit-eol/276729 | 2026-06-17 | Official EOL notice: Jetson Nano Dev Kit discontinued, module available until Jan 2027 |
| S2 | web | https://thinkrobotics.com/blogs/learn/jetson-nano-vs-raspberry-pi-5-for-ai-the-ultimate-performance-and-value-comparison | 2026-06-17 | Benchmark: Jetson Nano 30+ FPS YOLOv5 vs Pi 5 AI Kit 10-15 FPS; power analysis |
| S3 | web | https://zbotic.in/raspberry-pi-vs-jetson-nano-which-ai-compute-board-wins/ | 2026-06-17 | Pi 5 ~3× faster at CPU tasks (A76 vs A57); YOLOv4-tiny: Nano 15-25 FPS vs Pi 5 4-6 FPS CPU |
| S4 | web | https://docs.nvidia.com/jetson/jetpack/install-setup/index.html | 2026-06-17 | JetPack setup: firmware update required for Orin before flashing; SDK Manager path |
| S5 | web | https://www.reddit.com/r/computervision/comments/11xqc7x | 2026-06-17 | JetPack Python 3.6 compatibility trap; custom Qengineering image needed for modern YOLOv8 |
| S6 | codebase | `wiki/knowledge/entities/tools/vaic-reference-architecture.md` | 2026-06-17 | VAIC Python serial code (V5Comm.py) is identical on Jetson and Pi 5: /dev/ttyACM0, 115200 baud |
| S7 | codebase | `wiki/knowledge/entities/tools/raspberry-pi-5.md` | 2026-06-17 | Pi 5 specs: YOLO11n NCNN 8-10 FPS; 3-5W workload; USB-C power bank 12-15 hrs; $110 |
| S8 | web | https://forums.raspberrypi.com/viewtopic.php?t=373867 | 2026-06-17 | Pi 5 + Hailo-8L: YOLOv8s 80-120 FPS batch; optional NPU path |
| S9 | web | https://jetsonhacks.com/2024/12/17/jetson-orin-nano-super-developer-kit/ | 2026-06-17 | Orin Nano Super $249; backorder/high demand in early 2025 |
| S10 | web | https://forums.developer.nvidia.com/t/orin-dev-kit-power-requirements/273637 | 2026-06-17 | Orin Nano Super DC jack 7-20V; cannot power from USB-C 5V power bank |
| S11 | web | https://www.reddit.com/r/JetsonNano/comments/1awiopy/a_hot_jetson_nano/ | 2026-06-17 | Jetson Nano reaches 50°C+ after 20 min on 5V/2A supply; throttling occurs |
| S12 | web | https://edgeaistack.ai/blog/jetson-orin-nano-power-consumption/ | 2026-06-17 | Thermal throttling engages at 80°C; oscillating clock frequency = inconsistent inference latency |
| S13 | web | https://edgeaistack.ai/blog/jetson-orin-nano-power-consumption/ | 2026-06-17 | Orin Nano >15W sustained requires active fan; throttle loop without it in enclosures |
| S14 | web | https://www.researchgate.net/publication/391165194_Benchmarking_Edge_AI_Platforms_Performance_Analysis_of_NVIDIA_Jetson_and_Raspberry_Pi_5_with_Coral_TPU | 2026-06-17 | Peer-reviewed benchmark: Jetson Orin Nano higher peak but Pi 5 + Hailo superior TOPS/W and cost/TOPS |
| S15 | web | https://www.aliexpress.com/s/wiki-ssr/article/jetson-nano-vs-raspberry-pi-5-comparison | 2026-06-17 | JetPack GStreamer/VAAPI compatibility issues; open-source tools assume V4L2, broken in JetPack |

---

## Excerpts

### S1 — Jetson Nano Developer Kit EOL (NVIDIA Developer Forums)
https://forums.developer.nvidia.com/t/jetson-nano-developer-kit-eol/276729
> "The Jetson Nano Developer Kit (with 4GB memory) will be discontinued over the next few months as inventory declines. The Jetson Nano module will remain available through January 2027."

### S3 — Raspberry Pi vs Jetson Nano: Which AI Compute Board Wins? (Zbotic)
https://zbotic.in/raspberry-pi-vs-jetson-nano-which-ai-compute-board-wins/
> "The Cortex-A76 (Pi 5) is a fundamentally newer, more efficient microarchitecture than the Cortex-A57 (Jetson Nano). The gap is significant: The Pi 5 is approximately 3x faster at pure CPU tasks. For workloads that run on CPU — Python scripts, web servers, data processing, non-GPU ML inference — the Pi 5 runs circles around the Jetson Nano."
> "YOLOv4-tiny object detection: Jetson Nano ~15–25 FPS vs Pi 5 ~4–6 FPS (CPU)"
> "The original Jetson Nano Dev Kit (B01) has been discontinued by NVIDIA, and stock is increasingly scarce. Its successor, the Jetson Orin Nano, is a substantially better platform but costs 3–4x more."

### S5 — JetPack Python Compatibility Trap (Reddit r/computervision)
https://www.reddit.com/r/computervision/comments/11xqc7x
> "The one thing that really tripped me up was the NVIDIA provided OS and Python packages for the Nano did not play well with yolov8 because they're old. (It was Python 3.6, which is no longer supported). Once I found an alternative image to flash it was smooth sailing!"

### S10 — Orin Dev Kit Power Requirements (NVIDIA Developer Forums)
https://forums.developer.nvidia.com/t/orin-dev-kit-power-requirements/273637
> "I am using the Jetson Orin Nano Developer Kit on a battery-powered autonomous mobile robot. I see in the documentation that the range of DC voltages that can be put into the DC Jack is 7-20 V."
*(Note: 7-20V DC jack means standard USB-C 5V power banks cannot power the Orin Nano Super.)*

### S11 — Jetson Nano Thermal Under Load (Reddit r/JetsonNano)
https://www.reddit.com/r/JetsonNano/comments/1awiopy/a_hot_jetson_nano/
> "I started noticing a small bulge in powerbank so I left it and started using a 5V 2A charging brick with micro USB, and man does the nano get hot. Reached 50°c after using it for 20 minutes."

### S12 — Jetson Orin Nano Thermal Throttling (EdgeAI Stack)
https://edgeaistack.ai/blog/jetson-orin-nano-power-consumption/
> "Thermal throttling engages when the SoC junction temperature exceeds 80°C. At that point, the firmware reduces GPU and CPU clock frequencies automatically, which lowers power but also reduces throughput. In a poorly cooled enclosure, this creates a feedback loop: the workload slows, heat dissipates slightly, clocks recover, heat rises again—producing unstable latency rather than a clean thermal steady state."

### S14 — Peer-reviewed benchmark (Georgia Southern / ResearchGate, SoutheastCon 2025)
https://www.researchgate.net/publication/391165194_Benchmarking_Edge_AI_Platforms_Performance_Analysis_of_NVIDIA_Jetson_and_Raspberry_Pi_5_with_Coral_TPU
> "Our empirical conclusion that Jetson Orin Nano, especially in its 25 W 'super developer mode,' offers higher peak throughput but at higher cost and power than the more cost and energy-efficient Raspberry Pi 5 + Hailo configuration is consistent with recent benchmarking studies."

### S15 — JetPack GStreamer compatibility pain (AliExpress Wiki)
https://www.aliexpress.com/s/wiki-ssr/article/jetson-nano-vs-raspberry-pi-5-comparison
> "The Jetson relies heavily on nvcodec-accelerated media pipelines. Many open-source tools assume generic VAAPI/V4L2 interfaces present on general-purpose CPUs — an assumption broken inside JetPack environments until patched manually."
