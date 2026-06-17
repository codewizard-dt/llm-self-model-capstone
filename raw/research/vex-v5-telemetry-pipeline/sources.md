---
topic: how telemetry would be output, saved, and transferred from the VEX V5 to an external system for heavier modeling/LLM tasks
slug: vex-v5-telemetry-pipeline
researched: 2026-06-16
---

# Primary Sources — VEX V5 Telemetry Pipeline

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://www.vexforum.com/t/v5-brain-to-raspberry-pi-communication/124407 | 2026-06-16 | Confirmed microUSB on V5 → USB-A on Pi; `/dev/ttyACM0` is the user port; udev rule `ATTRS{idVendor}=="2888"` for stable naming |
| S2 | codebase | `raw/research/vexcode-v5/index.md` — "Communication" section | 2026-06-16 | V5 Brain exposes user port and system port over USB; user programs use `print()` / `sys.stdout` to write to user port; confirmed as the VEX AI Jetson Nano pattern |
| S3 | web | https://www.pyserial.com/docs/configuration | 2026-06-16 | `bytes_per_second(115200)` = 11,520 bytes/sec for 8N1 serial — confirmed throughput for contract payloads |
| S4 | codebase | `raw/research/vex-v5-advanced-toolchains/index.md` — "PROS Serial" section | 2026-06-16 | `pros::Serial` opens V5 Smart Ports as RS-485 at up to 921,600 baud; second coprocessor channel independent of USB |
| S5 | web | https://kb.vex.com/hc/en-us/articles/20676091646100-Data-Logging-with-a-VEX-Brain-and-Sensors-Using-Python | 2026-06-16 | Official VEX KB: `brain.sdcard.is_inserted()` API; buffered CSV append pattern; SD card data logging tutorial |
| S6 | web | https://api.vex.com/v5/home/python/SDcard.html | 2026-06-16 | "V5 Brain requires an SD card no larger than 32GB, formatted as FAT32. SD cards larger than 32GB use exFAT formatting by default, which is not compatible." |
| S7 | web | https://www.reddit.com/r/embedded/comments/1mum416/how_do_you_usually_handle_telemetry_collection/ | 2026-06-16 | Community consensus on embedded telemetry storage: JSONL / CSV for small projects; SQLite / InfluxDB for queried data; MQTT for streaming |
| S8 | web | https://link.springer.com/chapter/10.1007/978-3-030-50426-7_28 | 2026-06-16 | Comparative study: PostgreSQL fastest inserts on Pi; SQLite viable; paper confirms Raspberry Pi as a capable edge aggregation node |
| S9 | web | https://www.scitepress.org/Papers/2024/125581/125581.pdf | 2026-06-16 | EmbedDB 2024: EmbedDB outperforms SQLite for inserts on Pi 5; SQLite can lose factor-of-2 performance with an index — confirms JSONL append as simpler and faster for write-heavy telemetry |
| S10 | web | https://platform.claude.com/docs/en/build-with-claude/structured-outputs | 2026-06-16 | Anthropic Structured Outputs (beta): `output_config={"format":{"type":"json_schema","schema":...}}` guarantees schema-valid JSON from Claude Sonnet 4.5 and Opus 4.8; no parsing gymnastics |
| S11 | web | https://www.anthropic.com/news/message-batches-api | 2026-06-16 | Anthropic Message Batches API: GA; 50% cost discount vs synchronous; up to 100,000 requests/batch; results as JSONL; SLA best-effort <1 hour, guaranteed 24 hours |
| S12 | web | https://www.codewords.ai/blog/anthropic-batch-api | 2026-06-16 | Batch API detail: each request is a JSON object with `custom_id` + `params`; output JSONL streamed from `GET /v1/messages/batches/{id}/results`; confirmed 50% pricing |
| S13 | codebase | `raw/research/vision-vex-architecture/index.md` — "Pi-V5 Serial Communication" section | 2026-06-16 | Code snippet: `serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)` → `readline()` → `json.loads()` on Pi; `sys.stdout.write()` better than `brain.screen.print()` for clean serial output |

---

## Excerpts

### S1 — VEX Forum: V5 Brain to Raspberry Pi Communication
https://www.vexforum.com/t/v5-brain-to-raspberry-pi-communication/124407
> "Connect the VEX V5 Brain to one of the USB ports on the Raspberry Pi using a USB cable from the microUSB port on the V5 Brain to the USB port on the Raspberry Pi."
> "Modify udev Rules (if necessary): Sometimes, to ensure consistent device naming and permissions, you might need to add udev rules. Create a file in /etc/udev/rules.d/ (e.g., 99-vex.rules) and add a rule like: SUBSYSTEM=="tty", ATTRS{idVendor}=="2888", MODE="0666", SYMLINK+="vex_brain""

### S3 — PySerial Docs: Configuration
https://www.pyserial.com/docs/configuration
> "def bytes_per_second(baudrate, data_bits=8, parity=False, stop_bits=1): bits_per_byte = 1 + data_bits + (1 if parity else 0) + stop_bits return baudrate / bits_per_byte # 115200 baud, 8N1 = 11520 bytes/sec print(bytes_per_second(115200))"

### S5 — VEX KB: Data Logging with a VEX Brain and Sensors Using Python
https://kb.vex.com/hc/en-us/articles/20676091646100-Data-Logging-with-a-VEX-Brain-and-Sensors-Using-Python
> "Note: the brain.sdcard.is_inserted() function returns True if an SD card is inserted into the Brain."
> "we need to write the data to a Comma-Separated Values (CSV) file on the SD card for future examination and analysis"

### S6 — VEX V5 Python API: SD Card
https://api.vex.com/v5/home/python/SDcard.html
> "The V5 Brain requires an SD card no larger than 32GB, formatted as FAT32. SD cards larger than 32GB use exFAT formatting by default, which is not compatible with the V5 Brain."

### S7 — r/embedded: Telemetry collection from embedded devices
https://www.reddit.com/r/embedded/comments/1mum416/how_do_you_usually_handle_telemetry_collection/
> "Storage & Processing • For smaller projects, something like SQLite, InfluxDB, or TimescaleDB works fine and is cheap/free. • For logs, ELK/OpenSearch or Loki can be handy."

### S10 — Anthropic Docs: Structured Outputs
https://platform.claude.com/docs/en/build-with-claude/structured-outputs
> "Migrating from beta? The output_format parameter has moved to output_config.format, and beta headers are no longer required."
> (API example showing `output_config={"format":{"type":"json_schema","schema":{...}}}` returning validated JSON)

### S11 — Anthropic: Introducing the Message Batches API
https://www.anthropic.com/news/message-batches-api
> "Claude now offers a Message Batches API that processes up to large volumes of queries asynchronously at lower cost."
> "Update: The Message Batches API is Generally Available on the Anthropic API."

### S12 — Codewords: Anthropic Batch API
https://www.codewords.ai/blog/anthropic-batch-api
> "The Anthropic batch API accepts a JSONL file of message requests and processes them asynchronously. Each request in the batch is independent — it gets its own system prompt, messages array, and model parameters."
> "Claude Sonnet 4 charges $3 per million input tokens and $15 per million output tokens for synchronous requests. Batch processing cuts those to $1.50 and $7.50 respectively."
