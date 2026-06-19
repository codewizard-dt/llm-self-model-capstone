# Vexy Pi-to-V5 Protocol

Transport: newline-delimited UTF-8 JSON.

Initial physical transport: V5 Brain Micro-USB console/user serial port.

Every packet includes:

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

Heartbeat:

```json
{"v":1,"seq":4,"type":"heartbeat","sent_ms":1781880000030,"ttl_ms":200}
```

## V5 Response

```json
{"v":1,"ack":2,"type":"ack","state":"ok","recv_ms":1781880000050,"battery_mv":12300,"heading_deg":12.3,"fault":null}
```

Errors:

```json
{"v":1,"ack":2,"type":"ack","state":"rejected","recv_ms":1781880000050,"fault":"ttl_expired"}
```

## Safety Rules

- Brain rejects malformed JSON.
- Brain rejects unknown commands.
- Brain clamps all velocity values.
- Brain stops if no valid heartbeat or command arrives within the watchdog interval.
- Brain stops when command TTL expires.
- Pi treats missing ack as a fault and sends `stop` on reconnect.

