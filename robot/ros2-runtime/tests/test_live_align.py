"""Live integration test — align scenario.

Copy to the Pi, source the ROS workspace, then run:
    python3 test_live_align.py

Starts vexy-ros-stack.service if not already running.
Requires Brain slot 8 running and AprilTags physically visible to the camera.
Exits 0 on success, 1 on failure or timeout.
"""

import json
import subprocess
import sys
import time
import unittest

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except ModuleNotFoundError as exc:
    raise unittest.SkipTest("ROS 2 Python packages are not installed") from exc

STACK_SERVICE = "vexy-ros-stack.service"


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

# (action, payload_extras, timeout_s)  — all steps are nav steps
STEPS = [
    ("locate_nearest_apriltag", {}, 20.0),
    ("move_to_tag", {"tag_index": 0, "target_distance_m": 0.4064}, 20.0),
]


class AlignTestNode(Node):
    def __init__(self) -> None:
        super().__init__("operator_test_align")
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

    def run(self) -> bool:
        print("=== align test: locate → approach ===")
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


def main() -> None:
    print("=== pre-flight: camera stack ===")
    if not ensure_stack_running():
        sys.exit(1)
    rclpy.init()
    node = AlignTestNode()
    try:
        ok = node.run()
        sys.exit(0 if ok else 1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
