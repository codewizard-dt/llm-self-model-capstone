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


from .object_detection import Detection, detections_payload


class YoloNcnnNode(Node):
    def __init__(self) -> None:
        from sensor_msgs.msg import Image

        super().__init__("yolo_ncnn")
        self.declare_parameter("model_path", "")
        self.declare_parameter("image_topic", "/camera/image_rect")
        self.declare_parameter("detections_topic", "/vision/object_detections")
        self.declare_parameter("confidence_threshold", 0.35)
        self.declare_parameter("nms_iou_threshold", 0.45)
        self.declare_parameter("max_hz", 5.0)
        self.declare_parameter("classes_json", "[]")
        self.declare_parameter("class_names_json", "{}")
        self.declare_parameter("input_size", 640)
        self.declare_parameter("input_name", "")
        self.declare_parameter("output_name", "")

        self._model_path = (
            self.get_parameter("model_path").get_parameter_value().string_value
        )
        if not self._model_path:
            raise RuntimeError("model_path is required when yolo_ncnn_node is launched")

        self._confidence_threshold = (
            self.get_parameter("confidence_threshold")
            .get_parameter_value()
            .double_value
        )
        self._nms_iou_threshold = (
            self.get_parameter("nms_iou_threshold").get_parameter_value().double_value
        )
        max_hz = self.get_parameter("max_hz").get_parameter_value().double_value
        self._min_period_s = 0.0 if max_hz <= 0.0 else 1.0 / max_hz
        self._last_inference_s = 0.0
        self._class_filter = self._parse_class_filter(
            self.get_parameter("classes_json").get_parameter_value().string_value
        )
        self._detector = DirectNcnnYoloDetector(
            model_path=self._model_path,
            input_size=(
                self.get_parameter("input_size").get_parameter_value().integer_value
            ),
            input_name=(
                self.get_parameter("input_name").get_parameter_value().string_value
            ),
            output_name=(
                self.get_parameter("output_name").get_parameter_value().string_value
            ),
            class_names=self._parse_class_names(
                self.get_parameter("class_names_json")
                .get_parameter_value()
                .string_value
            ),
        )
        self._pub = self.create_publisher(
            String,
            self.get_parameter("detections_topic").get_parameter_value().string_value,
            10,
        )
        self.create_subscription(
            Image,
            self.get_parameter("image_topic").get_parameter_value().string_value,
            self._on_image,
            2,
        )

    def _on_image(self, msg) -> None:
        now_s = time.monotonic()
        if now_s - self._last_inference_s < self._min_period_s:
            return
        self._last_inference_s = now_s
        try:
            frame = image_to_bgr_array(msg)
            detections = self._detector.predict(
                frame,
                confidence_threshold=self._confidence_threshold,
                nms_iou_threshold=self._nms_iou_threshold,
                stamp_s=now_s,
            )
            if self._class_filter:
                detections = [
                    detection
                    for detection in detections
                    if detection.label in self._class_filter
                ]
        except Exception as exc:
            self.get_logger().warn(f"YOLO NCNN inference skipped: {exc}")
            return

        self._pub.publish(
            String(
                data=detections_payload(
                    detections=detections,
                    width=int(msg.width),
                    height=int(msg.height),
                    frame_id=str(msg.header.frame_id),
                    stamp_s=now_s,
                    model_path=self._model_path,
                )
            )
        )

    @staticmethod
    def _parse_class_filter(raw: str) -> set[str]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return set()
        if not isinstance(parsed, list):
            return set()
        return {str(item) for item in parsed}

    @staticmethod
    def _parse_class_names(raw: str) -> dict[int, str]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, list):
            return {index: str(label) for index, label in enumerate(parsed)}
        if isinstance(parsed, dict):
            return {int(key): str(value) for key, value in parsed.items()}
        return {}


class DirectNcnnYoloDetector:
    def __init__(
        self,
        *,
        model_path: str,
        input_size: int,
        input_name: str,
        output_name: str,
        class_names: dict[int, str],
    ) -> None:
        from pathlib import Path

        import ncnn  # type: ignore[import-not-found]

        root = Path(model_path)
        if root.is_dir():
            param_files = sorted(root.glob("*.param"))
            bin_files = sorted(root.glob("*.bin"))
            if not param_files or not bin_files:
                raise FileNotFoundError(
                    f"NCNN model dir must contain .param and .bin: {root}"
                )
            param_path, bin_path = param_files[0], bin_files[0]
        else:
            param_path = root.with_suffix(".param")
            bin_path = root.with_suffix(".bin")
        if not param_path.exists() or not bin_path.exists():
            raise FileNotFoundError(f"missing NCNN model files for {model_path}")

        self._ncnn = ncnn
        self._net = ncnn.Net()
        self._net.opt.use_vulkan_compute = False
        self._net.opt.num_threads = 4
        if self._net.load_param(str(param_path)) != 0:
            raise RuntimeError(f"failed to load NCNN params: {param_path}")
        if self._net.load_model(str(bin_path)) != 0:
            raise RuntimeError(f"failed to load NCNN weights: {bin_path}")
        self._input_size = max(32, int(input_size))
        self._input_name = input_name or self._default_name(
            self._net.input_names(), "in0"
        )
        self._output_name = output_name or self._default_name(
            self._net.output_names(), "out0"
        )
        self._class_names = class_names

    def predict(
        self,
        frame: Any,
        *,
        confidence_threshold: float,
        nms_iou_threshold: float,
        stamp_s: float,
    ) -> list[Detection]:
        import numpy as np

        padded, scale, pad_x, pad_y = letterbox(frame, self._input_size)
        mat = self._ncnn.Mat.from_pixels(
            padded,
            self._ncnn.Mat.PixelType.PIXEL_BGR2RGB,
            self._input_size,
            self._input_size,
        )
        mat.substract_mean_normalize([], [1.0 / 255.0, 1.0 / 255.0, 1.0 / 255.0])
        extractor = self._net.create_extractor()
        extractor.input(self._input_name, mat)
        ret, output = extractor.extract(self._output_name)
        if ret != 0:
            raise RuntimeError(f"NCNN inference failed for output {self._output_name}")

        predictions = normalize_yolo_output(np.array(output.numpy(), dtype=np.float32))
        original_h, original_w = frame.shape[:2]
        candidates = [
            detection
            for detection in (
                parse_yolo_row(
                    row,
                    confidence_threshold=confidence_threshold,
                    class_names=self._class_names,
                    stamp_s=stamp_s,
                    scale=scale,
                    pad_x=pad_x,
                    pad_y=pad_y,
                    original_w=original_w,
                    original_h=original_h,
                )
                for row in predictions
            )
            if detection is not None
        ]
        return non_max_suppression(candidates, iou_threshold=nms_iou_threshold)

    @staticmethod
    def _default_name(names: Any, fallback: str) -> str:
        try:
            values = list(names)
        except TypeError:
            return fallback
        return str(values[0]) if values else fallback


def image_to_bgr_array(msg):
    import numpy as np

    channels_by_encoding = {
        "bgr8": 3,
        "rgb8": 3,
        "bgra8": 4,
        "rgba8": 4,
        "mono8": 1,
    }
    channels = channels_by_encoding.get(msg.encoding)
    if channels is None:
        raise ValueError(f"unsupported image encoding {msg.encoding!r}")
    expected = int(msg.height) * int(msg.width) * channels
    data = np.frombuffer(msg.data, dtype=np.uint8)
    if data.size < expected:
        raise ValueError(
            f"image buffer too small: expected at least {expected}, got {data.size}"
        )
    frame = data[:expected].reshape((int(msg.height), int(msg.width), channels))
    if msg.encoding == "rgb8":
        frame = frame[:, :, ::-1]
    if msg.encoding == "bgra8":
        frame = frame[:, :, :3]
    if msg.encoding == "rgba8":
        frame = frame[:, :, 2::-1]
    if msg.encoding == "mono8":
        frame = np.repeat(frame, 3, axis=2)
    return frame


def letterbox(frame: Any, input_size: int):
    import cv2
    import numpy as np

    height, width = frame.shape[:2]
    scale = min(input_size / width, input_size / height)
    resized_w = max(1, int(round(width * scale)))
    resized_h = max(1, int(round(height * scale)))
    resized = cv2.resize(frame, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)
    padded = np.full((input_size, input_size, 3), 114, dtype=np.uint8)
    pad_x = (input_size - resized_w) // 2
    pad_y = (input_size - resized_h) // 2
    padded[pad_y : pad_y + resized_h, pad_x : pad_x + resized_w] = resized
    return padded, scale, pad_x, pad_y


def normalize_yolo_output(raw: Any):
    import numpy as np

    arr = np.squeeze(raw)
    if arr.ndim != 2:
        raise ValueError(f"unsupported YOLO NCNN output shape {raw.shape}")
    if arr.shape[0] < arr.shape[1] and arr.shape[0] <= 256:
        arr = arr.T
    if arr.shape[1] < 6:
        raise ValueError(f"YOLO output must have at least 6 columns, got {arr.shape}")
    return arr


def parse_yolo_row(
    row: Any,
    *,
    confidence_threshold: float,
    class_names: dict[int, str],
    stamp_s: float,
    scale: float,
    pad_x: int,
    pad_y: int,
    original_w: int,
    original_h: int,
) -> Detection | None:
    class_scores = row[4:]
    objectness = 1.0
    if row.shape[0] >= 7 and row[4] <= 1.0 and max(row[5:]) <= 1.0:
        objectness = float(row[4])
        class_scores = row[5:]
    class_id = int(class_scores.argmax())
    confidence = objectness * float(class_scores[class_id])
    if confidence < confidence_threshold:
        return None

    cx, cy, width, height = (float(value) for value in row[:4])
    x1 = (cx - width / 2.0 - pad_x) / scale
    y1 = (cy - height / 2.0 - pad_y) / scale
    x2 = (cx + width / 2.0 - pad_x) / scale
    y2 = (cy + height / 2.0 - pad_y) / scale
    x1 = max(0.0, min(float(original_w), x1))
    y1 = max(0.0, min(float(original_h), y1))
    x2 = max(0.0, min(float(original_w), x2))
    y2 = max(0.0, min(float(original_h), y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return Detection(
        label=class_names.get(class_id, str(class_id)),
        class_id=class_id,
        confidence=confidence,
        bbox_xyxy=(x1, y1, x2, y2),
        stamp_s=stamp_s,
    )


def non_max_suppression(
    detections: list[Detection], *, iou_threshold: float
) -> list[Detection]:
    kept: list[Detection] = []
    for detection in sorted(detections, key=lambda item: item.confidence, reverse=True):
        if any(
            detection.class_id == other.class_id
            and bbox_iou(detection.bbox_xyxy, other.bbox_xyxy) > iou_threshold
            for other in kept
        ):
            continue
        kept.append(detection)
    return kept


def bbox_iou(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection
    return 0.0 if union <= 0.0 else intersection / union


def main(args=None) -> None:
    if rclpy is None:
        raise RuntimeError("rclpy is required to run yolo_ncnn_node")
    rclpy.init(args=args)
    node = YoloNcnnNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
