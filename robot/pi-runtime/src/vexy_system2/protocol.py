from __future__ import annotations

import json
import time
from typing import Any

PROTOCOL_VERSION = 1
MAX_LINEAR = 0.35
MAX_OMEGA = 0.6
DEFAULT_TTL_MS = 200
MAX_TTL_MS = 1000


class ProtocolError(ValueError):
    pass


def now_ms() -> int:
    return int(time.time() * 1000)


def encode(packet: dict[str, Any]) -> bytes:
    return (json.dumps(packet, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def decode(line: bytes | str) -> dict[str, Any]:
    if isinstance(line, bytes):
        line = line.decode("utf-8", errors="replace")
    try:
        packet = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"invalid json: {exc}") from exc
    if not isinstance(packet, dict):
        raise ProtocolError("packet must be a json object")
    return packet


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def command(seq: int, cmd: str, **fields: Any) -> dict[str, Any]:
    packet = {
        "v": PROTOCOL_VERSION,
        "seq": seq,
        "type": "cmd",
        "cmd": cmd,
        "sent_ms": now_ms(),
        "ttl_ms": int(fields.pop("ttl_ms", DEFAULT_TTL_MS)),
    }
    packet.update(fields)
    return validate_outbound(packet)


def heartbeat(seq: int) -> dict[str, Any]:
    return {
        "v": PROTOCOL_VERSION,
        "seq": seq,
        "type": "heartbeat",
        "sent_ms": now_ms(),
        "ttl_ms": DEFAULT_TTL_MS,
    }


def stop(seq: int, reason: str = "operator") -> dict[str, Any]:
    return command(seq, "stop", reason=reason, ttl_ms=500)


def validate_outbound(packet: dict[str, Any]) -> dict[str, Any]:
    if packet.get("v") != PROTOCOL_VERSION:
        raise ProtocolError("unsupported protocol version")
    if not isinstance(packet.get("seq"), int):
        raise ProtocolError("seq must be an integer")
    if packet.get("type") not in {"cmd", "heartbeat"}:
        raise ProtocolError("type must be cmd or heartbeat")

    ttl_ms = int(packet.get("ttl_ms", DEFAULT_TTL_MS))
    packet["ttl_ms"] = clamp(ttl_ms, 1, MAX_TTL_MS)

    if packet["type"] == "heartbeat":
        return packet

    cmd = packet.get("cmd")
    if cmd not in {"stop", "drive", "turn", "set_goal"}:
        raise ProtocolError(f"unsupported command: {cmd}")

    if cmd == "drive":
        packet["vx"] = clamp(float(packet.get("vx", 0.0)), -MAX_LINEAR, MAX_LINEAR)
        packet["vy"] = clamp(float(packet.get("vy", 0.0)), -MAX_LINEAR, MAX_LINEAR)
        packet["omega"] = clamp(float(packet.get("omega", 0.0)), -MAX_OMEGA, MAX_OMEGA)
    elif cmd == "turn":
        packet["omega"] = clamp(float(packet.get("omega", 0.0)), -MAX_OMEGA, MAX_OMEGA)

    return packet


def ack(packet: dict[str, Any], **fields: Any) -> dict[str, Any]:
    response = {
        "v": PROTOCOL_VERSION,
        "ack": packet.get("seq"),
        "type": "ack",
        "state": "ok",
        "recv_ms": now_ms(),
    }
    response.update(fields)
    return response

