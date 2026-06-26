from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from typing import TextIO


DEFAULT_TOPIC = "/operator/annotation"
DEFAULT_SOURCE = "agent_hotkey"

LABEL_KEYS: dict[str, str] = {
    "1": "normal_drive",
    "2": "turning",
    "3": "contact",
    "4": "stuck_or_slipping",
    "5": "ball_controlled",
    "6": "scored_or_delivered",
    "0": "uncertain",
    " ": "clear_label",
    "space": "clear_label",
    "clear": "clear_label",
}

LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_:-]{0,63}$")


@dataclass(frozen=True)
class AnnotationCommand:
    label: str
    note: str = ""


def now_ms() -> int:
    return time.time_ns() // 1_000_000


def label_help() -> str:
    return "\n".join(
        [
            "1 normal_drive",
            "2 turning",
            "3 contact",
            "4 stuck_or_slipping",
            "5 ball_controlled",
            "6 scored_or_delivered",
            "0 uncertain",
            "space clear_label",
        ]
    )


def parse_annotation_command(raw: str) -> AnnotationCommand | None:
    text = raw.strip()
    if not text:
        return None

    if text in LABEL_KEYS:
        return AnnotationCommand(label=LABEL_KEYS[text])

    head, _, note = text.partition(" ")
    label = LABEL_KEYS.get(head, head)
    if not LABEL_PATTERN.match(label):
        raise ValueError(
            "annotation label must use lowercase letters, digits, '_', ':', or '-'"
        )
    return AnnotationCommand(label=label, note=note.strip())


def build_annotation(
    command: AnnotationCommand,
    *,
    source: str = DEFAULT_SOURCE,
    wall_ms: int | None = None,
) -> dict[str, object]:
    return {
        "type": "annotation",
        "label": command.label,
        "wall_ms": now_ms() if wall_ms is None else wall_ms,
        "source": source,
        "note": command.note,
    }


def annotation_json(
    raw: str,
    *,
    source: str = DEFAULT_SOURCE,
    wall_ms: int | None = None,
) -> str | None:
    command = parse_annotation_command(raw)
    if command is None:
        return None
    return json.dumps(
        build_annotation(command, source=source, wall_ms=wall_ms),
        sort_keys=True,
        separators=(",", ":"),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish timestamped operator state labels for driver telemetry runs."
    )
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument(
        "--print-labels",
        action="store_true",
        help="print the default key-to-label map and exit",
    )
    return parser


def run_console_publisher(
    *,
    topic: str = DEFAULT_TOPIC,
    source: str = DEFAULT_SOURCE,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
) -> int:
    try:
        import rclpy
        from rclpy.node import Node
        from std_msgs.msg import String
    except ImportError as exc:
        print(f"ROS 2 Python packages are required: {exc}", file=sys.stderr)
        return 2

    rclpy.init()
    node = Node("operator_annotation")
    publisher = node.create_publisher(String, topic, 10)
    print(label_help(), file=stdout)
    print("Type a key or custom label, then Enter. Ctrl-D exits.", file=stdout)

    try:
        for raw in stdin:
            try:
                payload = annotation_json(raw, source=source)
            except ValueError as exc:
                print(f"invalid annotation: {exc}", file=stdout)
                continue
            if payload is None:
                continue
            publisher.publish(String(data=payload))
            rclpy.spin_once(node, timeout_sec=0)
            print(payload, file=stdout)
    finally:
        node.destroy_node()
        rclpy.shutdown()

    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.print_labels:
        print(label_help())
        return 0
    return run_console_publisher(topic=args.topic, source=args.source)


if __name__ == "__main__":
    raise SystemExit(main())
