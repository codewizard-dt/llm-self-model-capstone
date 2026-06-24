from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import rclpy
from apriltag_msgs.msg import AprilTagDetectionArray
from rclpy.node import Node
from std_msgs.msg import String
from tf2_msgs.msg import TFMessage

from .vision_map import (
    TagDetection2D,
    build_scene_map,
    camera_from_apriltag_translation,
    parse_object_observations,
    parse_tag_anchors,
    pose_from_mapping,
    tag_id_from_frame_id,
)


DEFAULT_TAG_ANCHORS_JSON = json.dumps(
    {"0": {"x_m": 0.0, "y_m": 0.0, "yaw_rad": 0.0, "label": "origin_tag"}},
    sort_keys=True,
)


class SceneMapNode(Node):
    def __init__(self) -> None:
        super().__init__("scene_map")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("workspace_map_path", "")
        self.declare_parameter("tag_anchors_json", DEFAULT_TAG_ANCHORS_JSON)
        self.declare_parameter(
            "camera_in_robot_json", '{"x_m":0.0,"y_m":0.0,"yaw_rad":0.0}'
        )

        workspace_map_path = (
            self.get_parameter("workspace_map_path").get_parameter_value().string_value
        )
        if workspace_map_path:
            self._anchors = parse_tag_anchors(Path(workspace_map_path).read_text())
        else:
            self._anchors = parse_tag_anchors(
                self.get_parameter("tag_anchors_json")
                .get_parameter_value()
                .string_value
            )
        self._camera_in_robot = pose_from_mapping(
            json.loads(
                self.get_parameter("camera_in_robot_json")
                .get_parameter_value()
                .string_value
            )
        )
        self._map_frame = (
            self.get_parameter("map_frame").get_parameter_value().string_value
        )
        self._objects = []

        self._map_pub = self.create_publisher(String, "/vision/scene_map", 10)
        self.create_subscription(
            AprilTagDetectionArray,
            "/apriltag/detections",
            self._on_detections,
            10,
        )
        self.create_subscription(TFMessage, "/tf", self._on_tf, 10)
        self.create_subscription(
            String,
            "/vision/object_indications",
            self._on_object_indications,
            10,
        )

    def _on_object_indications(self, msg: String) -> None:
        try:
            self._objects = parse_object_observations(
                msg.data, stamp_s=time.monotonic()
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.get_logger().warn(f"ignored bad object indication: {exc}")

    def _on_detections(self, msg: AprilTagDetectionArray) -> None:
        # Jazzy apriltag_msgs/AprilTagDetection carries IDs/corners only; pose is
        # published on /tf. Keep this subscription as the detector activity input
        # and for compatibility with pose-bearing messages on other distros.
        now_s = time.monotonic()
        detections = [
            detection
            for detection in (
                self._tag_detection(raw_detection, now_s)
                for raw_detection in msg.detections
            )
            if detection is not None
        ]
        if not detections:
            return
        self._publish_scene(detections=detections, stamp_s=now_s)

    def _on_tf(self, msg: TFMessage) -> None:
        now_s = time.monotonic()
        detections = [
            detection
            for detection in (
                self._tag_detection_from_transform(transform, now_s)
                for transform in msg.transforms
            )
            if detection is not None
        ]
        if not detections:
            return
        self._publish_scene(detections=detections, stamp_s=now_s)

    def _publish_scene(
        self, *, detections: list[TagDetection2D], stamp_s: float
    ) -> None:
        try:
            scene = build_scene_map(
                anchors=self._anchors,
                detections=detections,
                object_observations=self._objects,
                camera_in_robot=self._camera_in_robot,
                frame_id=self._map_frame,
                stamp_s=stamp_s,
            )
        except ValueError as exc:
            self.get_logger().warn(f"scene map unavailable: {exc}")
            return

        self._map_pub.publish(String(data=scene.to_json_string()))

    def _tag_detection(self, detection: Any, now_s: float) -> TagDetection2D | None:
        tag_id = self._tag_id(detection)
        if tag_id is None:
            return None
        pose = getattr(
            getattr(getattr(detection, "pose", None), "pose", None), "pose", None
        )
        position = getattr(pose, "position", None)
        if position is None:
            return None

        yaw_rad = self._yaw_from_orientation(getattr(pose, "orientation", None))
        return TagDetection2D(
            tag_id=tag_id,
            camera_from_tag=camera_from_apriltag_translation(
                optical_x_m=float(getattr(position, "x", 0.0)),
                optical_z_m=float(getattr(position, "z", 0.0)),
                yaw_rad=yaw_rad,
            ),
            stamp_s=now_s,
            confidence=None,
        )

    def _tag_detection_from_transform(
        self, transform_stamped: Any, now_s: float
    ) -> TagDetection2D | None:
        tag_id = tag_id_from_frame_id(
            str(getattr(transform_stamped, "child_frame_id", ""))
        )
        if tag_id is None:
            return None
        transform = getattr(transform_stamped, "transform", None)
        translation = getattr(transform, "translation", None)
        if translation is None:
            return None
        yaw_rad = self._yaw_from_orientation(getattr(transform, "rotation", None))
        return TagDetection2D(
            tag_id=tag_id,
            camera_from_tag=camera_from_apriltag_translation(
                optical_x_m=float(getattr(translation, "x", 0.0)),
                optical_z_m=float(getattr(translation, "z", 0.0)),
                yaw_rad=yaw_rad,
            ),
            stamp_s=now_s,
            confidence=None,
        )

    @staticmethod
    def _tag_id(detection: Any) -> int | None:
        value = getattr(detection, "id", None)
        if isinstance(value, int):
            return value
        if isinstance(value, (list, tuple)) and value and isinstance(value[0], int):
            return value[0]
        return None

    @staticmethod
    def _yaw_from_orientation(orientation: Any) -> float:
        if orientation is None:
            return 0.0
        x = float(getattr(orientation, "x", 0.0))
        y = float(getattr(orientation, "y", 0.0))
        z = float(getattr(orientation, "z", 0.0))
        w = float(getattr(orientation, "w", 1.0))
        return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SceneMapNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
