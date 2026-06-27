from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vexy_ros.proof_runner import TELEMETRY_TOPICS, telemetry_bag_record_cmd  # noqa: E402


class TelemetryCaptureTests(unittest.TestCase):
    def test_bag_record_command_uses_mcap_storage(self) -> None:
        cmd = telemetry_bag_record_cmd(Path("/tmp/run-1/bag"))

        self.assertEqual(
            cmd[:7],
            ["ros2", "bag", "record", "-s", "mcap", "-o", "/tmp/run-1/bag"],
        )

    def test_bag_record_command_covers_operator_telemetry_topics(self) -> None:
        cmd = telemetry_bag_record_cmd("/tmp/run-1/bag")
        recorded_topics = cmd[7:]

        self.assertEqual(recorded_topics, list(TELEMETRY_TOPICS))
        self.assertEqual(len(recorded_topics), len(set(recorded_topics)))


if __name__ == "__main__":
    unittest.main()
