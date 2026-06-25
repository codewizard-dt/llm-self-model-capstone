from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.yolo_ncnn_node import image_to_bgr_array

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - depends on local ROS/NumPy env
    np = None


class ImageConversionTests(unittest.TestCase):
    @unittest.skipIf(np is None, "numpy is not installed")
    def test_bgra8_drops_alpha_and_keeps_bgr_order(self) -> None:
        msg = SimpleNamespace(
            encoding="bgra8",
            height=1,
            width=2,
            data=bytes([1, 2, 3, 255, 4, 5, 6, 128]),
        )

        frame = image_to_bgr_array(msg)

        self.assertEqual(frame.shape, (1, 2, 3))
        self.assertEqual(frame[0, 0].tolist(), [1, 2, 3])
        self.assertEqual(frame[0, 1].tolist(), [4, 5, 6])

    @unittest.skipIf(np is None, "numpy is not installed")
    def test_rgba8_converts_to_bgr_order(self) -> None:
        msg = SimpleNamespace(
            encoding="rgba8",
            height=1,
            width=1,
            data=bytes([10, 20, 30, 255]),
        )

        frame = image_to_bgr_array(msg)

        self.assertEqual(frame[0, 0].tolist(), [30, 20, 10])


if __name__ == "__main__":
    unittest.main()
