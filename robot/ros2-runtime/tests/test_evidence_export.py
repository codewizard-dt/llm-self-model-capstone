from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "robot" / "ros2-runtime" / "src"))
sys.path.insert(0, str(ROOT / "contracts" / "src"))

from contracts import ContractLine  # noqa: E402
from vexy_ros.evidence_export import contract_jsonl_from_bundle  # noqa: E402


FIXTURE = (
    ROOT / "robot" / "ros2-runtime" / "fixtures" / "align_to_tag_success_bundle.json"
)


class EvidenceExportTests(unittest.TestCase):
    def test_success_bundle_exports_contract_valid_jsonl(self) -> None:
        bundle = json.loads(FIXTURE.read_text())

        line = contract_jsonl_from_bundle(bundle)
        model = ContractLine.model_validate_json(line)

        self.assertEqual(model.task, "align_to_tag")
        self.assertEqual(
            model.source.raw_session_path, "proof/rosbags/align_to_tag_fixture"
        )
        self.assertEqual(model.source.telemetry_sample_count, 1)
        self.assertIsNotNone(model.vision)
        self.assertAlmostEqual(model.vision.apriltag_pose.x, 1.10)
        self.assertEqual(model.outcome["reason"], "success")
        self.assertIn("yaw_error_rad", model.gap)

    def test_bundle_without_motor_sample_fails_before_export(self) -> None:
        bundle = json.loads(FIXTURE.read_text())
        bundle["motor_samples"] = []

        with self.assertRaises(ValueError):
            contract_jsonl_from_bundle(bundle, validate=False)


if __name__ == "__main__":
    unittest.main()
