from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.localization_benchmark import summarize_localization_samples


class LocalizationBenchmarkTests(unittest.TestCase):
    def test_summarizes_camera_source_transform_and_residuals(self) -> None:
        summary = summarize_localization_samples(
            [
                {
                    "observed_tag_ids": [0, 1],
                    "localization": {
                        "tag_residual_m": 0.04,
                        "tag_residual_deg": 4.0,
                    },
                },
                {
                    "observed_tag_ids": [1, 2],
                    "localization": {
                        "tag_residual_m": 0.06,
                        "tag_residual_deg": 6.0,
                    },
                },
            ],
            camera_info_url="file:///tmp/camera.yaml",
            camera_in_robot_json='{"x_m":-0.3302,"y_m":0.1143,"yaw_rad":0.0}',
            map_name="gen0-grab-toss-v1",
            accepted_position_error_m=0.10,
            accepted_heading_error_deg=8.0,
        )

        self.assertEqual(summary["observed_tag_ids"], [0, 1, 2])
        self.assertAlmostEqual(summary["mean_position_error_m"], 0.05)
        self.assertAlmostEqual(summary["mean_heading_error_deg"], 5.0)
        self.assertTrue(summary["accepted_for_demo"])
        self.assertEqual(summary["camera_in_robot"]["x_m"], -0.3302)


if __name__ == "__main__":
    unittest.main()
