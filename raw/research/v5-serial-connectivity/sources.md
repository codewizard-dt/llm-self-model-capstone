---
topic: VEX V5 Brain stdout serial connectivity issue — why pros terminal drops and how to fix it; RPi impact
slug: v5-serial-connectivity
researched: 2026-06-21
---

# Primary Sources — V5 Serial Connectivity

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/v5-brain/.venv/.../pros/serial/devices/vex/v5_user_device.py::V5UserDevice.read` | 2026-06-21 | Shows terminal uses COBS packet decoding, not raw bytes; asserts msg ≥ 4 bytes |
| S2 | codebase | `robot/v5-brain/.venv/.../pros/serial/devices/vex/v5_device.py::find_v5_ports` | 2026-06-21 | macOS port selection: user port = device ending in '3', system = '1' |
| S3 | web | https://github.com/purduesigbots/pros (ser_driver.c) | 2026-06-21 | PROS kernel: stdout enabled by default in `ser_driver_initialize`; `&=` bug; COBS on by default |
| S4 | web | https://github.com/purduesigbots/pros-cli/issues/383 | 2026-06-21 | `pros terminal` produces no output over controller connection; direct connection works |
| S5 | web | https://github.com/purduesigbots/pros-cli/issues/305 | 2026-06-21 | `pros upload` / terminal fail when connected via controller; direct works |
| S6 | web | https://vexide.dev/blog/posts/serial-deep-dive/ | 2026-06-21 | Controller connection = 1 port; stdout requires UserFifoPacket (not raw COBS) |
| S7 | web | https://pros.cs.purdue.edu/v5/tutorials/topical/filesystem.html | 2026-06-21 | SD card is for file I/O only; serial stdout is USB-only; `serctl` activates/deactivates streams |

## Excerpts

### S4 — pros terminal not working over the controller (GitHub issue #383)
https://github.com/purduesigbots/pros-cli/issues/383
> "Plug in controller then run `pros mut` ... There is no output ... Plugging directly into the brain works and also this issue does not occur using cargo-v5"

### S6 — V5 Serial Protocol Deep Dive (vexide.dev)
https://vexide.dev/blog/posts/serial-deep-dive/
> "Controller: A USB connection to your controller which can be paired to your Brain via VEXnet, Bluetooth, or even a cable. This connection type is very similar to a direct connection with one exception: This method of communication only has one serial port (this port is often named a controller port). This port acts the same way as the system port in a direct brain connection. For this reason, stdio output has to be received with a UserFifoPacket. The response to this packet contains the incoming stdout buffer."

### S3 — PROS kernel ser_driver.c (purduesigbots/pros on GitHub)
https://github.com/purduesigbots/pros
```c
void ser_driver_initialize(void) {
    ser_driver_runtime_config |= E_COBS_ENABLED;  // start with cobs enabled
    set_initialize(&enabled_streams_set);
    set_add(&enabled_streams_set, STDOUT_STREAM_ID);  // 'sout' little endian — stdout ON by default
    ...
}

// stderr is ALWAYS guaranteed to be sent over the serial line. stdout and
// others may be disabled
static const uint32_t guaranteed_delivery_streams[] = {
    STDERR_STREAM_ID,
};
```
