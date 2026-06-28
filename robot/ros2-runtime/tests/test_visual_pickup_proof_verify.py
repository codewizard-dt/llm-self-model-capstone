from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vexy_ros.visual_pickup_proof_verify import (  # noqa: E402
    main,
    verify_visual_pickup_proof,
)


class VisualPickupProofVerifyTests(unittest.TestCase):
    def test_complete_artifacts_still_require_visual_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture_dir = _write_capture_dir(Path(tmp))
            verdict = verify_visual_pickup_proof(
                _successful_result(capture_dir),
                result_path=capture_dir / "probe-result.json",
                visual_confirmed=False,
            )

        self.assertEqual(verdict["status"], "failed")
        self.assertEqual(verdict["reason"], "visual_confirmed")

    def test_successful_result_with_visual_confirmation_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture_dir = _write_capture_dir(Path(tmp))
            verdict = verify_visual_pickup_proof(
                _successful_result(capture_dir),
                result_path=capture_dir / "probe-result.json",
                visual_confirmed=True,
            )

        self.assertEqual(verdict["status"], "succeeded")
        self.assertEqual(verdict["reason"], "grab_and_lift_proven")

    def test_arm_delta_too_small_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture_dir = _write_capture_dir(Path(tmp))
            result = _successful_result(capture_dir)
            result["attempts"][0]["lift_result"]["after_arm_position_deg"] = 10.0

            verdict = verify_visual_pickup_proof(
                result,
                result_path=capture_dir / "probe-result.json",
                visual_confirmed=True,
            )

        self.assertEqual(verdict["status"], "failed")
        self.assertEqual(verdict["reason"], "arm_delta_confirmed")

    def test_cli_writes_verdict_and_uses_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture_dir = _write_capture_dir(Path(tmp))
            result_path = capture_dir / "probe-result.json"
            result_path.write_text(json.dumps(_successful_result(capture_dir)))
            output_path = capture_dir / "verdict.json"

            with contextlib.redirect_stdout(io.StringIO()):
                code = main(
                    [
                        "--result",
                        str(result_path),
                        "--visual-confirmed",
                        "--output",
                        str(output_path),
                    ]
                )

            verdict = json.loads(output_path.read_text())
        self.assertEqual(code, 0)
        self.assertEqual(verdict["status"], "succeeded")


def _write_capture_dir(root: Path) -> Path:
    capture_dir = root / "vexy-visual-pickup-lift-test"
    images_dir = capture_dir / "images"
    bag_dir = capture_dir / "bag"
    images_dir.mkdir(parents=True)
    bag_dir.mkdir()
    (images_dir / "0001.jpg").write_bytes(b"jpg")
    for name in (
        "operator_status.jsonl",
        "vex_telemetry.jsonl",
        "vision_object_detections.jsonl",
    ):
        (capture_dir / name).write_text("{}\n")
    (bag_dir / "metadata.yaml").write_text("rosbag2_bagfile_information: {}\n")
    return capture_dir


def _successful_result(capture_dir: Path) -> dict[str, object]:
    return {
        "type": "visual_pickup_probe_result",
        "status": "succeeded",
        "reason": "arm_lift_confirmed",
        "attempts": [
            {
                "status": "succeeded",
                "reason": "has_object_true",
                "latest_status": {"has_object": True},
                "lift_result": {
                    "status": "succeeded",
                    "reason": "arm_lift_confirmed",
                    "before_arm_position_deg": 6.0,
                    "after_arm_position_deg": 28.0,
                    "min_arm_delta_deg": 15.0,
                },
            }
        ],
        "capture": {
            "out_dir": str(capture_dir),
            "image_count": 1,
            "last_image": str(capture_dir / "images" / "0001.jpg"),
            "jsonl_files": {
                "operator_status.jsonl": 1,
                "vex_telemetry.jsonl": 1,
                "vision_object_detections.jsonl": 1,
            },
            "bag_files": ["metadata.yaml"],
        },
    }


if __name__ == "__main__":
    unittest.main()
