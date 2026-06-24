from setuptools import find_packages, setup  # type: ignore[import-untyped]
import os
from glob import glob

package_name = "vexy_ros"

setup(
    name=package_name,
    version="0.2.0",
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
            "vexy_export_contract_jsonl = vexy_ros.evidence_export:main",
        ],
    },
)
