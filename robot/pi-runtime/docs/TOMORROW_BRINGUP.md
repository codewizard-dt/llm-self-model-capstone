# Tomorrow V5 Brain Bring-Up

## Before Plugging In

On the Pi:

```bash
cd ~/llm-self-model-capstone/robot/pi-runtime
PYTHONPATH=src scripts/smoke_test.sh
```

Expected: `smoke test ok`.

## Plug In The Brain

1. Connect a charged V5 Battery to the Brain.
2. Power on the Brain.
3. Connect Brain Micro-USB to the Raspberry Pi.
4. Run:

```bash
cd ~/llm-self-model-capstone/robot/pi-runtime
scripts/find_v5_serial.sh
```

Expected: one or two `/dev/ttyACM*` devices, ideally stable symlinks under `/dev/serial/by-id/`.

## Pick The User/Console Port

VEX docs describe the console serial port as separate from the project/download serial port. On macOS/Chromebook, their Web Serial UI says the console port is the Brain with the higher ID. On Linux we should test both `/dev/ttyACM*` devices and use the one that echoes user program output.

## Load Brain Program

Use either PROS or VEXcode. The Brain program must:

- Disable COBS if reading raw serial through PROS terminal streams.
- Read newline-delimited JSON from the user serial stream.
- Validate and clamp commands.
- Emit newline-delimited JSON acks.
- Stop motors on stale heartbeat or expired command.

See `../../v5-brain/pros_bridge/src/main.cpp` for a starter sketch and notes.

## Switch Pi Bridge To Real Serial

Create or edit the Pi-local override file:

```bash
mkdir -p ~/.config/vexy-system2
nano ~/.config/vexy-system2/local
```

Add:

```bash
VEXY_BRIDGE_MODE=serial
VEXY_SERIAL_PORT=/dev/serial/by-id/YOUR_V5_USER_PORT
VEXY_SERIAL_BAUD=115200
```

Then:

```bash
cd ~/llm-self-model-capstone/robot/pi-runtime
PYTHONPATH=src scripts/serial_ping_test.sh
```

## First Motion Test

Keep the robot on blocks. Send only:

```json
{"cmd":"stop"}
```

Then a very low TTL drive command:

```json
{"cmd":"drive","vx":0.05,"omega":0.0,"ttl_ms":100}
```

The expected failure mode is "nothing happens" or "brief twitch then stop", never continuous drive.
