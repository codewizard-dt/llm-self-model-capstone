from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from tf2_msgs.msg import TFMessage

from .bridge_protocol import PROTOCOL_VERSION, clamp, now_ms
from .vision_map import (
    Pose2D,
    camera_from_apriltag_translation,
    pose_from_mapping,
    robot_from_camera_pose,
    tag_id_from_frame_id,
)


class TagActionProof(Node):
    def __init__(self, *, camera_in_robot: Pose2D | None = None) -> None:
        super().__init__("tag_action_proof")
        self._cmd_pub = self.create_publisher(String, "/vex/cmd", 10)
        self.create_subscription(TFMessage, "/tf", self._on_tf, 10)
        self.create_subscription(String, "/vex/telemetry", self._on_telemetry, 10)
        self.create_subscription(String, "/vex/ack", self._on_ack, 10)
        self.create_subscription(String, "/vision/scene_map", self._on_scene_map, 10)
        self.latest_by_tag: dict[int, dict[str, float | int]] = {}
        self.observed_tags: set[int] = set()
        self.last_telemetry: dict[str, Any] | None = None
        self.last_ack: dict[str, Any] | None = None
        self.last_scene_map: dict[str, Any] | None = None
        self.commands_sent = 0
        self.last_command: dict[str, Any] | None = None
        self.seq = 24000
        self.camera_in_robot = camera_in_robot or Pose2D(0.0, 0.0, 0.0)

    def _on_tf(self, msg: TFMessage) -> None:
        stamp_s = time.monotonic()
        for stamped in msg.transforms:
            tag_id = tag_id_from_frame_id(stamped.child_frame_id)
            if tag_id is None:
                continue
            translation = stamped.transform.translation
            camera_from_tag = camera_from_apriltag_translation(
                optical_x_m=float(translation.x),
                optical_z_m=float(translation.z),
            )
            robot_from_tag = robot_from_camera_pose(
                camera_from_tag, self.camera_in_robot
            )
            forward_m = robot_from_tag.x_m
            left_m = robot_from_tag.y_m
            if forward_m <= 0.05:
                continue
            distance_m = math.hypot(forward_m, left_m)
            yaw_rad = math.atan2(left_m, forward_m)
            self.latest_by_tag[tag_id] = {
                "tag_id": tag_id,
                "stamp_s": stamp_s,
                "forward_m": forward_m,
                "left_m": left_m,
                "distance_m": distance_m,
                "yaw_rad": yaw_rad,
                "camera_forward_m": camera_from_tag.x_m,
                "camera_left_m": camera_from_tag.y_m,
            }
            self.observed_tags.add(tag_id)

    def _on_telemetry(self, msg: String) -> None:
        try:
            self.last_telemetry = json.loads(msg.data)
        except json.JSONDecodeError:
            return

    def _on_ack(self, msg: String) -> None:
        try:
            self.last_ack = json.loads(msg.data)
        except json.JSONDecodeError:
            return

    def _on_scene_map(self, msg: String) -> None:
        try:
            self.last_scene_map = json.loads(msg.data)
        except json.JSONDecodeError:
            return

    def spin_for(self, duration_s: float) -> None:
        deadline_s = time.monotonic() + duration_s
        while time.monotonic() < deadline_s:
            rclpy.spin_once(self, timeout_sec=0.02)

    def fresh_tag(
        self, *, tag_id: int | None = None, max_age_s: float = 0.45
    ) -> dict[str, float | int] | None:
        if tag_id is not None:
            candidate = self.latest_by_tag.get(tag_id)
            if candidate is None:
                return None
            if time.monotonic() - float(candidate["stamp_s"]) <= max_age_s:
                return candidate
            return None

        fresh = [
            item
            for item in self.latest_by_tag.values()
            if time.monotonic() - float(item["stamp_s"]) <= max_age_s
        ]
        if not fresh:
            return None
        return max(fresh, key=lambda item: float(item["stamp_s"]))

    def send(
        self,
        cmd: str,
        *,
        vx: float = 0.0,
        omega: float = 0.0,
        ttl_ms: int = 180,
        duration_ms: int | None = None,
        reason: str | None = None,
    ) -> None:
        self.seq += 1
        packet: dict[str, Any] = {
            "v": PROTOCOL_VERSION,
            "seq": self.seq,
            "type": "cmd",
            "cmd": cmd,
            "sent_ms": now_ms(),
            "ttl_ms": ttl_ms,
        }
        if cmd == "drive":
            packet.update({"vx": vx, "vy": 0.0, "omega": omega})
        elif cmd == "turn":
            packet["omega"] = omega
        elif cmd in {"grab", "lift", "release"} and duration_ms is not None:
            packet["duration_ms"] = duration_ms
        if reason:
            packet["reason"] = reason
        self.commands_sent += 1
        self.last_command = dict(packet)
        self._cmd_pub.publish(String(data=json.dumps(packet, separators=(",", ":"))))

    def stop(self, reason: str) -> None:
        self.send("stop", ttl_ms=200, reason=reason)
        self.spin_for(0.3)


def run_scan(
    node: TagActionProof,
    *,
    duration_s: float,
    omega: float,
    ttl_ms: int,
) -> None:
    deadline_s = time.monotonic() + duration_s
    while time.monotonic() < deadline_s:
        node.send("turn", omega=omega, ttl_ms=ttl_ms)
        node.spin_for(0.08)


def reacquire_visible_tag(
    node: TagActionProof,
    *,
    timeout_s: float,
    omega: float,
    ttl_ms: int,
) -> dict[str, float | int] | None:
    deadline_s = time.monotonic() + timeout_s
    while time.monotonic() < deadline_s:
        tag = node.fresh_tag(max_age_s=0.5)
        if tag is not None:
            return tag
        node.send("turn", omega=omega, ttl_ms=ttl_ms)
        node.spin_for(0.08)
    return node.fresh_tag(max_age_s=1.0)


def approach_tag(
    node: TagActionProof,
    *,
    tag_id: int,
    target_distance_m: float,
    timeout_s: float,
    drive_vx: float,
    turn_kp: float,
    max_omega: float,
    ttl_ms: int,
    stuck_window_s: float = 1.2,
    stuck_min_progress_m: float = 0.015,
    stuck_min_drive_vx: float = 0.03,
) -> tuple[bool, str, dict[str, float | int] | None]:
    deadline_s = time.monotonic() + timeout_s
    last_tag: dict[str, float | int] | None = None
    progress_window_start_s: float | None = None
    progress_window_start_distance_m: float | None = None
    while time.monotonic() < deadline_s:
        tag = node.fresh_tag(tag_id=tag_id, max_age_s=0.45)
        if tag is None:
            progress_window_start_s = None
            progress_window_start_distance_m = None
            node.send("turn", omega=0.25, ttl_ms=ttl_ms)
            node.spin_for(0.08)
            continue

        last_tag = tag
        distance_m = float(tag["distance_m"])
        if distance_m <= target_distance_m:
            return True, "target_distance_reached", tag

        yaw_rad = float(tag["yaw_rad"])
        omega = clamp(turn_kp * yaw_rad, -max_omega, max_omega)
        vx = drive_vx if abs(yaw_rad) <= 0.45 else 0.04
        if abs(yaw_rad) > 0.9:
            vx = 0.0
        now_s = time.monotonic()
        if vx >= stuck_min_drive_vx:
            if progress_window_start_distance_m is None or distance_m < (
                progress_window_start_distance_m - stuck_min_progress_m
            ):
                progress_window_start_s = now_s
                progress_window_start_distance_m = distance_m
            elif (
                progress_window_start_s is not None
                and now_s - progress_window_start_s >= stuck_window_s
            ):
                stuck_tag = dict(tag)
                stuck_tag.update(
                    {
                        "stuck_window_s": now_s - progress_window_start_s,
                        "stuck_distance_delta_m": distance_m - progress_window_start_distance_m,
                    }
                )
                return False, "stuck_no_progress", stuck_tag
        else:
            progress_window_start_s = None
            progress_window_start_distance_m = None
        node.send("drive", vx=vx, omega=omega, ttl_ms=ttl_ms)
        node.spin_for(0.08)
    return False, "timeout", last_tag


def visual_one_foot_scan(node: TagActionProof, args: argparse.Namespace) -> dict[str, Any]:
    node.spin_for(args.settle_s)
    start = reacquire_visible_tag(
        node,
        timeout_s=args.reacquire_timeout_s,
        omega=args.reacquire_omega,
        ttl_ms=args.ttl_ms,
    )
    node.stop("reacquire_complete")

    summary: dict[str, Any] = {
        "proof_kind": "visual_one_foot_and_scan",
        "closure_m": args.closure_m,
        "min_distance_m": args.min_distance_m,
        "scan_duration_s": args.scan_duration_s,
        "scan_omega": args.scan_omega,
        "visible_tag": None if start is None else int(start["tag_id"]),
        "start_distance_m": None if start is None else float(start["distance_m"]),
        "target_distance_m": None,
        "post_drive_distance_m": None,
        "distance_closed_m": None,
        "approach_reached_target": False,
        "approach_reason": "no_tag_reacquired" if start is None else None,
        "observed_tags_after_reacquire": sorted(node.observed_tags),
        "observed_tags_after_approach": None,
        "observed_tags_after_scan": None,
    }
    if start is not None:
        tag_id = int(start["tag_id"])
        start_distance_m = float(start["distance_m"])
        target_distance_m = max(args.min_distance_m, start_distance_m - args.closure_m)
        reached, reason, post_tag = approach_tag(
            node,
            tag_id=tag_id,
            target_distance_m=target_distance_m,
            timeout_s=args.approach_timeout_s,
            drive_vx=args.drive_vx,
            turn_kp=args.turn_kp,
            max_omega=args.max_omega,
            ttl_ms=args.ttl_ms,
            stuck_window_s=getattr(args, "stuck_window_s", 1.2),
            stuck_min_progress_m=getattr(args, "stuck_min_progress_m", 0.015),
            stuck_min_drive_vx=getattr(args, "stuck_min_drive_vx", 0.03),
        )
        node.stop("approach_complete")
        post_tag = node.fresh_tag(tag_id=tag_id, max_age_s=1.0) or post_tag
        post_distance_m = None if post_tag is None else float(post_tag["distance_m"])
        summary.update(
            {
                "target_distance_m": target_distance_m,
                "post_drive_distance_m": post_distance_m,
                "distance_closed_m": (
                    None if post_distance_m is None else start_distance_m - post_distance_m
                ),
                "approach_reached_target": reached,
                "approach_reason": reason,
                "observed_tags_after_approach": sorted(node.observed_tags),
            }
        )

    run_scan(
        node,
        duration_s=args.scan_duration_s,
        omega=args.scan_omega,
        ttl_ms=args.ttl_ms,
    )
    node.stop("scan_complete")
    node.spin_for(args.settle_s)
    summary["observed_tags_after_scan"] = sorted(node.observed_tags)
    return finalize_summary(node, summary)


def scan_only(node: TagActionProof, args: argparse.Namespace) -> dict[str, Any]:
    node.spin_for(args.settle_s)
    before = sorted(node.observed_tags)
    run_scan(
        node,
        duration_s=args.scan_duration_s,
        omega=args.scan_omega,
        ttl_ms=args.ttl_ms,
    )
    node.stop("scan_complete")
    node.spin_for(args.settle_s)
    after = sorted(node.observed_tags)
    return finalize_summary(
        node,
        {
            "proof_kind": "scan_only",
            "observed_tags_before_scan": before,
            "observed_tags_after_scan": after,
            "scan_duration_s": args.scan_duration_s,
            "scan_omega": args.scan_omega,
        },
    )


def finalize_summary(node: TagActionProof, summary: dict[str, Any]) -> dict[str, Any]:
    summary["observed_tags"] = sorted(node.observed_tags)
    summary["last_ack"] = node.last_ack
    summary["last_telemetry"] = node.last_telemetry
    summary["last_scene_map"] = getattr(node, "last_scene_map", None)
    summary["commands_sent"] = getattr(node, "commands_sent", None)
    summary["last_command"] = getattr(node, "last_command", None)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run bounded V5 tag-action proofs through /vex/cmd."
    )
    parser.add_argument(
        "--mode",
        choices=("visual-one-foot-scan", "scan-only"),
        default="visual-one-foot-scan",
    )
    parser.add_argument("--summary-out", type=Path)
    parser.add_argument("--closure-m", type=float, default=0.3048)
    parser.add_argument("--min-distance-m", type=float, default=0.45)
    parser.add_argument("--settle-s", type=float, default=1.0)
    parser.add_argument("--reacquire-timeout-s", type=float, default=14.0)
    parser.add_argument("--approach-timeout-s", type=float, default=14.0)
    parser.add_argument("--scan-duration-s", type=float, default=14.5)
    parser.add_argument("--drive-vx", type=float, default=0.14)
    parser.add_argument("--turn-kp", type=float, default=0.9)
    parser.add_argument("--max-omega", type=float, default=0.45)
    parser.add_argument("--reacquire-omega", type=float, default=0.35)
    parser.add_argument("--scan-omega", type=float, default=0.45)
    parser.add_argument("--ttl-ms", type=int, default=180)
    parser.add_argument("--stuck-window-s", type=float, default=1.2)
    parser.add_argument("--stuck-min-progress-m", type=float, default=0.015)
    parser.add_argument("--stuck-min-drive-vx", type=float, default=0.03)
    parser.add_argument(
        "--camera-in-robot-json",
        default='{"x_m":0.0,"y_m":0.0,"yaw_rad":0.0}',
        help="Measured camera pose in the robot/action frame.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rclpy.init()
    node = TagActionProof(
        camera_in_robot=pose_from_mapping(json.loads(args.camera_in_robot_json))
    )
    summary: dict[str, Any]
    try:
        if args.mode == "scan-only":
            summary = scan_only(node, args)
        else:
            summary = visual_one_foot_scan(node, args)
    finally:
        node.stop("tag_action_proof_finally")
        node.destroy_node()
        rclpy.shutdown()

    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.summary_out is not None:
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.summary_out.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
