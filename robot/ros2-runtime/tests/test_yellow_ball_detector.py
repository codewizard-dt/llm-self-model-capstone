from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.yellow_ball_detector_node import detect_yellow_balls

try:
    import cv2
except ModuleNotFoundError:  # pragma: no cover - depends on local ROS/OpenCV env
    cv2 = None


class YellowBallDetectorTests(unittest.TestCase):
    @staticmethod
    def _bgr_from_hsv(hue: int, saturation: int, value: int):
        import numpy as np

        hsv_pixel = np.array([[[hue, saturation, value]]], dtype=np.uint8)
        return tuple(
            int(channel) for channel in cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2BGR)[0, 0]
        )

    @unittest.skipIf(cv2 is None, "opencv-python is not installed")
    def test_detects_synthetic_yellow_ball(self) -> None:
        import numpy as np

        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.circle(frame, (160, 120), 30, (0, 255, 255), -1)

        detections = detect_yellow_balls(frame, stamp_s=12.0)

        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].label, "yellow_ball")
        self.assertGreater(detections[0].confidence, 0.6)
        self.assertLessEqual(detections[0].bbox_xyxy[0], 132.0)
        self.assertGreaterEqual(detections[0].bbox_xyxy[2], 188.0)

    @unittest.skipIf(cv2 is None, "opencv-python is not installed")
    def test_rejects_tiny_yellow_noise(self) -> None:
        import numpy as np

        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.circle(frame, (160, 120), 3, (0, 255, 255), -1)

        detections = detect_yellow_balls(frame, min_area_px=80.0)

        self.assertEqual(detections, [])

    @unittest.skipIf(cv2 is None, "opencv-python is not installed")
    def test_prefers_ball_over_warmer_yellow_box_graphic(self) -> None:
        import numpy as np

        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        triangle = np.array([[120, 160], [235, 120], [235, 195]], dtype=np.int32)
        cv2.fillPoly(frame, [triangle], self._bgr_from_hsv(6, 150, 190))
        cv2.circle(frame, (225, 150), 34, self._bgr_from_hsv(24, 220, 225), -1)

        detections = detect_yellow_balls(frame)

        self.assertEqual(len(detections), 1)
        x1, y1, x2, y2 = detections[0].bbox_xyxy
        self.assertGreaterEqual(x1, 185.0)
        self.assertLessEqual(x2, 260.0)
        self.assertGreaterEqual(y1, 115.0)
        self.assertLessEqual(y2, 185.0)

    @unittest.skipIf(cv2 is None, "opencv-python is not installed")
    def test_rejects_low_saturation_elongated_wall_patch(self) -> None:
        import numpy as np

        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        patch_color = self._bgr_from_hsv(24, 45, 170)
        cv2.ellipse(frame, (145, 95), (20, 54), 5, 0, 360, patch_color, -1)

        detections = detect_yellow_balls(frame, hsv_lower=(20, 25, 80))
        self.assertEqual(len(detections), 1)
        self.assertEqual(detect_yellow_balls(frame), [])

    @unittest.skipIf(cv2 is None, "opencv-python is not installed")
    def test_hsv_range_can_be_overridden_for_warmer_yellow_targets(self) -> None:
        import numpy as np

        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.circle(frame, (160, 120), 30, self._bgr_from_hsv(14, 180, 210), -1)

        self.assertEqual(detect_yellow_balls(frame), [])
        detections = detect_yellow_balls(frame, hsv_lower=(10, 25, 60))

        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].label, "yellow_ball")

    @unittest.skipIf(cv2 is None, "opencv-python is not installed")
    def test_returns_largest_valid_contour_by_default(self) -> None:
        import numpy as np

        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        yellow = self._bgr_from_hsv(24, 220, 225)
        cv2.circle(frame, (80, 120), 12, yellow, -1)
        cv2.circle(frame, (220, 120), 34, yellow, -1)

        detections = detect_yellow_balls(frame)

        self.assertEqual(len(detections), 1)
        self.assertGreaterEqual(detections[0].bbox_xyxy[0], 185.0)

    @unittest.skipIf(cv2 is None, "opencv-python is not installed")
    def test_can_return_multiple_yellow_balls_with_debug_metadata(self) -> None:
        import numpy as np

        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        yellow = self._bgr_from_hsv(24, 220, 225)
        for center in ((70, 120), (160, 120), (250, 120)):
            cv2.circle(frame, center, 22, yellow, -1)

        detections = detect_yellow_balls(frame, max_detections=5)

        self.assertEqual(len(detections), 3)
        payload = detections[0].to_json()
        self.assertEqual(payload["source"], "yellow_hsv")
        self.assertIn("area_px", payload)
        self.assertIn("circularity", payload)
        self.assertIn("fill_ratio", payload)


if __name__ == "__main__":
    unittest.main()
