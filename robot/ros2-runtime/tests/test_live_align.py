"""Live integration test — align scenario.

Copy to the Pi, source the ROS workspace, then run:
    python3 test_live_align.py [tag_id]

Defaults to AprilTag 0 when tag_id is omitted.

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
SEARCH_REASONS = {"stale_tag", "tag_not_visible"}
IN_PROGRESS_REASONS = {"align_started", "survey_started"}
SURVEY_SCAN_TIMEOUT_S = 18.0
PREDICTED_APPROACH_TIMEOUT_S = 20.0
PREDICTED_APPROACH_INTERVAL_S = 0.25


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
        self._action_results: list[dict] = []
        self._last_align_feedback: dict | None = None
        self._last_survey_feedback: dict | None = None
        self._known_tags: set[int] = set()
        self.create_subscription(String, "/operator/results", self._on_result, 10)
        self.create_subscription(String, "/operator/status", self._on_status, 10)
        self.create_subscription(String, "/operator/events", self._on_event, 10)
        self.create_subscription(
            String, "/align_to_tag/feedback", self._on_align_feedback, 10
        )
        self.create_subscription(
            String, "/align_to_tag/result", self._on_align_result, 10
        )
        self.create_subscription(
            String, "/survey/feedback", self._on_survey_feedback, 10
        )
        self.create_subscription(String, "/survey/result", self._on_survey_result, 10)

    def _on_result(self, msg: String) -> None:
        try:
            self._last_result = json.loads(msg.data)
        except json.JSONDecodeError:
            pass

    def _on_status(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        known_tags = payload.get("known_tags")
        if isinstance(known_tags, list):
            self._known_tags = {int(tag_id) for tag_id in known_tags}
        action = payload.get("action")
        if payload.get("type") == "operator_result" and action not in {
            "align_to_tag",
            "survey_scan",
        }:
            self._action_results.append(
                {
                    "method": action,
                    "success": bool(payload.get("success")),
                    "reason": payload.get("reason"),
                    "fault": payload.get("fault"),
                }
            )

    def _on_align_feedback(self, msg: String) -> None:
        try:
            self._last_align_feedback = json.loads(msg.data)
        except json.JSONDecodeError:
            return

    def _on_align_result(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        self._action_results.append(
            {
                "method": "align_to_tag",
                "success": bool(payload.get("success")),
                "reason": payload.get("reason"),
                "fault": payload.get("fault"),
                "final_yaw_error_rad": payload.get("final_yaw_error_rad"),
                "final_lateral_error_m": payload.get("final_lateral_error_m"),
                "final_distance_error_m": payload.get("final_distance_error_m"),
            }
        )

    def _on_survey_feedback(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        observed = payload.get("observed_tag_ids")
        if isinstance(observed, list):
            self._known_tags.update(int(tag_id) for tag_id in observed)
        self._last_survey_feedback = payload

    def _on_survey_result(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        observed = payload.get("observed_tag_ids")
        if isinstance(observed, list):
            self._known_tags.update(int(tag_id) for tag_id in observed)
        self._action_results.append(
            {
                "method": "survey_scan",
                "success": bool(payload.get("success")),
                "reason": payload.get("reason"),
                "observed_tag_ids": payload.get("observed_tag_ids", []),
                "fault": payload.get("fault"),
            }
        )

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

    def _wait_for_action_result(self, action: str, timeout_s: float) -> dict | None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)
            if self._last_rejection is not None:
                detail = self._last_rejection.get("detail", {})
                return {
                    "method": action,
                    "success": False,
                    "reason": "command_rejected",
                    "fault": detail.get("error"),
                }
            while self._action_results:
                result = self._action_results.pop(0)
                if result.get("method") != action:
                    continue
                if result.get("reason") in IN_PROGRESS_REASONS:
                    continue
                return result
        return None

    def _format_align_result(self, result: dict) -> str:
        details = [
            f"reason={result.get('reason')}",
            f"fault={result.get('fault')}",
            f"yaw={result.get('final_yaw_error_rad')}",
            f"lateral={result.get('final_lateral_error_m')}",
            f"distance={result.get('final_distance_error_m')}",
        ]
        if self._last_align_feedback is not None:
            details.extend(
                [
                    f"last_feedback={self._last_align_feedback.get('reason')}",
                    f"visible={self._last_align_feedback.get('tag_visible')}",
                ]
            )
        return "  ".join(details)

    def _reset_operator(self) -> bool:
        print("[reset_operator]")
        deadline = time.monotonic() + 5.0
        while self._cmd_pub.get_subscription_count() == 0:
            if time.monotonic() >= deadline:
                print("  TIMEOUT waiting for operator subscriber")
                return False
            rclpy.spin_once(self, timeout_sec=0.05)
        self._last_result = None
        self._action_results.clear()
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

    def _run_locate(self) -> bool:
        print("[locate_nearest_apriltag]")
        self._last_result = None
        self._last_rejection = None
        deadline = time.monotonic() + 20.0
        last_sent = 0.0
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)
            now = time.monotonic()
            if now - last_sent >= 1.0:
                self._send("locate_nearest_apriltag", {})
                last_sent = now
            if self._last_rejection is not None:
                detail = self._last_rejection.get("detail", {})
                print(f"  FAIL  command_rejected: {detail.get('error')}")
                return False
            result = self._last_result
            if result is None:
                continue
            outcome = result.get("outcome", {})
            self._last_result = None
            if outcome.get("method") != "locate_nearest_apriltag":
                continue
            if outcome.get("success"):
                tag_index = outcome.get("tag_index")
                if tag_index is not None:
                    self._known_tags.add(int(tag_index))
                print(f"  OK  {outcome.get('reason')}  tag={tag_index}")
                return True
            reason = outcome.get("reason", "")
            if reason in FAIL_REASONS:
                print(f"  FAIL  {reason}")
                return False
        print("  TIMEOUT after 20.0s")
        return False

    def _align_once(self, tag_id: int) -> dict | None:
        extras = {
            "tag_id": tag_id,
            "target_distance_m": 0.4064,
            "timeout_s": 15.0,
            "max_omega": 0.18,
            "min_turn_omega": 0.10,
        }
        print(f"[align_to_tag]  extras={extras}")
        self._last_rejection = None
        self._action_results.clear()
        self._last_align_feedback = None
        self._send("align_to_tag", extras)
        result = self._wait_for_action_result("align_to_tag", 25.0)
        if result is None:
            print("  TIMEOUT after 25.0s")
        else:
            print(f"  result: {self._format_align_result(result)}")
        return result

    def _search_for_tag(self, tag_id: int) -> bool:
        print(f"[survey_scan]  searching for AprilTag {tag_id}")
        self._last_rejection = None
        self._action_results.clear()
        self._last_survey_feedback = None
        self._send("survey_scan", {"duration_s": 14.5, "omega_rad_s": 0.45})
        started_at = time.monotonic()
        deadline = time.monotonic() + SURVEY_SCAN_TIMEOUT_S
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)
            if tag_id in self._known_tags:
                elapsed_s = time.monotonic() - started_at
                print(f"  OK  found tag {tag_id} after {elapsed_s:.1f}s")
                self._send("cancel_survey_scan", {})
                return True
            if self._last_rejection is not None:
                detail = self._last_rejection.get("detail", {})
                print(f"  FAIL  command_rejected: {detail.get('error')}")
                return False
            while self._action_results:
                result = self._action_results.pop(0)
                if result.get("method") != "survey_scan":
                    continue
                if result.get("reason") in IN_PROGRESS_REASONS:
                    continue
                if result.get("success") and tag_id in self._known_tags:
                    elapsed_s = time.monotonic() - started_at
                    print(
                        f"  OK  scan complete; found tag {tag_id} after {elapsed_s:.1f}s"
                    )
                    return True
                print(
                    f"  FAIL  scan ended without tag {tag_id}; "
                    f"known={sorted(self._known_tags)} reason={result.get('reason')} "
                    f"last_feedback={self._last_survey_feedback}"
                )
                return False
        print(
            f"  TIMEOUT after {SURVEY_SCAN_TIMEOUT_S}s; known={sorted(self._known_tags)}"
        )
        self._send("cancel_survey_scan", {})
        return False

    def _move_toward_predicted_tag(self, tag_id: int) -> bool:
        print(f"[move_to_tag]  predicted fallback for AprilTag {tag_id}")
        self._last_result = None
        self._last_rejection = None
        deadline = time.monotonic() + PREDICTED_APPROACH_TIMEOUT_S
        last_sent = 0.0
        extras = {"tag_id": tag_id, "target_distance_m": 0.4064}
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)
            now = time.monotonic()
            if now - last_sent >= PREDICTED_APPROACH_INTERVAL_S:
                self._send("move_to_tag", extras)
                last_sent = now
            if self._last_rejection is not None:
                detail = self._last_rejection.get("detail", {})
                print(f"  FAIL  command_rejected: {detail.get('error')}")
                return False
            result = self._last_result
            if result is None:
                continue
            outcome = result.get("outcome", {})
            self._last_result = None
            if outcome.get("method") != "move_to_tag":
                continue
            reason = str(outcome.get("reason", ""))
            command = outcome.get("command")
            source = outcome.get("localization_source")
            print(f"  event: {reason}  command={command}  source={source}")
            if outcome.get("success"):
                print(f"  OK  {reason}")
                return True
            if reason in FAIL_REASONS:
                print(f"  FAIL  {reason}")
                return False
            if tag_id in self._known_tags:
                print(f"  OK  tag {tag_id} became visible during predicted approach")
                return True
        print(f"  TIMEOUT after {PREDICTED_APPROACH_TIMEOUT_S}s")
        return False

    def run(self, tag_id: int) -> bool:
        print(
            f"=== align test: locate → search if needed → align to AprilTag {tag_id} ==="
        )
        if not self._reset_operator():
            return False
        if not self._run_locate():
            return False

        result = self._align_once(tag_id)
        if result is None:
            return False
        if result.get("success"):
            print(f"  OK  {result.get('reason')}")
            print("=== align test PASSED ===")
            return True

        reason = str(result.get("reason", ""))
        fault = str(result.get("fault", ""))
        if reason in SEARCH_REASONS or fault in SEARCH_REASONS:
            print(f"  target not visible yet: {reason or fault}")
            if self._search_for_tag(tag_id):
                result = self._align_once(tag_id)
                if result is None:
                    return False
                if result.get("success"):
                    print(f"  OK  {result.get('reason')}")
                    print("=== align test PASSED ===")
                    return True
            else:
                print(f"  tag {tag_id} not found by survey; using predicted map pose")
            if self._move_toward_predicted_tag(tag_id):
                result = self._align_once(tag_id)
                if result is not None and result.get("success"):
                    print(f"  OK  {result.get('reason')}")
                print("=== align test PASSED ===")
                return True

        print(f"  FAIL  {result.get('reason')}  fault={result.get('fault')}")
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tag_id",
        type=int,
        nargs="?",
        default=0,
        help=(
            "AprilTag ID to align to. Defaults to 0. "
            "The operator rejects IDs missing from the loaded map."
        ),
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
