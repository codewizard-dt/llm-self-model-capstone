from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _topic_to_filename(topic: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", topic).strip("_") + ".jsonl"


def extract_bag_to_jsonl(bag_dir: Path, out_dir: Path | None = None) -> dict[str, int]:
    """Read an MCAP bag and write one JSONL file per std_msgs/String topic.

    Each line in the output file is the deserialized JSON payload from the
    message's ``data`` field, with ``_bag_timestamp_ns`` injected.

    Returns a dict mapping output filename → message count.
    """
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from std_msgs.msg import String

    if out_dir is None:
        out_dir = bag_dir.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    storage_options = rosbag2_py.StorageOptions(uri=str(bag_dir), storage_id="mcap")
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )
    reader = rosbag2_py.SequentialReader()
    reader.open(storage_options, converter_options)

    topic_types = {
        info.topic_metadata.name: info.topic_metadata.type
        for info in reader.get_all_topics_and_types()
    }

    handles: dict[str, object] = {}
    counts: dict[str, int] = {}

    try:
        while reader.has_next():
            topic, data, timestamp_ns = reader.read_next()
            if topic_types.get(topic) != "std_msgs/msg/String":
                continue
            msg = deserialize_message(data, String)
            try:
                payload = json.loads(msg.data)
            except json.JSONDecodeError:
                payload = {"_raw": msg.data}
            payload["_bag_timestamp_ns"] = timestamp_ns

            fname = _topic_to_filename(topic)
            if fname not in handles:
                handles[fname] = (out_dir / fname).open("w")
                counts[fname] = 0
            handles[fname].write(json.dumps(payload, separators=(",", ":")) + "\n")
            counts[fname] += 1
    finally:
        for fh in handles.values():
            fh.close()

    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract std_msgs/String JSON payloads from an MCAP bag to JSONL files."
    )
    parser.add_argument("bag_dir", type=Path, help="Path to the MCAP bag directory")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory for JSONL files (default: parent of bag_dir)",
    )
    args = parser.parse_args(argv)

    counts = extract_bag_to_jsonl(args.bag_dir, args.out_dir)
    if not counts:
        print("No std_msgs/String topics found in bag.", file=sys.stderr)
        return 1
    for fname, count in sorted(counts.items()):
        print(f"  {fname}: {count} messages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
