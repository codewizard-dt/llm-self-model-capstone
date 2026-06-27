from __future__ import annotations

import time

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


from .object_detection import Detection, detections_payload
from .yolo_ncnn_node import image_to_bgr_array


class YellowBallDetectorNode(Node):
    def __init__(self) -> None:
        from sensor_msgs.msg import Image

        super().__init__("yellow_ball_detector")
        self.declare_parameter("image_topic", "/camera/image_rect")
        self.declare_parameter("detections_topic", "/vision/object_detections")
        self.declare_parameter("max_hz", 8.0)
        self.declare_parameter("min_area_px", 200.0)
        self.declare_parameter("min_circularity", 0.55)
        self.declare_parameter("max_detections", 1)
        self.declare_parameter("h_min", 20)
        self.declare_parameter("s_min", 80)
        self.declare_parameter("v_min", 100)
        self.declare_parameter("h_max", 45)
        self.declare_parameter("s_max", 255)
        self.declare_parameter("v_max", 255)
        self.declare_parameter("label", "yellow_ball")

        max_hz = float(self.get_parameter("max_hz").value)
        self._min_period_s = 0.0 if max_hz <= 0.0 else 1.0 / max_hz
        self._last_detection_s = 0.0
        self._min_area_px = float(self.get_parameter("min_area_px").value)
        self._min_circularity = float(self.get_parameter("min_circularity").value)
        self._max_detections = int(self.get_parameter("max_detections").value)
        self._hsv_lower = (
            int(self.get_parameter("h_min").value),
            int(self.get_parameter("s_min").value),
            int(self.get_parameter("v_min").value),
        )
        self._hsv_upper = (
            int(self.get_parameter("h_max").value),
            int(self.get_parameter("s_max").value),
            int(self.get_parameter("v_max").value),
        )
        self._label = str(self.get_parameter("label").value)
        self._pub = self.create_publisher(
            String,
            str(self.get_parameter("detections_topic").value),
            10,
        )
        self.create_subscription(
            Image,
            str(self.get_parameter("image_topic").value),
            self._on_image,
            2,
        )

    def _on_image(self, msg) -> None:
        now_s = time.monotonic()
        if now_s - self._last_detection_s < self._min_period_s:
            return
        self._last_detection_s = now_s
        try:
            frame = image_to_bgr_array(msg)
            detections = detect_yellow_balls(
                frame,
                label=self._label,
                min_area_px=self._min_area_px,
                min_circularity=self._min_circularity,
                max_detections=self._max_detections,
                hsv_lower=self._hsv_lower,
                hsv_upper=self._hsv_upper,
                stamp_s=now_s,
            )
        except Exception as exc:
            self.get_logger().warn(f"yellow ball detection skipped: {exc}")
            return

        self._pub.publish(
            String(
                data=detections_payload(
                    detections=detections,
                    width=int(msg.width),
                    height=int(msg.height),
                    frame_id=str(msg.header.frame_id),
                    stamp_s=now_s,
                    model_path="yellow_hsv",
                    source="yellow_ball_color",
                )
            )
        )


def detect_yellow_balls(
    frame,
    *,
    label: str = "yellow_ball",
    min_area_px: float = 200.0,
    min_circularity: float = 0.55,
    max_detections: int = 1,
    hsv_lower: tuple[int, int, int] = (20, 80, 100),
    hsv_upper: tuple[int, int, int] = (45, 255, 255),
    stamp_s: float | None = None,
) -> list[Detection]:
    import cv2
    import numpy as np

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # OpenCV hue is 0..179. The default range is tuned for the yellow ball
    # proof scene and intentionally excludes the warmer yellow/orange VEX box.
    lower = np.array(hsv_lower, dtype=np.uint8)
    upper = np.array(hsv_upper, dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((5, 5), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detections_by_area: list[tuple[float, Detection]] = []
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < min_area_px:
            continue
        perimeter = float(cv2.arcLength(contour, True))
        if perimeter <= 0.0:
            continue
        circularity = 4.0 * 3.141592653589793 * area / (perimeter * perimeter)
        if circularity < min_circularity:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        fill_ratio = area / float(max(1, width * height))
        confidence = max(0.0, min(1.0, 0.5 * circularity + 0.5 * fill_ratio))
        detections_by_area.append(
            (
                area,
                Detection(
                    label=label,
                    class_id=0,
                    confidence=confidence,
                    bbox_xyxy=(float(x), float(y), float(x + width), float(y + height)),
                    stamp_s=stamp_s,
                    metadata={
                        "area_px": area,
                        "circularity": circularity,
                        "fill_ratio": fill_ratio,
                        "source": "yellow_hsv",
                    },
                ),
            )
        )
    detections = [
        detection
        for _, detection in sorted(
            detections_by_area, key=lambda item: item[0], reverse=True
        )
    ]
    return detections[: max(0, max_detections)]


def main(args=None) -> None:
    if rclpy is None:
        raise RuntimeError("rclpy is required to run yellow_ball_detector_node")
    rclpy.init(args=args)
    node = YellowBallDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
