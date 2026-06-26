"""Live integration test — full ball delivery scenario.

Copy to the Pi, source the ROS workspace, then run:
    python3 test_live_deliver.py

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
import unittest

try:
    import rclpy
    from ament_index_python.packages import get_package_share_directory
    from rclpy.node import Node
    from std_msgs.msg import String
    from tf2_msgs.msg import TFMessage
except ModuleNotFoundError as exc:
    raise unittest.SkipTest("ROS 2 Python packages are not installed") from exc

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
    Pose2D,
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
    pathlib.Path(get_package_share_directory("vexy_ros"))
    / "config"
    / "maps"
    / f"{_map_name}.json"
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


FAIL_REASONS = {"disabled", "grab_failed", "unmapped_tag"}

# (method, args, kwargs, timeout_s, is_nav)
STEPS = [
    ("locate_nearest_apriltag", [], {}, 20.0, True),
    ("move_to_tag", [1], {}, 50.0, True),
    ("pickup_ball", [], {"duration_ms": 700}, 35.0, True),
    ("move_to_tag", [0], {}, 50.0, True),
    ("lift", [], {}, 3.0, False),
    ("release", [], {"duration_ms": 650}, 3.0, False),
]


class DeliverTestNode(Node):
    def __init__(self) -> None:
        super().__init__("operator_test_deliver")

        contract = json.loads((FIXTURES / "contract_deliver_ball.json").read_text())
        outline = json.loads((FIXTURES / "outline_deliver_ball.json").read_text())
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
        self.create_subscription(
            String, "/vision/object_indications", self._on_objects, 10
        )
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
            robot_from_tag = robot_from_camera_pose(
                camera_from_tag, self.camera_in_robot
            )
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
            VisionSnapshot(
                stamp_s=stamp_s, tags=dict(self._tags), objects=self._objects
            )
        )

    def _on_objects(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            return
        objects: list[ObjectObservation] = []
        stamp_s = time.monotonic()
        for item in payload:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "object"))
            if "forward_m" not in item or "left_m" not in item:
                continue
            camera_from_object = Pose2D(
                float(item.get("forward_m", 0.0)),
                float(item.get("left_m", 0.0)),
                float(item.get("yaw_rad", 0.0)),
            )
            robot_from_object = robot_from_camera_pose(
                camera_from_object, self.camera_in_robot
            )
            objects.append(
                ObjectObservation(
                    name=name,
                    category=name,
                    stamp_s=float(item.get("stamp_s", stamp_s)),
                    forward_m=robot_from_object.x_m,
                    left_m=robot_from_object.y_m,
                    confidence=(
                        float(item["confidence"])
                        if item.get("confidence") is not None
                        else None
                    ),
                    source=str(item.get("source", "object_indications")),
                )
            )
        self._objects = tuple(objects)
        self.op.update_vision(
            VisionSnapshot(
                stamp_s=stamp_s, tags=dict(self._tags), objects=self._objects
            )
        )

    def _on_telemetry(self, msg: String) -> None:
        try:
            raw = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        self.op.update_telemetry(telemetry_snapshot_from_mapping(raw))

    def run(self) -> bool:
        print(
            "=== deliver test: locate → approach ball → grab → approach bin → lift → release ==="
        )
        for method, args, kwargs, timeout_s, is_nav in STEPS:
            kw_str = f"  kwargs={kwargs}" if kwargs else ""
            print(f"[{method}]{kw_str}")
            if is_nav:
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
            else:
                result = getattr(self.op, method)(*args, **kwargs)
                print(f"  CMD sent  success={result.success}  reason={result.reason!r}")
                deadline = time.monotonic() + 3.0
                while time.monotonic() < deadline:
                    rclpy.spin_once(self, timeout_sec=0.02)
        print("=== deliver test PASSED ===")
        return True


def main() -> None:
    print("=== pre-flight: camera stack ===")
    if not ensure_stack_running():
        sys.exit(1)
    rclpy.init()
    node = DeliverTestNode()
    try:
        ok = node.run()
        sys.exit(0 if ok else 1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
