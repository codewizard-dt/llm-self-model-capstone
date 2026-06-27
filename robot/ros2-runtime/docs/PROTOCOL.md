# Vexy ROS Bridge Protocol

Transport: newline-delimited UTF-8 JSON over the V5 Brain user serial port.

The active Pi-side implementation is
[`bridge_protocol.py`](../src/vexy_ros/bridge_protocol.py). The Brain-side
implementation is `robot/v5-brain/pros_bridge/src/main.cpp`.

Every Pi-to-Brain packet includes:

- `v`: protocol version, currently `1`
- `seq`: integer sequence number
- `type`: `cmd` or `heartbeat`
- `sent_ms`: Unix epoch milliseconds
- `ttl_ms`: command expiration in milliseconds

## Commands

Stop:

```json
{"v":1,"seq":1,"type":"cmd","cmd":"stop","sent_ms":1781880000000,"ttl_ms":500,"reason":"operator"}
```

Drive:

```json
{"v":1,"seq":2,"type":"cmd","cmd":"drive","sent_ms":1781880000010,"ttl_ms":200,"vx":0.1,"vy":0.0,"omega":0.0}
```

Turn:

```json
{"v":1,"seq":3,"type":"cmd","cmd":"turn","sent_ms":1781880000020,"ttl_ms":200,"omega":0.2}
```

Brain routine:

```json
{"v":1,"seq":4,"type":"cmd","cmd":"routine","sent_ms":1781880000030,"ttl_ms":500,"slot":2}
```

Routine slots are fixed routines inside the running `pros_bridge` program, not
separate VEXos upload slots:

| Slot | Routine | What It Does |
|---|---|---|
| 2 | `spin_720` | bounded 720 degree in-place spin |
| 3 | `arm_full_cycle` | arm to bounded top target, pause, back to rest |
| 4 | `one_foot_forward_back` | one foot forward, pause, one foot back |

Heartbeat:

```json
{"v":1,"seq":5,"type":"heartbeat","sent_ms":1781880000040,"ttl_ms":200}
```

## V5 Response

```json
{"v":1,"ack":2,"type":"ack","state":"ok","recv_ms":1781880000050,"battery_mv":12300,"heading_deg":12.3,"fault":null}
```

Rejected command:

```json
{"v":1,"ack":2,"type":"ack","state":"rejected","recv_ms":1781880000050,"fault":"ttl_expired"}
```

## Safety Rules

- Brain rejects malformed JSON.
- Brain rejects unknown commands.
- Brain rejects routine slots outside `2`, `3`, and `4`.
- Brain rejects new drive/turn/routine commands with `fault:"busy"` while a
  routine is active.
- Brain clamps all velocity values.
- Brain stops if no valid heartbeat or command arrives within the watchdog
  interval.
- Brain stops when command TTL expires.
- Pi treats missing ack as a fault and sends `stop` on reconnect.
