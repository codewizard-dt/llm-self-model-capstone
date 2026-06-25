from __future__ import annotations

import json
import math
import time
from typing import Any, Mapping
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from tf2_msgs.msg import TFMessage

from ..bridge_protocol import PROTOCOL_VERSION, now_ms
from ..vision_map import (
    camera_from_apriltag_translation,
    parse_tag_anchors,
    pose_from_mapping,
    robot_from_camera_pose,
    tag_id_from_frame_id,
)
from .core import (
    MAX_TAG_ID,
    MIN_TAG_ID,
    CommandSink,
    ObjectObservation,
    Operator,
    OperatorEvent,
    PrimitiveCommand,
    TagObservation,
    TelemetrySnapshot,
    VisionSnapshot,
    packet_from_primitive,
    telemetry_snapshot_from_mapping,
)


class RosCommandSink(CommandSink):
    def __init__(self, node: Node) -> None:
        self.node = node
        self.pub = node.create_publisher(String, "/vex/cmd", 10)
        self.seq = 32000

    def send_command(self, command: PrimitiveCommand) -> int:
        self.seq += 1
        packet = packet_from_primitive(command, seq=self.seq)
        self.pub.publish(String(data=json.dumps(packet, separators=(",", ":"))))
        return self.seq


class OperatorNode(Node):
    def __init__(self) -> None:
        super().__init__("vexy_operator")
        self.declare_parameter(
            "camera_in_robot_json", '{"x_m":0.0,"y_m":0.0,"yaw_rad":0.0}'
        )
        self.declare_parameter("workspace_map_path", "")
        self.declare_parameter("tag_anchors_json", "")
        self.declare_parameter("task_contract_json", "")
        self.declare_parameter("task_outline_json", "")
        self.declare_parameter("command_topic", "/operator/command")
        self.declare_parameter("event_topic", "/operator/events")
        self.declare_parameter("result_topic", "/operator/results")
        self.declare_parameter("status_topic", "/operator/status")

        camera_raw = (
            self.get_parameter("camera_in_robot_json")
            .get_parameter_value()
            .string_value
        )
        self.camera_in_robot = pose_from_mapping(json.loads(camera_raw))
        april_tag_map = self._load_april_tag_map()
        task_contract = self._load_task_contract()
        task_outline = self._load_task_outline()
        self._tags: dict[int, TagObservation] = {}
        self._objects: tuple[ObjectObservation, ...] = ()
        self._last_scene_map: Mapping[str, Any] | None = None
        self._last_telemetry: TelemetrySnapshot | None = None
        self._event_pub = self.create_publisher(
            String,
            self.get_parameter("event_topic").get_parameter_value().string_value,
            10,
        )
        self._status_pub = self.create_publisher(
            String,
            self.get_parameter("status_topic").get_parameter_value().string_value,
            10,
        )
        self._result_pub = self.create_publisher(
            String,
            self.get_parameter("result_topic").get_parameter_value().string_value,
            10,
        )
        self._sink = RosCommandSink(self)
        self.operator = Operator(
            self._sink,
            april_tag_map=april_tag_map,
            camera_in_robot=self.camera_in_robot,
            task_contract=task_contract,
            task_outline=task_outline,
            event_sink=self._publish_event,
        )

        self.create_subscription(TFMessage, "/tf", self._on_tf, 10)
        self.create_subscription(String, "/vision/scene_map", self._on_scene_map, 10)
        self.create_subscription(
            String, "/vision/object_detections", self._on_object_detections, 10
        )
        self.create_subscription(
            String, "/vision/object_indications", self._on_object_indications, 10
        )
        self.create_subscription(String, "/vex/telemetry", self._on_telemetry, 10)
        self.create_subscription(
            String,
            self.get_parameter("command_topic").get_parameter_value().string_value,
            self._on_command,
            10,
        )
        self.create_timer(0.25, self._publish_status)

    def _load_april_tag_map(self) -> Mapping[int, Any]:
        workspace_map_path = (
            self.get_parameter("workspace_map_path").get_parameter_value().string_value
        )
        if workspace_map_path:
            return parse_tag_anchors(Path(workspace_map_path).read_text())

        tag_anchors_json = (
            self.get_parameter("tag_anchors_json").get_parameter_value().string_value
        )
        if tag_anchors_json:
            return parse_tag_anchors(tag_anchors_json)
        raise ValueError(
            "vexy_operator requires workspace_map_path or tag_anchors_json"
        )

    def _load_task_contract(self) -> Mapping[str, Any]:
        task_contract_json = (
            self.get_parameter("task_contract_json").get_parameter_value().string_value
        )
        if not task_contract_json:
            raise ValueError("vexy_operator requires task_contract_json")
        payload = json.loads(task_contract_json)
        if not isinstance(payload, Mapping):
            raise ValueError("task_contract_json must decode to a JSON object")
        return payload

    def _load_task_outline(self) -> Any:
        task_outline_json = (
            self.get_parameter("task_outline_json").get_parameter_value().string_value
        )
        if not task_outline_json:
            raise ValueError("vexy_operator requires task_outline_json")
        return json.loads(task_outline_json)

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
        self._refresh_vision(stamp_s=stamp_s)

    def _on_scene_map(self, msg: String) -> None:
        try:
            self._last_scene_map = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"ignored bad scene map: {exc}")
            return
        self._refresh_vision(stamp_s=time.monotonic())

    def _on_object_detections(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"ignored bad object detections: {exc}")
            return
        stamp_s = float(payload.get("stamp_s", time.monotonic()))
        objects: list[ObjectObservation] = list(self._objects)
        for item in payload.get("detections", []):
            if not isinstance(item, Mapping):
                continue
            objects.append(
                ObjectObservation(
                    name=str(item.get("label", item.get("name", "object"))),
                    category=str(item.get("label", item.get("name", "object"))),
                    stamp_s=float(item.get("stamp_s", stamp_s)),
                    confidence=(
                        float(item["confidence"])
                        if item.get("confidence") is not None
                        else None
                    ),
                    source=str(payload.get("source", "object_detections")),
                )
            )
        self._objects = tuple(objects[-50:])
        self._refresh_vision(stamp_s=time.monotonic())

    def _on_object_indications(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"ignored bad object indications: {exc}")
            return
        if isinstance(payload, Mapping):
            payload = [payload]
        objects: list[ObjectObservation] = []
        now_s = time.monotonic()
        for item in payload:
            if not isinstance(item, Mapping):
                continue
            name = str(item.get("name", "object"))
            objects.append(
                ObjectObservation(
                    name=name,
                    category=name,
                    stamp_s=float(item.get("stamp_s", now_s)),
                    forward_m=_optional_float(item.get("forward_m")),
                    left_m=_optional_float(item.get("left_m")),
                    confidence=(
                        float(item["confidence"])
                        if item.get("confidence") is not None
                        else None
                    ),
                    source=str(item.get("source", "object_indications")),
                )
            )
        self._objects = tuple(objects)
        self._refresh_vision(stamp_s=now_s)

    def _on_telemetry(self, msg: String) -> None:
        try:
            raw = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"ignored bad telemetry: {exc}")
            return
        self._last_telemetry = telemetry_snapshot_from_mapping(raw)
        self.operator.update_telemetry(self._last_telemetry)

    def _on_command(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
            action = str(payload.get("action", ""))
            result = self._dispatch_command(payload)
            self._publish_contract_result(action, result)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._publish_event(
                OperatorEvent(
                    name="command_rejected",
                    stamp_s=time.monotonic(),
                    detail={"error": str(exc), "raw": msg.data},
                )
            )
            return
        self._status_pub.publish(
            String(
                data=json.dumps(
                    {
                        "type": "operator_result",
                        "action": payload.get("action"),
                        "success": result.success,
                        "reason": result.reason,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
        )

    def _dispatch_command(self, payload: Mapping[str, Any]) -> Any:
        action = str(payload.get("action", ""))
        tag_index = _tag_index_from_payload(payload)
        if action == "locate_nearest_apriltag":
            self.operator.require_allowed_method(action)
            return self.operator.locate_nearest_apriltag()
        if action == "orient_to_tag":
            self.operator.require_allowed_method(action)
            if tag_index is None:
                raise ValueError("orient_to_tag requires tag_index")
            return self.operator.orient_to_tag(tag_index)
        if action == "move_to_tag":
            self.operator.require_allowed_method(action)
            if tag_index is None:
                raise ValueError("move_to_tag requires tag_index")
            target = payload.get("target_distance_m")
            return self.operator.move_to_tag(
                tag_index,
                target_distance_m=None if target is None else float(target),
            )
        if action in {"grab", "lift", "release"}:
            self.operator.require_allowed_method(action)
            duration = payload.get("duration_ms")
            method = getattr(self.operator, action)
            return method() if duration is None else method(duration_ms=int(duration))
        raise ValueError(f"unsupported operator action: {action}")

    def _refresh_vision(self, *, stamp_s: float) -> None:
        self.operator.update_vision(
            VisionSnapshot(
                stamp_s=stamp_s,
                tags=dict(self._tags),
                objects=self._objects,
                raw_scene_map=self._last_scene_map,
            )
        )

    def _publish_event(self, event: OperatorEvent) -> None:
        payload = {
            "type": "operator_event",
            "name": event.name,
            "stamp_s": event.stamp_s,
            "detail": dict(event.detail),
        }
        self._event_pub.publish(
            String(data=json.dumps(payload, separators=(",", ":"), sort_keys=True))
        )

    def _publish_contract_result(self, action: str, result: Any) -> None:
        payload = self.operator.contract_result(method_name=action, result=result)
        self._result_pub.publish(
            String(data=json.dumps(payload, separators=(",", ":"), sort_keys=True))
        )

    def _publish_status(self) -> None:
        telemetry = self._last_telemetry
        pose = self.operator.current_pose()
        payload = {
            "type": "operator_status",
            "stamp_s": time.monotonic(),
            "protocol_version": PROTOCOL_VERSION,
            "last_sent_ms": now_ms(),
            "available_tag_ids": list(self.operator.available_april_tag_ids),
            "camera_in_robot": self.operator.camera_in_robot.to_json(),
            "known_tags": sorted(self._tags),
            "object_categories": sorted({obj.category for obj in self._objects}),
            "telemetry_seen": telemetry is not None,
            "localization_source": self.operator.localization_source,
            "map_pose": None if pose is None else pose.to_json(),
            "has_object": self.operator.has_object(),
        }
        self._status_pub.publish(
            String(data=json.dumps(payload, separators=(",", ":"), sort_keys=True))
        )


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _tag_index_from_payload(payload: Mapping[str, Any]) -> int | None:
    if "tag_index" in payload:
        return int(payload["tag_index"])
    if "tag_id" in payload:
        return int(payload["tag_id"])
    return None


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = OperatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
