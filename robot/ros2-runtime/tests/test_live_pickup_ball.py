"""Live integration test — focused tag-1 ball pickup cycle.

Copy to the Pi, source the ROS workspace, then run:
    python3 test_live_pickup_ball.py

Starts vexy-ros-stack.service if not already running.
Requires Brain program slot 8 running and AprilTag 1 physically visible.
Exits 0 on success, 1 on failure or timeout.
"""

import argparse
import json
import subprocess
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path

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
TAG_1 = 1
ARM_UP_DEG = 300.0
ARM_DOWN_DEG = 0.0


def default_telemetry_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(f"/home/vexy/telemetry/live-pickup-{stamp}")


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


FAIL_REASONS = {
    "ball_not_found",
    "disabled",
    "grab_failed",
    "grab_not_confirmed",
    "unmapped_tag",
}
# (action, payload_extras, timeout_s, repeat_until_success, post_wait_s)
STEPS = [
    ("locate_nearest_apriltag", {}, 20.0, True, 0.0),
    ("move_to_tag", {"tag_index": TAG_1}, 50.0, True, 0.0),
    ("pickup_ball", {"duration_ms": 700}, 35.0, True, 0.0),
    ("arm", {"target_deg": ARM_UP_DEG}, 5.0, False, 4.0),
    ("arm", {"target_deg": ARM_DOWN_DEG}, 5.0, False, 4.0),
    ("release", {"duration_ms": 650}, 3.0, False, 1.0),
]


class PickupBallTestNode(Node):
    def __init__(self) -> None:
        super().__init__("operator_test_pickup_ball")
        self._cmd_pub = self.create_publisher(String, "/operator/command", 10)
        self._last_result: dict | None = None
        self._telemetry_count = 0
        self._last_arm_position_deg: float | None = None
        self.create_subscription(String, "/operator/results", self._on_result, 10)
        self.create_subscription(String, "/operator/events", self._on_event, 10)
        self.create_subscription(String, "/vex/telemetry", self._on_telemetry, 10)

    def _on_result(self, msg: String) -> None:
        try:
            self._last_result = json.loads(msg.data)
        except json.JSONDecodeError:
            pass

    def _on_event(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
            print(f"  event: {payload.get('name')}  {payload.get('detail')}")
        except json.JSONDecodeError:
            pass

    def _on_telemetry(self, msg: String) -> None:
        self._telemetry_count += 1
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        for sample in payload.get("motor_samples", []):
            if not isinstance(sample, dict):
                continue
            if sample.get("device") != "arm" and sample.get("subsystem") != "arm":
                continue
            values = sample.get("values", {})
            if not isinstance(values, dict):
                continue
            position = values.get("position_deg")
            if position is not None:
                self._last_arm_position_deg = float(position)
                return

    def _send(self, action: str, extras: dict) -> None:
        self._cmd_pub.publish(
            String(data=json.dumps({"action": action, **extras}, separators=(",", ":")))
        )

    def _wait_for_operator_command_subscription(self, timeout_s: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            if self._cmd_pub.get_subscription_count() > 0:
                return True
        print("  FAIL  operator command subscription not discovered")
        return False

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

    def _wait_for_arm_target(self, target_deg: float, timeout_s: float) -> bool:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)
            position = self._last_arm_position_deg
            if position is not None and abs(position - target_deg) <= 15.0:
                print(f"  ARM at {position:.1f} deg")
                return True
        print(
            "  FAIL  arm_target_not_reached"
            f" target={target_deg:.1f}"
            f" last={self._last_arm_position_deg}"
        )
        return False

    def _run_repeated_step(self, action: str, extras: dict, timeout_s: float) -> bool:
        deadline = time.monotonic() + timeout_s
        last_sent = 0.0
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)
            now = time.monotonic()
            if now - last_sent >= 0.05:
                self._send(action, extras)
                last_sent = now
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
                return True
            reason = outcome.get("reason", "")
            if reason in FAIL_REASONS:
                print(f"  FAIL  {reason}")
                return False
        print(f"  TIMEOUT after {timeout_s}s")
        return False

    def _run_single_step(
        self, action: str, extras: dict, timeout_s: float, post_wait_s: float
    ) -> bool:
        self._last_result = None
        self._send(action, extras)
        result = self._wait_for_result(action, timeout_s)
        if result is None:
            print(f"  TIMEOUT after {timeout_s}s")
            return False
        outcome = result.get("outcome", {})
        if not outcome.get("success"):
            print(f"  FAIL  {outcome.get('reason')}")
            return False
        print(f"  OK  {outcome.get('reason')}")
        if action == "arm":
            return self._wait_for_arm_target(
                float(extras["target_deg"]),
                post_wait_s if post_wait_s > 0 else timeout_s,
            )
        deadline = time.monotonic() + post_wait_s
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)
        return True

    def run(self) -> bool:
        print("=== pickup test: tag 1 → pickup → arm up/down → release ===")
        if not self._wait_for_operator_command_subscription():
            return False
        if not self._reset_operator():
            return False
        for action, extras, timeout_s, repeat_until_success, post_wait_s in STEPS:
            extras_str = f"  extras={extras}" if extras else ""
            print(f"[{action}]{extras_str}")
            self._last_result = None
            if repeat_until_success:
                ok = self._run_repeated_step(action, extras, timeout_s)
            else:
                ok = self._run_single_step(action, extras, timeout_s, post_wait_s)
            if not ok:
                return False
        print("=== pickup test PASSED ===")
        return True

    @property
    def telemetry_count(self) -> int:
        return self._telemetry_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
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
            label="test_live_pickup_ball.py",
        )
        time.sleep(max(0.0, args.capture_settle_s))
    rclpy.init()
    node = PickupBallTestNode()
    try:
        ok = node.run()
        print(f"=== telemetry samples seen by test node: {node.telemetry_count} ===")
        sys.exit(0 if ok else 1)
    finally:
        node.destroy_node()
        rclpy.shutdown()
        stop_operator_run_capture(capture_processes)
        if capture_processes:
            print(f"=== telemetry written under: {telemetry_dir} ===")


if __name__ == "__main__":
    main()
