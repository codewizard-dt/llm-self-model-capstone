from __future__ import annotations

import argparse
import importlib
import json
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
    def __init__(self, name: str) -> None:
        self.name = name
        self.publishers: list[Publisher] = []

    def create_publisher(self, *_args: Any) -> Publisher:
        publisher = Publisher()
        self.publishers.append(publisher)
        return publisher

    def create_subscription(self, *_args: Any) -> object:
        return object()

    def destroy_node(self) -> None:
        return None


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
    tf2_msgs_msg.TFMessage = object

    sys.modules.setdefault("rclpy", rclpy)
    sys.modules.setdefault("rclpy.node", rclpy_node)
    sys.modules.setdefault("std_msgs", std_msgs)
    sys.modules.setdefault("std_msgs.msg", std_msgs_msg)
    sys.modules.setdefault("tf2_msgs", tf2_msgs)
    sys.modules.setdefault("tf2_msgs.msg", tf2_msgs_msg)


install_ros_stubs()
tag_action_proof = importlib.import_module("vexy_ros.tag_action_proof")


class FakeProofNode:
    def __init__(self) -> None:
        self.observed_tags: set[int] = set()
        self.last_ack = {"state": "ok", "ack": 12}
        self.last_telemetry = {"motion_enabled": True}
        self.commands_sent = 9
        self.last_command = {"cmd": "stop", "reason": "scan_complete"}
        self.stop_reasons: list[str] = []
        self.spin_calls: list[float] = []
        self.post_tag: dict[str, float | int] | None = None

    def spin_for(self, duration_s: float) -> None:
        self.spin_calls.append(duration_s)

    def stop(self, reason: str) -> None:
        self.stop_reasons.append(reason)

    def fresh_tag(
        self, *, tag_id: int | None = None, max_age_s: float = 1.0
    ) -> dict[str, float | int] | None:
        _ = tag_id, max_age_s
        return self.post_tag


class TagActionProofTests(unittest.TestCase):
    def test_send_publishes_bounded_json_command_and_tracks_it(self) -> None:
        node = tag_action_proof.TagActionProof()

        node.send(
            "drive",
            vx=0.14,
            omega=0.2,
            ttl_ms=180,
            reason="unit_test_drive",
        )

        published = json.loads(node._cmd_pub.messages[-1].data)
        self.assertEqual(published["v"], 1)
        self.assertEqual(published["type"], "cmd")
        self.assertEqual(published["cmd"], "drive")
        self.assertEqual(published["vx"], 0.14)
        self.assertEqual(published["vy"], 0.0)
        self.assertEqual(published["omega"], 0.2)
        self.assertEqual(published["ttl_ms"], 180)
        self.assertEqual(published["reason"], "unit_test_drive")
        self.assertEqual(node.commands_sent, 1)
        self.assertEqual(node.last_command, published)

    def test_visual_one_foot_scan_summary_records_closure_and_scan_tags(self) -> None:
        node = FakeProofNode()
        start = {"tag_id": 2, "distance_m": 1.2}
        post = {"tag_id": 2, "distance_m": 0.9}
        node.post_tag = post

        def fake_reacquire(_node: FakeProofNode, **_kwargs: Any) -> dict[str, float]:
            _node.observed_tags.add(2)
            return start

        def fake_approach(
            _node: FakeProofNode, *, target_distance_m: float, **_kwargs: Any
        ) -> tuple[bool, str, dict[str, float]]:
            self.assertAlmostEqual(target_distance_m, 0.8952)
            _node.observed_tags.add(2)
            return True, "target_distance_reached", post

        def fake_scan(_node: FakeProofNode, **_kwargs: Any) -> None:
            _node.observed_tags.update({2, 5})

        original_reacquire = tag_action_proof.reacquire_visible_tag
        original_approach = tag_action_proof.approach_tag
        original_scan = tag_action_proof.run_scan
        tag_action_proof.reacquire_visible_tag = fake_reacquire
        tag_action_proof.approach_tag = fake_approach
        tag_action_proof.run_scan = fake_scan
        try:
            summary = tag_action_proof.visual_one_foot_scan(
                node,
                argparse.Namespace(
                    settle_s=0.1,
                    reacquire_timeout_s=2.0,
                    reacquire_omega=0.35,
                    ttl_ms=180,
                    min_distance_m=0.45,
                    closure_m=0.3048,
                    approach_timeout_s=4.0,
                    drive_vx=0.14,
                    turn_kp=0.9,
                    max_omega=0.45,
                    scan_duration_s=14.5,
                    scan_omega=0.45,
                ),
            )
        finally:
            tag_action_proof.reacquire_visible_tag = original_reacquire
            tag_action_proof.approach_tag = original_approach
            tag_action_proof.run_scan = original_scan

        self.assertEqual(summary["proof_kind"], "visual_one_foot_and_scan")
        self.assertEqual(summary["visible_tag"], 2)
        self.assertAlmostEqual(summary["closure_m"], 0.3048)
        self.assertAlmostEqual(summary["start_distance_m"], 1.2)
        self.assertAlmostEqual(summary["target_distance_m"], 0.8952)
        self.assertAlmostEqual(summary["post_drive_distance_m"], 0.9)
        self.assertAlmostEqual(summary["distance_closed_m"], 0.3)
        self.assertTrue(summary["approach_reached_target"])
        self.assertEqual(summary["approach_reason"], "target_distance_reached")
        self.assertEqual(summary["observed_tags_after_reacquire"], [2])
        self.assertEqual(summary["observed_tags_after_approach"], [2])
        self.assertEqual(summary["observed_tags_after_scan"], [2, 5])
        self.assertEqual(summary["observed_tags"], [2, 5])
        self.assertEqual(summary["last_ack"], {"state": "ok", "ack": 12})
        self.assertEqual(summary["last_telemetry"], {"motion_enabled": True})
        self.assertEqual(summary["commands_sent"], 9)
        self.assertEqual(
            summary["last_command"], {"cmd": "stop", "reason": "scan_complete"}
        )
        self.assertEqual(
            node.stop_reasons,
            ["reacquire_complete", "approach_complete", "scan_complete"],
        )

    def test_scan_only_summary_records_before_and_after_tags(self) -> None:
        node = FakeProofNode()
        node.observed_tags.add(1)

        def fake_scan(_node: FakeProofNode, **_kwargs: Any) -> None:
            _node.observed_tags.update({1, 3})

        original_scan = tag_action_proof.run_scan
        tag_action_proof.run_scan = fake_scan
        try:
            summary = tag_action_proof.scan_only(
                node,
                argparse.Namespace(
                    settle_s=0.1,
                    scan_duration_s=5.0,
                    scan_omega=0.4,
                    ttl_ms=180,
                ),
            )
        finally:
            tag_action_proof.run_scan = original_scan

        self.assertEqual(summary["proof_kind"], "scan_only")
        self.assertEqual(summary["observed_tags_before_scan"], [1])
        self.assertEqual(summary["observed_tags_after_scan"], [1, 3])
        self.assertEqual(summary["observed_tags"], [1, 3])
        self.assertEqual(summary["scan_duration_s"], 5.0)
        self.assertEqual(summary["scan_omega"], 0.4)


if __name__ == "__main__":
    unittest.main()
