"""Stationary claw and ball-vision calibration harness.

Run on the Raspberry Pi with the V5 Brain program already running in slot 8:

    cd /home/vexy/llm-self-model-capstone
    source /opt/ros/jazzy/setup.bash
    source /home/vexy/ros2_ws/install/setup.bash
    python3 operator/tests/test_static_claw_ball_calibration.py

The harness keeps the drivetrain stopped. It only sends stop/release/grab
commands while collecting telemetry and ball-vision estimates.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import unittest
from dataclasses import asdict, dataclass
from typing import Any, Literal

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except ModuleNotFoundError as exc:
    raise unittest.SkipTest("ROS 2 Python packages are not installed") from exc

from vexy_ros.operator._core import (
    OperatorConfig,
    PrimitiveCommand,
    packet_from_primitive,
    telemetry_snapshot_from_mapping,
)
from vexy_ros.vision_map import (
    DEFAULT_CAMERA_IN_ROBOT,
    Pose2D,
    pose_from_mapping,
    robot_from_camera_pose,
)


STACK_SERVICE = "vexy-ros-stack.service"
BALL_LABELS = {"yellow ball", "yellow_ball", "sports ball", "sports_ball", "ball"}
CalibrationCommand = Literal["stop", "release", "grab"]
DEFAULT_BALL_POSITIONS = (
    "centered at the claw mouth",
    "slightly left of the claw mouth",
    "slightly right of the claw mouth",
    "too far in front of the claw",
    "inside the claw capture zone",
)


@dataclass(frozen=True)
class VisionEstimate:
    name: str
    age_s: float
    confidence: float | None
    camera_forward_m: float
    camera_left_m: float
    claw_forward_m: float
    claw_left_m: float
    in_capture_window: bool
    source: str


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


def _parse_json_payload(raw: str) -> Any | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _items_from_payload(payload: Any, *, list_key: str) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        raw_items = payload.get(list_key, payload.get("objects", payload))
    else:
        raw_items = payload
    if isinstance(raw_items, dict):
        raw_items = [raw_items]
    if not isinstance(raw_items, list):
        return []
    return [item for item in raw_items if isinstance(item, dict)]


def _label_for(item: dict[str, Any]) -> str:
    return str(item.get("label", item.get("name", "object"))).lower()


def _format_float(value: float | None, *, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _prompt(message: str) -> str:
    try:
        return input(message).strip()
    except EOFError:
        return ""


class StaticClawCalibrationNode(Node):
    def __init__(self, *, camera_in_robot_json: str) -> None:
        super().__init__("static_claw_ball_calibration")
        self.config = OperatorConfig()
        self.camera_in_robot = pose_from_mapping(json.loads(camera_in_robot_json))
        self.seq = 920000
        self.last_ack: dict[str, Any] | None = None
        self.last_telemetry_raw: dict[str, Any] | None = None
        self.last_telemetry_stamp_s: float | None = None
        self._detections: list[tuple[float, dict[str, Any]]] = []
        self._indications: list[tuple[float, dict[str, Any]]] = []

        self._pub = self.create_publisher(String, "/vex/cmd", 10)
        self.create_subscription(String, "/vex/telemetry", self._on_telemetry, 10)
        self.create_subscription(String, "/vex/ack", self._on_ack, 10)
        self.create_subscription(
            String, "/vision/object_detections", self._on_detections, 10
        )
        self.create_subscription(
            String, "/vision/object_indications", self._on_indications, 10
        )

    def send(
        self, cmd: CalibrationCommand, *, duration_ms: int | None = None, reason: str
    ) -> dict[str, Any]:
        self.seq += 1
        ttl_ms = max(200, min(1500, int(duration_ms or 200)))
        command = PrimitiveCommand(
            cmd=cmd,
            ttl_ms=ttl_ms,
            duration_ms=duration_ms,
            reason=reason,
        )
        packet = packet_from_primitive(command, seq=self.seq)
        self._pub.publish(
            String(data=json.dumps(packet, separators=(",", ":"), sort_keys=True))
        )
        print(
            f"  sent seq={packet['seq']} cmd={packet['cmd']} duration_ms={packet.get('duration_ms')}"
        )
        return packet

    def stop(self, *, reason: str) -> None:
        self.send("stop", reason=reason)

    def spin_for(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)

    def clear_vision_buffers(self) -> None:
        self._detections.clear()
        self._indications.clear()

    def telemetry_summary(self) -> dict[str, Any]:
        if self.last_telemetry_raw is None:
            return {"status": "missing"}
        snapshot = telemetry_snapshot_from_mapping(self.last_telemetry_raw)
        manipulator = snapshot.manipulator_sample
        return {
            "status": "ok",
            "age_s": (
                None
                if self.last_telemetry_stamp_s is None
                else round(time.monotonic() - self.last_telemetry_stamp_s, 3)
            ),
            "motion_enabled": snapshot.motion_enabled,
            "estop": snapshot.estop,
            "drive_ports_ok": snapshot.drive_ports_ok,
            "left_vel_rpm": snapshot.left_vel_rpm,
            "right_vel_rpm": snapshot.right_vel_rpm,
            "manipulator": None if manipulator is None else asdict(manipulator),
        }

    def print_telemetry_summary(self) -> None:
        summary = self.telemetry_summary()
        if summary["status"] != "ok":
            print("  telemetry: missing")
            return
        manipulator = summary["manipulator"] or {}
        print(
            "  telemetry: "
            f"motion_enabled={summary['motion_enabled']} "
            f"estop={summary['estop']} "
            f"drive_ports_ok={summary['drive_ports_ok']} "
            f"left_rpm={_format_float(summary['left_vel_rpm'], digits=1)} "
            f"right_rpm={_format_float(summary['right_vel_rpm'], digits=1)} "
            f"claw_pos_deg={_format_float(manipulator.get('position_deg'), digits=1)} "
            f"claw_vel_rpm={_format_float(manipulator.get('velocity_rpm'), digits=1)} "
            f"claw_current_a={_format_float(manipulator.get('current_amp'), digits=2)}"
        )

    def recent_detection_count(self, *, window_s: float) -> int:
        cutoff = time.monotonic() - window_s
        return sum(
            1
            for _, item in self._detections
            if _label_for(item) in BALL_LABELS and _ >= cutoff
        )

    def best_estimates(self, *, window_s: float) -> list[VisionEstimate]:
        now_s = time.monotonic()
        cutoff = now_s - window_s
        estimates: list[VisionEstimate] = []
        for stamp_s, item in self._indications:
            if stamp_s < cutoff or _label_for(item) not in BALL_LABELS:
                continue
            if "forward_m" not in item or "left_m" not in item:
                continue
            camera_from_object = Pose2D(
                float(item.get("forward_m", 0.0)),
                float(item.get("left_m", 0.0)),
                float(item.get("yaw_rad", 0.0)),
            )
            claw_from_object = robot_from_camera_pose(
                camera_from_object, self.camera_in_robot
            )
            confidence = item.get("confidence")
            estimates.append(
                VisionEstimate(
                    name=str(item.get("name", item.get("label", "ball"))),
                    age_s=now_s - stamp_s,
                    confidence=None if confidence is None else float(confidence),
                    camera_forward_m=camera_from_object.x_m,
                    camera_left_m=camera_from_object.y_m,
                    claw_forward_m=claw_from_object.x_m,
                    claw_left_m=claw_from_object.y_m,
                    in_capture_window=(
                        claw_from_object.x_m <= self.config.ball_capture_forward_m
                        and abs(claw_from_object.y_m)
                        <= self.config.ball_capture_lateral_m
                    ),
                    source=str(item.get("source", "object_indications")),
                )
            )
        return sorted(
            estimates,
            key=lambda estimate: (
                not estimate.in_capture_window,
                estimate.age_s,
                abs(estimate.claw_left_m),
            ),
        )

    def print_vision_summary(self, *, window_s: float) -> list[VisionEstimate]:
        detection_count = self.recent_detection_count(window_s=window_s)
        estimates = self.best_estimates(window_s=window_s)
        print(
            f"  raw yellow-ball detections in last {window_s:.1f}s: {detection_count}"
        )
        if not estimates:
            print("  object indications: no recent ball estimate")
            return []
        print(
            "  object indications "
            f"(capture <= {self.config.ball_capture_forward_m:.2f}m forward, "
            f"|left| <= {self.config.ball_capture_lateral_m:.2f}m):"
        )
        for estimate in estimates[:3]:
            print(
                "    "
                f"{estimate.name} conf={_format_float(estimate.confidence, digits=2)} "
                f"age={estimate.age_s:.2f}s "
                f"camera=({_format_float(estimate.camera_forward_m)}, "
                f"{_format_float(estimate.camera_left_m)})m "
                f"claw=({_format_float(estimate.claw_forward_m)}, "
                f"{_format_float(estimate.claw_left_m)})m "
                f"capture={estimate.in_capture_window}"
            )
        return estimates

    def _on_telemetry(self, msg: String) -> None:
        payload = _parse_json_payload(msg.data)
        if isinstance(payload, dict):
            self.last_telemetry_raw = payload
            self.last_telemetry_stamp_s = time.monotonic()

    def _on_ack(self, msg: String) -> None:
        payload = _parse_json_payload(msg.data)
        if isinstance(payload, dict):
            self.last_ack = payload

    def _on_detections(self, msg: String) -> None:
        payload = _parse_json_payload(msg.data)
        stamp_s = time.monotonic()
        for item in _items_from_payload(payload, list_key="detections"):
            self._detections.append((stamp_s, item))
        self._detections = self._detections[-100:]

    def _on_indications(self, msg: String) -> None:
        payload = _parse_json_payload(msg.data)
        stamp_s = time.monotonic()
        for item in _items_from_payload(payload, list_key="objects"):
            self._indications.append((stamp_s, item))
        self._indications = self._indications[-100:]


def run_calibration(args: argparse.Namespace) -> list[dict[str, Any]]:
    if not args.skip_stack_start:
        print("=== pre-flight: camera stack ===")
        ensure_stack_running()

    rclpy.init()
    node = StaticClawCalibrationNode(camera_in_robot_json=args.camera_in_robot_json)
    transcript: list[dict[str, Any]] = []
    try:
        print("=== stationary claw/ball calibration ===")
        print(
            "Make sure the robot has clear space around the claw. Drivetrain commands are not used."
        )
        node.spin_for(args.settle_s)
        node.stop(reason="static_calibration_initial_stop")
        node.spin_for(0.5)
        node.print_telemetry_summary()

        print("\nEstablishing start state: CLOSE the claw.")
        node.send(
            "grab",
            duration_ms=args.close_ms,
            reason="static_calibration_initial_close_claw",
        )
        node.spin_for(args.after_claw_s)
        node.stop(reason="static_calibration_stop_after_initial_close")
        node.spin_for(0.3)
        node.print_telemetry_summary()
        transcript.append(
            {
                "step": "initial_close_claw",
                "telemetry": node.telemetry_summary(),
                "user_observation": _prompt(
                    "Observed claw state after INITIAL CLOSE: "
                ),
            }
        )

        _prompt("\nPress Enter to OPEN the claw, or Ctrl-C to abort. ")
        node.send(
            "release",
            duration_ms=args.open_ms,
            reason="static_calibration_open_claw",
        )
        node.spin_for(args.after_claw_s)
        node.stop(reason="static_calibration_stop_after_open")
        node.spin_for(0.3)
        node.print_telemetry_summary()
        transcript.append(
            {
                "step": "open_claw",
                "telemetry": node.telemetry_summary(),
                "user_observation": _prompt("Observed claw state after OPEN: "),
            }
        )

        _prompt("\nPress Enter to CLOSE the claw, or Ctrl-C to abort. ")
        node.send(
            "grab", duration_ms=args.close_ms, reason="static_calibration_close_claw"
        )
        node.spin_for(args.after_claw_s)
        node.stop(reason="static_calibration_stop_after_close")
        node.spin_for(0.3)
        node.print_telemetry_summary()
        transcript.append(
            {
                "step": "close_claw",
                "telemetry": node.telemetry_summary(),
                "user_observation": _prompt("Observed claw state after CLOSE: "),
            }
        )

        if args.ball_rounds:
            _prompt(
                "\nPress Enter to REOPEN the claw for ball placement, or Ctrl-C to abort. "
            )
            node.send(
                "release",
                duration_ms=args.open_ms,
                reason="static_calibration_reopen_for_ball_samples",
            )
            node.spin_for(args.after_claw_s)
            node.stop(reason="static_calibration_stop_after_reopen")
            node.spin_for(0.3)
            node.print_telemetry_summary()
            transcript.append(
                {
                    "step": "reopen_for_ball_samples",
                    "telemetry": node.telemetry_summary(),
                    "user_observation": _prompt("Observed claw state after REOPEN: "),
                }
            )
            print("\n=== ball vision samples ===")
        for position in DEFAULT_BALL_POSITIONS if args.ball_rounds else ():
            _prompt(f"\nPlace the ball {position}, then press Enter to sample vision. ")
            node.clear_vision_buffers()
            node.spin_for(args.sample_s)
            node.print_telemetry_summary()
            estimates = node.print_vision_summary(window_s=args.sample_s)
            transcript.append(
                {
                    "step": "ball_sample",
                    "position": position,
                    "telemetry": node.telemetry_summary(),
                    "estimates": [asdict(estimate) for estimate in estimates[:3]],
                    "user_observation": _prompt(
                        "What do you physically see? Include visible/not visible and distance: "
                    ),
                }
            )

        return transcript
    finally:
        try:
            if rclpy.ok():
                node.stop(reason="static_calibration_final_stop")
                node.spin_for(0.3)
        finally:
            node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stationary claw and ball-vision calibration harness."
    )
    parser.add_argument(
        "--open-ms", type=int, default=600, help="release duration for opening claw"
    )
    parser.add_argument(
        "--close-ms", type=int, default=700, help="grab duration for closing claw"
    )
    parser.add_argument(
        "--after-claw-s", type=float, default=1.0, help="settle time after claw command"
    )
    parser.add_argument(
        "--sample-s", type=float, default=3.0, help="vision sample window per ball pose"
    )
    parser.add_argument(
        "--settle-s", type=float, default=1.0, help="initial ROS settle time"
    )
    parser.add_argument(
        "--camera-in-robot-json",
        default=DEFAULT_CAMERA_IN_ROBOT,
        help="camera pose in claw/robot frame as JSON",
    )
    parser.add_argument(
        "--skip-stack-start",
        action="store_true",
        help=f"do not start/restart {STACK_SERVICE}",
    )
    parser.add_argument(
        "--no-ball-rounds",
        dest="ball_rounds",
        action="store_false",
        help="only test open/close claw commands",
    )
    parser.set_defaults(ball_rounds=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        transcript = run_calibration(args)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(130)

    print("\n=== calibration transcript ===")
    print(json.dumps(transcript, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
