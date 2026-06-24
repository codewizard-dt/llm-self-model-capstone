from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable, Literal, Mapping

from .bridge_protocol import PROTOCOL_VERSION

RecordKind = Literal["ack", "telemetry", "status", "unknown"]
EventKind = Literal["ack", "telemetry", "status"]

ACK_TYPES = {"ack"}
TELEMETRY_TYPES = {"telemetry", "sample", "event"}
STATUS_TYPES = {"bridge_status", "status", "fault", "error"}
TELEMETRY_FIELDS = {
    "battery_mv",
    "heading_deg",
    "left_rpm",
    "right_rpm",
    "motor_temps",
    "pose",
    "imu",
    "encoders",
}


@dataclass(frozen=True)
class PendingAck:
    seq: int
    packet_type: str
    command: str | None
    sent_at_s: float
    deadline_at_s: float
    ttl_ms: int | None


@dataclass(frozen=True)
class DemuxEvent:
    kind: EventKind
    payload: dict[str, Any]


def classify_record(record: Mapping[str, Any]) -> RecordKind:
    record_type = record.get("type")
    if record_type in ACK_TYPES or "ack" in record:
        return "ack"
    if record_type in TELEMETRY_TYPES:
        return "telemetry"
    if record_type in STATUS_TYPES:
        return "status"
    if TELEMETRY_FIELDS.intersection(record):
        return "telemetry"
    return "unknown"


def bridge_status(
    reason: str,
    message: str,
    *,
    state: str = "fault",
    now_s: float | None = None,
    **fields: Any,
) -> dict[str, Any]:
    observed_s = time.monotonic() if now_s is None else now_s
    status = {
        "v": PROTOCOL_VERSION,
        "type": "bridge_status",
        "state": state,
        "reason": reason,
        "message": message,
        "observed_ms": int(observed_s * 1000),
    }
    status.update(fields)
    return status


class BrainStreamDemux:
    def __init__(
        self,
        *,
        ack_timeout_s: float = 0.4,
        telemetry_stale_s: float = 2.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.ack_timeout_s = ack_timeout_s
        self.telemetry_stale_s = telemetry_stale_s
        self._clock = clock or time.monotonic
        self._started_at_s = self._clock()
        self._pending: dict[int, PendingAck] = {}
        self._last_telemetry_at_s: float | None = None
        self._last_stale_report_at_s: float | None = None

    def has_pending(self, seq: int) -> bool:
        return seq in self._pending

    def register_sent(
        self, packet: Mapping[str, Any], now_s: float | None = None
    ) -> None:
        seq = packet.get("seq")
        if not isinstance(seq, int):
            return
        observed_s = self._resolve_now(now_s)
        ttl_ms = packet.get("ttl_ms")
        self._pending[seq] = PendingAck(
            seq=seq,
            packet_type=str(packet.get("type", "")),
            command=packet.get("cmd") if isinstance(packet.get("cmd"), str) else None,
            sent_at_s=observed_s,
            deadline_at_s=observed_s + self.ack_timeout_s,
            ttl_ms=ttl_ms if isinstance(ttl_ms, int) else None,
        )

    def forget(self, seq: int) -> None:
        self._pending.pop(seq, None)

    def consume_line(
        self, line: bytes | str, now_s: float | None = None
    ) -> list[DemuxEvent]:
        observed_s = self._resolve_now(now_s)
        text = self._line_to_text(line)
        if not text:
            return []

        try:
            record = json.loads(text)
        except json.JSONDecodeError as exc:
            return [
                DemuxEvent(
                    "status",
                    bridge_status(
                        "bad_json",
                        f"bad JSON from Brain: {exc}",
                        now_s=observed_s,
                        raw=text[:200],
                    ),
                )
            ]

        if not isinstance(record, dict):
            return [
                DemuxEvent(
                    "status",
                    bridge_status(
                        "bad_json",
                        "Brain line must decode to a JSON object",
                        now_s=observed_s,
                        raw=text[:200],
                    ),
                )
            ]

        version = record.get("v")
        if version is not None and version != PROTOCOL_VERSION:
            return [
                DemuxEvent(
                    "status",
                    bridge_status(
                        "unsupported_protocol",
                        f"unsupported Brain protocol version: {version}",
                        now_s=observed_s,
                        brain_record=record,
                    ),
                )
            ]

        kind = classify_record(record)
        if kind == "ack":
            events = [DemuxEvent("ack", dict(record))]
            ack_seq = record.get("ack")
            if isinstance(ack_seq, int) and self.has_pending(ack_seq):
                self.forget(ack_seq)
            else:
                events.append(
                    DemuxEvent(
                        "status",
                        bridge_status(
                            "unexpected_ack",
                            "ack did not match a pending command sequence",
                            state="warn",
                            now_s=observed_s,
                            ack=ack_seq,
                        ),
                    )
                )
            return events

        if kind == "telemetry":
            self._last_telemetry_at_s = observed_s
            return [DemuxEvent("telemetry", dict(record))]

        if kind == "status":
            return [DemuxEvent("status", dict(record))]

        return [
            DemuxEvent(
                "status",
                bridge_status(
                    "unknown_record",
                    "Brain JSON record was neither ack nor telemetry",
                    state="warn",
                    now_s=observed_s,
                    brain_record=record,
                ),
            )
        ]

    def check_timeouts(self, now_s: float | None = None) -> list[DemuxEvent]:
        observed_s = self._resolve_now(now_s)
        events: list[DemuxEvent] = []

        for pending in list(self._pending.values()):
            if observed_s >= pending.deadline_at_s:
                self.forget(pending.seq)
                events.append(
                    DemuxEvent(
                        "status",
                        bridge_status(
                            "missing_ack",
                            "no ack received before the bridge timeout",
                            now_s=observed_s,
                            seq=pending.seq,
                            packet_type=pending.packet_type,
                            command=pending.command,
                            age_ms=int((observed_s - pending.sent_at_s) * 1000),
                            ttl_ms=pending.ttl_ms,
                        ),
                    )
                )

        events.extend(self._check_stale_telemetry(observed_s))
        return events

    def _check_stale_telemetry(self, observed_s: float) -> list[DemuxEvent]:
        if self.telemetry_stale_s <= 0:
            return []

        last_seen = self._last_telemetry_at_s or self._started_at_s
        age_s = observed_s - last_seen
        if age_s < self.telemetry_stale_s:
            return []
        if (
            self._last_stale_report_at_s is not None
            and observed_s - self._last_stale_report_at_s < self.telemetry_stale_s
        ):
            return []

        self._last_stale_report_at_s = observed_s
        reason = (
            "stale_telemetry"
            if self._last_telemetry_at_s is not None
            else "no_telemetry"
        )
        message = (
            "no telemetry sample has arrived yet"
            if self._last_telemetry_at_s is None
            else "telemetry sample is stale"
        )
        return [
            DemuxEvent(
                "status",
                bridge_status(
                    reason, message, now_s=observed_s, age_ms=int(age_s * 1000)
                ),
            )
        ]

    def _resolve_now(self, now_s: float | None) -> float:
        return self._clock() if now_s is None else now_s

    @staticmethod
    def _line_to_text(line: bytes | str) -> str:
        if isinstance(line, bytes):
            return line.decode("utf-8", errors="replace").strip()
        return line.strip()
