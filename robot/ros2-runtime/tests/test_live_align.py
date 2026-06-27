"""Live integration test — align scenario.

Copy to the Pi, source the ROS workspace, then run:
    python3 test_live_align.py 0

Starts vexy-ros-stack.service if not already running.
Requires Brain slot 8 running and the requested AprilTag physically visible to the camera.
Exits 0 on success, 1 on failure or timeout.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
    from vexy_ros.operator_run_capture import (
        start_operator_run_capture,
        stop_operator_run_capture,
    )
except ModuleNotFoundError as exc:
    raise unittest.SkipTest("ROS 2 Python packages are not installed") from exc

STACK_SERVICE = "vexy-ros-stack.service"


def default_telemetry_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(f"/home/vexy/telemetry/live-align-{stamp}")


def ensure_stack_running() -> bool:
    r = subprocess.run(
        ["systemctl", "--user", "is-active", STACK_SERVICE],
        capture_output=True,
        text=True,
    )
    if r.stdout.strip() == "active":
        print(f"  {STACK_SERVICE} already active.")
    else:
        print(f"  Starting {STACK_SERVICE}...")
        subprocess.run(["systemctl", "--user", "restart", STACK_SERVICE], check=True)
        print("  Waiting 10 s for stack warmup...")
        time.sleep(10)
    return True


FAIL_REASONS = {"stuck", "spinout", "disabled", "unmapped_tag", "command_rejected"}


def build_steps(tag_id: int) -> list[tuple[str, dict, float]]:
    return [
        ("locate_nearest_apriltag", {}, 20.0),
        ("align_to_tag", {"tag_id": tag_id, "target_distance_m": 0.4064}, 20.0),
    ]


class AlignTestNode(Node):
    def __init__(self) -> None:
        super().__init__("operator_test_align")
        self._cmd_pub = self.create_publisher(String, "/operator/command", 10)
        self._last_result: dict | None = None
        self._last_rejection: dict | None = None
        self.create_subscription(String, "/operator/results", self._on_result, 10)
        self.create_subscription(String, "/operator/events", self._on_event, 10)

    def _on_result(self, msg: String) -> None:
        try:
            self._last_result = json.loads(msg.data)
        except json.JSONDecodeError:
            pass

    def _on_event(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
            print(f"  event: {payload.get('name')}  {payload.get('detail')}")
            if payload.get("name") == "command_rejected":
                self._last_rejection = payload
        except json.JSONDecodeError:
            pass

    def _send(self, action: str, extras: dict) -> None:
        self._cmd_pub.publish(
            String(data=json.dumps({"action": action, **extras}, separators=(",", ":")))
        )

    def _wait_for_result(self, action: str, timeout_s: float) -> dict | None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)
            result = self._last_result
            if result is None:
                continue
            outcome = result.get("outcome", {})
            if outcome.get("method") != action:
                self._last_result = None
                continue
            self._last_result = None
            return result
        return None

    def _reset_operator(self) -> bool:
        print("[reset_operator]")
        deadline = time.monotonic() + 5.0
        while self._cmd_pub.get_subscription_count() == 0:
            if time.monotonic() >= deadline:
                print("  TIMEOUT waiting for operator subscriber")
                return False
            rclpy.spin_once(self, timeout_sec=0.05)
        self._last_result = None
        self._send("reset_operator", {})
        result = self._wait_for_result("reset_operator", 3.0)
        if result is None:
            print("  TIMEOUT after 3.0s")
            return False
        outcome = result.get("outcome", {})
        if not outcome.get("success"):
            print(f"  FAIL  {outcome.get('reason')}")
            return False
        print(f"  OK  {outcome.get('reason')}")
        return True

    def run(self, tag_id: int) -> bool:
        print(f"=== align test: locate → align to AprilTag {tag_id} ===")
        if not self._reset_operator():
            return False
        for action, extras, timeout_s in build_steps(tag_id):
            extras_str = f"  extras={extras}" if extras else ""
            print(f"[{action}]{extras_str}")
            self._last_result = None
            self._last_rejection = None
            deadline = time.monotonic() + timeout_s
            succeeded = False
            last_sent = 0.0
            while time.monotonic() < deadline:
                rclpy.spin_once(self, timeout_sec=0.02)
                now = time.monotonic()
                if now - last_sent >= 0.05:
                    self._send(action, extras)
                    last_sent = now
                if self._last_rejection is not None:
                    detail = self._last_rejection.get("detail", {})
                    print(f"  FAIL  command_rejected: {detail.get('error')}")
                    return False
                result = self._last_result
                if result is None:
                    continue
                outcome = result.get("outcome", {})
                if outcome.get("method") != action:
                    self._last_result = None
                    continue
                self._last_result = None
                if outcome.get("success"):
                    print(f"  OK  {outcome.get('reason')}")
                    succeeded = True
                    break
                reason = outcome.get("reason", "")
                if reason in FAIL_REASONS:
                    print(f"  FAIL  {reason}")
                    return False
            if not succeeded:
                print(f"  TIMEOUT after {timeout_s}s")
                return False
        print("=== align test PASSED ===")
        return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tag_id",
        type=int,
        nargs="?",
        default=0,
        help="AprilTag ID to align to. The operator rejects IDs missing from the loaded map.",
    )
    parser.add_argument("--telemetry-dir", type=Path, default=None)
    parser.add_argument("--no-telemetry-capture", action="store_true")
    parser.add_argument("--capture-settle-s", type=float, default=1.0)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    print("=== pre-flight: camera stack ===")
    if not ensure_stack_running():
        sys.exit(1)
    telemetry_dir = args.telemetry_dir or default_telemetry_dir()
    capture_processes: list[subprocess.Popen] = []
    if not args.no_telemetry_capture:
        print(f"=== telemetry capture: {telemetry_dir} ===")
        capture_processes = start_operator_run_capture(
            telemetry_dir,
            label="test_live_align.py",
        )
        time.sleep(max(0.0, args.capture_settle_s))
    rclpy.init()
    node = AlignTestNode()
    try:
        ok = node.run(args.tag_id)
        sys.exit(0 if ok else 1)
    finally:
        node.destroy_node()
        rclpy.shutdown()
        stop_operator_run_capture(capture_processes)
        if capture_processes:
            print(f"=== telemetry written under: {telemetry_dir} ===")


if __name__ == "__main__":
    main()
