---
topic: "$research Can you research if you can output telemetry while I'm driving it with the controller? That would be pretty baller. Figure out a way to get telemetry while I'm driving. And I'll tell you at certain intervals what state the robot's in."
slug: driver-telemetry-labeling
researched: 2026-06-26
---

# Primary Sources — Driver Telemetry While Using the Controller

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/v5-brain/pros_bridge/src/main.cpp` | 2026-06-26 | Existing Brain bridge has `emit_json`, `emit_telemetry`, motor sample JSON, receive/watchdog/routine/telemetry tasks, and starts those tasks from `opcontrol()`. |
| S2 | codebase | `robot/v5-brain/pros_bridge/README.md` | 2026-06-26 | Documents that telemetry is emitted separately every 500 ms and includes contract-shaped motor samples. |
| S3 | codebase | `robot/pi-runtime/docs/BRAIN_INTERFACE.md` | 2026-06-26 | Documents V5 USB serial interfaces, user port for telemetry, 115200 setting, approximate throughput, COBS/JSON behavior, and JSONL capture pattern. |
| S4 | codebase | `robot/ros2-runtime/src/vexy_ros/bridge_demux.py::BrainStreamDemux.consume_line` | 2026-06-26 | Shows current demux logic classifies JSON lines into ack, telemetry, and status events. |
| S5 | codebase | `robot/ros2-runtime/src/vexy_ros/vex_bridge_node.py::VexBridgeNode._publish_event` | 2026-06-26 | Shows demuxed telemetry is published to `/vex/telemetry`. |
| S6 | codebase | `robot/ros2-runtime/docs/runbook/03-recording.md` | 2026-06-26 | Shows MCAP recording commands already include `/vex/telemetry` with camera/vision/bridge topics. |
| S7 | codebase | `robot/ros2-runtime/src/vexy_ros/evidence_export.py::_normalize_motor_sample` | 2026-06-26 | Shows exporter normalizes telemetry `motor_samples` into contract-shaped field names. |
| S8 | context7 | `/websites/pros_cs_purdue_edu_v5` — "controller API opcontrol" | 2026-06-26 | PROS controller docs show analog/digital controller reads and motor control in `opcontrol()`. |
| S9 | web | https://pros.cs.purdue.edu/v5/tutorials/topical/multitasking.html | 2026-06-26 | PROS multitasking docs explain tasks, delays in loops, scheduler behavior, and synchronization/ownership risks. |
| S10 | web | https://pros.cs.purdue.edu/v5/tutorials/topical/filesystem.html | 2026-06-26 | PROS filesystem/serial docs explain stdout/stdin serial access and disabling COBS for direct serial reads. |
| S11 | web | https://pros.cs.purdue.edu/v5/tutorials/topical/controller.html | 2026-06-26 | PROS controller docs state analog range and show controller-to-motor examples. |
| S12 | brave-search | `PROS V5 stdout printf serial user port disable COBS telemetry controller opcontrol documentation` | 2026-06-26 | Located official PROS serial/filesystem docs and generic serial docs; used to corroborate COBS and serial behavior. |

## Excerpts

### S1 — `robot/v5-brain/pros_bridge/src/main.cpp`

> Lines 16-18: "It keeps command acknowledgements and telemetry as separate JSON records, stops on watchdog/TTL expiry..."

> Lines 89-97: `emit_json` prints, appends a newline, flushes stdout, and guards output with `stdout_mutex`.

> Lines 377-406: `emit_telemetry()` emits `type:"telemetry"` with battery, safety, routine, drive position/velocity, and `motor_samples`.

> Lines 752-755: `telemetry_task` calls `emit_telemetry()` then delays `TELEMETRY_MS`.

> Lines 774-778: `opcontrol()` starts receive, routine, watchdog, and telemetry tasks.

### S2 — `robot/v5-brain/pros_bridge/README.md`

> "A separate telemetry task emits `type:\"telemetry\"` records every 500 ms so the ROS bridge can prove `/vex/telemetry` independently from `/vex/ack`."

> "Telemetry includes `motor_samples` for `left_drive`, `right_drive`, and `arm` using the same field names required by the contract JSONL exporter."

### S3 — `robot/pi-runtime/docs/BRAIN_INTERFACE.md`

> "Read telemetry from the USER port = `…-if02` = `/dev/ttyACM1`. `ttyACM0`/`if00` is the system port and carries no program output."

> "Line settings: 115200 8N1."

> "Throughput ceiling ≈ 11,520 B/s. Keep telemetry lines compact."

> "The Brain program disables COBS ... and emits plain newline-delimited JSON on the user port via `printf` + `fflush`."

### S4 — `robot/ros2-runtime/src/vexy_ros/bridge_demux.py::BrainStreamDemux.consume_line`

> `consume_line` parses JSON, classifies it, returns `DemuxEvent("ack", ...)`, `DemuxEvent("telemetry", ...)`, or `DemuxEvent("status", ...)`.

### S5 — `robot/ros2-runtime/src/vexy_ros/vex_bridge_node.py::VexBridgeNode._publish_event`

> `_publish_event` publishes `event.kind == "telemetry"` as a JSON string through `self._telem_pub`.

### S6 — `robot/ros2-runtime/docs/runbook/03-recording.md`

> "ros2 bag record /camera/image_raw ... /vex/cmd /vex/ack /vex/telemetry /vex/bridge_status"

> "Extract `/vision/scene_map`, `/vex/ack`, `/vex/telemetry`, and `/vex/bridge_status` messages to newline-delimited JSON"

### S7 — `robot/ros2-runtime/src/vexy_ros/evidence_export.py::_normalize_motor_sample`

> `_normalize_motor_sample` returns device, subsystem, `api_binding`, `sample_ms`, `values`, and `source_api` with contract motor fields.

### S8 — Context7 PROS V5 docs

> "Feedback from the V5 Controller comes in two forms - analog and digital."

> "The analog data is a value in the range of [-127,127], and digital data is either 1 or 0"

> Example shows `pros::Controller master (E_CONTROLLER_MASTER);` and `master.get_analog(E_CONTROLLER_ANALOG_LEFT_Y)` inside `opcontrol()`.

### S9 — PROS Multitasking docs

https://pros.cs.purdue.edu/v5/tutorials/topical/multitasking.html

> "Tasks are a great tool to do multiple things at once"

> "If your task performs some repeated action ... include a `delay()`"

> "Without a `delay()` statement, your task could starve the processor"

> "The PROS task scheduler is a preemptive, priority-based, round-robin scheduler."

> "Mutexes stand for mutual exclusion; only one task can hold a mutex at any given time."

### S10 — PROS Filesystem / Serial docs

https://pros.cs.purdue.edu/v5/tutorials/topical/filesystem.html

> "It’s also possible to interact with the serial communications (`stdin`, `stdout`, etc.) through the filesystem drivers."

> "If you want to read the serial comms yourself ... disable COBS."

### S11 — PROS Controller docs

https://pros.cs.purdue.edu/v5/tutorials/topical/controller.html

> "The analog data is a value in the range of [-127,127]"

> "Retrieve analog values from the V5 Controller"

> Example shows `example_motor = master.get_analog(E_CONTROLLER_ANALOG_LEFT_Y);`

### S12 — Brave Search result

Query: `PROS V5 stdout printf serial user port disable COBS telemetry controller opcontrol documentation`

> Result identified official PROS Filesystem page with snippet: "If you want to read the serial comms yourself ... disable COBS."
