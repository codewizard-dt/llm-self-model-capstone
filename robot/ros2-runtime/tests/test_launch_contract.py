from __future__ import annotations

import ast
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LaunchContractTests(unittest.TestCase):
    def test_launch_file_declares_rectified_tag_pipeline(self) -> None:
        launch_text = (ROOT / "launch" / "vexy.launch.py").read_text()

        ast.parse(launch_text)
        self.assertIn("camera_info_url", launch_text)
        self.assertIn("FrameDurationLimits", launch_text)
        self.assertIn("camera_info_url is required", launch_text)
        self.assertIn("camera_info_url must be a URL", launch_text)
        self.assertIn('package="image_proc"', launch_text)
        self.assertIn('executable="rectify_node"', launch_text)
        self.assertIn('("image", "/camera/image_raw")', launch_text)
        self.assertIn('("image_rect", "/camera/image_rect")', launch_text)
        self.assertIn('package="apriltag_ros"', launch_text)
        self.assertIn('executable="apriltag_node"', launch_text)
        self.assertIn('("detections", "/apriltag/detections")', launch_text)
        self.assertIn('executable="scene_map_node"', launch_text)
        self.assertIn("workspace_map_path", launch_text)
        self.assertIn("table-grab-toss-v1.json", launch_text)
        self.assertIn("camera_in_robot_json", launch_text)
        self.assertIn('executable="align_to_tag_node"', launch_text)

    def test_apriltag_config_names_the_expected_first_proof_tag(self) -> None:
        config_text = (ROOT / "config" / "apriltag_36h11.yaml").read_text()

        self.assertIn("apriltag:", config_text)
        self.assertIn("family: 36h11", config_text)
        self.assertIn("size: 0.200", config_text)
        self.assertIn("refine: true", config_text)
        self.assertIn("ids: [0]", config_text)
        self.assertIn("frames: [tag36h11_0]", config_text)
        self.assertIn("sizes: [0.200]", config_text)

    def test_camera_info_config_is_nonzero_and_marked_as_starter(self) -> None:
        config_text = (ROOT / "config" / "imx708_wide_640x480.yaml").read_text()

        self.assertIn(
            "Replace this with a measured camera_calibration output", config_text
        )
        self.assertIn("camera_matrix:", config_text)
        self.assertIn("data: [430.0, 0.0, 320.0", config_text)
        self.assertIn("distortion_coefficients:", config_text)

    def test_package_declares_runtime_dependencies_and_config_install(self) -> None:
        package = ET.parse(ROOT / "package.xml").getroot()
        exec_depends = {node.text for node in package.findall("exec_depend")}
        setup_text = (ROOT / "setup.py").read_text()

        self.assertIn("apriltag_ros", exec_depends)
        self.assertIn("apriltag_msgs", exec_depends)
        self.assertIn("image_proc", exec_depends)
        self.assertIn('glob("config/*.yaml")', setup_text)
        self.assertIn('glob("config/maps/*.json")', setup_text)
        self.assertIn("align_to_tag_node = vexy_ros.align_to_tag_node:main", setup_text)
        self.assertIn("scene_map_node = vexy_ros.scene_map_node:main", setup_text)
        self.assertIn(
            "vexy_export_contract_jsonl = vexy_ros.evidence_export:main", setup_text
        )


if __name__ == "__main__":
    sys.exit(unittest.main())
