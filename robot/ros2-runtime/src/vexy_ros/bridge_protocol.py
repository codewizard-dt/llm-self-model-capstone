from __future__ import annotations

import json
import time
from typing import Any, Mapping

PROTOCOL_VERSION = 1
MAX_LINEAR = 0.35
MAX_OMEGA = 0.6
DEFAULT_TTL_MS = 200
MAX_TTL_MS = 5000
ROUTINE_SLOTS = {2, 3, 4}
COMMANDS = {
    "stop",
    "drive",
    "turn",
    "set_goal",
    "routine",
    "grab",
    "lift",
    "release",
    "arm",
}
DEFAULT_RELEASE_MS = 650
DEFAULT_GRAB_MS = 700
DEFAULT_LIFT_MS = 900
MAX_CLAW_MS = 1500
MAX_ARM_TARGET_DEG = 360.0


class BridgeProtocolError(ValueError):
    pass


def now_ms() -> int:
    return int(time.monotonic() * 1000)


def encode_packet(packet: Mapping[str, Any]) -> bytes:
    return (json.dumps(packet, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normalize_outbound(packet: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(packet)

    if normalized.get("v") != PROTOCOL_VERSION:
        raise BridgeProtocolError(f"unsupported protocol version: {normalized.get('v')}")
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
        normalized["vx"] = clamp(float(normalized.get("vx", 0.0)), -MAX_LINEAR, MAX_LINEAR)
        normalized["vy"] = clamp(float(normalized.get("vy", 0.0)), -MAX_LINEAR, MAX_LINEAR)
        normalized["omega"] = clamp(float(normalized.get("omega", 0.0)), -MAX_OMEGA, MAX_OMEGA)
    elif cmd == "turn":
        normalized["omega"] = clamp(
            float(normalized.get("omega", 0.0)), -MAX_OMEGA, MAX_OMEGA
        )
    elif cmd == "routine":
        try:
            slot = int(normalized.get("slot"))
        except (TypeError, ValueError) as exc:
            raise BridgeProtocolError("routine slot must be an integer") from exc
        if slot not in ROUTINE_SLOTS:
            raise BridgeProtocolError("routine slot must be one of 2, 3, or 4")
        normalized["slot"] = slot
        normalized["omega"] = clamp(float(normalized.get("omega", 0.0)), -MAX_OMEGA, MAX_OMEGA)
    elif cmd == "arm":
        try:
            target_deg = float(normalized.get("target_deg"))
        except (TypeError, ValueError) as exc:
            raise BridgeProtocolError("target_deg must be a number") from exc
        normalized["target_deg"] = clamp(target_deg, 0.0, MAX_ARM_TARGET_DEG)
    elif cmd in {"grab", "lift", "release"}:
        try:
            default_duration_ms = {
                "grab": DEFAULT_GRAB_MS,
                "lift": DEFAULT_LIFT_MS,
                "release": DEFAULT_RELEASE_MS,
            }[cmd]
            duration_ms = int(normalized.get("duration_ms", default_duration_ms))
        except (TypeError, ValueError) as exc:
            raise BridgeProtocolError("duration_ms must be an integer") from exc
        normalized["duration_ms"] = int(clamp(duration_ms, 1, MAX_CLAW_MS))

    return normalized


def heartbeat_packet(seq: int) -> dict[str, Any]:
    return {
        "v": PROTOCOL_VERSION,
        "seq": seq,
        "type": "heartbeat",
        "sent_ms": now_ms(),
        "ttl_ms": DEFAULT_TTL_MS,
    }
