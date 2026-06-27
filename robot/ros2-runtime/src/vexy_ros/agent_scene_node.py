from __future__ import annotations

import json
import time
from typing import Any

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .agent_scene import agent_scene_json


class AgentSceneNode(Node):
    def __init__(self) -> None:
        super().__init__("agent_scene")
        self.declare_parameter("publish_hz", 3.0)
        self.declare_parameter("include_debug_tracks", False)
        self.declare_parameter("scene_topic", "/vision/scene_map")
        self.declare_parameter("tracks_topic", "/vision/object_tracks")
        self.declare_parameter("agent_scene_topic", "/vision/agent_scene")
        self.declare_parameter("operator_status_topic", "/operator/status")

        self._latest: dict[str, dict[str, Any]] = {}
        self._include_debug_tracks = bool(
            self.get_parameter("include_debug_tracks").value
        )
        self._pub = self.create_publisher(
            String,
            str(self.get_parameter("agent_scene_topic").value),
            10,
        )
        self.create_subscription(
            String,
            str(self.get_parameter("scene_topic").value),
            lambda msg: self._capture_json("scene_map", msg),
            10,
        )
        self.create_subscription(
            String,
            str(self.get_parameter("tracks_topic").value),
            lambda msg: self._capture_json("object_tracks", msg),
            10,
        )
        self.create_subscription(
            String,
            "/vex/telemetry",
            lambda msg: self._capture_json("telemetry", msg),
            10,
        )
        self.create_subscription(
            String,
            "/vex/bridge_status",
            lambda msg: self._capture_json("bridge_status", msg),
            10,
        )
        self.create_subscription(
            String,
            "/task_plan/current",
            lambda msg: self._capture_json("task_plan", msg),
            10,
        )
        self.create_subscription(
            String,
            str(self.get_parameter("operator_status_topic").value),
            lambda msg: self._capture_json("operator_status", msg),
            10,
        )
        publish_hz = float(self.get_parameter("publish_hz").value)
        period_s = 0.5 if publish_hz <= 0.0 else 1.0 / publish_hz
        self.create_timer(period_s, self._publish_agent_scene)

    def _capture_json(self, key: str, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"ignored bad {key}: {exc}")
            return
        if isinstance(payload, dict):
            self._latest[key] = payload

    def _publish_agent_scene(self) -> None:
        self._pub.publish(
            String(
                data=agent_scene_json(
                    scene_map=self._latest.get("scene_map"),
                    object_tracks=self._latest.get("object_tracks"),
                    telemetry=self._latest.get("telemetry"),
                    bridge_status=self._latest.get("bridge_status"),
                    task_plan=self._latest.get("task_plan"),
                    operator_status=self._latest.get("operator_status"),
                    now_s=time.monotonic(),
                    include_debug_tracks=self._include_debug_tracks,
                )
            )
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = AgentSceneNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
