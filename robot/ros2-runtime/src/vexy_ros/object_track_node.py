from __future__ import annotations

import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .object_tracking import (
    ObjectTracker,
    object_tracks_json,
    parse_object_indications,
)


class ObjectTrackNode(Node):
    def __init__(self) -> None:
        super().__init__("object_track")
        self.declare_parameter("indications_topic", "/vision/object_indications")
        self.declare_parameter("tracks_topic", "/vision/object_tracks")
        self.declare_parameter("publish_hz", 4.0)
        self.declare_parameter("min_hits", 3)
        self.declare_parameter("association_gate_m", 0.25)
        self.declare_parameter("stale_after_s", 0.75)
        self.declare_parameter("expire_after_s", 3.0)
        self.declare_parameter("include_expired", False)

        self._tracker = ObjectTracker(
            min_hits=int(self.get_parameter("min_hits").value),
            association_gate_m=float(self.get_parameter("association_gate_m").value),
            stale_after_s=float(self.get_parameter("stale_after_s").value),
            expire_after_s=float(self.get_parameter("expire_after_s").value),
        )
        self._include_expired = bool(self.get_parameter("include_expired").value)
        self._pub = self.create_publisher(
            String,
            str(self.get_parameter("tracks_topic").value),
            10,
        )
        self.create_subscription(
            String,
            str(self.get_parameter("indications_topic").value),
            self._on_indications,
            10,
        )
        publish_hz = float(self.get_parameter("publish_hz").value)
        period_s = 0.5 if publish_hz <= 0.0 else 1.0 / publish_hz
        self.create_timer(period_s, self._publish_tracks)

    def _on_indications(self, msg: String) -> None:
        now_s = time.monotonic()
        try:
            indications = parse_object_indications(msg.data, stamp_s=now_s)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self.get_logger().warn(f"ignored bad object indication: {exc}")
            return
        self._tracker.update(indications, now_s=now_s)
        self._publish_tracks()

    def _publish_tracks(self) -> None:
        now_s = time.monotonic()
        self._pub.publish(
            String(
                data=object_tracks_json(
                    self._tracker,
                    now_s=now_s,
                    include_expired=self._include_expired,
                )
            )
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ObjectTrackNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
