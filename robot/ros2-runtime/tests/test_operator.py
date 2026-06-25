from __future__ import annotations

import importlib
import json
import math
import sys
import time
import types
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[1] / "contracts" / "src"))

from vexy_ros.operator.core import (  # noqa: E402
    MotorSample,
    Operator,
    OperatorEvent,
    PacketCommandSink,
    TagObservation,
    TelemetrySnapshot,
    VisionSnapshot,
    telemetry_snapshot_from_mapping,
)
from vexy_ros.vision_map import Pose2D, TagAnchor  # noqa: E402


APRIL_TAG_MAP = {
    tag_id: TagAnchor(tag_id, Pose2D(float(tag_id), 0.0, 0.0)) for tag_id in range(15)
}
TASK_CONTRACT = {
    "schema_version": "1.0",
    "session_id": "operator-test",
    "generation": 0,
    "round": 0,
    "task": "operator_test",
    "motor_samples": [{"device": "left_drive"}],
    "predicted": {"success": True},
    "gap": {"distance_error_m": 0.0},
}
TASK_OUTLINE = (
    ("locate_nearest_apriltag", ()),
    ("orient_to_tag", (0,)),
    ("move_to_tag", (1,)),
    ("grab", (), {"duration_ms": 700}),
    ("lift", ()),
    ("release", ()),
)


def make_operator(
    sink: PacketCommandSink,
    *,
    clock: Any = time.monotonic,
    event_sink: Any = None,
) -> Operator:
    return Operator(
        sink,
        april_tag_map=APRIL_TAG_MAP,
        camera_in_robot=Pose2D(0.0, -0.08, 0.0),
        task_contract=TASK_CONTRACT,
        task_outline=TASK_OUTLINE,
        clock=clock,
        event_sink=event_sink,
    )


class OperatorCoreTests(unittest.TestCase):
    def test_tag_abstractions_take_zero_based_index_argument(self) -> None:
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0)

        for tag_id in range(15):
            self.assertFalse(hasattr(operator, f"orient_to_tag_{tag_id}"))
            self.assertFalse(hasattr(operator, f"move_to_tag_{tag_id}"))
        self.assertTrue(callable(operator.orient_to_tag))
        self.assertTrue(callable(operator.move_to_tag))

    def test_operator_requires_apriltag_map_and_task_contract(self) -> None:
        sink = PacketCommandSink()
        with self.assertRaises(ValueError):
            Operator(
                sink,
                april_tag_map={},
                camera_in_robot=Pose2D(0.0, 0.0, 0.0),
                task_contract=TASK_CONTRACT,
            )
        with self.assertRaises(ValueError):
            Operator(
                sink,
                april_tag_map=APRIL_TAG_MAP,
                camera_in_robot=Pose2D(0.0, 0.0, 0.0),
                task_contract={},
                task_outline=TASK_OUTLINE,
            )
        with self.assertRaises(ValueError):
            Operator(
                sink,
                april_tag_map=APRIL_TAG_MAP,
                camera_in_robot=Pose2D(0.0, 0.0, 0.0),
                task_contract=TASK_CONTRACT,
            )

    def test_task_contract_requires_operator_method_tuples_not_primitives(self) -> None:
        sink = PacketCommandSink()
        with self.assertRaises(ValueError):
            Operator(
                sink,
                april_tag_map=APRIL_TAG_MAP,
                camera_in_robot=Pose2D(0.0, 0.0, 0.0),
                task_contract=TASK_CONTRACT,
                task_outline=(("drive", ()),),
            )
        with self.assertRaises(ValueError):
            Operator(
                sink,
                april_tag_map=APRIL_TAG_MAP,
                camera_in_robot=Pose2D(0.0, 0.0, 0.0),
                task_contract=TASK_CONTRACT,
                task_outline=(("move_to_tag", ()),),
            )
        operator = Operator(
            sink,
            april_tag_map=APRIL_TAG_MAP,
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=TASK_OUTLINE,
        )
        self.assertEqual(
            operator.task_contract.method_plan[0], ("locate_nearest_apriltag", (), {})
        )
        self.assertEqual(operator.task_contract.method_plan[2][0], "move_to_tag")
        self.assertIn("move_to_tag", operator.allowed_operator_methods)

    def test_operator_method_allowlist_comes_from_task_outline(self) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map=APRIL_TAG_MAP,
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=(("move_to_tag", (1,), {"target_distance_m": 0.45}),),
        )

        operator.require_allowed_method("move_to_tag")
        with self.assertRaises(ValueError):
            operator.require_allowed_method("grab")

    def test_operator_uses_loaded_map_as_available_tag_set(self) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={0: APRIL_TAG_MAP[0]},
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=TASK_OUTLINE,
            clock=lambda: 10.0,
        )
        self.assertEqual(operator.available_april_tag_ids, (0,))
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={
                    0: TagObservation(0, 9.9, forward_m=1.0, left_m=0.0),
                    1: TagObservation(1, 9.9, forward_m=0.2, left_m=0.0),
                },
            )
        )

        result = operator.locate_nearest_apriltag()

        self.assertTrue(result.success)
        self.assertEqual(result.tag.tag_id if result.tag else None, 0)
        with self.assertRaises(ValueError):
            operator.move_to_tag(1)

    def test_locate_nearest_apriltag_uses_fresh_distance(self) -> None:
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0)
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={
                    0: TagObservation(0, 9.9, forward_m=1.0, left_m=0.0),
                    2: TagObservation(2, 9.9, forward_m=0.4, left_m=0.1),
                },
            )
        )

        result = operator.locate_nearest_apriltag()

        self.assertTrue(result.success)
        self.assertEqual(result.tag.tag_id if result.tag else None, 2)
        self.assertEqual(sink.packets, [])
        self.assertEqual(result.localization_source, "apriltag")
        self.assertIsNotNone(result.map_pose)

    def test_move_to_tag_derives_standoff_from_loaded_map_role(self) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={0: TagAnchor(0, Pose2D(0.8, 0.0, math.pi / 2), "bin")},
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=(("move_to_tag", (0,)),),
            clock=lambda: 10.0,
        )
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={0: TagObservation(0, 9.9, forward_m=0.8, left_m=0.0)},
            )
        )

        result = operator.move_to_tag(0)

        self.assertEqual(result.reason, "moving_to_tag")
        self.assertAlmostEqual(result.target_distance_m, 0.38)
        self.assertIsNotNone(result.target_pose)
        self.assertAlmostEqual(result.target_pose.x_m, 0.8)
        self.assertAlmostEqual(result.target_pose.y_m, 0.38)

    def test_pose_is_estimated_from_visible_mapped_apriltags(self) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={0: TagAnchor(0, Pose2D(2.0, 0.0, 0.0))},
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=TASK_OUTLINE,
            clock=lambda: 10.0,
        )

        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={0: TagObservation(0, 9.9, forward_m=1.0, left_m=0.0)},
            )
        )

        pose = operator.current_pose()
        self.assertEqual(operator.localization_source, "apriltag")
        self.assertIsNotNone(pose)
        self.assertAlmostEqual(pose.x_m, 1.0)
        self.assertAlmostEqual(pose.y_m, 0.0)

    def test_pose_dead_reckons_when_no_apriltags_are_visible(self) -> None:
        now = 10.0

        def clock() -> float:
            return now

        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={0: TagAnchor(0, Pose2D(2.0, 0.0, 0.0))},
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=TASK_OUTLINE,
            clock=clock,
        )
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={0: TagObservation(0, 9.9, forward_m=1.0, left_m=0.0)},
            )
        )
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={0: TagObservation(0, 9.9, forward_m=0.8, left_m=0.0)},
            )
        )
        operator.move_to_tag(0, target_distance_m=0.4)
        now = 10.1
        operator.update_vision(VisionSnapshot(stamp_s=10.1, tags={}))

        pose = operator.current_pose()
        self.assertEqual(operator.localization_source, "dead_reckoning")
        self.assertIsNotNone(pose)
        self.assertGreater(pose.x_m, 1.0)

    def test_orient_wrapper_sends_turn_then_stop(self) -> None:
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0)
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={1: TagObservation(1, 9.9, forward_m=1.0, left_m=0.2)},
            )
        )

        result = operator.orient_to_tag(1)

        self.assertFalse(result.success)
        self.assertEqual(sink.packets[-1]["cmd"], "turn")
        self.assertEqual(sink.packets[-1]["reason"], "orient_to_tag_1")

        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={1: TagObservation(1, 9.9, forward_m=1.0, left_m=0.0)},
            )
        )
        result = operator.orient_to_tag(1)

        self.assertTrue(result.success)
        self.assertEqual(sink.packets[-1]["cmd"], "stop")

    def test_move_to_tag_reports_spinout_event_from_high_wheel_no_progress(
        self,
    ) -> None:
        events: list[OperatorEvent] = []
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0, event_sink=events.append)
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={1: TagObservation(1, 9.9, forward_m=0.8, left_m=0.0)},
            )
        )
        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=9.9,
                left_vel_rpm=35.0,
                right_vel_rpm=35.0,
                motion_enabled=True,
                drive_ports_ok=True,
            )
        )

        first = operator.move_to_tag(1, target_distance_m=0.4)
        self.assertEqual(first.reason, "moving_to_tag")
        second = operator.move_to_tag(1, target_distance_m=0.4)

        self.assertFalse(second.success)
        self.assertEqual(second.reason, "slip")
        self.assertEqual(events[-1].name, "spinout")
        self.assertEqual(sink.packets[-1]["cmd"], "stop")

    def test_move_to_tag_reports_stuck_from_low_wheel_velocity(self) -> None:
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0)
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={1: TagObservation(1, 9.9, forward_m=0.8, left_m=0.0)},
            )
        )
        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=9.9,
                left_vel_rpm=0.0,
                right_vel_rpm=0.0,
                motion_enabled=True,
                drive_ports_ok=True,
            )
        )

        operator.move_to_tag(1, target_distance_m=0.4)
        result = operator.move_to_tag(1, target_distance_m=0.4)

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "stuck")
        self.assertEqual(sink.packets[-1]["reason"], "operator_stuck")

    def test_grabbed_event_uses_manipulator_telemetry(self) -> None:
        events: list[OperatorEvent] = []
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0, event_sink=events.append)
        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=9.9,
                motor_samples=(
                    MotorSample(
                        device="release_motor",
                        subsystem="manipulator",
                        sample_ms=100,
                        velocity_rpm=0.5,
                        current_amp=0.4,
                    ),
                ),
            )
        )

        result = operator.grab()

        self.assertTrue(result.has_object)
        self.assertEqual(events[-1].name, "grabbed")
        self.assertEqual(sink.packets[-1]["cmd"], "grab")

    def test_telemetry_parser_extracts_manipulator_sample(self) -> None:
        snapshot = telemetry_snapshot_from_mapping(
            {
                "motion_enabled": True,
                "drive_ports_ok": True,
                "left_vel_rpm": 1.0,
                "right_vel_rpm": 2.0,
                "motor_samples": [
                    {
                        "device": "release_motor",
                        "subsystem": "manipulator",
                        "sample_ms": 42,
                        "values": {"velocity_rpm": 0.0, "current_amp": 0.5},
                    }
                ],
            },
            stamp_s=3.0,
        )

        self.assertIsNotNone(snapshot.manipulator_sample)
        self.assertEqual(snapshot.manipulator_sample.current_amp, 0.5)

    def test_contract_result_matches_locked_contract_shape(self) -> None:
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0)
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={1: TagObservation(1, 9.9, forward_m=0.8, left_m=0.0)},
            )
        )
        operator.update_telemetry(
            telemetry_snapshot_from_mapping(
                {
                    "t_ms": 1234,
                    "motion_enabled": True,
                    "drive_ports_ok": True,
                    "left_vel_rpm": 1.0,
                    "right_vel_rpm": 2.0,
                    "motor_samples": [
                        {
                            "device": "release_motor",
                            "subsystem": "manipulator",
                            "sample_ms": 1234,
                            "values": {
                                "position_deg": 1.0,
                                "velocity_rpm": 0.0,
                                "current_amp": 0.5,
                                "power_w": 0.0,
                                "torque_nm": 0.0,
                                "efficiency_pct": 0.0,
                                "temperature_c": 30.0,
                            },
                        }
                    ],
                },
                stamp_s=10.0,
            )
        )
        result = operator.move_to_tag(1, target_distance_m=0.45)

        payload = operator.contract_result(method_name="move_to_tag", result=result)

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["task"], "operator_test")
        self.assertEqual(payload["motor_samples"][0]["subsystem"], "claw")
        self.assertEqual(payload["motor_samples"][0]["api_binding"], "vexcode_python")
        self.assertEqual(
            set(payload["motor_samples"][0]["source_api"]),
            {
                "position_deg",
                "velocity_rpm",
                "current_amp",
                "power_w",
                "torque_nm",
                "efficiency_pct",
                "temperature_c",
            },
        )
        self.assertIn("object_detected", payload["vision"])
        self.assertEqual(payload["outcome"]["method"], "move_to_tag")


class String:
    def __init__(self, data: str = "") -> None:
        self.data = data


class Publisher:
    def __init__(self) -> None:
        self.messages: list[String] = []

    def publish(self, msg: String) -> None:
        self.messages.append(msg)


class Node:
    parameter_defaults: dict[str, Any] = {}

    def __init__(self, name: str) -> None:
        self.name = name
        self.publishers: list[Publisher] = []
        self._parameters = {
            "camera_in_robot_json": '{"x_m":0.0,"y_m":0.0,"yaw_rad":0.0}',
            "workspace_map_path": "",
            "tag_anchors_json": json.dumps(
                {
                    str(tag_id): {"x_m": float(tag_id), "y_m": 0.0, "yaw_rad": 0.0}
                    for tag_id in range(15)
                }
            ),
            "task_contract_json": json.dumps(
                {
                    "schema_version": "1.0",
                    "session_id": "operator-node-test",
                    "generation": 0,
                    "round": 0,
                    "task": "operator_node_test",
                    "motor_samples": [{"device": "left_drive"}],
                    "predicted": {"success": True},
                    "gap": {"distance_error_m": 0.0},
                }
            ),
            "task_outline_json": json.dumps(
                [
                    ["locate_nearest_apriltag", []],
                    ["move_to_tag", [1]],
                    ["grab", [], {"duration_ms": 700}],
                ]
            ),
            "command_topic": "/operator/command",
            "event_topic": "/operator/events",
            "result_topic": "/operator/results",
            "status_topic": "/operator/status",
        }
        self._parameters.update(self.parameter_defaults)

    def declare_parameter(self, name: str, default: Any) -> None:
        self._parameters.setdefault(name, default)

    def get_parameter(self, name: str) -> Any:
        value = self._parameters[name]
        return types.SimpleNamespace(
            get_parameter_value=lambda: types.SimpleNamespace(string_value=value)
        )

    def create_publisher(self, *_args: Any) -> Publisher:
        publisher = Publisher()
        self.publishers.append(publisher)
        return publisher

    def create_subscription(self, *_args: Any) -> object:
        return object()

    def create_timer(self, *_args: Any) -> object:
        return object()

    def get_logger(self) -> Any:
        return types.SimpleNamespace(warn=lambda *_args, **_kwargs: None)

    def destroy_node(self) -> None:
        return None


def install_ros_stubs() -> None:
    rclpy = types.ModuleType("rclpy")
    rclpy.spin = lambda *_args, **_kwargs: None
    rclpy.init = lambda *_args, **_kwargs: None
    rclpy.shutdown = lambda: None

    rclpy_node = types.ModuleType("rclpy.node")
    rclpy_node.Node = Node

    std_msgs = types.ModuleType("std_msgs")
    std_msgs_msg = types.ModuleType("std_msgs.msg")
    std_msgs_msg.String = String

    tf2_msgs = types.ModuleType("tf2_msgs")
    tf2_msgs_msg = types.ModuleType("tf2_msgs.msg")
    tf2_msgs_msg.TFMessage = object

    sys.modules["rclpy"] = rclpy
    sys.modules["rclpy.node"] = rclpy_node
    sys.modules["std_msgs"] = std_msgs
    sys.modules["std_msgs.msg"] = std_msgs_msg
    sys.modules["tf2_msgs"] = tf2_msgs
    sys.modules["tf2_msgs.msg"] = tf2_msgs_msg


class OperatorNodeTests(unittest.TestCase):
    def tearDown(self) -> None:
        Node.parameter_defaults = {}

    def test_node_accepts_ad_hoc_move_command(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()
        stamp_s = time.monotonic()
        node.operator.update_vision(
            VisionSnapshot(
                stamp_s=stamp_s,
                tags={1: TagObservation(1, stamp_s, forward_m=0.8, left_m=0.0)},
            )
        )

        node._on_command(
            String(
                data=json.dumps(
                    {
                        "action": "move_to_tag",
                        "tag_index": 1,
                    }
                )
            )
        )

        cmd_packet = json.loads(node._sink.pub.messages[-1].data)
        self.assertEqual(cmd_packet["cmd"], "drive")
        self.assertEqual(cmd_packet["reason"], "move_to_tag_1")
        result_payload = json.loads(node._result_pub.messages[-1].data)
        self.assertEqual(result_payload["schema_version"], "1.0")
        self.assertEqual(result_payload["outcome"]["method"], "move_to_tag")

    def test_node_applies_camera_offset_to_tag_observations(self) -> None:
        Node.parameter_defaults = {
            "camera_in_robot_json": '{"x_m":0.0,"y_m":-0.08,"yaw_rad":0.0}'
        }
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()
        msg = types.SimpleNamespace(
            transforms=[
                types.SimpleNamespace(
                    child_frame_id="tag36h11_1",
                    transform=types.SimpleNamespace(
                        translation=types.SimpleNamespace(x=0.0, z=1.0)
                    ),
                )
            ]
        )

        node._on_tf(msg)

        observed = node.operator.vision.tags[1]
        self.assertAlmostEqual(observed.forward_m, 1.0)
        self.assertAlmostEqual(observed.left_m, -0.08)
        self.assertAlmostEqual(node.operator.camera_in_robot.y_m, -0.08)

    def test_node_rejects_bad_ad_hoc_command_with_event(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()

        node._on_command(String(data=json.dumps({"action": "nope"})))

        event = json.loads(node._event_pub.messages[-1].data)
        self.assertEqual(event["name"], "command_rejected")


if __name__ == "__main__":
    unittest.main()
