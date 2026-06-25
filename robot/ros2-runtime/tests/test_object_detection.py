from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.object_detection import (
    CameraIntrinsics,
    Detection,
    indications_from_detections,
    intrinsics_from_camera_info,
    parse_detections_payload,
    parse_dimensions_json,
)


class ObjectDetectionTests(unittest.TestCase):
    def test_builds_camera_relative_indication_from_bbox_and_intrinsics(self) -> None:
        detections = [
            Detection(
                label="bin",
                class_id=0,
                confidence=0.9,
                bbox_xyxy=(280.0, 180.0, 360.0, 280.0),
            )
        ]
        dimensions = parse_dimensions_json('{"bin":{"height_m":0.20}}')

        indications = indications_from_detections(
            detections,
            intrinsics=CameraIntrinsics(fx=560.0, fy=560.0, cx=320.0, cy=240.0),
            dimensions=dimensions,
            min_confidence=0.35,
        )

        self.assertEqual(indications[0]["name"], "bin")
        self.assertAlmostEqual(indications[0]["forward_m"], 1.12)
        self.assertAlmostEqual(indications[0]["left_m"], -0.0)
        self.assertEqual(indications[0]["source"], "yolo_ncnn")

    def test_yellow_ball_dimension_maps_from_alias_label(self) -> None:
        detections = [
            Detection(
                label="yellow_ball",
                class_id=0,
                confidence=0.9,
                bbox_xyxy=(300.0, 200.0, 340.0, 240.0),
            )
        ]
        dimensions = parse_dimensions_json('{"yellow_ball":{"diameter_m":0.065}}')

        indications = indications_from_detections(
            detections,
            intrinsics=CameraIntrinsics(fx=560.0, fy=560.0, cx=320.0, cy=240.0),
            dimensions=dimensions,
            min_confidence=0.35,
            source="yellow_ball_color",
        )

        self.assertEqual(indications[0]["name"], "yellow_ball")
        self.assertEqual(indications[0]["source"], "yellow_ball_color")
        self.assertAlmostEqual(indications[0]["forward_m"], 0.91)

    def test_filters_low_confidence_and_uses_default_height(self) -> None:
        detections = [
            Detection(
                label="unknown",
                class_id=99,
                confidence=0.2,
                bbox_xyxy=(10.0, 10.0, 20.0, 20.0),
            ),
            Detection(
                label="unknown",
                class_id=99,
                confidence=0.8,
                bbox_xyxy=(300.0, 200.0, 340.0, 260.0),
            ),
        ]

        indications = indications_from_detections(
            detections,
            intrinsics=CameraIntrinsics(fx=500.0, fy=500.0, cx=320.0, cy=240.0),
            dimensions={},
            default_height_m=0.12,
            min_confidence=0.35,
        )

        self.assertEqual(len(indications), 1)
        self.assertAlmostEqual(indications[0]["forward_m"], 1.0)

    def test_parses_detection_payload_and_camera_info(self) -> None:
        raw = json.dumps(
            {
                "detections": [
                    {
                        "label": "cup",
                        "class_id": 41,
                        "confidence": 0.7,
                        "bbox_xywh": [10, 20, 30, 40],
                    }
                ]
            }
        )

        parsed = parse_detections_payload(raw)
        intrinsics = intrinsics_from_camera_info(
            [558.0, 0.0, 421.0, 0.0, 557.0, 251.0, 0.0, 0.0, 1.0]
        )

        self.assertEqual(parsed[0].bbox_xyxy, (10.0, 20.0, 40.0, 60.0))
        self.assertEqual(intrinsics.cx, 421.0)


if __name__ == "__main__":
    unittest.main()
