from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .task_plan import build_task_plan, parse_task_plan_request
from .vision_map import scene_map_from_json


class TaskPlanNode(Node):
    def __init__(self) -> None:
        super().__init__("task_plan")
        self.declare_parameter("scene_map_topic", "/vision/scene_map")
        self.declare_parameter("request_topic", "/task_plan/request")
        self.declare_parameter("plan_topic", "/task_plan/current")
        self._scene = None
        self._plan_pub = self.create_publisher(
            String,
            self.get_parameter("plan_topic").get_parameter_value().string_value,
            10,
        )
        self.create_subscription(
            String,
            self.get_parameter("scene_map_topic").get_parameter_value().string_value,
            self._on_scene_map,
            10,
        )
        self.create_subscription(
            String,
            self.get_parameter("request_topic").get_parameter_value().string_value,
            self._on_request,
            10,
        )

    def _on_scene_map(self, msg: String) -> None:
        try:
            self._scene = scene_map_from_json(msg.data)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.get_logger().warn(f"ignored bad scene map: {exc}")

    def _on_request(self, msg: String) -> None:
        try:
            request = parse_task_plan_request(msg.data)
            plan = build_task_plan(self._scene, request)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._publish_blocked(f"bad_request:{exc}")
            return

        self._plan_pub.publish(String(data=json.dumps(plan, separators=(",", ":"))))

    def _publish_blocked(self, reason: str) -> None:
        self._plan_pub.publish(
            String(
                data=json.dumps(
                    {
                        "type": "task_plan",
                        "status": "blocked",
                        "executable_now": False,
                        "blocked_reason": reason,
                        "steps": [],
                    },
                    separators=(",", ":"),
                )
            )
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TaskPlanNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
