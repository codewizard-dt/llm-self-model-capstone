from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.bridge_demux import BrainStreamDemux
from vexy_ros.bridge_protocol import (
    MAX_ARM_TARGET_DEG,
    MAX_CLAW_MS,
    MAX_TTL_MS,
    BridgeProtocolError,
    heartbeat_packet,
    normalize_outbound,
)


class BridgeDemuxTests(unittest.TestCase):
    def test_interleaved_ack_and_telemetry_route_separately(self) -> None:
        demux = BrainStreamDemux(ack_timeout_s=0.2, telemetry_stale_s=0)
        demux.register_sent(
            {"v": 1, "seq": 7, "type": "cmd", "cmd": "stop", "ttl_ms": 200}, now_s=1.0
        )

        telemetry = demux.consume_line(
            json.dumps({"v": 1, "type": "telemetry", "heading_deg": 12.5}) + "\n",
            now_s=1.01,
        )
        ack = demux.consume_line(
            json.dumps({"v": 1, "type": "ack", "ack": 7, "state": "ok"}) + "\n",
            now_s=1.02,
        )
        event = demux.consume_line(
            json.dumps({"v": 1, "type": "event", "name": "watchdog_ok"}) + "\n",
            now_s=1.03,
        )

        self.assertEqual([item.kind for item in telemetry], ["telemetry"])
        self.assertEqual([item.kind for item in ack], ["ack"])
        self.assertEqual([item.kind for item in event], ["telemetry"])
        self.assertFalse(demux.has_pending(7))

    def test_missing_ack_fault_does_not_block_later_telemetry(self) -> None:
        demux = BrainStreamDemux(ack_timeout_s=0.2, telemetry_stale_s=0)
        demux.register_sent(
            {"v": 1, "seq": 8, "type": "heartbeat", "ttl_ms": 200}, now_s=1.0
        )

        timeout_events = demux.check_timeouts(now_s=1.25)
        telemetry_events = demux.consume_line(
            json.dumps({"v": 1, "type": "sample", "battery_mv": 12300}) + "\n",
            now_s=1.26,
        )

        self.assertEqual(timeout_events[0].kind, "status")
        self.assertEqual(timeout_events[0].payload["reason"], "missing_ack")
        self.assertEqual(timeout_events[0].payload["seq"], 8)
        self.assertEqual([item.kind for item in telemetry_events], ["telemetry"])

    def test_bad_json_reports_status(self) -> None:
        events = BrainStreamDemux(telemetry_stale_s=0).consume_line(
            "{not json}\n", now_s=1.0
        )

        self.assertEqual(events[0].kind, "status")
        self.assertEqual(events[0].payload["reason"], "bad_json")

    def test_unsupported_protocol_reports_status(self) -> None:
        events = BrainStreamDemux(telemetry_stale_s=0).consume_line(
            json.dumps({"v": 99, "type": "ack", "ack": 1}) + "\n",
            now_s=1.0,
        )

        self.assertEqual(events[0].kind, "status")
        self.assertEqual(events[0].payload["reason"], "unsupported_protocol")

    def test_heartbeat_and_stop_ttl_stay_bounded(self) -> None:
        heartbeat = normalize_outbound(heartbeat_packet(1))
        stop = normalize_outbound(
            {
                "v": 1,
                "seq": 2,
                "type": "cmd",
                "cmd": "stop",
                "sent_ms": 1,
                "ttl_ms": 999999,
            }
        )

        self.assertEqual(heartbeat["ttl_ms"], 200)
        self.assertEqual(stop["ttl_ms"], MAX_TTL_MS)

    def test_routine_command_accepts_only_slots_two_through_four(self) -> None:
        routine = normalize_outbound(
            {
                "v": 1,
                "seq": 3,
                "type": "cmd",
                "cmd": "routine",
                "sent_ms": 1,
                "ttl_ms": 500,
                "slot": "3",
            }
        )

        self.assertEqual(routine["slot"], 3)
        with self.assertRaises(BridgeProtocolError):
            normalize_outbound(
                {
                    "v": 1,
                    "seq": 4,
                    "type": "cmd",
                    "cmd": "routine",
                    "sent_ms": 1,
                    "ttl_ms": 500,
                    "slot": 5,
                }
            )

    def test_claw_command_duration_stays_bounded(self) -> None:
        for cmd in ("grab", "lift", "release"):
            with self.subTest(cmd=cmd):
                packet = normalize_outbound(
                    {
                        "v": 1,
                        "seq": 3,
                        "type": "cmd",
                        "cmd": cmd,
                        "sent_ms": 1,
                        "ttl_ms": 999999,
                        "duration_ms": 999999,
                    }
                )

                self.assertEqual(packet["ttl_ms"], MAX_TTL_MS)
                self.assertEqual(packet["duration_ms"], MAX_CLAW_MS)

    def test_arm_command_target_stays_bounded(self) -> None:
        packet = normalize_outbound(
            {
                "v": 1,
                "seq": 4,
                "type": "cmd",
                "cmd": "arm",
                "sent_ms": 1,
                "ttl_ms": 200,
                "target_deg": 999999,
            }
        )

        self.assertEqual(packet["target_deg"], MAX_ARM_TARGET_DEG)


if __name__ == "__main__":
    unittest.main()
