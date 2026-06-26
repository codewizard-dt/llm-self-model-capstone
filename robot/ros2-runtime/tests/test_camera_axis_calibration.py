"""Stationary camera-to-robot centerline calibration harness.

Run on the Raspberry Pi with a white measuring tape laid on the robot forward
axis:

    cd /home/vexy/llm-self-model-capstone
    source /opt/ros/jazzy/setup.bash
    source /home/vexy/ros2_ws/install/setup.bash
    python3 operator/tests/test_camera_axis_calibration.py

The robot stays still. The script samples /camera/image_rect, detects the white
tape line, and records image-space offsets that should drive camera_in_robot
y_m/yaw_rad calibration.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

from vexy_ros.bridge_protocol import now_ms, normalize_outbound
from vexy_ros.yolo_ncnn_node import image_to_bgr_array


STACK_SERVICE = "vexy-ros-stack.service"


@dataclass(frozen=True)
class TapeEstimate:
    stamp_s: float
    width_px: int
    height_px: int
    mask_area_px: int
    bottom_y_px: float
    mid_y_px: float
    bottom_x_px: float
    mid_x_px: float
    bottom_offset_px: float
    mid_offset_px: float
    line_angle_deg: float
    confidence: float


def ensure_stack_running() -> None:
    result = subprocess.run(
        ["systemctl", "--user", "is-active", STACK_SERVICE],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout.strip() == "active":
        print(f"  {STACK_SERVICE} already active.")
        return
    print(f"  Starting {STACK_SERVICE}...")
    subprocess.run(["systemctl", "--user", "restart", STACK_SERVICE], check=True)
    print("  Waiting 10 s for stack warmup...")
    time.sleep(10)


def _prompt(message: str) -> str:
    try:
        return input(message).strip()
    except EOFError:
        return ""


def detect_white_tape(
    frame: Any,
    *,
    min_value: int,
    max_saturation: int,
    roi_top_fraction: float,
    min_area_px: int,
) -> TapeEstimate | None:
    import cv2
    import numpy as np

    height, width = frame.shape[:2]
    roi_top = int(max(0, min(height - 1, round(height * roi_top_fraction))))
    roi = frame[roi_top:, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lower = np.array([0, 0, min_value], dtype=np.uint8)
    upper = np.array([179, max_saturation, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((5, 5), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    points = cv2.findNonZero(mask)
    if points is None or len(points) < min_area_px:
        return None

    points_f = points.reshape(-1, 2).astype(np.float32)
    points_f[:, 1] += float(roi_top)
    vx, vy, x0, y0 = (float(v) for v in cv2.fitLine(points_f, cv2.DIST_L2, 0, 0.01, 0.01))
    if abs(vy) < 1e-6:
        return None

    bottom_y = float(height - 1)
    mid_y = float(roi_top + (height - roi_top) * 0.5)
    bottom_x = x0 + (bottom_y - y0) * vx / vy
    mid_x = x0 + (mid_y - y0) * vx / vy
    center_x = (width - 1) / 2.0
    vertical_angle_deg = math.degrees(math.atan2(vx, vy))
    area = int(len(points_f))
    roi_area = max(1, (height - roi_top) * width)
    confidence = min(1.0, area / float(max(min_area_px, roi_area * 0.08)))
    return TapeEstimate(
        stamp_s=time.monotonic(),
        width_px=width,
        height_px=height,
        mask_area_px=area,
        bottom_y_px=bottom_y,
        mid_y_px=mid_y,
        bottom_x_px=float(bottom_x),
        mid_x_px=float(mid_x),
        bottom_offset_px=float(bottom_x - center_x),
        mid_offset_px=float(mid_x - center_x),
        line_angle_deg=vertical_angle_deg,
        confidence=confidence,
    )


class CameraAxisCalibrationNode(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("camera_axis_calibration")
        self.args = args
        self.seq = 930000
        self.estimates: list[TapeEstimate] = []
        self._pub = self.create_publisher(String, "/vex/cmd", 10)
        self.create_subscription(Image, args.image_topic, self._on_image, 2)

    def stop(self, *, reason: str) -> None:
        self.seq += 1
        packet = normalize_outbound(
            {
                "v": 1,
                "seq": self.seq,
                "type": "cmd",
                "cmd": "stop",
                "sent_ms": now_ms(),
                "ttl_ms": 200,
                "reason": reason,
            }
        )
        self._pub.publish(String(data=json.dumps(packet, separators=(",", ":"))))

    def clear(self) -> None:
        self.estimates.clear()

    def spin_for(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)

    def _on_image(self, msg: Image) -> None:
        try:
            estimate = detect_white_tape(
                image_to_bgr_array(msg),
                min_value=self.args.min_value,
                max_saturation=self.args.max_saturation,
                roi_top_fraction=self.args.roi_top_fraction,
                min_area_px=self.args.min_area_px,
            )
        except Exception as exc:
            self.get_logger().warn(f"tape detection skipped: {exc}")
            return
        if estimate is not None:
            self.estimates.append(estimate)
            self.estimates = self.estimates[-100:]


def summarize_estimates(estimates: list[TapeEstimate]) -> dict[str, Any]:
    if not estimates:
        return {"status": "missing", "count": 0}
    bottom_offsets = [estimate.bottom_offset_px for estimate in estimates]
    mid_offsets = [estimate.mid_offset_px for estimate in estimates]
    angles = [estimate.line_angle_deg for estimate in estimates]
    confidences = [estimate.confidence for estimate in estimates]
    latest = estimates[-1]
    return {
        "status": "ok",
        "count": len(estimates),
        "latest": asdict(latest),
        "mean_bottom_offset_px": sum(bottom_offsets) / len(bottom_offsets),
        "mean_mid_offset_px": sum(mid_offsets) / len(mid_offsets),
        "mean_line_angle_deg": sum(angles) / len(angles),
        "mean_confidence": sum(confidences) / len(confidences),
    }


def print_summary(summary: dict[str, Any]) -> None:
    if summary["status"] != "ok":
        print("  tape: no line detected")
        return
    latest = summary["latest"]
    print(
        "  tape: "
        f"samples={summary['count']} "
        f"bottom_offset={summary['mean_bottom_offset_px']:.1f}px "
        f"mid_offset={summary['mean_mid_offset_px']:.1f}px "
        f"angle={summary['mean_line_angle_deg']:.2f}deg "
        f"confidence={summary['mean_confidence']:.2f}"
    )
    print(
        "  latest: "
        f"image={latest['width_px']}x{latest['height_px']} "
        f"bottom_x={latest['bottom_x_px']:.1f}px "
        f"mid_x={latest['mid_x_px']:.1f}px "
        f"mask_area={latest['mask_area_px']}px"
    )


def run_calibration(args: argparse.Namespace) -> list[dict[str, Any]]:
    if not args.skip_stack_start:
        print("=== pre-flight: camera stack ===")
        ensure_stack_running()

    rclpy.init()
    node = CameraAxisCalibrationNode(args)
    transcript: list[dict[str, Any]] = []
    try:
        print("=== camera forward-axis tape calibration ===")
        print("Robot will remain still. Lay the white tape along the robot forward centerline.")
        node.spin_for(args.settle_s)
        node.stop(reason="camera_axis_calibration_initial_stop")
        for index in range(args.rounds):
            _prompt(f"\nTape placement {index + 1}/{args.rounds} ready; press Enter to sample. ")
            node.clear()
            node.spin_for(args.sample_s)
            summary = summarize_estimates(node.estimates)
            print_summary(summary)
            transcript.append(
                {
                    "step": "tape_sample",
                    "index": index + 1,
                    "summary": summary,
                    "user_observation": _prompt("Physical note for this tape placement: "),
                }
            )
        return transcript
    finally:
        try:
            node.stop(reason="camera_axis_calibration_final_stop")
            node.spin_for(0.2)
        finally:
            node.destroy_node()
            rclpy.shutdown()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stationary white-tape camera centerline calibration harness."
    )
    parser.add_argument("--image-topic", default="/camera/image_rect")
    parser.add_argument("--sample-s", type=float, default=3.0)
    parser.add_argument("--settle-s", type=float, default=1.0)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--min-value", type=int, default=185)
    parser.add_argument("--max-saturation", type=int, default=70)
    parser.add_argument("--roi-top-fraction", type=float, default=0.45)
    parser.add_argument("--min-area-px", type=int, default=300)
    parser.add_argument(
        "--skip-stack-start",
        action="store_true",
        help=f"do not start/restart {STACK_SERVICE}",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        transcript = run_calibration(args)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(130)
    print("\n=== camera axis calibration transcript ===")
    print(json.dumps(transcript, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
