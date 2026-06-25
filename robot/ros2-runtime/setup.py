from setuptools import find_packages, setup  # type: ignore[import-untyped]
import os
from glob import glob

package_name = "vexy_ros"

setup(
    name=package_name,
    version="0.3.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (
            os.path.join("share", package_name, "config", "maps"),
            glob("config/maps/*.json"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="David Taylor",
    maintainer_email="dt@davidtaylor.codes",
    description="ROS 2 Jazzy runtime for VEX V5 + Raspberry Pi 5 coprocessor",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "vex_bridge_node = vexy_ros.vex_bridge_node:main",
            "align_to_tag_node = vexy_ros.align_to_tag_node:main",
            "scene_map_node = vexy_ros.scene_map_node:main",
            "yolo_ncnn_node = vexy_ros.yolo_ncnn_node:main",
            "yellow_ball_detector_node = vexy_ros.yellow_ball_detector_node:main",
            "object_indication_node = vexy_ros.object_indication_node:main",
            "task_plan_node = vexy_ros.task_plan_node:main",
            "survey_scan_node = vexy_ros.survey_scan_node:main",
            "vexy_export_contract_jsonl = vexy_ros.evidence_export:main",
            "vexy_tag_action_proof = vexy_ros.tag_action_proof:main",
            "vexy_run_calibrated_tag_proof = vexy_ros.proof_runner:main",
            "vexy_scene_observation_proof = vexy_ros.observation_proof:main",
            "vexy_calibrate_camera = vexy_ros.camera_calibration_capture:main",
        ],
    },
)
