from __future__ import annotations

import json
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo
from std_msgs.msg import String

from .object_detection import (
    detections_source,
    indications_from_detections,
    intrinsics_from_camera_info,
    parse_detections_payload,
    parse_dimensions_json,
)


DEFAULT_OBJECT_DIMENSIONS_JSON = json.dumps(
    {
        "*": {"height_m": 0.12},
        "bin": {"height_m": 0.20, "width_m": 0.30},
        "bottle": {"height_m": 0.20, "width_m": 0.065},
        "cup": {"height_m": 0.12, "width_m": 0.08},
        "sports ball": {"diameter_m": 0.065},
        "yellow ball": {"diameter_m": 0.065},
    },
    sort_keys=True,
)


class ObjectIndicationNode(Node):
    def __init__(self) -> None:
        super().__init__("object_indication")
        self.declare_parameter("detections_topic", "/vision/object_detections")
        self.declare_parameter("camera_info_topic", "/camera/camera_info")
        self.declare_parameter("indications_topic", "/vision/object_indications")
        self.declare_parameter("object_dimensions_json", DEFAULT_OBJECT_DIMENSIONS_JSON)
        self.declare_parameter("default_height_m", 0.12)
        self.declare_parameter("min_confidence", 0.35)
        self.declare_parameter("floor_projection_enabled", False)
        self.declare_parameter("camera_height_m", 0.0)
        self.declare_parameter("camera_pitch_rad", 0.0)

        dimensions_raw = (
            self.get_parameter("object_dimensions_json")
            .get_parameter_value()
            .string_value
        )
        self._dimensions = parse_dimensions_json(dimensions_raw)
        self._default_height_m = (
            self.get_parameter("default_height_m").get_parameter_value().double_value
        )
        self._min_confidence = (
            self.get_parameter("min_confidence").get_parameter_value().double_value
        )
        self._floor_projection_enabled = bool(
            self.get_parameter("floor_projection_enabled").value
        )
        self._camera_height_m = float(self.get_parameter("camera_height_m").value)
        self._camera_pitch_rad = float(self.get_parameter("camera_pitch_rad").value)
        self._intrinsics = None
        self._pub = self.create_publisher(
            String,
            self.get_parameter("indications_topic").get_parameter_value().string_value,
            10,
        )
        self.create_subscription(
            CameraInfo,
            self.get_parameter("camera_info_topic").get_parameter_value().string_value,
            self._on_camera_info,
            10,
        )
        self.create_subscription(
            String,
            self.get_parameter("detections_topic").get_parameter_value().string_value,
            self._on_detections,
            10,
        )

    def _on_camera_info(self, msg: CameraInfo) -> None:
        try:
            self._intrinsics = intrinsics_from_camera_info(list(msg.k))
        except ValueError as exc:
            self.get_logger().warn(f"ignored bad camera info: {exc}")

    def _on_detections(self, msg: String) -> None:
        if self._intrinsics is None:
            self.get_logger().warn("object detections ignored until CameraInfo arrives")
            return
        try:
            source = detections_source(msg.data)
            detections = parse_detections_payload(msg.data)
            indications = indications_from_detections(
                detections,
                intrinsics=self._intrinsics,
                dimensions=self._dimensions,
                default_height_m=self._default_height_m,
                min_confidence=self._min_confidence,
                source=source,
                floor_projection_enabled=self._floor_projection_enabled,
                camera_height_m=self._camera_height_m,
                camera_pitch_rad=self._camera_pitch_rad,
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self.get_logger().warn(f"ignored bad object detection payload: {exc}")
            return
        if not indications:
            return

        payload = {
            "type": "object_indications",
            "source": "yolo_ncnn_projection",
            "stamp_s": time.monotonic(),
            "objects": indications,
        }
        self._pub.publish(
            String(data=json.dumps(payload["objects"], separators=(",", ":")))
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ObjectIndicationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
