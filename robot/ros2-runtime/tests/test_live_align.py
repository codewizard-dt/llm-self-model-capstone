"""Live integration test — align scenario.

Copy to the Pi, source the ROS workspace, then run:
    python3 test_live_align.py

Starts vexy-ros-stack.service if not already running.
Requires Brain slot 8 running and AprilTags physically visible to the camera.
Exits 0 on success, 1 on failure or timeout.
"""

import json
import math
import os
import pathlib
import subprocess
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from tf2_msgs.msg import TFMessage

from ament_index_python.packages import get_package_share_directory
from vexy_ros.operator.node import RosCommandSink
from vexy_ros.operator.core import (
    MAX_TAG_ID,
    MIN_TAG_ID,
    ObjectObservation,
    Operator,
    TagObservation,
    VisionSnapshot,
    telemetry_snapshot_from_mapping,
)
from vexy_ros.vision_map import (
    DEFAULT_CAMERA_IN_ROBOT,
    camera_from_apriltag_translation,
    parse_tag_anchors,
    pose_from_mapping,
    robot_from_camera_pose,
    tag_id_from_frame_id,
)

HERE = pathlib.Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"

_map_name = os.environ.get("VEXY_MAP", "gen0-grab-toss-v1")
MAP_FILE = (
    pathlib.Path(get_package_share_directory("vexy_ros")) / "config" / "maps" / f"{_map_name}.json"
)

STACK_SERVICE = "vexy-ros-stack.service"


def ensure_stack_running() -> bool:
    r = subprocess.run(
        ["systemctl", "--user", "is-active", STACK_SERVICE],
        capture_output=True,
        text=True,
    )
    if r.stdout.strip() == "active":
        print(f"  {STACK_SERVICE} already active.")
    else:
        print(f"  Starting {STACK_SERVICE}...")
        subprocess.run(["systemctl", "--user", "restart", STACK_SERVICE], check=True)
        print("  Waiting 10 s for stack warmup...")
        time.sleep(10)
    return True


FAIL_REASONS = {"stuck", "spinout", "disabled", "unmapped_tag"}

# (method, args, kwargs, timeout_s)
STEPS = [
    ("locate_nearest_apriltag", [], {}, 20.0),
    ("orient_to_tag", [0], {}, 15.0),
    ("move_to_tag", [0], {"target_distance_m": 0.4064}, 20.0),
]


class AlignTestNode(Node):
    def __init__(self) -> None:
        super().__init__("operator_test_align")

        contract = json.loads((FIXTURES / "contract_align_minimal.json").read_text())
        outline = json.loads((FIXTURES / "outline_align_only.json").read_text())
        april_tag_map = parse_tag_anchors(MAP_FILE.read_text())
        camera_in_robot = pose_from_mapping(json.loads(DEFAULT_CAMERA_IN_ROBOT))

        self._tags: dict[int, TagObservation] = {}
        self._objects: tuple[ObjectObservation, ...] = ()
        self.camera_in_robot = camera_in_robot

        sink = RosCommandSink(self)
        self.op = Operator(
            sink,
            april_tag_map=april_tag_map,
            camera_in_robot=camera_in_robot,
            task_contract=contract,
            task_outline=outline,
            event_sink=lambda e: print(f"  event: {e.name}  {e.detail}"),
        )

        self.create_subscription(TFMessage, "/tf", self._on_tf, 10)
        self.create_subscription(String, "/vex/telemetry", self._on_telemetry, 10)

    def _on_tf(self, msg: TFMessage) -> None:
        stamp_s = time.monotonic()
        for stamped in msg.transforms:
            tag_id = tag_id_from_frame_id(stamped.child_frame_id)
            if tag_id is None or not MIN_TAG_ID <= tag_id <= MAX_TAG_ID:
                continue
            translation = stamped.transform.translation
            camera_from_tag = camera_from_apriltag_translation(
                optical_x_m=float(translation.x),
                optical_z_m=float(translation.z),
            )
            robot_from_tag = robot_from_camera_pose(camera_from_tag, self.camera_in_robot)
            if robot_from_tag.x_m <= 0.05:
                continue
            self._tags[tag_id] = TagObservation(
                tag_id=tag_id,
                stamp_s=stamp_s,
                forward_m=robot_from_tag.x_m,
                left_m=robot_from_tag.y_m,
                distance_m=math.hypot(robot_from_tag.x_m, robot_from_tag.y_m),
                yaw_rad=math.atan2(robot_from_tag.y_m, robot_from_tag.x_m),
            )
        self.op.update_vision(
            VisionSnapshot(stamp_s=stamp_s, tags=dict(self._tags), objects=self._objects)
        )

    def _on_telemetry(self, msg: String) -> None:
        try:
            raw = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        self.op.update_telemetry(telemetry_snapshot_from_mapping(raw))

    def run(self) -> bool:
        print("=== align test: locate → orient → approach ===")
        for method, args, kwargs, timeout_s in STEPS:
            kw_str = f"  kwargs={kwargs}" if kwargs else ""
            print(f"[{method}]{kw_str}")
            deadline = time.monotonic() + timeout_s
            succeeded = False
            while time.monotonic() < deadline:
                rclpy.spin_once(self, timeout_sec=0.02)
                result = getattr(self.op, method)(*args, **kwargs)
                if result.success:
                    print(f"  OK  {result.reason}")
                    succeeded = True
                    break
                if result.reason in FAIL_REASONS:
                    print(f"  FAIL  {result.reason}")
                    return False
            if not succeeded:
                print(f"  TIMEOUT after {timeout_s}s")
                return False
        print("=== align test PASSED ===")
        return True


def main() -> None:
    print("=== pre-flight: camera stack ===")
    if not ensure_stack_running():
        sys.exit(1)
    rclpy.init()
    node = AlignTestNode()
    try:
        ok = node.run()
        sys.exit(0 if ok else 1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
