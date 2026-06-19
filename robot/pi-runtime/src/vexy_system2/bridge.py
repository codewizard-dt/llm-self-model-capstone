from __future__ import annotations

import argparse
import os
import socketserver
import threading
import time
from pathlib import Path
from typing import Any

from . import protocol
from .state import atomic_write_json, ensure_dir


class FakeV5Brain:
    def __init__(self) -> None:
        self.started_ms = protocol.now_ms()
        self.last_cmd: dict[str, Any] | None = None
        self.heading_deg = 0.0
        self.battery_mv = 12300
        self.estop = False

    def handle(self, packet: dict[str, Any]) -> dict[str, Any]:
        if packet.get("type") == "cmd":
            self.last_cmd = packet
            if packet.get("cmd") == "stop":
                self.estop = packet.get("reason") == "operator_estop"
            elif packet.get("cmd") == "turn":
                self.heading_deg = (self.heading_deg + float(packet.get("omega", 0.0)) * 5.0) % 360
        return protocol.ack(
            packet,
            mode="sim",
            battery_mv=self.battery_mv,
            heading_deg=round(self.heading_deg, 2),
            uptime_ms=protocol.now_ms() - self.started_ms,
            last_cmd=self.last_cmd,
            estop=self.estop,
        )


class SerialV5Brain:
    def __init__(self, port: str, baud: int, timeout: float) -> None:
        import serial

        self.serial = serial.Serial(port=port, baudrate=baud, timeout=timeout, write_timeout=timeout)

    def handle(self, packet: dict[str, Any]) -> dict[str, Any]:
        self.serial.write(protocol.encode(packet))
        self.serial.flush()
        line = self.serial.readline()
        if not line:
            raise TimeoutError("no response from V5 Brain serial bridge")
        return protocol.decode(line)


class Bridge:
    def __init__(self, brain: FakeV5Brain | SerialV5Brain, state_dir: Path) -> None:
        self.brain = brain
        self.state_dir = state_dir
        self.lock = threading.Lock()
        self.last_packet: dict[str, Any] | None = None
        self.last_response: dict[str, Any] | None = None
        self.last_error: str | None = None
        ensure_dir(state_dir)
        self.write_state()

    def handle_line(self, line: bytes) -> dict[str, Any]:
        try:
            packet = protocol.validate_outbound(protocol.decode(line))
            with self.lock:
                response = self.brain.handle(packet)
                self.last_packet = packet
                self.last_response = response
                self.last_error = None
                self.write_state()
            return response
        except Exception as exc:
            with self.lock:
                self.last_error = str(exc)
                self.write_state()
            return {
                "v": protocol.PROTOCOL_VERSION,
                "type": "error",
                "state": "error",
                "error": str(exc),
                "recv_ms": protocol.now_ms(),
            }

    def write_state(self) -> None:
        atomic_write_json(
            self.state_dir / "bridge.json",
            {
                "updated_ms": protocol.now_ms(),
                "last_packet": self.last_packet,
                "last_response": self.last_response,
                "last_error": self.last_error,
            },
        )


class Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        bridge: Bridge = self.server.bridge  # type: ignore[attr-defined]
        for line in self.rfile:
            response = bridge.handle_line(line)
            self.wfile.write(protocol.encode(response))
            self.wfile.flush()


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vexy V5 command bridge")
    parser.add_argument("--host", default=os.getenv("VEXY_BRIDGE_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("VEXY_BRIDGE_PORT", "8765")))
    parser.add_argument("--mode", choices=["sim", "serial"], default=os.getenv("VEXY_BRIDGE_MODE", "sim"))
    parser.add_argument("--serial-port", default=os.getenv("VEXY_SERIAL_PORT", ""))
    parser.add_argument("--baud", type=int, default=int(os.getenv("VEXY_SERIAL_BAUD", "115200")))
    parser.add_argument("--state-dir", default=os.getenv("VEXY_STATE_DIR", "/tmp/vexy-system2"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "serial":
        if not args.serial_port:
            raise SystemExit("--serial-port or VEXY_SERIAL_PORT is required in serial mode")
        brain: FakeV5Brain | SerialV5Brain = SerialV5Brain(args.serial_port, args.baud, timeout=0.4)
    else:
        brain = FakeV5Brain()

    bridge = Bridge(brain=brain, state_dir=Path(args.state_dir))
    with ThreadedServer((args.host, args.port), Handler) as server:
        server.bridge = bridge  # type: ignore[attr-defined]
        print(f"vexy bridge listening on {args.host}:{args.port} mode={args.mode}", flush=True)
        while True:
            server.handle_request()
            time.sleep(0.001)


if __name__ == "__main__":
    main()

