from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import rclpy

from .bridge_protocol import DEFAULT_GRAB_MS, DEFAULT_LIFT_MS, DEFAULT_RELEASE_MS
from .tag_action_proof import (
    TagActionProof,
    approach_tag,
    finalize_summary,
    run_scan,
)
from .vision_map import DEFAULT_CAMERA_IN_ROBOT, pose_from_mapping


def _approach_required_tag(
    node: TagActionProof,
    *,
    label: str,
    tag_id: int,
    target_distance_m: float,
    timeout_s: float,
    drive_vx: float,
    turn_kp: float,
    max_omega: float,
    ttl_ms: int,
) -> dict[str, Any]:
    start_tag = node.fresh_tag(tag_id=tag_id, max_age_s=1.0)
    reached, reason, post_tag = approach_tag(
        node,
        tag_id=tag_id,
        target_distance_m=target_distance_m,
        timeout_s=timeout_s,
        drive_vx=drive_vx,
        turn_kp=turn_kp,
        max_omega=max_omega,
        ttl_ms=ttl_ms,
    )
    node.stop(f"{label}_approach_complete")
    return {
        "label": label,
        "tag_id": tag_id,
        "target_distance_m": target_distance_m,
        "start_distance_m": (
            None if start_tag is None else float(start_tag["distance_m"])
        ),
        "start_left_m": (
            None if start_tag is None else _optional_float(start_tag, "left_m")
        ),
        "start_yaw_rad": (
            None if start_tag is None else _optional_float(start_tag, "yaw_rad")
        ),
        "post_distance_m": (
            None if post_tag is None else float(post_tag["distance_m"])
        ),
        "post_left_m": (
            None if post_tag is None else _optional_float(post_tag, "left_m")
        ),
        "post_yaw_rad": (
            None if post_tag is None else _optional_float(post_tag, "yaw_rad")
        ),
        "reached_target": reached,
        "reason": reason,
        "observed_tags": sorted(node.observed_tags),
    }


def _optional_float(raw: dict[str, Any], key: str) -> float | None:
    value = raw.get(key)
    return None if value is None else float(value)


def _wait_for_ack(
    node: TagActionProof,
    *,
    seq: int,
    timeout_s: float,
) -> dict[str, Any] | None:
    deadline_s = time.monotonic() + timeout_s
    while time.monotonic() < deadline_s:
        ack = node.last_ack
        if isinstance(ack, dict) and ack.get("ack") == seq:
            return ack
        node.spin_for(0.05)
    return node.last_ack


def _run_timed_claw_action(
    node: TagActionProof,
    *,
    cmd: str,
    duration_ms: int,
    ack_timeout_s: float,
    settle_s: float,
    reason: str,
) -> dict[str, Any]:
    node.last_ack = None
    node.send(cmd, duration_ms=duration_ms, ttl_ms=max(200, duration_ms), reason=reason)
    seq = node.seq
    ack = _wait_for_ack(node, seq=seq, timeout_s=ack_timeout_s)
    node.spin_for(settle_s)
    return {
        "cmd": cmd,
        "duration_ms": duration_ms,
        "ack": ack,
        "ack_state": None if ack is None else ack.get("state"),
        "succeeded": isinstance(ack, dict) and ack.get("state") == "ok",
    }


def deliver_ball(node: TagActionProof, args: argparse.Namespace) -> dict[str, Any]:
    node.spin_for(args.settle_s)
    run_scan(
        node,
        duration_s=args.scan_duration_s,
        omega=args.scan_omega,
        ttl_ms=args.ttl_ms,
    )
    node.stop("workspace_orientation_complete")
    node.spin_for(args.settle_s)

    summary: dict[str, Any] = {
        "program": "deliver_ball",
        "status": "running",
        "ball_tag_id": args.ball_tag_id,
        "bin_tag_id": args.bin_tag_id,
        "camera_in_robot": pose_from_mapping(
            json.loads(args.camera_in_robot_json)
        ).to_json(),
        "observed_tags_after_orientation": sorted(node.observed_tags),
        "ball_approach": None,
        "grab": None,
        "bin_approach": None,
        "lift": None,
        "release": None,
    }
    if not node.observed_tags:
        summary.update({"status": "failed", "reason": "no_apriltags_observed"})
        return finalize_summary(node, summary)

    ball_approach = _approach_required_tag(
        node,
        label="ball_loading",
        tag_id=args.ball_tag_id,
        target_distance_m=args.ball_distance_m,
        timeout_s=args.approach_timeout_s,
        drive_vx=args.drive_vx,
        turn_kp=args.turn_kp,
        max_omega=args.max_omega,
        ttl_ms=args.ttl_ms,
    )
    summary["ball_approach"] = ball_approach
    if not ball_approach["reached_target"]:
        summary.update({"status": "failed", "reason": "ball_tag_approach_failed"})
        return finalize_summary(node, summary)

    grab = _run_timed_claw_action(
        node,
        cmd="grab",
        duration_ms=args.grab_ms,
        ack_timeout_s=args.ack_timeout_s,
        settle_s=args.grab_settle_s,
        reason="grab_ball",
    )
    summary["grab"] = grab
    if not grab["succeeded"]:
        summary.update({"status": "failed", "reason": "grab_failed"})
        return finalize_summary(node, summary)
    node.stop("grab_complete")

    bin_approach = _approach_required_tag(
        node,
        label="bin",
        tag_id=args.bin_tag_id,
        target_distance_m=args.bin_distance_m,
        timeout_s=args.approach_timeout_s,
        drive_vx=args.drive_vx,
        turn_kp=args.turn_kp,
        max_omega=args.max_omega,
        ttl_ms=args.ttl_ms,
    )
    summary["bin_approach"] = bin_approach
    if not bin_approach["reached_target"]:
        summary.update({"status": "failed", "reason": "bin_tag_approach_failed"})
        return finalize_summary(node, summary)

    lift = _run_timed_claw_action(
        node,
        cmd="lift",
        duration_ms=args.lift_ms,
        ack_timeout_s=args.ack_timeout_s,
        settle_s=args.lift_settle_s,
        reason="raise_claw_for_bin",
    )
    summary["lift"] = lift
    if not lift["succeeded"]:
        summary.update({"status": "failed", "reason": "lift_failed"})
        return finalize_summary(node, summary)
    node.stop("lift_complete")

    release = _run_timed_claw_action(
        node,
        cmd="release",
        duration_ms=args.release_ms,
        ack_timeout_s=args.ack_timeout_s,
        settle_s=args.drop_settle_s,
        reason="drop_ball_in_bin",
    )
    summary["release"] = release
    if not release["succeeded"]:
        summary.update({"status": "failed", "reason": "release_failed"})
        return finalize_summary(node, summary)
    node.stop("release_complete")

    summary.update({"status": "succeeded", "reason": "ball_delivered"})
    return finalize_summary(node, summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Orient with AprilTags, grab the ball, drive to the bin, lift, and release."
    )
    parser.add_argument("--summary-out", type=Path)
    parser.add_argument("--ball-tag-id", type=int, default=1)
    parser.add_argument("--bin-tag-id", type=int, default=0)
    parser.add_argument("--ball-distance-m", type=float, default=0.45)
    parser.add_argument("--bin-distance-m", type=float, default=0.38)
    parser.add_argument("--settle-s", type=float, default=1.0)
    parser.add_argument("--grab-settle-s", type=float, default=0.4)
    parser.add_argument("--lift-settle-s", type=float, default=0.4)
    parser.add_argument("--drop-settle-s", type=float, default=0.4)
    parser.add_argument("--ack-timeout-s", type=float, default=1.5)
    parser.add_argument("--approach-timeout-s", type=float, default=16.0)
    parser.add_argument("--scan-duration-s", type=float, default=14.5)
    parser.add_argument("--drive-vx", type=float, default=0.14)
    parser.add_argument("--turn-kp", type=float, default=0.9)
    parser.add_argument("--max-omega", type=float, default=0.45)
    parser.add_argument("--scan-omega", type=float, default=0.45)
    parser.add_argument("--ttl-ms", type=int, default=180)
    parser.add_argument("--grab-ms", type=int, default=DEFAULT_GRAB_MS)
    parser.add_argument("--lift-ms", type=int, default=DEFAULT_LIFT_MS)
    parser.add_argument("--release-ms", type=int, default=DEFAULT_RELEASE_MS)
    parser.add_argument(
        "--camera-in-robot-json",
        default=DEFAULT_CAMERA_IN_ROBOT,
        help="Measured camera pose in the robot/action frame.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rclpy.init()
    node = TagActionProof(
        camera_in_robot=pose_from_mapping(json.loads(args.camera_in_robot_json))
    )
    try:
        summary = deliver_ball(node, args)
    finally:
        node.stop("deliver_ball_finally")
        node.destroy_node()
        rclpy.shutdown()

    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.summary_out is not None:
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.summary_out.write_text(text)
    print(text, end="")
    return 0
