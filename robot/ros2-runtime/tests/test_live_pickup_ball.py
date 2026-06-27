"""Live integration test — focused tag-1 ball pickup cycle.

Copy to the Pi, source the ROS workspace, then run:
    python3 test_live_pickup_ball.py

Starts vexy-ros-stack.service if not already running.
Requires Brain program slot 8 running and AprilTag 1 physically visible.
Exits 0 on success, 1 on failure or timeout.
"""

import argparse
import json
import signal
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


FAIL_REASONS = {"disabled", "grab_failed", "grab_not_confirmed", "unmapped_tag"}
TELEMETRY_TOPICS = (
    "/operator/run_start",
    "/operator/events",
    "/operator/results",
    "/operator/status",
    "/vex/telemetry",
)

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

    def _on_telemetry(self, _msg: String) -> None:
        self._telemetry_count += 1

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
        deadline = time.monotonic() + post_wait_s
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)
        return True

    def run(self) -> bool:
        print("=== pickup test: tag 1 → pickup → arm up/down → release ===")
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


def start_telemetry_capture(
    telemetry_dir: Path, *, bag_record: bool
) -> list[subprocess.Popen]:
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    (telemetry_dir / "test.txt").write_text("test_live_pickup_ball.py\n")
    processes = [
        subprocess.Popen(
            [
                "ros2",
                "run",
                "vexy_ros",
                "vexy_telemetry_writer_node",
                "--out-dir",
                str(telemetry_dir),
                "--run-id",
                telemetry_dir.name,
            ],
            stdout=(telemetry_dir / "telemetry-writer.log").open("w"),
            stderr=subprocess.STDOUT,
        )
    ]
    if bag_record:
        processes.append(
            subprocess.Popen(
                [
                    "ros2",
                    "bag",
                    "record",
                    "-o",
                    str(telemetry_dir / "bag"),
                    *TELEMETRY_TOPICS,
                ],
                stdout=(telemetry_dir / "bag-record.log").open("w"),
                stderr=subprocess.STDOUT,
            )
        )
    return processes


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=8)
        return
    except subprocess.TimeoutExpired:
        pass
    process.terminate()
    try:
        process.wait(timeout=3)
        return
    except subprocess.TimeoutExpired:
        pass
    process.kill()
    process.wait(timeout=3)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--telemetry-dir", type=Path, default=None)
    parser.add_argument("--no-bag-record", action="store_true")
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
        capture_processes = start_telemetry_capture(
            telemetry_dir, bag_record=not args.no_bag_record
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
        for process in reversed(capture_processes):
            stop_process(process)
        if capture_processes:
            print(f"=== telemetry written under: {telemetry_dir} ===")


if __name__ == "__main__":
    main()
