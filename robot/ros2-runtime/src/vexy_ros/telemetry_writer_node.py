from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

TELEMETRY_TOPICS = (
    "/operator/run_start",
    "/operator/events",
    "/operator/results",
    "/operator/status",
    "/vex/telemetry",
)


def _topic_to_filename(topic: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", topic).strip("_") + ".jsonl"


class TelemetryWriterNode(Node):
    def __init__(self, out_dir: Path) -> None:
        super().__init__("vexy_telemetry_writer")
        self._out_dir = out_dir
        self._out_dir.mkdir(parents=True, exist_ok=True)
        self._files: dict[str, object] = {}
        for topic in TELEMETRY_TOPICS:
            self.create_subscription(String, topic, self._make_callback(topic), 10)
        self.get_logger().info(f"Writing telemetry JSON to {out_dir}")

    def _make_callback(self, topic: str):
        def _cb(msg: String) -> None:
            try:
                payload = json.loads(msg.data)
            except json.JSONDecodeError:
                payload = {"_raw": msg.data}
            payload["_wall_s"] = time.time()
            fname = _topic_to_filename(topic)
            if fname not in self._files:
                self._files[fname] = (self._out_dir / fname).open("a")
            self._files[fname].write(json.dumps(payload, separators=(",", ":")) + "\n")
            self._files[fname].flush()
        return _cb

    def close_files(self) -> None:
        for fh in self._files.values():
            fh.close()
        self._files.clear()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Subscribe to operator topics and write each message as a JSON line."
    )
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="Directory to write JSONL files into")
    args, ros_args = parser.parse_known_args(argv)

    rclpy.init(args=ros_args)
    node = TelemetryWriterNode(args.out_dir)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close_files()
        node.destroy_node()
        rclpy.shutdown()
