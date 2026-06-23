"""
ROS 2 node bridging the VEX V5 Brain over USB serial.

Topics
------
Subscribed:
  /vex/cmd  (std_msgs/String) — newline-delimited JSON command packet
Published:
  /vex/telemetry  (std_msgs/String) — JSON ack/telemetry from the Brain

The node also publishes a heartbeat every HEARTBEAT_INTERVAL_S if no command
arrives, keeping the Brain's watchdog alive and preventing it from issuing a
motor stop.

Wire protocol is identical to the Bookworm bridge (vexy_system2):
  - Protocol version 1
  - Newline-delimited compact JSON (no spaces)
  - Commands: stop | drive | turn | heartbeat | set_goal
  - Acks: {"v":1,"ack":<seq>,"type":"ack","state":"ok",...}
"""

import json
import threading
import time

import rclpy
import serial
from rclpy.node import Node
from std_msgs.msg import String

PROTOCOL_VERSION = 1
MAX_LINEAR = 0.35
MAX_OMEGA = 0.6
DEFAULT_TTL_MS = 200
HEARTBEAT_INTERVAL_S = 0.15  # send heartbeat if idle > this many seconds


def _now_ms() -> int:
    return int(time.monotonic() * 1000)


def _encode(packet: dict) -> bytes:
    return (json.dumps(packet, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


class VexBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("vex_bridge")

        self.declare_parameter("serial_port", "/dev/ttyACM0")
        self.declare_parameter("baud_rate", 115200)
        self.declare_parameter("serial_timeout", 0.4)

        port = self.get_parameter("serial_port").get_parameter_value().string_value
        baud = self.get_parameter("baud_rate").get_parameter_value().integer_value
        timeout = self.get_parameter("serial_timeout").get_parameter_value().double_value

        self._seq = 0
        self._lock = threading.Lock()
        self._last_cmd_time = time.monotonic()

        try:
            self._serial = serial.Serial(port=port, baudrate=baud, timeout=timeout, write_timeout=timeout)
            self.get_logger().info(f"connected to V5 Brain on {port} @ {baud}")
        except serial.SerialException as exc:
            self.get_logger().error(f"cannot open {port}: {exc}")
            self._serial = None

        self._telem_pub = self.create_publisher(String, "/vex/telemetry", 10)
        self._cmd_sub = self.create_subscription(String, "/vex/cmd", self._on_cmd, 10)
        self._heartbeat_timer = self.create_timer(HEARTBEAT_INTERVAL_S, self._maybe_heartbeat)

    # ------------------------------------------------------------------
    # Command subscriber
    # ------------------------------------------------------------------

    def _on_cmd(self, msg: String) -> None:
        try:
            packet = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"bad JSON on /vex/cmd: {exc}")
            return

        validated = self._validate(packet)
        if validated is None:
            return

        self._last_cmd_time = time.monotonic()
        self._send_and_publish(validated)

    # ------------------------------------------------------------------
    # Heartbeat timer — fires every HEARTBEAT_INTERVAL_S
    # ------------------------------------------------------------------

    def _maybe_heartbeat(self) -> None:
        if time.monotonic() - self._last_cmd_time >= HEARTBEAT_INTERVAL_S:
            self._seq += 1
            hb = {
                "v": PROTOCOL_VERSION,
                "seq": self._seq,
                "type": "heartbeat",
                "sent_ms": _now_ms(),
                "ttl_ms": DEFAULT_TTL_MS,
            }
            self._send_and_publish(hb)

    # ------------------------------------------------------------------
    # Validate outbound packet (mirrors protocol.validate_outbound)
    # ------------------------------------------------------------------

    def _validate(self, packet: dict) -> dict | None:
        if packet.get("v") != PROTOCOL_VERSION:
            self.get_logger().warn(f"unsupported protocol version: {packet.get('v')}")
            return None
        if not isinstance(packet.get("seq"), int):
            self.get_logger().warn("seq must be an integer")
            return None
        ptype = packet.get("type")
        if ptype not in {"cmd", "heartbeat"}:
            self.get_logger().warn(f"type must be cmd or heartbeat, got: {ptype!r}")
            return None

        ttl = int(packet.get("ttl_ms", DEFAULT_TTL_MS))
        packet["ttl_ms"] = max(1, min(ttl, 5000))

        if ptype == "heartbeat":
            return packet

        cmd = packet.get("cmd")
        if cmd not in {"stop", "drive", "turn", "set_goal"}:
            self.get_logger().warn(f"unsupported cmd: {cmd!r}")
            return None

        if cmd == "drive":
            packet["vx"] = _clamp(float(packet.get("vx", 0.0)), -MAX_LINEAR, MAX_LINEAR)
            packet["vy"] = _clamp(float(packet.get("vy", 0.0)), -MAX_LINEAR, MAX_LINEAR)
            packet["omega"] = _clamp(float(packet.get("omega", 0.0)), -MAX_OMEGA, MAX_OMEGA)
        elif cmd == "turn":
            packet["omega"] = _clamp(float(packet.get("omega", 0.0)), -MAX_OMEGA, MAX_OMEGA)

        return packet

    # ------------------------------------------------------------------
    # Serial send + publish ack
    # ------------------------------------------------------------------

    def _send_and_publish(self, packet: dict) -> None:
        if self._serial is None:
            return

        try:
            with self._lock:
                self._serial.write(_encode(packet))
                self._serial.flush()
                line = self._serial.readline()

            if not line:
                self.get_logger().warn("timeout: no ack from V5 Brain")
                return

            ack = json.loads(line.decode("utf-8").strip())
            self._telem_pub.publish(String(data=json.dumps(ack)))

        except serial.SerialException as exc:
            self.get_logger().error(f"serial error: {exc}")
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"bad JSON from Brain: {exc}")

    def destroy_node(self) -> None:
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
