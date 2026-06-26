from __future__ import annotations

import json
import time
from typing import Any

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except ModuleNotFoundError:  # pragma: no cover - allows pure helper tests off ROS.
    rclpy = None  # type: ignore[assignment]

    class Node:  # type: ignore[no-redef]
        pass

    class String:  # type: ignore[no-redef]
        def __init__(self, *, data: str = "") -> None:
            self.data = data


from .object_detection import Detection, parse_detections_payload
from .yolo_ncnn_node import image_to_bgr_array


class ObjectOverlayNode(Node):
    def __init__(self) -> None:
        from sensor_msgs.msg import Image

        super().__init__("object_overlay")
        self.declare_parameter("image_topic", "/camera/image_rect")
        self.declare_parameter("detections_topic", "/vision/object_detections")
        self.declare_parameter("overlay_topic", "/vision/object_overlay")
        self.declare_parameter("max_detection_age_s", 0.5)

        self._detections: list[Detection] = []
        self._last_detection_s = 0.0
        self._max_detection_age_s = float(
            self.get_parameter("max_detection_age_s").value
        )
        self._pub = self.create_publisher(
            Image,
            str(self.get_parameter("overlay_topic").value),
            2,
        )
        self.create_subscription(
            Image,
            str(self.get_parameter("image_topic").value),
            self._on_image,
            2,
        )
        self.create_subscription(
            String,
            str(self.get_parameter("detections_topic").value),
            self._on_detections,
            10,
        )

    def _on_detections(self, msg: String) -> None:
        try:
            self._detections = parse_detections_payload(msg.data)
            self._last_detection_s = time.monotonic()
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self.get_logger().warn(f"object overlay ignored detections: {exc}")

    def _on_image(self, msg: Any) -> None:
        try:
            frame = image_to_bgr_array(msg)
            detections = (
                self._detections
                if time.monotonic() - self._last_detection_s
                <= self._max_detection_age_s
                else []
            )
            overlay = draw_detections(frame, detections)
            out = bgr_array_to_image_msg(overlay, header=msg.header)
        except Exception as exc:
            self.get_logger().warn(f"object overlay skipped frame: {exc}")
            return
        self._pub.publish(out)


def draw_detections(frame: Any, detections: list[Detection]):
    import cv2

    overlay = frame.copy()
    for detection in detections:
        x1, y1, x2, y2 = _clamped_box(
            detection.bbox_xyxy, overlay.shape[1], overlay.shape[0]
        )
        if x2 <= x1 or y2 <= y1:
            continue
        color = (0, 255, 0)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
        label = f"{detection.label} {detection.confidence:.2f}"
        (text_w, text_h), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        label_y = max(text_h + baseline + 2, y1)
        cv2.rectangle(
            overlay,
            (x1, label_y - text_h - baseline - 4),
            (min(overlay.shape[1] - 1, x1 + text_w + 6), label_y + 2),
            color,
            -1,
        )
        cv2.putText(
            overlay,
            label,
            (x1 + 3, label_y - baseline - 1),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
    return overlay


def bgr_array_to_image_msg(frame: Any, *, header: Any):
    from sensor_msgs.msg import Image

    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("overlay frame must be HxWx3 BGR")
    msg = Image()
    msg.header = header
    msg.height = int(frame.shape[0])
    msg.width = int(frame.shape[1])
    msg.encoding = "bgr8"
    msg.is_bigendian = 0
    msg.step = int(frame.shape[1] * 3)
    msg.data = frame.tobytes()
    return msg


def _clamped_box(
    bbox: tuple[float, float, float, float], width: int, height: int
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    return (
        max(0, min(width - 1, int(round(x1)))),
        max(0, min(height - 1, int(round(y1)))),
        max(0, min(width - 1, int(round(x2)))),
        max(0, min(height - 1, int(round(y2)))),
    )


def main(args=None) -> None:
    if rclpy is None:
        raise RuntimeError("rclpy is required to run object_overlay_node")
    rclpy.init(args=args)
    node = ObjectOverlayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
