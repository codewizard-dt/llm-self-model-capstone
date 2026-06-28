from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vexy_ros.visual_pickup_probe import (  # noqa: E402
    best_ball_detection,
    has_object_from_status,
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
                        {"label": "yellow_ball", "confidence": 1.0, "bbox_xyxy": [1, 2]},
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


if __name__ == "__main__":
    unittest.main()
