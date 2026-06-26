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
    DEFAULT_CAMERA_IN_ROBOT,
    TagDetection2D,
    build_scene_map,
    camera_from_apriltag_translation,
    localization_confidence,
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
        self.declare_parameter("camera_in_robot_json", DEFAULT_CAMERA_IN_ROBOT)
        self.declare_parameter("publish_hz", 3.0)
        self.declare_parameter("tag_max_age_s", 0.75)

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
        self._latest_detections: dict[int, TagDetection2D] = {}
        self._last_scene_payload: dict[str, Any] | None = None
        self._last_pose_stamp_s: float | None = None
        self._tag_max_age_s = float(self.get_parameter("tag_max_age_s").value)

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
        self.create_subscription(
            String,
            "/vision/object_tracks",
            self._on_object_tracks,
            10,
        )
        publish_hz = float(self.get_parameter("publish_hz").value)
        period_s = 0.5 if publish_hz <= 0.0 else 1.0 / publish_hz
        self.create_timer(period_s, self._publish_scene)

    def _on_object_indications(self, msg: String) -> None:
        try:
            self._objects = parse_object_observations(
                msg.data, stamp_s=time.monotonic()
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.get_logger().warn(f"ignored bad object indication: {exc}")

    def _on_object_tracks(self, msg: String) -> None:
        try:
            self._objects = parse_object_observations(
                msg.data, stamp_s=time.monotonic()
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.get_logger().warn(f"ignored bad object tracks: {exc}")

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
        self._remember_detections(detections)
        self._publish_scene(stamp_s=now_s)

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
        self._remember_detections(detections)
        self._publish_scene(stamp_s=now_s)

    def _publish_scene(self, *, stamp_s: float | None = None) -> None:
        now_s = time.monotonic() if stamp_s is None else stamp_s
        detections = [
            detection
            for detection in self._latest_detections.values()
            if now_s - detection.stamp_s <= self._tag_max_age_s
        ]
        if not detections:
            self._publish_stale_scene(now_s=now_s)
            return
        try:
            scene = build_scene_map(
                anchors=self._anchors,
                detections=detections,
                object_observations=self._objects,
                camera_in_robot=self._camera_in_robot,
                frame_id=self._map_frame,
                stamp_s=now_s,
            )
        except ValueError as exc:
            self.get_logger().warn(f"scene map unavailable: {exc}")
            return

        payload = scene.to_json()
        self._last_scene_payload = payload
        self._last_pose_stamp_s = now_s
        self._map_pub.publish(
            String(data=json.dumps(payload, separators=(",", ":"), sort_keys=True))
        )

    def _remember_detections(self, detections: list[TagDetection2D]) -> None:
        for detection in detections:
            self._latest_detections[detection.tag_id] = detection

    def _publish_stale_scene(self, *, now_s: float) -> None:
        if self._last_scene_payload is None or self._last_pose_stamp_s is None:
            return
        payload = json.loads(json.dumps(self._last_scene_payload))
        pose_age_s = max(0.0, now_s - self._last_pose_stamp_s)
        localization = dict(payload.get("localization") or {})
        visible_anchor_count = int(localization.get("visible_anchor_count", 0))
        tag_residual_m = float(localization.get("tag_residual_m", 0.0))
        tag_residual_deg = float(localization.get("tag_residual_deg", 0.0))
        localization.update(
            {
                "source": "stale_apriltag",
                "pose_age_s": pose_age_s,
                "pose_confidence": localization_confidence(
                    visible_anchor_count=visible_anchor_count,
                    tag_residual_m=tag_residual_m,
                    tag_residual_deg=tag_residual_deg,
                    pose_age_s=pose_age_s,
                ),
            }
        )
        payload["stamp_s"] = now_s
        payload["localization"] = localization
        self._last_scene_payload = payload
        self._map_pub.publish(
            String(data=json.dumps(payload, separators=(",", ":"), sort_keys=True))
        )

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
