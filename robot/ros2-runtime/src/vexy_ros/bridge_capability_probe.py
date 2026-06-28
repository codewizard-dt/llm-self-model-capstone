from __future__ import annotations

import argparse
import json
import time
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


def command_supported_from_ack(ack: Mapping[str, Any] | None, command: str) -> bool:
    if ack is None or ack.get("state") != "ok":
        return False
    supported = ack.get("supported_commands")
    if isinstance(supported, list):
        return command in {str(item) for item in supported}
    return command == "arm" and ack.get("fault") is None


def command_rejection_reason(ack: Mapping[str, Any] | None) -> str:
    if ack is None:
        return "missing_ack"
    if ack.get("state") == "ok":
        return "accepted"
    return str(ack.get("fault") or ack.get("state") or "rejected")


class BridgeCapabilityProbe(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("bridge_capability_probe")
        self.args = args
        self.acks: list[dict[str, Any]] = []
        self.telemetry: list[dict[str, Any]] = []
        self._cmd_pub = self.create_publisher(String, args.vex_command_topic, 10)
        self.create_subscription(String, args.ack_topic, self._on_ack, 50)
        self.create_subscription(String, args.telemetry_topic, self._on_telemetry, 20)

    def _on_ack(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is not None:
            self.acks.append(payload)

    def _on_telemetry(self, msg: String) -> None:
        payload = _loads_json(msg.data)
        if payload is not None:
            self.telemetry.append(payload)
            self.telemetry = self.telemetry[-20:]

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

    def run(self) -> dict[str, Any]:
        self.wait_for_subscriber(self.args.subscriber_timeout_s)
        self.spin_for(self.args.initial_settle_s)
        seq = int(self.args.seq)
        packet = {
            "v": 1,
            "seq": seq,
            "type": "cmd",
            "cmd": "arm",
            "target_deg": float(self.args.arm_target_deg),
            "sent_ms": int(time.monotonic() * 1000),
            "ttl_ms": int(self.args.arm_ttl_ms),
            "reason": "bridge_capability_probe_arm",
        }
        self._cmd_pub.publish(
            String(data=json.dumps(packet, separators=(",", ":"), sort_keys=True))
        )
        deadline_s = time.monotonic() + max(0.0, self.args.ack_timeout_s)
        matched_ack: dict[str, Any] | None = None
        while time.monotonic() < deadline_s:
            self.spin_for(0.05)
            matched_ack = next((ack for ack in self.acks if ack.get("ack") == seq), None)
            if matched_ack is not None:
                break
        self.spin_for(self.args.post_probe_s)
        arm_supported = command_supported_from_ack(matched_ack, "arm")
        return {
            "type": "bridge_capability_probe_result",
            "status": "succeeded" if arm_supported else "failed",
            "reason": (
                "arm_command_supported"
                if arm_supported
                else f"arm_command_{command_rejection_reason(matched_ack)}"
            ),
            "arm_command_supported": arm_supported,
            "sent_packet": packet,
            "matched_ack": matched_ack,
            "ack_tail": self.acks[-20:],
            "telemetry_tail": self.telemetry[-5:],
        }


def _loads_json(raw: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe whether the running V5 Brain bridge supports direct arm commands."
    )
    parser.add_argument("--seq", type=int, default=912345)
    parser.add_argument("--arm-target-deg", type=float, default=40.0)
    parser.add_argument("--arm-ttl-ms", type=int, default=4000)
    parser.add_argument("--subscriber-timeout-s", type=float, default=5.0)
    parser.add_argument("--ack-timeout-s", type=float, default=6.0)
    parser.add_argument("--initial-settle-s", type=float, default=0.5)
    parser.add_argument("--post-probe-s", type=float, default=1.0)
    parser.add_argument("--output", default="")
    parser.add_argument("--vex-command-topic", default="/vex/cmd")
    parser.add_argument("--ack-topic", default="/vex/ack")
    parser.add_argument("--telemetry-topic", default="/vex/telemetry")
    return parser


def main(argv: list[str] | None = None) -> None:
    if rclpy is None:
        raise RuntimeError("rclpy is required to run bridge_capability_probe")
    parser = build_parser()
    args = parser.parse_args(argv)
    rclpy.init(args=None)
    node = BridgeCapabilityProbe(args)
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
