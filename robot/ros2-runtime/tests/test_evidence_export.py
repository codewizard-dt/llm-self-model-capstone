from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "robot" / "ros2-runtime" / "src"))
sys.path.insert(0, str(ROOT / "contracts" / "src"))

from contracts import ContractLine  # noqa: E402
from vexy_ros.evidence_export import (  # noqa: E402
    bundle_from_proof_dir,
    bundle_from_tag_action_summary,
    contract_jsonl_from_bundle,
    main,
)


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

    def test_live_shape_top_level_motor_samples_are_normalized(self) -> None:
        bundle = json.loads(FIXTURE.read_text())
        bundle["motor_samples"] = [
            {
                "device": "left_drive",
                "subsystem": "drivetrain",
                "sample_ms": 4100,
                "values": {
                    "position_deg": 540.0,
                    "velocity_rpm": 22.0,
                    "current_amp": 1.4,
                    "power_w": 16.8,
                    "torque_nm": 0.5,
                    "efficiency_pct": 70.0,
                    "temperature_c": 35.0,
                },
            }
        ]

        line = contract_jsonl_from_bundle(bundle)
        model = ContractLine.model_validate_json(line)

        self.assertEqual(model.motor_samples[0].api_binding, "vexcode_python")
        self.assertEqual(
            model.motor_samples[0].source_api["position_deg"],
            "left_drive.position(DEGREES)",
        )

    def test_tag_action_summary_builds_contract_bundle(self) -> None:
        summary = live_tag_action_summary()

        bundle = bundle_from_tag_action_summary(
            summary,
            proof_dir=Path("/home/vexy/proof/tag-approach-scan-20260624-142154"),
            session_id="tag_approach_scan_20260624_142154",
        )
        line = contract_jsonl_from_bundle(bundle)
        model = ContractLine.model_validate_json(line)

        self.assertEqual(bundle["session_id"], "tag_approach_scan_20260624_142154")
        self.assertEqual(model.task, "align_to_tag")
        self.assertEqual(
            model.source.raw_session_path,
            "/home/vexy/proof/tag-approach-scan-20260624-142154",
        )
        self.assertEqual(model.source.telemetry_sample_count, 1)
        self.assertEqual(model.outcome["observed_tags_after_scan"], [0, 1])
        self.assertAlmostEqual(model.gap["distance_error_m"], -0.005040343806100522)
        self.assertAlmostEqual(model.gap["closure_error_m"], 0.005040343806100522)
        self.assertAlmostEqual(model.vision.apriltag_pose.x, 1.1)

    def test_proof_dir_cli_writes_bundle_and_default_contract_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proof_dir = Path(tmp) / "tag-approach-scan-20260624-142154"
            proof_dir.mkdir()
            (proof_dir / "summary.json").write_text(
                json.dumps(live_tag_action_summary())
            )
            (proof_dir / "mcap").mkdir()

            bundle = bundle_from_proof_dir(proof_dir)
            code = main(["--proof-dir", str(proof_dir)])

            self.assertEqual(bundle["session_id"], "tag_approach_scan_20260624_142154")
            self.assertEqual(code, 0)
            bundle_path = proof_dir / "tag_action_bundle.json"
            jsonl_path = (
                proof_dir / "contract" / "tag_approach_scan_20260624_142154.jsonl"
            )
            self.assertTrue(bundle_path.exists())
            self.assertTrue(jsonl_path.exists())
            ContractLine.model_validate_json(jsonl_path.read_text())


def live_tag_action_summary() -> dict[str, object]:
    return {
        "approach_reached_target": True,
        "approach_reason": "target_distance_reached",
        "closure_m": 0.3048,
        "distance_closed_m": 0.30984034380610054,
        "last_scene_map": {
            "robot_pose": {"x_m": 1.1, "y_m": 0.34, "yaw_rad": 0.03},
            "tags": {"0": {"x_m": 0.0, "y_m": 0.0, "yaw_rad": 0.0}},
            "objects": [],
        },
        "last_telemetry": {
            "motor_samples": [
                {
                    "device": "left_drive",
                    "sample_ms": 2013509,
                    "subsystem": "drivetrain",
                    "values": {
                        "position_deg": -6291.0,
                        "velocity_rpm": 0.0,
                        "current_amp": 0.0,
                        "power_w": 0.0,
                        "torque_nm": 0.0,
                        "efficiency_pct": 0.0,
                        "temperature_c": 40.0,
                    },
                }
            ],
            "t_ms": 2013509,
        },
        "observed_tags_after_scan": [0, 1],
        "post_drive_distance_m": 0.49019852825168614,
        "start_distance_m": 0.8000388720577867,
        "target_distance_m": 0.49523887205778666,
        "visible_tag": 1,
    }


if __name__ == "__main__":
    unittest.main()
