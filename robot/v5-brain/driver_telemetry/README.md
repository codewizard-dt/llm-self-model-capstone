# Slot 7 Driver Telemetry

Buildable PROS project for manual driving calibration. Upload this project to
VEX Brain slot `7`; it intentionally does not replace the slot 4 guarded ROS
bridge.

Behavior:

- The V5 controller owns drivetrain, arm, and claw motor commands.
- The Brain emits raw newline-delimited JSON telemetry on the user serial port.
- Heartbeat packets are acked so the existing ROS serial bridge can keep reading.
- ROS `drive`, `turn`, `routine`, `grab`, `lift`, and `release` commands are
  rejected with `fault:"manual_mode"` while this program is running.
- `stop` is accepted; if the packet contains `operator_estop`, the estop latch
  stays active until the program restarts.

Build and upload:

```bash
cd robot/v5-brain/driver_telemetry
pros make clean && pros make
pros upload --slot 7 \
  --name "Slot 7 Driver Telemetry" \
  --description "Slot 7 Driver Telemetry: manual controller drive with JSON telemetry" \
  --after none
pros v5 run 7
```

Expected Brain screen banner:

```text
slot 7 driver telemetry
manual controller owns drive
```
