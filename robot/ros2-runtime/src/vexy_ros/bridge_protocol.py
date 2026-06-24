from __future__ import annotations

import json
import time
from typing import Any, Mapping

PROTOCOL_VERSION = 1
MAX_LINEAR = 0.35
MAX_OMEGA = 0.6
DEFAULT_TTL_MS = 200
MAX_TTL_MS = 5000
COMMANDS = {"stop", "drive", "turn", "set_goal"}


class BridgeProtocolError(ValueError):
    pass


def now_ms() -> int:
    return int(time.monotonic() * 1000)


def encode_packet(packet: Mapping[str, Any]) -> bytes:
    return (json.dumps(packet, separators=(",", ":"), sort_keys=True) + "\n").encode(
        "utf-8"
    )


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normalize_outbound(packet: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(packet)

    if normalized.get("v") != PROTOCOL_VERSION:
        raise BridgeProtocolError(
            f"unsupported protocol version: {normalized.get('v')}"
        )
    if not isinstance(normalized.get("seq"), int):
        raise BridgeProtocolError("seq must be an integer")

    ptype = normalized.get("type")
    if ptype not in {"cmd", "heartbeat"}:
        raise BridgeProtocolError(f"type must be cmd or heartbeat, got: {ptype!r}")

    try:
        ttl = int(normalized.get("ttl_ms", DEFAULT_TTL_MS))
    except (TypeError, ValueError) as exc:
        raise BridgeProtocolError("ttl_ms must be an integer") from exc
    normalized["ttl_ms"] = int(clamp(ttl, 1, MAX_TTL_MS))

    if ptype == "heartbeat":
        return normalized

    cmd = normalized.get("cmd")
    if cmd not in COMMANDS:
        raise BridgeProtocolError(f"unsupported cmd: {cmd!r}")

    if cmd == "drive":
        normalized["vx"] = clamp(
            float(normalized.get("vx", 0.0)), -MAX_LINEAR, MAX_LINEAR
        )
        normalized["vy"] = clamp(
            float(normalized.get("vy", 0.0)), -MAX_LINEAR, MAX_LINEAR
        )
        normalized["omega"] = clamp(
            float(normalized.get("omega", 0.0)), -MAX_OMEGA, MAX_OMEGA
        )
    elif cmd == "turn":
        normalized["omega"] = clamp(
            float(normalized.get("omega", 0.0)), -MAX_OMEGA, MAX_OMEGA
        )

    return normalized


def heartbeat_packet(seq: int) -> dict[str, Any]:
    return {
        "v": PROTOCOL_VERSION,
        "seq": seq,
        "type": "heartbeat",
        "sent_ms": now_ms(),
        "ttl_ms": DEFAULT_TTL_MS,
    }
