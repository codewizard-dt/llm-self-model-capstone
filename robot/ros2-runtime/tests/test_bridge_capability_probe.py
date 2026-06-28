from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vexy_ros.bridge_capability_probe import (  # noqa: E402
    command_rejection_reason,
    command_supported_from_ack,
)


class BridgeCapabilityProbeHelperTests(unittest.TestCase):
    def test_command_supported_from_explicit_command_list(self) -> None:
        self.assertTrue(
            command_supported_from_ack(
                {"state": "ok", "supported_commands": ["stop", "arm"]}, "arm"
            )
        )
        self.assertFalse(
            command_supported_from_ack(
                {"state": "ok", "supported_commands": ["stop"]}, "arm"
            )
        )

    def test_command_supported_falls_back_to_ok_arm_ack(self) -> None:
        self.assertTrue(command_supported_from_ack({"state": "ok", "fault": None}, "arm"))
        self.assertFalse(
            command_supported_from_ack(
                {"state": "rejected", "fault": "unknown_command"}, "arm"
            )
        )

    def test_command_rejection_reason_is_stable(self) -> None:
        self.assertEqual(command_rejection_reason(None), "missing_ack")
        self.assertEqual(command_rejection_reason({"state": "ok"}), "accepted")
        self.assertEqual(
            command_rejection_reason(
                {"state": "rejected", "fault": "unknown_command"}
            ),
            "unknown_command",
        )


if __name__ == "__main__":
    unittest.main()
