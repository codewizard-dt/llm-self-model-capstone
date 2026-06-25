from __future__ import annotations

import json
import math
import time
from dataclasses import asdict
from typing import Any

import rclpy
from apriltag_msgs.msg import AprilTagDetectionArray
from rclpy.node import Node
from std_msgs.msg import String
from tf2_msgs.msg import TFMessage

from .align_to_tag import (
    AlignDecision,
    AlignToTagController,
    AlignToTagGoal,
    BridgeHealth,
    TagObservation,
    VexCommand,
)
from .bridge_protocol import PROTOCOL_VERSION, now_ms
from .vision_map import (
    camera_from_apriltag_translation,
    pose_from_mapping,
    robot_from_camera_pose,
    tag_id_from_frame_id,
)


class AlignToTagNode(Node):
    def __init__(self) -> None:
        super().__init__("align_to_tag")

        self.declare_parameter("control_period_s", 0.15)
        self.declare_parameter(
            "camera_in_robot_json", '{"x_m":0.0,"y_m":0.0,"yaw_rad":0.0}'
        )

        self._controller = AlignToTagController()
        self._camera_in_robot = pose_from_mapping(
            json.loads(
                self.get_parameter("camera_in_robot_json")
                .get_parameter_value()
                .string_value
            )
        )
        self._seq = 0
        self._latest_tag: TagObservation | None = None
        self._bridge = BridgeHealth(stamp_s=None)
        self._cancel_requested = False

        self._cmd_pub = self.create_publisher(String, "/vex/cmd", 10)
        self._feedback_pub = self.create_publisher(String, "/align_to_tag/feedback", 10)
        self._result_pub = self.create_publisher(String, "/align_to_tag/result", 10)

        self.create_subscription(String, "/align_to_tag/goal", self._on_goal, 10)
        self.create_subscription(String, "/align_to_tag/cancel", self._on_cancel, 10)
        self.create_subscription(String, "/vex/ack", self._on_ack, 10)
        self.create_subscription(
            String, "/vex/bridge_status", self._on_bridge_status, 10
        )
        self.create_subscription(
            AprilTagDetectionArray,
            "/apriltag/detections",
            self._on_detections,
            10,
        )
        self.create_subscription(TFMessage, "/tf", self._on_tf, 10)

        period = (
            self.get_parameter("control_period_s").get_parameter_value().double_value
        )
        self.create_timer(period, self._tick)

    def _on_goal(self, msg: String) -> None:
        try:
            raw = json.loads(msg.data)
            goal = AlignToTagGoal(**raw)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._publish_result(
                {"success": False, "reason": "bad_goal", "fault": str(exc)}
            )
            return

        decision = self._controller.start(
            goal,
            now_s=time.monotonic(),
            tag=self._latest_tag,
            bridge=self._bridge,
        )
        self._handle_decision(decision)

    def _on_cancel(self, msg: String) -> None:
        self._cancel_requested = True

    def _on_ack(self, msg: String) -> None:
        try:
            ack = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        ack_seq = ack.get("ack")
        self._bridge = BridgeHealth(
            stamp_s=time.monotonic(),
            last_ack_seq=ack_seq if isinstance(ack_seq, int) else None,
            fault=ack.get("fault") if isinstance(ack.get("fault"), str) else None,
            status=str(ack.get("state", "ack")),
        )

    def _on_bridge_status(self, msg: String) -> None:
        try:
            status = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        state = str(status.get("state", "unknown"))
        fault = None
        if state == "fault":
            fault = str(status.get("reason", "bridge_fault"))
        self._bridge = BridgeHealth(
            stamp_s=time.monotonic(),
            last_ack_seq=self._bridge.last_ack_seq,
            fault=fault,
            status=state,
        )

    def _on_detections(self, msg: AprilTagDetectionArray) -> None:
        now_s = time.monotonic()
        for detection in msg.detections:
            tag_id = self._tag_id(detection)
            if tag_id is None:
                continue
            observation = self._tag_observation(detection, tag_id, now_s)
            if observation is not None:
                self._latest_tag = observation
                return

    def _on_tf(self, msg: TFMessage) -> None:
        now_s = time.monotonic()
        for transform in msg.transforms:
            observation = self._tag_observation_from_transform(transform, now_s)
            if observation is not None:
                self._latest_tag = observation
                return

    def _tick(self) -> None:
        decision = self._controller.step(
            now_s=time.monotonic(),
            tag=self._latest_tag,
            bridge=self._bridge,
            cancel=self._cancel_requested,
        )
        self._cancel_requested = False
        self._handle_decision(decision)

    def _handle_decision(self, decision: AlignDecision) -> None:
        self._feedback_pub.publish(
            String(data=json.dumps(asdict(decision.feedback), sort_keys=True))
        )
        if decision.command is not None:
            self._publish_command(decision.command)
        if decision.result is not None:
            self._publish_result(asdict(decision.result))

    def _publish_command(self, command: VexCommand) -> None:
        self._seq += 1
        packet: dict[str, Any] = {
            "v": PROTOCOL_VERSION,
            "seq": self._seq,
            "type": "cmd",
            "cmd": command.cmd,
            "sent_ms": now_ms(),
            "ttl_ms": command.ttl_ms,
        }
        if command.cmd == "drive":
            packet.update({"vx": command.vx, "vy": command.vy, "omega": command.omega})
        if command.reason:
            packet["reason"] = command.reason
        self._cmd_pub.publish(
            String(data=json.dumps(packet, separators=(",", ":"), sort_keys=True))
        )

    def _publish_result(self, payload: dict[str, Any]) -> None:
        self._result_pub.publish(String(data=json.dumps(payload, sort_keys=True)))

    @staticmethod
    def _tag_id(detection: Any) -> int | None:
        value = getattr(detection, "id", None)
        if isinstance(value, int):
            return value
        if isinstance(value, (list, tuple)) and value and isinstance(value[0], int):
            return value[0]
        return None

    def _tag_observation(
        self, detection: Any, tag_id: int, now_s: float
    ) -> TagObservation | None:
        pose = getattr(
            getattr(getattr(detection, "pose", None), "pose", None), "pose", None
        )
        position = getattr(pose, "position", None)
        if position is None:
            return None

        camera_from_tag = camera_from_apriltag_translation(
            optical_x_m=float(getattr(position, "x", 0.0)),
            optical_z_m=float(getattr(position, "z", 0.0)),
        )
        robot_from_tag = robot_from_camera_pose(camera_from_tag, self._camera_in_robot)
        distance = math.sqrt(robot_from_tag.x_m**2 + robot_from_tag.y_m**2)
        yaw_error = math.atan2(robot_from_tag.y_m, robot_from_tag.x_m)
        return TagObservation(
            tag_id=tag_id,
            stamp_s=now_s,
            yaw_error_rad=yaw_error,
            lateral_error_m=robot_from_tag.y_m,
            distance_m=distance,
            confidence=None,
        )

    def _tag_observation_from_transform(
        self, transform_stamped: Any, now_s: float
    ) -> TagObservation | None:
        tag_id = tag_id_from_frame_id(
            str(getattr(transform_stamped, "child_frame_id", ""))
        )
        if tag_id is None:
            return None
        transform = getattr(transform_stamped, "transform", None)
        translation = getattr(transform, "translation", None)
        if translation is None:
            return None

        camera_from_tag = camera_from_apriltag_translation(
            optical_x_m=float(getattr(translation, "x", 0.0)),
            optical_z_m=float(getattr(translation, "z", 0.0)),
        )
        robot_from_tag = robot_from_camera_pose(camera_from_tag, self._camera_in_robot)
        distance = math.sqrt(robot_from_tag.x_m**2 + robot_from_tag.y_m**2)
        yaw_error = math.atan2(robot_from_tag.y_m, robot_from_tag.x_m)
        return TagObservation(
            tag_id=tag_id,
            stamp_s=now_s,
            yaw_error_rad=yaw_error,
            lateral_error_m=robot_from_tag.y_m,
            distance_m=distance,
            confidence=None,
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = AlignToTagNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
