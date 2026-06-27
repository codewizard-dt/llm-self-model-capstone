"""Write /camera/image_rect frames as JPEG (or PPM fallback) files to disk.

Launched by start_operator_run_capture alongside vexy_telemetry_writer_node.
Saves one file per frame under <out_dir>/images/<wall_ms>.jpg at the requested fps.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any


def _save_frame(msg: Any, out_dir: Path, wall_ms: int) -> str:
    width = int(msg.width)
    height = int(msg.height)
    encoding = str(msg.encoding)
    data = bytes(msg.data)

    channels_by_encoding = {"bgr8": 3, "rgb8": 3, "mono8": 1}
    channels = channels_by_encoding.get(encoding)
    if channels is None:
        raise ValueError(f"unsupported image encoding {encoding!r}")

    try:
        import cv2
        import numpy as np

        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, channels))
        if encoding == "rgb8":
            arr = arr[:, :, ::-1]
        ok, buf = cv2.imencode(".jpg", arr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            raise ValueError("cv2.imencode failed")
        path = out_dir / f"{wall_ms:013d}.jpg"
        path.write_bytes(buf.tobytes())
        return path.name
    except (ImportError, ModuleNotFoundError):
        pass

    # PPM fallback (no cv2)
    if encoding == "bgr8":
        rgb = bytearray()
        for i in range(0, len(data), 3):
            rgb.extend([data[i + 2], data[i + 1], data[i]])
        rgb_bytes = bytes(rgb)
    elif encoding == "rgb8":
        rgb_bytes = data
    else:
        rgb_bytes = bytes(b for b in data for _ in range(3))
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path = out_dir / f"{wall_ms:013d}.ppm"
    path.write_bytes(header + rgb_bytes)
    return path.name


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--topic", default="/camera/image_rect")
    parser.add_argument("--fps", type=float, default=1.0)
    args = parser.parse_args()

    images_dir = args.out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image

    min_interval_s = 1.0 / max(0.01, args.fps)
    last_saved_s: float = 0.0

    class ImageWriterNode(Node):
        def __init__(self) -> None:
            super().__init__("vexy_image_writer")
            self.create_subscription(Image, args.topic, self._on_image, 2)
            self.get_logger().info(
                f"vexy_image_writer: {args.topic} → {images_dir} @ {args.fps} fps"
            )

        def _on_image(self, msg: Image) -> None:
            nonlocal last_saved_s
            now_s = time.monotonic()
            if now_s - last_saved_s < min_interval_s:
                return
            last_saved_s = now_s
            wall_ms = int(time.time() * 1000)
            try:
                name = _save_frame(msg, images_dir, wall_ms)
                self.get_logger().debug(f"saved {name}")
            except Exception as exc:
                self.get_logger().error(f"image write failed: {exc}")

    rclpy.init()
    node = ImageWriterNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
