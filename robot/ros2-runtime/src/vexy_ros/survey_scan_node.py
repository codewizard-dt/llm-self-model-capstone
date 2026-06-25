from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Any

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .align_to_tag import BridgeHealth, VexCommand
from .bridge_protocol import PROTOCOL_VERSION, now_ms
from .survey_scan import SurveyScanController, SurveyScanGoal, SurveyTelemetry


class SurveyScanNode(Node):
    def __init__(self) -> None:
        super().__init__("survey_scan")

        self.declare_parameter("control_period_s", 0.1)

        self._controller = SurveyScanController()
        self._seq = 42000
        self._bridge = BridgeHealth(stamp_s=None)
        self._telemetry = SurveyTelemetry(stamp_s=None)
        self._observed_tag_ids: list[int] = []
        self._cancel_requested = False

        self._cmd_pub = self.create_publisher(String, "/vex/cmd", 10)
        self._feedback_pub = self.create_publisher(String, "/survey/feedback", 10)
        self._result_pub = self.create_publisher(String, "/survey/result", 10)

        self.create_subscription(String, "/survey/goal", self._on_goal, 10)
        self.create_subscription(String, "/survey/cancel", self._on_cancel, 10)
        self.create_subscription(String, "/vex/ack", self._on_ack, 10)
        self.create_subscription(String, "/vex/telemetry", self._on_telemetry, 10)
        self.create_subscription(
            String, "/vex/bridge_status", self._on_bridge_status, 10
        )
        self.create_subscription(String, "/vision/scene_map", self._on_scene_map, 10)

        period = float(self.get_parameter("control_period_s").value)
        self.create_timer(period, self._tick)

    def _on_goal(self, msg: String) -> None:
        try:
            raw = json.loads(msg.data)
            goal = SurveyScanGoal(
                duration_s=float(raw.get("duration_s", 14.5)),
                omega_rad_s=float(raw.get("omega_rad_s", raw.get("omega", 0.45))),
                max_step_ms=int(raw.get("max_step_ms", raw.get("ttl_ms", 180))),
                ack_stale_s=float(raw.get("ack_stale_s", 0.8)),
                telemetry_stale_s=float(raw.get("telemetry_stale_s", 1.0)),
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._publish_result(
                {"success": False, "reason": "bad_goal", "fault": str(exc)}
            )
            return

        decision = self._controller.start(
            goal,
            now_s=time.monotonic(),
            bridge=self._bridge,
            telemetry=self._telemetry,
            observed_tag_ids=self._observed_tag_ids,
        )
        self._handle_decision(decision)

    def _on_cancel(self, msg: String) -> None:
        self._cancel_requested = True

    def _on_ack(self, msg: String) -> None:
        try:
            ack = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        ack_seq = ack.get("ack")
        fault = ack.get("fault") if isinstance(ack.get("fault"), str) else None
        self._bridge = BridgeHealth(
            stamp_s=time.monotonic(),
            last_ack_seq=ack_seq if isinstance(ack_seq, int) else None,
            fault=fault,
            status=str(ack.get("state", "ack")),
        )

    def _on_telemetry(self, msg: String) -> None:
        try:
            telemetry = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        self._telemetry = SurveyTelemetry(
            stamp_s=time.monotonic(),
            motion_enabled=bool(telemetry.get("motion_enabled", False)),
            estop=bool(telemetry.get("estop", False)),
            drive_ports_ok=bool(telemetry.get("drive_ports_ok", False)),
            left_pos_deg=_optional_float(telemetry.get("left_pos_deg")),
            right_pos_deg=_optional_float(telemetry.get("right_pos_deg")),
            left_vel_rpm=_optional_float(telemetry.get("left_vel_rpm")),
            right_vel_rpm=_optional_float(telemetry.get("right_vel_rpm")),
        )

    def _on_bridge_status(self, msg: String) -> None:
        try:
            status = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        state = str(status.get("state", "unknown"))
        fault = None
        if state == "fault":
            fault = str(status.get("reason", "bridge_fault"))
        self._bridge = BridgeHealth(
            stamp_s=time.monotonic() if fault else self._bridge.stamp_s,
            last_ack_seq=self._bridge.last_ack_seq,
            fault=fault,
            status=state,
        )

    def _on_scene_map(self, msg: String) -> None:
        try:
            scene = json.loads(msg.data)
            tag_ids = [int(tag_id) for tag_id in scene.get("observed_tag_ids", [])]
        except (TypeError, ValueError, json.JSONDecodeError):
            return
        self._observed_tag_ids = sorted(tag_ids)

    def _tick(self) -> None:
        decision = self._controller.step(
            now_s=time.monotonic(),
            bridge=self._bridge,
            telemetry=self._telemetry,
            observed_tag_ids=self._observed_tag_ids,
            cancel=self._cancel_requested,
        )
        self._cancel_requested = False
        self._handle_decision(decision)

    def _handle_decision(self, decision) -> None:
        self._feedback_pub.publish(
            String(data=json.dumps(asdict(decision.feedback), sort_keys=True))
        )
        if decision.command is not None:
            self._publish_command(decision.command)
        if decision.result is not None:
            self._publish_result(asdict(decision.result))

    def _publish_command(self, command: VexCommand) -> None:
        self._seq += 1
        packet: dict[str, Any] = {
            "v": PROTOCOL_VERSION,
            "seq": self._seq,
            "type": "cmd",
            "cmd": command.cmd,
            "sent_ms": now_ms(),
            "ttl_ms": command.ttl_ms,
        }
        if command.cmd == "turn":
            packet["omega"] = command.omega
        if command.cmd == "drive":
            packet.update({"vx": command.vx, "vy": command.vy, "omega": command.omega})
        if command.reason:
            packet["reason"] = command.reason
        self._cmd_pub.publish(
            String(data=json.dumps(packet, separators=(",", ":"), sort_keys=True))
        )

    def _publish_result(self, payload: dict[str, Any]) -> None:
        self._result_pub.publish(String(data=json.dumps(payload, sort_keys=True)))


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SurveyScanNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
