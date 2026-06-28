from __future__ import annotations

import argparse
import itertools
import json
import math
import time
from pathlib import Path
from typing import Any, Mapping

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except ModuleNotFoundError:  # pragma: no cover - lets helper tests run off ROS.
    rclpy = None  # type: ignore[assignment]

    class Node:  # type: ignore[no-redef]
        pass

    class String:  # type: ignore[no-redef]
        def __init__(self, *, data: str = "") -> None:
            self.data = data


from .bridge_protocol import PROTOCOL_VERSION, now_ms
from .operator._core import PICKUP_CONFIG_FIELDS, OperatorConfig
from .vision_map import Pose2D, pose_from_mapping, robot_from_camera_pose


PICKUP_IN_PROGRESS_REASONS = {
    "opening_claw",
    "moving_to_ball",
    "closing_claw",
    "searching_for_ball",
    "verifying_grab",
    "no_fresh_apriltag",
    "tag_not_visible",
}
TERMINAL_FAILURE_REASONS = {
    "ball_not_found",
    "ball_capture_zone_missing",
    "grab_failed",
    "grab_not_confirmed",
    "pickup_attempts_exhausted",
}
CONFIG_FIELD_ORDER = tuple(PICKUP_CONFIG_FIELDS)
DEFAULT_OPERATOR_CONFIG = OperatorConfig()


class PickupGoalLoop(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("pickup_goal_loop")
        self.args = args
        self._operator_command_pub = self.create_publisher(
            String, args.operator_command_topic, 10
        )
        self._vex_cmd_pub = self.create_publisher(String, args.vex_command_topic, 10)
        self.create_subscription(
            String, args.operator_status_topic, self._on_status, 20
        )
        self.create_subscription(
            String, args.operator_result_topic, self._on_result, 20
        )
        self.create_subscription(String, args.operator_event_topic, self._on_event, 50)
        self.create_subscription(
            String, args.object_indications_topic, self._on_object_indications, 20
        )
        self.create_subscription(String, args.telemetry_topic, self._on_telemetry, 20)
        self.create_subscription(String, args.ack_topic, self._on_ack, 20)
        self.seq = int(args.seq_start)
        self.latest_operator_status: dict[str, Any] | None = None
        self.latest_operator_summary: dict[str, Any] | None = None
        self.latest_telemetry: dict[str, Any] | None = None
        self.latest_ack: dict[str, Any] | None = None
        self.results: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []
        self.object_indications: list[dict[str, Any]] = []
        self.commands_sent = 0
        self.stops_sent = 0

    def _on_status(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is None:
            return
        if payload.get("type") == "operator_status":
            self.latest_operator_status = payload
        elif payload.get("type") == "operator_result":
            self.latest_operator_summary = payload

    def _on_result(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is not None:
            self.results.append(payload)

    def _on_event(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is not None:
            self.events.append(payload)

    def _on_object_indications(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is None:
            return
        if isinstance(payload, Mapping):
            raw_items = payload.get("objects", payload.get("indications", [payload]))
        else:
            raw_items = payload
        if not isinstance(raw_items, list):
            return
        received_s = time.monotonic()
        for item in raw_items:
            if not isinstance(item, Mapping):
                continue
            record = dict(item)
            record["_received_s"] = received_s
            self.object_indications.append(record)
        self.object_indications = self.object_indications[-100:]

    def _on_telemetry(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is not None:
            self.latest_telemetry = payload

    def _on_ack(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is not None:
            self.latest_ack = payload

    def spin_for(self, duration_s: float) -> None:
        deadline_s = time.monotonic() + max(0.0, duration_s)
        while time.monotonic() < deadline_s:
            assert rclpy is not None
            rclpy.spin_once(self, timeout_sec=0.05)

    def publish_operator_command(self, payload: Mapping[str, Any]) -> None:
        self.commands_sent += 1
        self._operator_command_pub.publish(
            String(
                data=json.dumps(dict(payload), separators=(",", ":"), sort_keys=True)
            )
        )

    def stop(self, reason: str) -> None:
        self.seq += 1
        self.stops_sent += 1
        packet = {
            "v": PROTOCOL_VERSION,
            "seq": self.seq,
            "type": "cmd",
            "cmd": "stop",
            "sent_ms": now_ms(),
            "ttl_ms": 200,
            "reason": reason,
        }
        self._vex_cmd_pub.publish(
            String(data=json.dumps(packet, separators=(",", ":"), sort_keys=True))
        )
        self.spin_for(0.25)

    def wait_for_status(self, timeout_s: float) -> bool:
        deadline_s = time.monotonic() + max(0.0, timeout_s)
        while time.monotonic() < deadline_s:
            if self.latest_operator_status is not None:
                return True
            self.spin_for(0.1)
        return self.latest_operator_status is not None

    def configure_pickup(self, config: Mapping[str, float]) -> None:
        if not config:
            return
        self.publish_operator_command({"action": "configure_pickup", "config": config})
        self.spin_for(self.args.configure_settle_s)

    def reset_operator(self) -> None:
        self.publish_operator_command({"action": "reset_operator"})
        self.spin_for(self.args.reset_settle_s)

    def run_attempt(
        self, attempt_index: int, *, candidate_index: int
    ) -> dict[str, Any]:
        started_s = time.monotonic()
        processed_result_index = len(self.results)
        next_command_s = 0.0
        terminal: dict[str, Any] | None = None
        pickup_results: list[dict[str, Any]] = []
        reason = "attempt_timeout"

        while time.monotonic() - started_s < self.args.attempt_timeout_s:
            now_s = time.monotonic()
            if now_s >= next_command_s:
                self.publish_operator_command(
                    {"action": "pickup_ball", "duration_ms": self.args.grab_ms}
                )
                next_command_s = now_s + self.args.command_period_s

            self.spin_for(0.05)
            for result in self.results[processed_result_index:]:
                processed_result_index += 1
                outcome = result.get("outcome") if isinstance(result, Mapping) else None
                if not isinstance(outcome, Mapping):
                    continue
                if outcome.get("method") != "pickup_ball":
                    continue
                pickup_results.append(result)
                result_reason = str(outcome.get("reason", ""))
                success = bool(outcome.get("success", False))
                if success and result_reason == "ball_grabbed":
                    terminal = result
                    reason = result_reason
                    break
                if result_reason in TERMINAL_FAILURE_REASONS:
                    terminal = result
                    reason = result_reason
                    break
                if not success and result_reason not in PICKUP_IN_PROGRESS_REASONS:
                    terminal = result
                    reason = result_reason or "pickup_failed"
                    break
            if terminal is not None:
                break

        self.stop(f"pickup_goal_loop_attempt_{attempt_index}_stop")
        verification = self.verify_terminal_success(terminal)
        succeeded = bool(terminal) and verification["success"]
        return {
            "candidate": candidate_index,
            "attempt": attempt_index,
            "status": "succeeded" if succeeded else "failed",
            "reason": "ball_grabbed" if succeeded else reason,
            "duration_s": round(time.monotonic() - started_s, 3),
            "terminal_result": terminal,
            "verification": verification,
            "pickup_result_count": len(pickup_results),
            "latest_operator_status": self.latest_operator_status,
            "latest_operator_summary": self.latest_operator_summary,
            "latest_telemetry": self.latest_telemetry,
            "latest_ack": self.latest_ack,
        }

    def verify_terminal_success(
        self, terminal: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        self.spin_for(self.args.post_verify_s)
        status = self.latest_operator_status
        outcome = terminal.get("outcome") if isinstance(terminal, Mapping) else None
        terminal_ok = (
            isinstance(outcome, Mapping)
            and bool(outcome.get("success", False))
            and outcome.get("reason") == "ball_grabbed"
        )
        has_object = (
            bool(status.get("has_object")) if isinstance(status, Mapping) else False
        )
        outside = self.fresh_balls_outside_claw()
        success = terminal_ok and has_object and not outside
        return {
            "success": success,
            "terminal_ball_grabbed": terminal_ok,
            "status_seen": status is not None,
            "status_has_object": has_object,
            "outside_ball_count": len(outside),
            "outside_balls": outside[:5],
        }

    def active_pickup_config(self) -> dict[str, float]:
        status = self.latest_operator_status or {}
        raw_config = (
            status.get("pickup_config") if isinstance(status, Mapping) else None
        )
        config: dict[str, float] = {}
        if isinstance(raw_config, Mapping):
            for key in CONFIG_FIELD_ORDER:
                if raw_config.get(key) is not None:
                    config[key] = float(raw_config[key])
        for key in CONFIG_FIELD_ORDER:
            if key not in config:
                config[key] = float(getattr(DEFAULT_OPERATOR_CONFIG, key))
        return config

    def camera_in_robot(self) -> Pose2D | None:
        status = self.latest_operator_status or {}
        raw_pose = (
            status.get("camera_in_robot") if isinstance(status, Mapping) else None
        )
        if not isinstance(raw_pose, Mapping):
            return None
        try:
            return pose_from_mapping(raw_pose)
        except (TypeError, ValueError):
            return None

    def fresh_balls_outside_claw(self) -> list[dict[str, Any]]:
        config = self.active_pickup_config()
        camera_in_robot = self.camera_in_robot()
        now_s = time.monotonic()
        outside: list[dict[str, Any]] = []
        for item in self.object_indications:
            if not _is_ball_indication(item):
                continue
            stamp_s = float(item.get("stamp_s", item.get("_received_s", now_s)))
            if now_s - stamp_s > self.args.object_stale_s:
                continue
            robot_pose = _robot_object_pose(item, camera_in_robot=camera_in_robot)
            if robot_pose is None:
                outside.append(
                    {
                        "name": _indication_name(item),
                        "reason": "pose_unavailable",
                        "confidence": item.get("confidence"),
                    }
                )
                continue
            lateral_error_m = robot_pose.y_m - config["ball_claw_lateral_target_m"]
            in_claw_zone = (
                robot_pose.x_m <= config["ball_capture_forward_m"]
                and abs(lateral_error_m) <= config["ball_capture_lateral_m"]
            )
            if not in_claw_zone:
                outside.append(
                    {
                        "name": _indication_name(item),
                        "forward_m": robot_pose.x_m,
                        "left_m": robot_pose.y_m,
                        "lateral_error_m": lateral_error_m,
                        "confidence": item.get("confidence"),
                    }
                )
        return outside

    def run(self, configs: list[Mapping[str, float]]) -> dict[str, Any]:
        started_wall_s = time.time()
        self.wait_for_status(self.args.status_timeout_s)
        candidates: list[dict[str, Any]] = []
        flat_attempts: list[dict[str, Any]] = []
        attempts: list[dict[str, Any]] = []
        succeeded = False
        reason = "no_attempts"
        last_config: Mapping[str, float] = {}
        attempt_count = max(1, int(self.args.attempts))
        try:
            for candidate_index, config in enumerate(configs or [{}], start=1):
                last_config = config
                attempts = []
                if self.args.reset:
                    self.reset_operator()
                self.configure_pickup(config)
                for attempt_index in range(1, attempt_count + 1):
                    attempt = self.run_attempt(
                        attempt_index, candidate_index=candidate_index
                    )
                    attempts.append(attempt)
                    flat_attempts.append(attempt)
                    reason = str(attempt["reason"])
                    if attempt["status"] == "succeeded":
                        succeeded = True
                        reason = "ball_grabbed"
                        break
                    if attempt_index < attempt_count:
                        self.reset_operator()
                        self.spin_for(self.args.between_attempts_s)

                candidates.append(
                    {
                        "candidate": candidate_index,
                        "status": "succeeded" if succeeded else "failed",
                        "reason": "ball_grabbed" if succeeded else reason,
                        "config": dict(config),
                        "attempts": attempts,
                    }
                )
                if succeeded:
                    break
                if candidate_index < len(configs):
                    self.reset_operator()
                    self.spin_for(self.args.between_attempts_s)
        finally:
            self.stop("pickup_goal_loop_finally")

        return {
            "type": "pickup_goal_loop_result",
            "status": "succeeded" if succeeded else "failed",
            "reason": "ball_grabbed" if succeeded else reason,
            "started_wall_s": started_wall_s,
            "finished_wall_s": time.time(),
            "candidates": candidates,
            "attempts": flat_attempts,
            "commands_sent": self.commands_sent,
            "stops_sent": self.stops_sent,
            "configured_pickup": dict(last_config),
            "active_pickup_config": self.active_pickup_config(),
        }


def _loads_json(raw: str) -> dict[str, Any] | list[Any] | None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, (dict, list)):
        return payload
    return None


def _indication_name(item: Mapping[str, Any]) -> str:
    return str(item.get("name", item.get("class", item.get("label", "object"))))


def _is_ball_indication(item: Mapping[str, Any]) -> bool:
    return "ball" in _indication_name(item).lower()


def _robot_object_pose(
    item: Mapping[str, Any], *, camera_in_robot: Pose2D | None
) -> Pose2D | None:
    if item.get("forward_m") is None or item.get("left_m") is None:
        return None
    try:
        camera_from_object = Pose2D(
            float(item["forward_m"]),
            float(item["left_m"]),
            float(item.get("yaw_rad", 0.0)),
        )
    except (TypeError, ValueError):
        return None
    if camera_in_robot is None:
        return camera_from_object
    return robot_from_camera_pose(camera_from_object, camera_in_robot)


def collect_pickup_config(args: argparse.Namespace) -> dict[str, float]:
    config: dict[str, float] = {}
    if args.config_json:
        payload = json.loads(args.config_json)
        if not isinstance(payload, Mapping):
            raise ValueError("--config-json must decode to a JSON object")
        config.update(_validate_pickup_config(payload))
    for key in CONFIG_FIELD_ORDER:
        value = getattr(args, key)
        if value is not None:
            config[key] = float(value)
    return _validate_pickup_config(config)


def collect_pickup_config_candidates(
    args: argparse.Namespace,
) -> list[dict[str, float]]:
    base = collect_pickup_config(args)
    candidates: list[dict[str, float]] = []

    if args.sweep_json:
        payload = json.loads(args.sweep_json)
        if not isinstance(payload, list):
            raise ValueError("--sweep-json must decode to a JSON array")
        for item in payload:
            if not isinstance(item, Mapping):
                raise ValueError("--sweep-json entries must be JSON objects")
            candidates.append(_validate_pickup_config({**base, **item}))

    sweep_fields = {
        "ball_claw_lateral_target_m": _parse_float_list(
            args.sweep_ball_claw_lateral_target_m
        ),
        "ball_close_forward_m": _parse_float_list(args.sweep_ball_close_forward_m),
        "ball_capture_lateral_m": _parse_float_list(args.sweep_ball_capture_lateral_m),
    }
    sweep_fields = {key: values for key, values in sweep_fields.items() if values}
    if sweep_fields:
        keys = tuple(sweep_fields)
        for values in itertools.product(*(sweep_fields[key] for key in keys)):
            updates = dict(zip(keys, values, strict=True))
            candidates.append(_validate_pickup_config({**base, **updates}))

    if not candidates:
        candidates.append(base)
    return _dedupe_configs(candidates)


def _parse_float_list(raw: str) -> list[float]:
    if not raw:
        return []
    values: list[float] = []
    for part in raw.split(","):
        text = part.strip()
        if not text:
            continue
        values.append(float(text))
    return values


def _dedupe_configs(configs: list[dict[str, float]]) -> list[dict[str, float]]:
    seen: set[str] = set()
    unique: list[dict[str, float]] = []
    for config in configs:
        key = json.dumps(config, sort_keys=True, separators=(",", ":"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(config)
    return unique


def _validate_pickup_config(raw_config: Mapping[str, Any]) -> dict[str, float]:
    extra = sorted(set(raw_config) - set(PICKUP_CONFIG_FIELDS))
    if extra:
        raise ValueError(f"unsupported pickup config keys: {extra}")
    config: dict[str, float] = {}
    for key, raw_value in raw_config.items():
        value = float(raw_value)
        if not math.isfinite(value):
            raise ValueError(f"pickup config {key} must be finite")
        minimum, maximum = PICKUP_CONFIG_FIELDS[key]
        if value < minimum or value > maximum:
            raise ValueError(
                f"pickup config {key} must be between {minimum} and {maximum}"
            )
        config[key] = value
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run repeated operator pickup attempts until strict ball-grab proof."
    )
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--attempt-timeout-s", type=float, default=45.0)
    parser.add_argument("--command-period-s", type=float, default=0.25)
    parser.add_argument("--grab-ms", type=int, default=700)
    parser.add_argument("--post-verify-s", type=float, default=0.8)
    parser.add_argument("--between-attempts-s", type=float, default=1.0)
    parser.add_argument("--status-timeout-s", type=float, default=3.0)
    parser.add_argument("--configure-settle-s", type=float, default=0.5)
    parser.add_argument("--reset-settle-s", type=float, default=0.5)
    parser.add_argument("--object-stale-s", type=float, default=1.0)
    parser.add_argument("--no-reset", dest="reset", action="store_false")
    parser.set_defaults(reset=True)
    parser.add_argument("--config-json", default="")
    parser.add_argument("--sweep-json", default="")
    parser.add_argument("--sweep-ball-claw-lateral-target-m", default="")
    parser.add_argument("--sweep-ball-close-forward-m", default="")
    parser.add_argument("--sweep-ball-capture-lateral-m", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--seq-start", type=int, default=42000)
    parser.add_argument("--operator-command-topic", default="/operator/command")
    parser.add_argument("--operator-status-topic", default="/operator/status")
    parser.add_argument("--operator-result-topic", default="/operator/results")
    parser.add_argument("--operator-event-topic", default="/operator/events")
    parser.add_argument(
        "--object-indications-topic", default="/vision/object_indications"
    )
    parser.add_argument("--telemetry-topic", default="/vex/telemetry")
    parser.add_argument("--ack-topic", default="/vex/ack")
    parser.add_argument("--vex-command-topic", default="/vex/cmd")
    for key in CONFIG_FIELD_ORDER:
        parser.add_argument(f"--{key.replace('_', '-')}", type=float, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    if rclpy is None:
        raise RuntimeError("rclpy is required to run vexy_pickup_goal_loop")
    parser = build_parser()
    args = parser.parse_args(argv)
    configs = collect_pickup_config_candidates(args)
    rclpy.init(args=None)
    node = PickupGoalLoop(args)
    try:
        summary = node.run(configs)
    finally:
        node.destroy_node()
        rclpy.shutdown()
    output = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).expanduser().write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
