from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except ModuleNotFoundError:  # pragma: no cover - keeps helper tests ROS-free.
    rclpy = None  # type: ignore[assignment]

    class Node:  # type: ignore[no-redef]
        pass

    class String:  # type: ignore[no-redef]
        def __init__(self, *, data: str = "") -> None:
            self.data = data


@dataclass(frozen=True)
class BallDetection:
    bbox_xyxy: tuple[float, float, float, float]
    confidence: float
    stamp_s: float | None = None

    @property
    def cx(self) -> float:
        return (self.bbox_xyxy[0] + self.bbox_xyxy[2]) / 2.0

    @property
    def cy(self) -> float:
        return (self.bbox_xyxy[1] + self.bbox_xyxy[3]) / 2.0

    @property
    def width(self) -> float:
        return self.bbox_xyxy[2] - self.bbox_xyxy[0]

    @property
    def height(self) -> float:
        return self.bbox_xyxy[3] - self.bbox_xyxy[1]

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["cx"] = self.cx
        payload["cy"] = self.cy
        payload["width"] = self.width
        payload["height"] = self.height
        payload["bbox_xyxy"] = list(self.bbox_xyxy)
        return payload


def parse_float_list(raw: str) -> list[float]:
    values: list[float] = []
    for part in raw.split(","):
        text = part.strip()
        if not text:
            continue
        values.append(float(text))
    return values


def best_ball_detection(payload: Mapping[str, Any]) -> BallDetection | None:
    detections = payload.get("detections")
    if not isinstance(detections, list):
        return None
    candidates: list[BallDetection] = []
    for item in detections:
        if not isinstance(item, Mapping):
            continue
        label = str(item.get("label", item.get("name", ""))).strip().lower()
        if label not in {"yellow_ball", "ball", "sports_ball"}:
            continue
        bbox = item.get("bbox_xyxy")
        if not isinstance(bbox, list | tuple) or len(bbox) != 4:
            continue
        try:
            candidate = BallDetection(
                bbox_xyxy=tuple(float(value) for value in bbox),  # type: ignore[arg-type]
                confidence=float(item.get("confidence") or 0.0),
                stamp_s=(
                    float(item["stamp_s"]) if item.get("stamp_s") is not None else None
                ),
            )
        except (TypeError, ValueError):
            continue
        if candidate.width > 0.0 and candidate.height > 0.0:
            candidates.append(candidate)
    if not candidates:
        return None
    return max(candidates, key=lambda detection: detection.confidence)


def has_object_from_status(status: Mapping[str, Any] | None) -> bool:
    return bool(status and status.get("has_object") is True)


class VisualPickupProbe(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("visual_pickup_probe")
        self.args = args
        self.seq = int(args.seq_start)
        self.latest_detection: BallDetection | None = None
        self.latest_detection_seen_s: float | None = None
        self.latest_status: dict[str, Any] | None = None
        self.latest_telemetry: dict[str, Any] | None = None
        self.latest_ack: dict[str, Any] | None = None
        self.acks: list[dict[str, Any]] = []
        self.commands: list[dict[str, Any]] = []

        self._cmd_pub = self.create_publisher(String, args.vex_command_topic, 10)
        self.create_subscription(String, args.ack_topic, self._on_ack, 50)
        self.create_subscription(
            String, args.object_detections_topic, self._on_object_detections, 20
        )
        self.create_subscription(String, args.operator_status_topic, self._on_status, 20)
        self.create_subscription(String, args.telemetry_topic, self._on_telemetry, 20)

    def _on_ack(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is None:
            return
        self.latest_ack = payload
        self.acks.append(payload)
        self.acks = self.acks[-200:]

    def _on_object_detections(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is None:
            return
        detection = best_ball_detection(payload)
        if detection is None:
            return
        self.latest_detection = detection
        self.latest_detection_seen_s = time.monotonic()

    def _on_status(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is not None and payload.get("type") == "operator_status":
            self.latest_status = payload

    def _on_telemetry(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is not None:
            self.latest_telemetry = payload

    def spin_for(self, duration_s: float) -> None:
        deadline_s = time.monotonic() + max(0.0, duration_s)
        while time.monotonic() < deadline_s:
            assert rclpy is not None
            rclpy.spin_once(self, timeout_sec=0.05)

    def wait_for_subscriber(self, timeout_s: float) -> bool:
        deadline_s = time.monotonic() + max(0.0, timeout_s)
        while self._cmd_pub.get_subscription_count() < 1 and time.monotonic() < deadline_s:
            self.spin_for(0.1)
        return self._cmd_pub.get_subscription_count() >= 1

    def fresh_detection(self) -> BallDetection | None:
        if self.latest_detection_seen_s is None:
            return None
        if time.monotonic() - self.latest_detection_seen_s > self.args.max_detection_age_s:
            return None
        return self.latest_detection

    def send(self, cmd: str, **fields: Any) -> dict[str, Any]:
        self.seq += 1
        packet = {
            "v": 1,
            "seq": self.seq,
            "type": "cmd",
            "cmd": cmd,
            "sent_ms": int(time.monotonic() * 1000),
            "ttl_ms": int(fields.pop("ttl_ms", self.args.command_ttl_ms)),
        }
        packet.update(fields)
        self._cmd_pub.publish(
            String(data=json.dumps(packet, separators=(",", ":"), sort_keys=True))
        )
        self.commands.append(packet)
        self.spin_for(0.04)
        return packet

    def stop(self, reason: str) -> None:
        self.send("stop", ttl_ms=self.args.stop_ttl_ms, reason=reason)
        self.spin_for(self.args.stop_settle_s)

    def run_candidate(self, target_px: float, candidate_index: int) -> dict[str, Any]:
        self.spin_for(self.args.initial_settle_s)
        initial = self.fresh_detection()
        self.send(
            "release",
            duration_ms=self.args.release_ms,
            ttl_ms=max(self.args.release_ms, self.args.command_ttl_ms),
            reason=f"visual_probe_{candidate_index}_open",
        )
        self.spin_for(self.args.open_settle_s)
        for _ in range(self.args.backoff_pulses):
            self.send(
                "drive",
                vx=-abs(self.args.backoff_vx),
                vy=0.0,
                omega=0.0,
                ttl_ms=self.args.command_ttl_ms,
                reason=f"visual_probe_{candidate_index}_backoff",
            )
            self.spin_for(self.args.pulse_spacing_s)
        self.stop(f"visual_probe_{candidate_index}_backoff_stop")

        align_samples = self._align_to_target(target_px, candidate_index)
        self.stop(f"visual_probe_{candidate_index}_align_stop")
        aligned = self.fresh_detection()
        approach_samples = self._approach_to_width(target_px, candidate_index)
        self.stop(f"visual_probe_{candidate_index}_approach_stop")
        preclose = self.fresh_detection()
        close_packet = self.send(
            "grab",
            duration_ms=self.args.grab_ms,
            ttl_ms=max(self.args.grab_ms, self.args.command_ttl_ms),
            reason=f"visual_probe_{candidate_index}_close",
        )
        self.spin_for(self.args.post_close_s)
        self.stop(f"visual_probe_{candidate_index}_post_close_stop")
        self.spin_for(self.args.post_verify_s)
        terminal = self.fresh_detection()
        return {
            "candidate": candidate_index,
            "target_px": target_px,
            "status": "succeeded" if has_object_from_status(self.latest_status) else "failed",
            "reason": (
                "has_object_true"
                if has_object_from_status(self.latest_status)
                else "grab_not_confirmed"
            ),
            "initial_detection": None if initial is None else initial.to_json(),
            "align_samples": align_samples,
            "aligned_detection": None if aligned is None else aligned.to_json(),
            "approach_samples": approach_samples,
            "preclose_detection": None if preclose is None else preclose.to_json(),
            "terminal_detection": None if terminal is None else terminal.to_json(),
            "close_packet": close_packet,
            "latest_status": self.latest_status,
            "latest_telemetry": self.latest_telemetry,
            "latest_ack": self.latest_ack,
            "ack_tail": self.acks[-20:],
        }

    def _align_to_target(self, target_px: float, candidate_index: int) -> list[dict[str, float]]:
        samples: list[dict[str, float]] = []
        deadline_s = time.monotonic() + self.args.align_timeout_s
        while time.monotonic() < deadline_s:
            detection = self.fresh_detection()
            if detection is None:
                self.send(
                    "drive",
                    vx=0.0,
                    vy=0.0,
                    omega=self.args.reacquire_omega,
                    ttl_ms=self.args.command_ttl_ms,
                    reason=f"visual_probe_{candidate_index}_reacquire",
                )
                self.spin_for(self.args.pulse_spacing_s)
                continue
            error = detection.cx - target_px
            samples.append(
                {"cx": detection.cx, "width": detection.width, "error_px": error}
            )
            if abs(error) <= self.args.align_tolerance_px:
                break
            omega = -self.args.align_omega if error > 0.0 else self.args.align_omega
            self.send(
                "drive",
                vx=0.0,
                vy=0.0,
                omega=omega,
                ttl_ms=self.args.command_ttl_ms,
                reason=f"visual_probe_{candidate_index}_align",
            )
            self.spin_for(self.args.pulse_spacing_s)
        return samples

    def _approach_to_width(
        self, target_px: float, candidate_index: int
    ) -> list[dict[str, float]]:
        samples: list[dict[str, float]] = []
        deadline_s = time.monotonic() + self.args.approach_timeout_s
        while time.monotonic() < deadline_s:
            detection = self.fresh_detection()
            if detection is None:
                self.send(
                    "drive",
                    vx=0.0,
                    vy=0.0,
                    omega=self.args.reacquire_omega,
                    ttl_ms=self.args.command_ttl_ms,
                    reason=f"visual_probe_{candidate_index}_lost_ball",
                )
                self.spin_for(self.args.pulse_spacing_s)
                continue
            error = detection.cx - target_px
            samples.append(
                {"cx": detection.cx, "width": detection.width, "error_px": error}
            )
            if detection.width >= self.args.approach_width_px:
                break
            omega = max(
                -self.args.approach_max_omega,
                min(self.args.approach_max_omega, -self.args.approach_kp * error),
            )
            vx = self.args.approach_vx if abs(error) <= self.args.approach_vx_error_px else self.args.approach_slow_vx
            self.send(
                "drive",
                vx=vx,
                vy=0.0,
                omega=omega,
                ttl_ms=self.args.command_ttl_ms,
                reason=f"visual_probe_{candidate_index}_approach",
            )
            self.spin_for(self.args.pulse_spacing_s)
        return samples

    def run(self) -> dict[str, Any]:
        targets = parse_float_list(self.args.target_px)
        if not targets:
            raise ValueError("--target-px requires at least one value")
        subscriber_ready = self.wait_for_subscriber(self.args.subscriber_timeout_s)
        attempts = [
            self.run_candidate(target, index)
            for index, target in enumerate(targets, start=1)
        ]
        success = next((attempt for attempt in attempts if attempt["status"] == "succeeded"), None)
        return {
            "type": "visual_pickup_probe_result",
            "status": "succeeded" if success else "failed",
            "reason": "has_object_true" if success else "grab_not_confirmed",
            "subscriber_ready": subscriber_ready,
            "targets": targets,
            "attempts": attempts,
            "commands_sent": len(self.commands),
            "command_tail": self.commands[-30:],
        }


def _loads_json(raw: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Visual-servo yellow ball pickup probe using bbox pixel targets."
    )
    parser.add_argument("--target-px", default="360,430")
    parser.add_argument("--align-tolerance-px", type=float, default=18.0)
    parser.add_argument("--approach-width-px", type=float, default=76.0)
    parser.add_argument("--approach-kp", type=float, default=0.006)
    parser.add_argument("--approach-max-omega", type=float, default=0.18)
    parser.add_argument("--align-omega", type=float, default=0.20)
    parser.add_argument("--reacquire-omega", type=float, default=0.12)
    parser.add_argument("--approach-vx", type=float, default=0.045)
    parser.add_argument("--approach-slow-vx", type=float, default=0.025)
    parser.add_argument("--approach-vx-error-px", type=float, default=70.0)
    parser.add_argument("--backoff-pulses", type=int, default=5)
    parser.add_argument("--backoff-vx", type=float, default=0.055)
    parser.add_argument("--pulse-spacing-s", type=float, default=0.15)
    parser.add_argument("--initial-settle-s", type=float, default=0.6)
    parser.add_argument("--open-settle-s", type=float, default=1.0)
    parser.add_argument("--stop-settle-s", type=float, default=0.2)
    parser.add_argument("--post-close-s", type=float, default=2.2)
    parser.add_argument("--post-verify-s", type=float, default=0.5)
    parser.add_argument("--align-timeout-s", type=float, default=9.0)
    parser.add_argument("--approach-timeout-s", type=float, default=7.5)
    parser.add_argument("--subscriber-timeout-s", type=float, default=5.0)
    parser.add_argument("--max-detection-age-s", type=float, default=1.0)
    parser.add_argument("--command-ttl-ms", type=int, default=230)
    parser.add_argument("--stop-ttl-ms", type=int, default=200)
    parser.add_argument("--release-ms", type=int, default=650)
    parser.add_argument("--grab-ms", type=int, default=1500)
    parser.add_argument("--seq-start", type=int, default=610000)
    parser.add_argument("--output", default="")
    parser.add_argument("--vex-command-topic", default="/vex/cmd")
    parser.add_argument("--ack-topic", default="/vex/ack")
    parser.add_argument("--object-detections-topic", default="/vision/object_detections")
    parser.add_argument("--operator-status-topic", default="/operator/status")
    parser.add_argument("--telemetry-topic", default="/vex/telemetry")
    return parser


def main(argv: list[str] | None = None) -> None:
    if rclpy is None:
        raise RuntimeError("rclpy is required to run visual_pickup_probe")
    parser = build_parser()
    args = parser.parse_args(argv)
    rclpy.init(args=None)
    node = VisualPickupProbe(args)
    try:
        summary = node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()
    output = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).expanduser().write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
