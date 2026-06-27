"""Live integration test — align to each AprilTag in sequence.

Copy to the Pi, source the ROS workspace, then run:
    python3 test_live_align_each_apriltag.py

Visits tags 0, 1, 2 in order: orient then move to 0.3048 m (1 ft) standoff.
Prints arrival distance for each tag so results can be compared to the contract.
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
TARGET_DISTANCE_M = 0.3048  # 1 foot standoff per contract


def default_telemetry_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(f"/home/vexy/telemetry/live-align-each-{stamp}")


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


FAIL_REASONS = {"disabled", "unmapped_tag"}

# (action, payload_extras, timeout_s)  — all steps are nav steps
STEPS = [
    ("locate_nearest_apriltag", {}, 20.0),
    ("orient_to_tag", {"tag_index": 0}, 15.0),
    ("move_to_tag", {"tag_index": 0, "target_distance_m": TARGET_DISTANCE_M}, 30.0),
    ("orient_to_tag", {"tag_index": 1}, 15.0),
    ("move_to_tag", {"tag_index": 1, "target_distance_m": TARGET_DISTANCE_M}, 30.0),
    ("orient_to_tag", {"tag_index": 2}, 15.0),
    ("move_to_tag", {"tag_index": 2, "target_distance_m": TARGET_DISTANCE_M}, 30.0),
]


class AlignEachTagTestNode(Node):
    def __init__(self) -> None:
        super().__init__("operator_test_align_each_apriltag")
        self._cmd_pub = self.create_publisher(String, "/operator/command", 10)
        self._last_result: dict | None = None
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

    def run(self) -> bool:
        print(
            "=== align-each-apriltag test: locate → orient+approach tag 0 → 1 → 2 ==="
        )
        if not self._reset_operator():
            return False
        arrival_distances: dict[int, float] = {}

        for action, extras, timeout_s in STEPS:
            extras_str = f"  extras={extras}" if extras else ""
            print(f"[{action}]{extras_str}")
            self._last_result = None
            deadline = time.monotonic() + timeout_s
            succeeded = False
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
                    tag_index = extras.get("tag_index")
                    if action == "move_to_tag" and tag_index is not None:
                        gap = result.get("gap", {})
                        target_m = float(outcome.get("target_distance_m") or TARGET_DISTANCE_M)
                        dist = target_m + float(gap.get("distance_error_m", 0.0))
                        arrival_distances[tag_index] = dist
                        error_m = dist - TARGET_DISTANCE_M
                        print(
                            f"  OK  {outcome.get('reason')}"
                            f"  arrived={dist:.3f} m"
                            f"  error={error_m:+.3f} m"
                        )
                    else:
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

        print()
        print("=== summary ===")
        print(f"  target standoff : {TARGET_DISTANCE_M:.4f} m")
        for tag_id in sorted(arrival_distances):
            dist = arrival_distances[tag_id]
            error_m = dist - TARGET_DISTANCE_M
            print(f"  tag {tag_id}  arrived={dist:.4f} m  error={error_m:+.4f} m")
        print("=== align-each-apriltag test PASSED ===")
        return True


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
            label="test_live_align_each_apriltag.py",
        )
        time.sleep(max(0.0, args.capture_settle_s))
    rclpy.init()
    node = AlignEachTagTestNode()
    try:
        ok = node.run()
        sys.exit(0 if ok else 1)
    finally:
        node.destroy_node()
        rclpy.shutdown()
        stop_operator_run_capture(capture_processes)
        if capture_processes:
            print(f"=== telemetry written under: {telemetry_dir} ===")


if __name__ == "__main__":
    main()
