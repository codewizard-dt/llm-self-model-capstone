from __future__ import annotations

import importlib
import sys
import types
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class String:
    def __init__(self, data: str = "") -> None:
        self.data = data


class Publisher:
    def __init__(self) -> None:
        self.messages: list[String] = []

    def publish(self, msg: String) -> None:
        self.messages.append(msg)


class Node:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def create_publisher(self, *_args: Any, **_kwargs: Any) -> Publisher:
        return Publisher()

    def create_subscription(self, *_args: Any, **_kwargs: Any) -> object:
        return object()

    def destroy_node(self) -> None:
        pass


class TFMessage:
    pass


def install_ros_stubs() -> None:
    rclpy = types.ModuleType("rclpy")
    rclpy.spin_once = lambda *_args, **_kwargs: None
    rclpy.init = lambda: None
    rclpy.shutdown = lambda: None

    rclpy_node = types.ModuleType("rclpy.node")
    rclpy_node.Node = Node

    std_msgs = types.ModuleType("std_msgs")
    std_msgs_msg = types.ModuleType("std_msgs.msg")
    std_msgs_msg.String = String

    tf2_msgs = types.ModuleType("tf2_msgs")
    tf2_msgs_msg = types.ModuleType("tf2_msgs.msg")
    tf2_msgs_msg.TFMessage = TFMessage

    sys.modules.setdefault("rclpy", rclpy)
    sys.modules.setdefault("rclpy.node", rclpy_node)
    sys.modules.setdefault("std_msgs", std_msgs)
    sys.modules.setdefault("std_msgs.msg", std_msgs_msg)
    sys.modules.setdefault("tf2_msgs", tf2_msgs)
    sys.modules.setdefault("tf2_msgs.msg", tf2_msgs_msg)


install_ros_stubs()
deliver_ball = importlib.import_module("vexy_ros.deliver_ball")


class FakeNode:
    def __init__(self) -> None:
        self.observed_tags: set[int] = set()
        self.last_ack: dict[str, Any] | None = None
        self.last_telemetry = {"motion_enabled": True}
        self.last_scene_map = {"tags": []}
        self.commands_sent = 0
        self.last_command: dict[str, Any] | None = None
        self.seq = 100
        self.stop_reasons: list[str] = []
        self.spin_calls: list[float] = []
        self.sent: list[dict[str, Any]] = []
        self.tags = {
            0: {"tag_id": 0, "distance_m": 0.6},
            1: {"tag_id": 1, "distance_m": 0.7},
        }

    def spin_for(self, duration_s: float) -> None:
        self.spin_calls.append(duration_s)

    def stop(self, reason: str) -> None:
        self.stop_reasons.append(reason)
        self.last_command = {"cmd": "stop", "reason": reason}

    def fresh_tag(
        self, *, tag_id: int | None = None, max_age_s: float = 1.0
    ) -> dict[str, float | int] | None:
        del max_age_s
        if tag_id is None:
            return next(iter(self.tags.values()), None)
        return self.tags.get(tag_id)

    def send(
        self,
        cmd: str,
        *,
        vx: float = 0.0,
        omega: float = 0.0,
        ttl_ms: int = 180,
        duration_ms: int | None = None,
        reason: str | None = None,
    ) -> None:
        del vx, omega
        self.seq += 1
        packet: dict[str, Any] = {"seq": self.seq, "cmd": cmd, "ttl_ms": ttl_ms}
        if duration_ms is not None:
            packet["duration_ms"] = duration_ms
        if reason is not None:
            packet["reason"] = reason
        self.sent.append(packet)
        self.commands_sent += 1
        self.last_command = packet
        if cmd in {"grab", "lift", "release"}:
            self.last_ack = {"ack": self.seq, "state": "ok"}


class DeliverBallTests(unittest.TestCase):
    def test_parser_defaults_to_map_role_tag_ids(self) -> None:
        args = deliver_ball.build_parser().parse_args([])

        self.assertEqual(args.ball_tag_id, 1)
        self.assertEqual(args.bin_tag_id, 0)
        self.assertGreater(args.grab_ms, 0)
        self.assertGreater(args.lift_ms, 0)
        self.assertGreater(args.release_ms, 0)
        self.assertEqual(
            args.camera_in_robot_json,
            deliver_ball.DEFAULT_CAMERA_IN_ROBOT,
        )

    def test_deliver_ball_runs_scan_ball_bin_release_sequence(self) -> None:
        node = FakeNode()
        approached: list[int] = []

        def fake_scan(_node: FakeNode, **_kwargs: Any) -> None:
            _node.observed_tags.update({0, 1})

        def fake_approach(
            _node: FakeNode, *, tag_id: int, target_distance_m: float, **_kwargs: Any
        ) -> tuple[bool, str, dict[str, float | int]]:
            approached.append(tag_id)
            return (
                True,
                "target_distance_reached",
                {
                    "tag_id": tag_id,
                    "distance_m": target_distance_m,
                },
            )

        original_scan = deliver_ball.run_scan
        original_approach = deliver_ball.approach_tag
        deliver_ball.run_scan = fake_scan
        deliver_ball.approach_tag = fake_approach
        try:
            summary = deliver_ball.deliver_ball(
                node,
                deliver_ball.build_parser().parse_args(
                    ["--scan-duration-s", "0.01", "--settle-s", "0.0"]
                ),
            )
        finally:
            deliver_ball.run_scan = original_scan
            deliver_ball.approach_tag = original_approach

        self.assertEqual(summary["status"], "succeeded")
        self.assertEqual(summary["reason"], "ball_delivered")
        self.assertEqual(approached, [1, 0])
        manipulator_commands = [packet["cmd"] for packet in node.sent]
        self.assertEqual(manipulator_commands, ["grab", "lift", "release"])
        self.assertEqual(node.sent[0]["reason"], "grab_ball")
        self.assertEqual(node.sent[1]["reason"], "raise_claw_for_bin")
        self.assertEqual(node.sent[-1]["reason"], "drop_ball_in_bin")
        self.assertTrue(summary["grab"]["succeeded"])
        self.assertTrue(summary["lift"]["succeeded"])
        self.assertTrue(summary["release"]["succeeded"])
        self.assertIn("workspace_orientation_complete", node.stop_reasons)
        self.assertIn("grab_complete", node.stop_reasons)
        self.assertIn("lift_complete", node.stop_reasons)
        self.assertIn("release_complete", node.stop_reasons)

    def test_deliver_ball_fails_when_orientation_sees_no_tags(self) -> None:
        node = FakeNode()
        node.tags = {}

        def fake_scan(_node: FakeNode, **_kwargs: Any) -> None:
            return None

        original_scan = deliver_ball.run_scan
        deliver_ball.run_scan = fake_scan
        try:
            summary = deliver_ball.deliver_ball(
                node,
                deliver_ball.build_parser().parse_args(
                    ["--scan-duration-s", "0.01", "--settle-s", "0.0"]
                ),
            )
        finally:
            deliver_ball.run_scan = original_scan

        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["reason"], "no_apriltags_observed")
        self.assertEqual(node.sent, [])


if __name__ == "__main__":
    unittest.main()
