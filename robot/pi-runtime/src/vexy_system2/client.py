from __future__ import annotations

import socket
from typing import Any

from . import protocol


def send_packet(packet: dict[str, Any], host: str = "127.0.0.1", port: int = 8765, timeout: float = 1.0) -> dict[str, Any]:
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(protocol.encode(packet))
        reader = sock.makefile("rb")
        return protocol.decode(reader.readline())

