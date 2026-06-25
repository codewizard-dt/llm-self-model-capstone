from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .bridge_protocol import now_ms, normalize_outbound
from .task_plan import build_task_plan, parse_task_plan_request
from .vision_map import scene_map_from_json


class TaskPlanNode(Node):
    def __init__(self) -> None:
        super().__init__("task_plan")
        self.declare_parameter("scene_map_topic", "/vision/scene_map")
        self.declare_parameter("request_topic", "/task_plan/request")
        self.declare_parameter("plan_topic", "/task_plan/current")
        self.declare_parameter("align_goal_topic", "/align_to_tag/goal")
        self.declare_parameter("survey_goal_topic", "/survey/goal")
        self.declare_parameter("vex_cmd_topic", "/vex/cmd")
        self._scene = None
        self._routine_seq = 100000
        self._plan_pub = self.create_publisher(
            String,
            self.get_parameter("plan_topic").get_parameter_value().string_value,
            10,
        )
        self._align_goal_pub = self.create_publisher(
            String,
            self.get_parameter("align_goal_topic").get_parameter_value().string_value,
            10,
        )
        self._survey_goal_pub = self.create_publisher(
            String,
            self.get_parameter("survey_goal_topic").get_parameter_value().string_value,
            10,
        )
        self._vex_cmd_pub = self.create_publisher(
            String,
            self.get_parameter("vex_cmd_topic").get_parameter_value().string_value,
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
        if request.dispatch and plan.get("executable_now"):
            for step in plan.get("steps", []):
                if not step.get("dispatchable"):
                    continue
                if step.get("type") == "align_to_tag":
                    self._align_goal_pub.publish(
                        String(data=json.dumps(step["goal"], separators=(",", ":")))
                    )
                    break
                if step.get("type") == "survey_scan":
                    self._survey_goal_pub.publish(
                        String(data=json.dumps(step["goal"], separators=(",", ":")))
                    )
                    break
                if step.get("type") == "brain_routine":
                    self._publish_routine_command(step["cmd"])
                    break

    def _publish_routine_command(self, template: dict) -> None:
        self._routine_seq += 1
        packet = dict(template)
        packet["seq"] = self._routine_seq
        packet["sent_ms"] = now_ms()
        normalized = normalize_outbound(packet)
        self._vex_cmd_pub.publish(
            String(data=json.dumps(normalized, separators=(",", ":")))
        )

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
