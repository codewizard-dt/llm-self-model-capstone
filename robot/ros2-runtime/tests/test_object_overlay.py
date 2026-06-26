from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.object_detection import Detection
from vexy_ros.object_overlay_node import draw_detections

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - depends on local ROS/NumPy env
    np = None


class ObjectOverlayTests(unittest.TestCase):
    @unittest.skipIf(np is None, "numpy is not installed")
    def test_draws_detection_box_on_frame_copy(self) -> None:
        frame = np.zeros((80, 100, 3), dtype=np.uint8)
        detection = Detection(
            label="yellow_ball",
            class_id=0,
            confidence=0.91,
            bbox_xyxy=(10.0, 20.0, 40.0, 60.0),
        )

        overlay = draw_detections(frame, [detection])

        self.assertFalse(np.array_equal(frame, overlay))
        self.assertEqual(frame[20, 10].tolist(), [0, 0, 0])
        self.assertEqual(overlay[20, 10].tolist(), [0, 255, 0])


if __name__ == "__main__":
    sys.exit(unittest.main())
