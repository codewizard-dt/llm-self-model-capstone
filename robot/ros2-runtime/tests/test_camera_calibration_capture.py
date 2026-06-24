from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vexy_ros.camera_calibration_capture import (  # noqa: E402
    build_parser,
    camera_info_yaml,
    main,
)


class CameraCalibrationCaptureTests(unittest.TestCase):
    def test_camera_info_yaml_matches_ros_camera_info_shape(self) -> None:
        text = camera_info_yaml(
            width=640,
            height=480,
            camera_name="imx708_wide",
            camera_matrix=[430.0, 0.0, 320.0, 0.0, 431.0, 240.0, 0.0, 0.0, 1.0],
            distortion_coefficients=[-0.2, 0.03, 0.0, 0.0, 0.0],
            rectification_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
            projection_matrix=[
                430.0,
                0.0,
                320.0,
                0.0,
                0.0,
                431.0,
                240.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
            ],
        )

        self.assertIn("image_width: 640", text)
        self.assertIn("image_height: 480", text)
        self.assertIn("camera_name: imx708_wide", text)
        self.assertIn("distortion_model: plumb_bob", text)
        self.assertIn("camera_matrix:", text)
        self.assertIn("projection_matrix:", text)
        self.assertIn("data: [430", text)

    def test_parser_defaults_match_documented_checkerboard(self) -> None:
        args = build_parser().parse_args([])

        self.assertEqual(args.image_topic, "/camera/image_raw")
        self.assertEqual(args.cols, 8)
        self.assertEqual(args.rows, 6)
        self.assertEqual(args.square_m, 0.025)
        self.assertEqual(args.camera_name, "imx708_wide")

    def test_invalid_geometry_exits_before_ros_runtime_required(self) -> None:
        self.assertEqual(main(["--cols", "0"]), 2)
        self.assertEqual(main(["--square-m", "0"]), 2)
        self.assertEqual(main(["--samples", "2"]), 2)

    def test_setup_declares_camera_calibration_entrypoint(self) -> None:
        setup_text = (ROOT / "setup.py").read_text()

        ast.parse(setup_text)
        self.assertIn(
            "vexy_calibrate_camera = vexy_ros.camera_calibration_capture:main",
            setup_text,
        )

    def test_live_camera_bgra_encoding_is_supported(self) -> None:
        source = (
            ROOT / "src" / "vexy_ros" / "camera_calibration_capture.py"
        ).read_text()

        self.assertIn('"bgra8"', source)
        self.assertIn("COLOR_BGRA2GRAY", source)


if __name__ == "__main__":
    unittest.main()
