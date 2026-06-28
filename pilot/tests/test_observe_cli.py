from __future__ import annotations

import importlib
import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from contracts import PilotObservation

from pilot import observe


def _payloads(
    *,
    bridge: bool = True,
    malformed_agent_scene: bool = False,
) -> dict[str, str]:
    agent_scene = (
        "{not-json"
        if malformed_agent_scene
        else json.dumps(
            {
                "robot": {
                    "pose": {"x_m": 1.0, "y_m": 2.0, "heading_rad": 0.5},
                    "pose_confidence": 0.8,
                    "bridge_status": "ok",
                },
                "localization": {"confidence": 0.8, "age_ms": 25},
                "objects": [
                    {
                        "id": "cube-red-1",
                        "class": "red_cube",
                        "confidence": 0.92,
                        "status": "confirmed",
                    }
                ],
            }
        )
    )
    payloads = {
        "/vision/agent_scene": agent_scene,
        "/vision/object_tracks": json.dumps(
            {
                "tracks": [
                    {
                        "id": "cube-red-1",
                        "class": "red_cube",
                        "confidence": 0.92,
                        "status": "confirmed",
                    }
                ]
            }
        ),
        "/vex/telemetry": json.dumps(
            {
                "battery_pct": 79,
                "last_heartbeat_age_ms": 12,
                "arm_deg": 18,
            }
        ),
        "/vision/scene_map": json.dumps({"tags": []}),
        "/task_plan/current": json.dumps({"phase": "survey"}),
        "/operator/status": json.dumps({"claw_state": "open"}),
    }
    if bridge:
        payloads["/vex/bridge_status"] = json.dumps({"state": "ok", "observed_ms": 100})
    return payloads


@dataclass
class FakeClock:
    now_s: float = 0.0

    def __call__(self) -> float:
        return self.now_s

    def advance(self, seconds: float) -> None:
        self.now_s += seconds


@dataclass
class FakeRosFactory:
    message_batches: list[dict[str, str]]
    clock: FakeClock = field(default_factory=FakeClock)
    interrupt_after_spins: int | None = None

    def __post_init__(self) -> None:
        self.rclpy = FakeRclpy(self)

    def runtime(self) -> observe.RosRuntime:
        return observe.RosRuntime(rclpy=self.rclpy, string_msg_type=FakeString)


class FakeString:
    def __init__(self, data: str) -> None:
        self.data = data


class FakeRclpy:
    def __init__(self, factory: FakeRosFactory) -> None:
        self.factory = factory
        self.nodes: list[FakeNode] = []
        self.init_called = False
        self.shutdown_called = False
        self.spin_count = 0

    def init(self, *, args: object = None) -> None:
        assert args is None
        self.init_called = True

    def create_node(self, name: str) -> FakeNode:
        node = FakeNode(name)
        self.nodes.append(node)
        return node

    def spin_once(self, node: FakeNode, *, timeout_sec: float) -> None:
        self.spin_count += 1
        if (
            self.factory.interrupt_after_spins is not None
            and self.spin_count > self.factory.interrupt_after_spins
        ):
            raise KeyboardInterrupt

        if self.factory.message_batches:
            for topic, payload in self.factory.message_batches.pop(0).items():
                node.emit(topic, payload)
        self.factory.clock.advance(max(timeout_sec, 0.05))

    def shutdown(self) -> None:
        self.shutdown_called = True


class FakeNode:
    def __init__(self, name: str) -> None:
        self.name = name
        self.subscriptions: dict[str, Any] = {}
        self.publishers: list[str] = []
        self.destroyed = False

    def create_subscription(
        self,
        msg_type: type[FakeString],
        topic: str,
        callback: Any,
        qos_profile: int,
    ) -> object:
        assert msg_type is FakeString
        assert qos_profile == 10
        self.subscriptions[topic] = callback
        return object()

    def create_publisher(self, msg_type: object, topic: str, qos_profile: int) -> object:
        self.publishers.append(topic)
        return object()

    def emit(self, topic: str, data: str) -> None:
        self.subscriptions[topic](FakeString(data))

    def destroy_node(self) -> None:
        self.destroyed = True


class TrackingOutput:
    def __init__(self) -> None:
        self.text = ""
        self.closed = False
        self.flush_count = 0

    def write(self, value: str) -> int:
        assert not self.closed
        self.text += value
        return len(value)

    def flush(self) -> None:
        assert not self.closed
        self.flush_count += 1

    def close(self) -> None:
        self.closed = True


def _jsonl(text: str) -> list[Mapping[str, Any]]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def test_parser_requires_objective() -> None:
    parser = observe.build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["observe", "--duration-s", "1"])

    assert exc.value.code == 2


def test_observe_imports_without_ros_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            if fullname == "rclpy" or fullname.startswith(("rclpy.", "std_msgs.")):
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.observe", None)

    module = importlib.import_module("pilot.observe")

    assert module.READ_ONLY_TOPIC_FIELDS["/vision/agent_scene"] == "agent_scene"
    assert "rclpy" not in sys.modules


def test_missing_ros_dependency_exits_with_clear_error(capsys: pytest.CaptureFixture[str]) -> None:
    def missing_ros() -> observe.RosRuntime:
        raise observe.ObserveCliError("ROS dependencies are required", observe.EXIT_ROS_DEPENDENCY)

    code = observe.main(
        ["observe", "--objective", "collect", "--duration-s", "1"], ros_loader=missing_ros
    )

    assert code == observe.EXIT_ROS_DEPENDENCY
    assert "ROS dependencies are required" in capsys.readouterr().err


def test_stdout_jsonl_default_is_contract_valid(capsys: pytest.CaptureFixture[str]) -> None:
    fake = FakeRosFactory([_payloads()])

    code = observe.main(
        ["observe", "--objective", "collect the red cube", "--duration-s", "1", "--count", "1"],
        ros_loader=fake.runtime,
        clock=fake.clock,
    )

    assert code == observe.EXIT_OK
    rows = _jsonl(capsys.readouterr().out)
    assert len(rows) == 1
    snapshot = PilotObservation.model_validate(rows[0])
    assert snapshot.objective == "collect the red cube"
    assert snapshot.visible_objects[0].object_id == "cube-red-1"


def test_out_file_receives_jsonl_instead_of_stdout(
    tmp_path: pytest.TempPathFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out_path = tmp_path / "observe.jsonl"
    fake = FakeRosFactory([_payloads()])

    code = observe.main(
        [
            "observe",
            "--objective",
            "write proof",
            "--duration-s",
            "1",
            "--count",
            "1",
            "--out",
            str(out_path),
        ],
        ros_loader=fake.runtime,
        clock=fake.clock,
    )

    assert code == observe.EXIT_OK
    assert capsys.readouterr().out == ""
    rows = _jsonl(out_path.read_text(encoding="utf-8"))
    assert PilotObservation.model_validate(rows[0]).objective == "write proof"


def test_count_bounds_snapshot_emission(capsys: pytest.CaptureFixture[str]) -> None:
    fake = FakeRosFactory([_payloads()])

    code = observe.main(
        [
            "observe",
            "--objective",
            "bounded",
            "--duration-s",
            "5",
            "--count",
            "2",
            "--snapshot-interval-s",
            "0.05",
        ],
        ros_loader=fake.runtime,
        clock=fake.clock,
    )

    assert code == observe.EXIT_OK
    assert len(_jsonl(capsys.readouterr().out)) == 2


def test_duration_only_bound_closes_output_after_complete_jsonl(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRosFactory([_payloads()])
    output = TrackingOutput()

    def open_tracking(path: Path | None) -> tuple[TrackingOutput, bool]:
        assert path == Path("duration-only.jsonl")
        return output, True

    monkeypatch.setattr(observe, "_open_output", open_tracking)

    code = observe.main(
        [
            "observe",
            "--objective",
            "duration only",
            "--duration-s",
            "0.12",
            "--snapshot-interval-s",
            "1",
            "--out",
            "duration-only.jsonl",
        ],
        ros_loader=fake.runtime,
        clock=fake.clock,
    )

    captured = capsys.readouterr()
    assert code == observe.EXIT_OK
    assert captured.out == ""
    assert captured.err == ""
    assert output.closed
    assert output.flush_count == 1
    assert output.text.endswith("\n")
    assert output.text.count("\n") == 1
    rows = _jsonl(output.text)
    assert len(rows) == 1
    assert PilotObservation.model_validate(rows[0]).objective == "duration only"


def test_strict_readiness_fails_when_required_topic_missing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeRosFactory([_payloads(bridge=False)])

    code = observe.main(
        [
            "observe",
            "--objective",
            "strict",
            "--duration-s",
            "1",
            "--readiness-timeout-s",
            "0.1",
        ],
        ros_loader=fake.runtime,
        clock=fake.clock,
    )

    assert code == observe.EXIT_READINESS
    assert "/vex/bridge_status" in capsys.readouterr().err


def test_strict_readiness_fails_when_required_payload_malformed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeRosFactory([_payloads(malformed_agent_scene=True)])

    code = observe.main(
        ["observe", "--objective", "strict", "--duration-s", "1"],
        ros_loader=fake.runtime,
        clock=fake.clock,
    )

    assert code == observe.EXIT_READINESS
    assert "required topic /vision/agent_scene is malformed" in capsys.readouterr().err


def test_subscribes_only_to_read_only_topics_and_creates_no_publishers() -> None:
    fake = FakeRosFactory([_payloads()])

    code = observe.main(
        ["observe", "--objective", "read only", "--duration-s", "1", "--count", "1"],
        ros_loader=fake.runtime,
        clock=fake.clock,
    )

    assert code == observe.EXIT_OK
    node = fake.rclpy.nodes[0]
    assert set(node.subscriptions) == set(observe.READ_ONLY_TOPIC_FIELDS)
    assert node.publishers == []
    assert "/operator/command" not in node.subscriptions
    assert "/task_plan/request" not in node.subscriptions
    assert "/vex/cmd" not in node.subscriptions


def test_keyboard_interrupt_returns_cleanly_after_complete_lines(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeRosFactory([_payloads()], interrupt_after_spins=1)

    code = observe.main(
        [
            "observe",
            "--objective",
            "interruptible",
            "--duration-s",
            "5",
            "--snapshot-interval-s",
            "0.05",
        ],
        ros_loader=fake.runtime,
        clock=fake.clock,
    )

    assert code == observe.EXIT_OK
    rows = _jsonl(capsys.readouterr().out)
    assert len(rows) == 1
    assert PilotObservation.model_validate(rows[0]).objective == "interruptible"
