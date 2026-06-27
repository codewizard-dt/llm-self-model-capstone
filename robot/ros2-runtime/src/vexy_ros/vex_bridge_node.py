"""
ROS 2 node bridging the VEX V5 Brain over USB serial.

Topics
------
Subscribed:
  /vex/cmd  (std_msgs/String) — newline-delimited JSON command packet
Published:
  /vex/ack  (std_msgs/String) — JSON acknowledgement from the Brain
  /vex/telemetry  (std_msgs/String) — JSON telemetry/sample/event from the Brain
  /vex/bridge_status  (std_msgs/String) — bridge fault/status JSON

The node also publishes a heartbeat every HEARTBEAT_INTERVAL_S if no command
arrives, keeping the Brain's watchdog alive and preventing it from issuing a
motor stop.

Wire protocol:
  - Protocol version 1
  - Newline-delimited compact JSON (no spaces)
  - Commands: stop | drive | turn | heartbeat | set_goal
  - Acks: {"v":1,"ack":<seq>,"type":"ack","state":"ok",...}
"""

import json
import glob
import shlex
import subprocess
import threading
import time

import rclpy
import serial
from rclpy.node import Node
from std_msgs.msg import String

from .bridge_demux import BrainStreamDemux, DemuxEvent, bridge_status
from .bridge_protocol import (
    BridgeProtocolError,
    encode_packet,
    heartbeat_packet,
    normalize_outbound,
)

HEARTBEAT_INTERVAL_S = 0.15  # send heartbeat if idle > this many seconds
DEFAULT_BRAIN_PROGRAM_SLOT = 8
DEFAULT_BRAIN_PROGRAM_START_COMMAND = "pros v5 run {slot}"


class VexBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("vex_bridge")

        self.declare_parameter("serial_port", "")
        self.declare_parameter("baud_rate", 115200)
        self.declare_parameter("serial_timeout", 0.1)
        self.declare_parameter("ack_timeout_s", 0.4)
        self.declare_parameter("telemetry_stale_s", 2.0)
        self.declare_parameter("brain_program_slot", DEFAULT_BRAIN_PROGRAM_SLOT)
        self.declare_parameter(
            "brain_program_start_command", DEFAULT_BRAIN_PROGRAM_START_COMMAND
        )
        self.declare_parameter("brain_program_start_timeout_s", 8.0)
        self.declare_parameter("brain_program_start_settle_s", 2.0)

        configured_port = (
            self.get_parameter("serial_port").get_parameter_value().string_value
        )
        baud = self.get_parameter("baud_rate").get_parameter_value().integer_value
        timeout = (
            self.get_parameter("serial_timeout").get_parameter_value().double_value
        )
        ack_timeout_s = (
            self.get_parameter("ack_timeout_s").get_parameter_value().double_value
        )
        telemetry_stale_s = (
            self.get_parameter("telemetry_stale_s").get_parameter_value().double_value
        )
        brain_program_slot = (
            self.get_parameter("brain_program_slot").get_parameter_value().integer_value
        )
        brain_program_start_command = (
            self.get_parameter("brain_program_start_command")
            .get_parameter_value()
            .string_value
        )
        brain_program_start_timeout_s = (
            self.get_parameter("brain_program_start_timeout_s")
            .get_parameter_value()
            .double_value
        )
        brain_program_start_settle_s = (
            self.get_parameter("brain_program_start_settle_s")
            .get_parameter_value()
            .double_value
        )

        self._seq = 0
        self._write_lock = threading.Lock()
        self._last_cmd_time = time.monotonic()
        self._stop_reader = threading.Event()
        self._reader_thread: threading.Thread | None = None
        self._serial: serial.Serial | None = None
        self._demux = BrainStreamDemux(
            ack_timeout_s=ack_timeout_s,
            telemetry_stale_s=telemetry_stale_s,
        )
        self._last_status_signature: tuple[object, ...] | None = None
        self._last_status_emit_s = 0.0

        self._ack_pub = self.create_publisher(String, "/vex/ack", 10)
        self._telem_pub = self.create_publisher(String, "/vex/telemetry", 10)
        self._status_pub = self.create_publisher(String, "/vex/bridge_status", 10)
        self._cmd_sub = self.create_subscription(String, "/vex/cmd", self._on_cmd, 10)
        self._heartbeat_timer = self.create_timer(
            HEARTBEAT_INTERVAL_S, self._maybe_heartbeat
        )
        self._health_timer = self.create_timer(0.1, self._check_bridge_health)

        self._start_brain_program_slot(
            slot=brain_program_slot,
            command_template=brain_program_start_command,
            timeout_s=brain_program_start_timeout_s,
            settle_s=brain_program_start_settle_s,
        )
        port = self._resolve_serial_port(configured_port)
        try:
            self._serial = serial.Serial(
                port=port, baudrate=baud, timeout=timeout, write_timeout=timeout
            )
            self.get_logger().info(f"connected to V5 Brain on {port} @ {baud}")
            self._publish_status(
                bridge_status(
                    "serial_connected",
                    "connected to V5 Brain serial port",
                    state="ok",
                    port=port,
                    baud_rate=baud,
                )
            )
            self._start_reader()
        except serial.SerialException as exc:
            self.get_logger().error(f"cannot open {port}: {exc}")
            self._publish_status(
                bridge_status(
                    "serial_unavailable", f"cannot open {port}: {exc}", port=port
                )
            )

    def _start_brain_program_slot(
        self,
        *,
        slot: int,
        command_template: str,
        timeout_s: float,
        settle_s: float,
    ) -> None:
        command_template = command_template.strip()
        if not command_template:
            self._publish_status(
                bridge_status(
                    "brain_program_autostart_disabled",
                    f"V5 Brain program slot {slot} autostart is disabled",
                    state="warn",
                    slot=slot,
                )
            )
            return

        command = command_template.format(slot=slot)
        argv = shlex.split(command)
        if not argv:
            return

        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=max(0.1, timeout_s),
                check=False,
            )
        except FileNotFoundError as exc:
            self._publish_status(
                bridge_status(
                    "brain_program_start_unavailable",
                    f"cannot start V5 Brain program slot {slot}: {exc}",
                    slot=slot,
                    command=command,
                )
            )
            return
        except subprocess.TimeoutExpired:
            self._publish_status(
                bridge_status(
                    "brain_program_start_timeout",
                    f"timed out starting V5 Brain program slot {slot}",
                    slot=slot,
                    command=command,
                    timeout_s=timeout_s,
                )
            )
            return

        if completed.returncode != 0:
            stderr = (completed.stderr or completed.stdout or "").strip()
            self._publish_status(
                bridge_status(
                    "brain_program_start_failed",
                    f"failed to start V5 Brain program slot {slot}",
                    slot=slot,
                    command=command,
                    returncode=completed.returncode,
                    stderr=stderr[-400:],
                )
            )
            return

        self._publish_status(
            bridge_status(
                "brain_program_start_requested",
                f"requested V5 Brain program slot {slot}",
                state="ok",
                slot=slot,
                command=command,
            )
        )
        if settle_s > 0.0:
            time.sleep(settle_s)

    def _resolve_serial_port(self, configured_port: str) -> str:
        if configured_port and configured_port.lower() != "auto":
            return configured_port

        candidates = []
        for pattern in (
            "/dev/serial/by-id/*VEX*if02",
            "/dev/serial/by-id/*VEX*if02*",
            "/dev/ttyACM1",
            "/dev/ttyACM0",
        ):
            candidates.extend(glob.glob(pattern))

        if candidates:
            port = sorted(candidates)[0]
            self.get_logger().info(f"auto-selected V5 serial port {port}")
            return port

        self.get_logger().warn("no V5 serial device found during auto-discovery")
        return "/dev/ttyACM1"

    # ------------------------------------------------------------------
    # Command subscriber
    # ------------------------------------------------------------------

    def _on_cmd(self, msg: String) -> None:
        try:
            packet = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"bad JSON on /vex/cmd: {exc}")
            self._publish_status(
                bridge_status("bad_command_json", f"bad JSON on /vex/cmd: {exc}")
            )
            return

        validated = self._validate(packet)
        if validated is None:
            return

        self._last_cmd_time = time.monotonic()
        self._send_packet(validated)

    # ------------------------------------------------------------------
    # Heartbeat timer — fires every HEARTBEAT_INTERVAL_S
    # ------------------------------------------------------------------

    def _maybe_heartbeat(self) -> None:
        if time.monotonic() - self._last_cmd_time >= HEARTBEAT_INTERVAL_S:
            self._seq += 1
            self._send_packet(heartbeat_packet(self._seq))

    # ------------------------------------------------------------------
    # Validate outbound packet (mirrors protocol.validate_outbound)
    # ------------------------------------------------------------------

    def _validate(self, packet: dict) -> dict | None:
        try:
            return normalize_outbound(packet)
        except (BridgeProtocolError, TypeError, ValueError) as exc:
            self.get_logger().warn(str(exc))
            self._publish_status(
                bridge_status("invalid_command", str(exc), command=packet)
            )
            return None

    # ------------------------------------------------------------------
    # Serial reader + writer
    # ------------------------------------------------------------------

    def _start_reader(self) -> None:
        self._reader_thread = threading.Thread(
            target=self._reader_loop, name="vex-serial-reader", daemon=True
        )
        self._reader_thread.start()

    def _reader_loop(self) -> None:
        while not self._stop_reader.is_set():
            serial_obj = self._serial
            if serial_obj is None:
                return
            try:
                line = serial_obj.readline()
            except serial.SerialException as exc:
                self._mark_serial_fault(serial_obj, f"serial read error: {exc}")
                return

            if not line:
                continue

            for event in self._demux.consume_line(line):
                self._publish_event(event)

    def _send_packet(self, packet: dict) -> None:
        serial_obj = self._serial
        if serial_obj is None or not serial_obj.is_open:
            self._publish_status(
                bridge_status("serial_unavailable", "serial port is not open")
            )
            return

        seq = packet.get("seq")
        if isinstance(seq, int):
            self._demux.register_sent(packet)

        try:
            with self._write_lock:
                serial_obj = self._serial
                if serial_obj is None or not serial_obj.is_open:
                    self._publish_status(
                        bridge_status("serial_unavailable", "serial port is not open")
                    )
                    if isinstance(seq, int):
                        self._demux.forget(seq)
                    return
                serial_obj.write(encode_packet(packet))
                serial_obj.flush()
        except serial.SerialException as exc:
            if isinstance(seq, int):
                self._demux.forget(seq)
            self._mark_serial_fault(serial_obj, f"serial write error: {exc}")

    def _check_bridge_health(self) -> None:
        for event in self._demux.check_timeouts():
            self._publish_event(event)

    def _publish_event(self, event: DemuxEvent) -> None:
        if event.kind == "ack":
            self._ack_pub.publish(
                String(data=json.dumps(event.payload, sort_keys=True))
            )
            return
        if event.kind == "telemetry":
            self._telem_pub.publish(
                String(data=json.dumps(event.payload, sort_keys=True))
            )
            return
        self._publish_status(event.payload)

    def _publish_status(self, payload: dict) -> None:
        now_s = time.monotonic()
        signature = (
            payload.get("state"),
            payload.get("reason"),
            payload.get("seq"),
            payload.get("message"),
        )
        if (
            signature == self._last_status_signature
            and now_s - self._last_status_emit_s < 1.0
        ):
            return
        self._last_status_signature = signature
        self._last_status_emit_s = now_s
        self._status_pub.publish(String(data=json.dumps(payload, sort_keys=True)))

        reason = payload.get("reason")
        message = payload.get("message")
        state = payload.get("state")
        if state == "fault":
            self.get_logger().warn(f"bridge fault: {reason}: {message}")
        elif state == "warn":
            self.get_logger().warn(f"bridge warning: {reason}: {message}")
        else:
            self.get_logger().info(f"bridge status: {reason}: {message}")

    def _mark_serial_fault(
        self, serial_obj: serial.Serial | None, message: str
    ) -> None:
        self.get_logger().error(message)
        with self._write_lock:
            if serial_obj is not None and self._serial is serial_obj:
                self._serial = None
        if serial_obj is not None and serial_obj.is_open:
            try:
                serial_obj.close()
            except serial.SerialException:
                pass
        self._publish_status(bridge_status("serial_disconnect", message))

    def destroy_node(self) -> None:
        self._stop_reader.set()
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=1.0)
        if self._serial and self._serial.is_open:
            self._serial.close()
        super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = VexBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
