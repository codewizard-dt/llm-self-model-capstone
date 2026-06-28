from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vexy_ros.visual_pickup_probe import (  # noqa: E402
    ack_rejection_reason,
    ack_state_ok,
    arm_position_deg_from_telemetry,
    best_ball_detection,
    capture_artifact_summary,
    has_object_from_status,
    lift_proof_from_positions,
    parse_float_list,
)


class VisualPickupProbeHelperTests(unittest.TestCase):
    def test_parse_float_list_skips_empty_parts(self) -> None:
        self.assertEqual(parse_float_list("360, 430,, 455"), [360.0, 430.0, 455.0])

    def test_best_ball_detection_uses_highest_confidence_yellow_ball(self) -> None:
        detection = best_ball_detection(
            {
                "detections": [
                    {
                        "label": "yellow_ball",
                        "confidence": 0.4,
                        "bbox_xyxy": [10, 20, 30, 40],
                    },
                    {
                        "label": "bin",
                        "confidence": 0.9,
                        "bbox_xyxy": [1, 2, 3, 4],
                    },
                    {
                        "label": "yellow_ball",
                        "confidence": 0.8,
                        "bbox_xyxy": [100, 200, 150, 260],
                    },
                ]
            }
        )

        assert detection is not None
        self.assertEqual(detection.bbox_xyxy, (100.0, 200.0, 150.0, 260.0))
        self.assertEqual(detection.cx, 125.0)
        self.assertEqual(detection.width, 50.0)

    def test_best_ball_detection_rejects_bad_boxes(self) -> None:
        self.assertIsNone(
            best_ball_detection(
                {
                    "detections": [
                        {
                            "label": "yellow_ball",
                            "confidence": 1.0,
                            "bbox_xyxy": [1, 2],
                        },
                        {
                            "label": "yellow_ball",
                            "confidence": 1.0,
                            "bbox_xyxy": [5, 5, 5, 10],
                        },
                    ]
                }
            )
        )

    def test_has_object_from_status_requires_true(self) -> None:
        self.assertTrue(has_object_from_status({"has_object": True}))
        self.assertFalse(has_object_from_status({"has_object": False}))
        self.assertFalse(has_object_from_status(None))

    def test_arm_position_deg_from_motor_sample_values(self) -> None:
        self.assertEqual(
            arm_position_deg_from_telemetry(
                {
                    "motor_samples": [
                        {
                            "device": "left_drive",
                            "values": {"position_deg": 123.0},
                        },
                        {
                            "device": "arm",
                            "values": {"position_deg": "41.5"},
                        },
                    ]
                }
            ),
            41.5,
        )

    def test_arm_position_deg_from_nested_arm_fallback(self) -> None:
        self.assertEqual(
            arm_position_deg_from_telemetry({"arm": {"position_deg": 32}}),
            32.0,
        )

    def test_lift_proof_requires_positive_arm_delta(self) -> None:
        self.assertEqual(
            lift_proof_from_positions(6.0, 24.0, min_delta_deg=15.0),
            (True, "arm_lift_confirmed"),
        )
        self.assertEqual(
            lift_proof_from_positions(6.0, 14.0, min_delta_deg=15.0),
            (False, "arm_delta_too_small"),
        )
        self.assertEqual(
            lift_proof_from_positions(None, 24.0, min_delta_deg=15.0),
            (False, "missing_before_arm_position"),
        )

    def test_ack_helpers_surface_brain_rejections(self) -> None:
        self.assertTrue(ack_state_ok({"state": "ok"}))
        self.assertFalse(
            ack_state_ok({"state": "rejected", "fault": "unknown_command"})
        )
        self.assertEqual(
            ack_rejection_reason({"state": "rejected", "fault": "unknown_command"}),
            "unknown_command",
        )

    def test_capture_artifact_summary_counts_evidence_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            images_dir = out_dir / "images"
            images_dir.mkdir()
            (images_dir / "001.jpg").write_bytes(b"jpg")
            (images_dir / "002.ppm").write_bytes(b"ppm")
            (out_dir / "vex_telemetry.jsonl").write_text("{}\n{}\n")
            (out_dir / "operator_status.jsonl").write_text("{}\n")
            (out_dir / "image-writer.log").write_text("ok\n")
            bag_dir = out_dir / "bag"
            bag_dir.mkdir()
            (bag_dir / "metadata.yaml").write_text("rosbag2_bagfile_information: {}\n")

            summary = capture_artifact_summary(out_dir)

        self.assertEqual(summary["image_count"], 2)
        self.assertTrue(str(summary["first_image"]).endswith("001.jpg"))
        self.assertTrue(str(summary["last_image"]).endswith("002.ppm"))
        self.assertEqual(summary["jsonl_files"]["vex_telemetry.jsonl"], 2)
        self.assertEqual(summary["jsonl_files"]["operator_status.jsonl"], 1)
        self.assertEqual(summary["bag_files"], ["metadata.yaml"])
        self.assertEqual(summary["log_files"], ["image-writer.log"])


if __name__ == "__main__":
    unittest.main()
