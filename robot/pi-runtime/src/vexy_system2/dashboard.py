from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from . import protocol
from .client import send_packet
from .state import read_json


class Dashboard(BaseHTTPRequestHandler):
    state_dir: Path
    bridge_host: str
    bridge_port: int

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.startswith("/latest.jpg"):
            img = self.state_dir / "latest.jpg"
            if img.exists():
                self._send(200, img.read_bytes(), "image/jpeg")
            else:
                self._send(404, b"missing", "text/plain")
            return
        if self.path.startswith("/state"):
            payload = {
                "bridge": read_json(self.state_dir / "bridge.json"),
                "camera": read_json(self.state_dir / "camera.json"),
            }
            self._send(200, json.dumps(payload, indent=2).encode(), "application/json")
            return
        self._send(200, self.render().encode(), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode()
        values = parse_qs(body)
        seq = protocol.now_ms() % 1_000_000
        action = values.get("action", ["stop"])[0]
        if action == "drive":
            packet = protocol.command(
                seq,
                "drive",
                vx=float(values.get("vx", ["0"])[0]),
                vy=0.0,
                omega=float(values.get("omega", ["0"])[0]),
                ttl_ms=200,
            )
        else:
            packet = protocol.stop(seq, reason="operator_estop")
        try:
            response = send_packet(packet, self.bridge_host, self.bridge_port)
        except Exception as exc:
            response = {"state": "error", "error": str(exc)}
        self._send(200, json.dumps(response, indent=2).encode(), "application/json")

    def render(self) -> str:
        bridge = read_json(self.state_dir / "bridge.json")
        camera = read_json(self.state_dir / "camera.json")
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="2">
  <title>Vexy System 2</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 24px; background: #101418; color: #eef5f7; }}
    main {{ display: grid; grid-template-columns: minmax(320px, 640px) minmax(320px, 1fr); gap: 24px; align-items: start; }}
    img {{ max-width: 100%; border: 1px solid #2d3942; }}
    pre {{ white-space: pre-wrap; background: #172028; padding: 12px; border: 1px solid #2d3942; overflow: auto; }}
    button {{ font-size: 16px; padding: 10px 14px; margin-right: 8px; }}
    input {{ width: 90px; }}
  </style>
</head>
<body>
  <h1>Vexy System 2</h1>
  <main>
    <section>
      <img src="/latest.jpg?cache={protocol.now_ms()}" alt="latest camera frame">
      <form method="post">
        <input type="hidden" name="action" value="stop">
        <button type="submit">STOP</button>
      </form>
      <form method="post">
        <input type="hidden" name="action" value="drive">
        vx <input name="vx" value="0.10">
        omega <input name="omega" value="0.0">
        <button type="submit">Send Drive</button>
      </form>
    </section>
    <section>
      <h2>Bridge</h2>
      <pre>{json.dumps(bridge, indent=2)}</pre>
      <h2>Camera</h2>
      <pre>{json.dumps(camera, indent=2)}</pre>
    </section>
  </main>
</body>
</html>"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vexy local dashboard")
    parser.add_argument("--host", default=os.getenv("VEXY_DASHBOARD_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("VEXY_DASHBOARD_PORT", "8080")))
    parser.add_argument("--state-dir", default=os.getenv("VEXY_STATE_DIR", "/tmp/vexy-system2"))
    parser.add_argument("--bridge-host", default=os.getenv("VEXY_BRIDGE_HOST", "127.0.0.1"))
    parser.add_argument("--bridge-port", type=int, default=int(os.getenv("VEXY_BRIDGE_PORT", "8765")))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    Dashboard.state_dir = Path(args.state_dir)
    Dashboard.bridge_host = args.bridge_host
    Dashboard.bridge_port = args.bridge_port
    server = ThreadingHTTPServer((args.host, args.port), Dashboard)
    print(f"dashboard listening on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

