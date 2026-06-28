"""Observe-only ROS JSONL CLI for live pilot evidence."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from pilot.live_observation import build_live_observation

READ_ONLY_TOPIC_FIELDS: dict[str, str] = {
    "/vision/agent_scene": "agent_scene",
    "/vision/scene_map": "scene_map",
    "/vision/object_tracks": "object_tracks",
    "/vex/telemetry": "telemetry",
    "/vex/bridge_status": "bridge_status",
    "/task_plan/current": "task_plan",
    "/operator/status": "operator_status",
}
REQUIRED_TOPICS: tuple[str, ...] = (
    "/vision/agent_scene",
    "/vision/object_tracks",
    "/vex/telemetry",
    "/vex/bridge_status",
)

DEFAULT_DURATION_S = 30.0
DEFAULT_READINESS_TIMEOUT_S = 5.0
DEFAULT_SNAPSHOT_INTERVAL_S = 1.0

EXIT_OK = 0
EXIT_ROS_DEPENDENCY = 10
EXIT_READINESS = 11
EXIT_RUNTIME = 12
EXIT_OUTPUT = 13


@dataclass(frozen=True, slots=True)
class ObserveConfig:
    objective: str
    duration_s: float = DEFAULT_DURATION_S
    count: int | None = None
    out: Path | None = None
    readiness_timeout_s: float = DEFAULT_READINESS_TIMEOUT_S
    snapshot_interval_s: float = DEFAULT_SNAPSHOT_INTERVAL_S


@dataclass(frozen=True, slots=True)
class RosRuntime:
    rclpy: Any
    string_msg_type: Any


class ObserveCliError(Exception):
    """Expected observe CLI failure with a stable process exit code."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class TopicCache:
    """Cache latest decoded read-only topic payloads by mapper keyword."""

    def __init__(self) -> None:
        self._payloads: dict[str, Mapping[str, Any]] = {}
        self._malformed_required: dict[str, str] = {}

    def update(self, topic: str, raw_data: str) -> None:
        try:
            decoded = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            self._record_malformed(topic, f"invalid JSON at byte {exc.pos}: {exc.msg}")
            return

        if not isinstance(decoded, Mapping):
            self._record_malformed(topic, "payload must be a JSON object")
            return

        field = READ_ONLY_TOPIC_FIELDS[topic]
        self._payloads[field] = decoded

    @property
    def ready(self) -> bool:
        return not self.malformed_required and not self.missing_required_topics()

    @property
    def malformed_required(self) -> Mapping[str, str]:
        return self._malformed_required

    def missing_required_topics(self) -> list[str]:
        return [
            topic
            for topic in REQUIRED_TOPICS
            if READ_ONLY_TOPIC_FIELDS[topic] not in self._payloads
        ]

    def mapper_kwargs(self) -> dict[str, Mapping[str, Any] | None]:
        return {field: self._payloads.get(field) for field in READ_ONLY_TOPIC_FIELDS.values()}

    def _record_malformed(self, topic: str, reason: str) -> None:
        if topic in REQUIRED_TOPICS:
            self._malformed_required[topic] = reason


class ObserveNode:
    """Small adapter around rclpy so tests can replace the runtime boundary."""

    def __init__(self, runtime: RosRuntime, cache: TopicCache) -> None:
        self.node = runtime.rclpy.create_node("pilot_observe")
        for topic in READ_ONLY_TOPIC_FIELDS:
            self.node.create_subscription(
                runtime.string_msg_type,
                topic,
                self._callback(topic, cache),
                10,
            )

    def destroy(self) -> None:
        destroy_node = getattr(self.node, "destroy_node", None)
        if destroy_node is not None:
            destroy_node()

    @staticmethod
    def _callback(topic: str, cache: TopicCache) -> Callable[[Any], None]:
        def on_message(message: Any) -> None:
            cache.update(topic, str(getattr(message, "data", "")))

        return on_message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pilot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    observe = subparsers.add_parser(
        "observe",
        help="emit observe-only PilotObservation JSONL from read-only ROS evidence topics",
    )
    observe.add_argument("--objective", required=True, help="live task objective for snapshots")
    observe.add_argument(
        "--duration-s",
        type=_positive_float,
        default=DEFAULT_DURATION_S,
        help=f"wall-clock observe bound in seconds (default: {DEFAULT_DURATION_S:g})",
    )
    observe.add_argument(
        "--count",
        type=_positive_int,
        default=None,
        help="optional maximum number of snapshots to emit",
    )
    observe.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write JSONL to this file instead of stdout",
    )
    observe.add_argument(
        "--readiness-timeout-s",
        type=_positive_float,
        default=DEFAULT_READINESS_TIMEOUT_S,
        help=(
            "seconds to wait for /vision/agent_scene, /vision/object_tracks, "
            "/vex/telemetry, and /vex/bridge_status"
        ),
    )
    observe.add_argument(
        "--snapshot-interval-s",
        type=_positive_float,
        default=DEFAULT_SNAPSHOT_INTERVAL_S,
        help=f"minimum seconds between snapshots (default: {DEFAULT_SNAPSHOT_INTERVAL_S:g})",
    )
    return parser


def main(
    argv: list[str] | None = None,
    *,
    ros_loader: Callable[[], RosRuntime] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    if ros_loader is None:
        ros_loader = load_ros_runtime

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "observe":
            return run_observe(
                ObserveConfig(
                    objective=args.objective,
                    duration_s=args.duration_s,
                    count=args.count,
                    out=args.out,
                    readiness_timeout_s=args.readiness_timeout_s,
                    snapshot_interval_s=args.snapshot_interval_s,
                ),
                ros_loader=ros_loader,
                clock=clock,
            )
    except ObserveCliError as exc:
        print(f"pilot observe: {exc}", file=sys.stderr)
        return exc.exit_code

    parser.error("unknown command")
    return EXIT_RUNTIME


def run_observe(
    config: ObserveConfig,
    *,
    ros_loader: Callable[[], RosRuntime] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    if ros_loader is None:
        ros_loader = load_ros_runtime

    runtime = ros_loader()
    cache = TopicCache()
    output: TextIO | None = None
    should_close = False
    initialized = False
    observe_node: ObserveNode | None = None
    try:
        output, should_close = _open_output(config.out)
        runtime.rclpy.init(args=None)
        initialized = True
        observe_node = ObserveNode(runtime, cache)
        _observe_loop(config, runtime, observe_node, cache, output, clock)
        return EXIT_OK
    except KeyboardInterrupt:
        return EXIT_OK
    except OSError as exc:
        raise ObserveCliError(f"could not write observations: {exc}", EXIT_OUTPUT) from exc
    except ValueError as exc:
        raise ObserveCliError(f"could not build observation: {exc}", EXIT_RUNTIME) from exc
    finally:
        if observe_node is not None:
            observe_node.destroy()
        if initialized:
            runtime.rclpy.shutdown()
        if should_close and output is not None:
            output.close()


def load_ros_runtime() -> RosRuntime:
    try:
        import rclpy
        from std_msgs.msg import String
    except ImportError as exc:
        raise ObserveCliError(
            "ROS dependencies are required for live observe; source a ROS 2 environment "
            "with rclpy and std_msgs available",
            EXIT_ROS_DEPENDENCY,
        ) from exc

    return RosRuntime(rclpy=rclpy, string_msg_type=String)


def _observe_loop(
    config: ObserveConfig,
    runtime: RosRuntime,
    observe_node: ObserveNode,
    cache: TopicCache,
    output: TextIO,
    clock: Callable[[], float],
) -> None:
    start_s = clock()
    duration_deadline_s = start_s + config.duration_s
    readiness_deadline_s = start_s + min(config.readiness_timeout_s, config.duration_s)
    next_snapshot_s = start_s
    snapshot_count = 0

    while True:
        now_s = clock()
        if not cache.ready and now_s >= readiness_deadline_s:
            _raise_readiness_error(cache)
        if now_s >= duration_deadline_s:
            if not cache.ready:
                _raise_readiness_error(cache)
            return

        timeout_s = _spin_timeout(
            now_s=now_s,
            duration_deadline_s=duration_deadline_s,
            readiness_deadline_s=readiness_deadline_s,
            next_snapshot_s=next_snapshot_s,
            ready=cache.ready,
        )
        runtime.rclpy.spin_once(observe_node.node, timeout_sec=timeout_s)
        now_s = clock()

        if cache.malformed_required:
            _raise_readiness_error(cache)
        if not cache.ready:
            continue
        if now_s < next_snapshot_s:
            continue

        _write_snapshot(config, cache, output, observed_ms=_observed_ms(now_s))
        snapshot_count += 1
        if config.count is not None and snapshot_count >= config.count:
            return
        next_snapshot_s = now_s + config.snapshot_interval_s


def _write_snapshot(
    config: ObserveConfig,
    cache: TopicCache,
    output: TextIO,
    *,
    observed_ms: int,
) -> None:
    snapshot = build_live_observation(
        objective=config.objective,
        observed_ms=observed_ms,
        **cache.mapper_kwargs(),
    )
    output.write(snapshot.model_dump_json())
    output.write("\n")
    output.flush()


def _spin_timeout(
    *,
    now_s: float,
    duration_deadline_s: float,
    readiness_deadline_s: float,
    next_snapshot_s: float,
    ready: bool,
) -> float:
    deadlines = [duration_deadline_s]
    if ready:
        deadlines.append(next_snapshot_s)
    else:
        deadlines.append(readiness_deadline_s)
    return max(0.0, min(0.1, *(deadline - now_s for deadline in deadlines)))


def _raise_readiness_error(cache: TopicCache) -> None:
    if cache.malformed_required:
        topic, reason = next(iter(cache.malformed_required.items()))
        raise ObserveCliError(f"required topic {topic} is malformed: {reason}", EXIT_READINESS)

    missing = cache.missing_required_topics()
    raise ObserveCliError(
        "strict readiness not reached; missing required topic(s): " + ", ".join(missing),
        EXIT_READINESS,
    )


def _open_output(path: Path | None) -> tuple[TextIO, bool]:
    if path is None:
        return sys.stdout, False
    return path.open("w", encoding="utf-8"), True


def _observed_ms(monotonic_s: float) -> int:
    return max(0, int(round(monotonic_s * 1000)))


def _positive_float(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return value


def _positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
