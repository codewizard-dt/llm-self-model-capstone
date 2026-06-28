from __future__ import annotations

import importlib
import json
import sys
from dataclasses import dataclass, field
from typing import Any

import pytest
from contracts import (
    BridgeHealth,
    ClawCloseSkillCommand,
    ClawOpenSkillCommand,
    CommandStatus,
    LocalizationState,
    ManipulatorState,
    PilotObservation,
    PilotTaskPhase,
    SurveySceneSkillCommand,
    VerifyDropSkillCommand,
    VerifyGraspSkillCommand,
)

from pilot import ros_execution


def _observation_payloads() -> dict[str, str]:
    return {
        "/vision/agent_scene": json.dumps(
            {
                "robot": {"bridge_status": "ok"},
                "objects": [{"id": "ball-1", "class": "yellow_ball", "confidence": 0.9}],
            }
        ),
        "/vision/object_tracks": json.dumps(
            {"tracks": [{"id": "ball-1", "class": "yellow_ball", "confidence": 0.9}]}
        ),
        "/vex/telemetry": json.dumps({"last_heartbeat_age_ms": 10, "battery_pct": 80}),
        "/vex/bridge_status": json.dumps({"state": "ok", "observed_ms": 990}),
        "/operator/status": json.dumps({"claw_state": "open"}),
        "/vision/scene_map": json.dumps({"tags": []}),
    }


def _healthy_observation() -> PilotObservation:
    return PilotObservation(
        observed_ms=1000,
        task_phase=PilotTaskPhase.IDLE,
        objective="pm4 proof",
        localization=LocalizationState(pose=None, confidence=0.0, age_ms=0),
        manipulator=ManipulatorState(claw_state="open", held_object_id=None),
        bridge=BridgeHealth(state="ok", last_heartbeat_age_ms=10),
    )


@dataclass
class FakeClock:
    now_s: float = 1.0

    def __call__(self) -> float:
        return self.now_s

    def advance(self, seconds: float) -> None:
        self.now_s += max(seconds, 0.01)


@dataclass
class FakeRosFactory:
    message_batches: list[dict[str, str]]
    clock: FakeClock = field(default_factory=FakeClock)

    def __post_init__(self) -> None:
        self.rclpy = FakeRclpy(self)

    def runtime(self) -> ros_execution.RosRuntime:
        return ros_execution.RosRuntime(rclpy=self.rclpy, string_msg_type=FakeString)


class FakeString:
    def __init__(self, data: str) -> None:
        self.data = data


class FakeRclpy:
    def __init__(self, factory: FakeRosFactory) -> None:
        self.factory = factory
        self.nodes: list[FakeNode] = []
        self.init_called = False
        self.shutdown_called = False

    def init(self, *, args: object = None) -> None:
        assert args is None
        self.init_called = True

    def create_node(self, name: str) -> "FakeNode":
        node = FakeNode(name)
        self.nodes.append(node)
        return node

    def spin_once(self, node: "FakeNode", *, timeout_sec: float) -> None:
        if self.factory.message_batches:
            for topic, payload in self.factory.message_batches.pop(0).items():
                node.emit(topic, payload)
        self.factory.clock.advance(timeout_sec)

    def shutdown(self) -> None:
        self.shutdown_called = True


class FakePublisher:
    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.messages: list[str] = []

    def publish(self, message: FakeString) -> None:
        self.messages.append(message.data)


class FakeNode:
    def __init__(self, name: str) -> None:
        self.name = name
        self.subscriptions: dict[str, Any] = {}
        self.publishers: dict[str, FakePublisher] = {}
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

    def create_publisher(
        self,
        msg_type: type[FakeString],
        topic: str,
        qos_profile: int,
    ) -> FakePublisher:
        assert msg_type is FakeString
        assert qos_profile == 10
        publisher = FakePublisher(topic)
        self.publishers[topic] = publisher
        return publisher

    def emit(self, topic: str, data: str) -> None:
        if topic in self.subscriptions:
            self.subscriptions[topic](FakeString(data))

    def destroy_node(self) -> None:
        self.destroyed = True


def _publisher_payloads(node: FakeNode, topic: str) -> list[dict[str, Any]]:
    return [json.loads(raw) for raw in node.publishers[topic].messages]


def test_ros_execution_imports_without_ros_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            if fullname == "rclpy" or fullname.startswith(("rclpy.", "std_msgs.")):
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.ros_execution", None)

    module = importlib.import_module("pilot.ros_execution")

    assert module.SURVEY_GOAL_TOPIC == "/survey/goal"
    assert "rclpy" not in sys.modules


def test_survey_scene_publishes_goal_and_maps_success_result() -> None:
    fake = FakeRosFactory(
        [
            _observation_payloads(),
            {
                "/survey/result": json.dumps(
                    {"success": True, "reason": "success", "duration_s": 3.0}
                )
            },
        ]
    )
    transport = ros_execution.PM4HardwareTransport(fake.runtime(), clock=fake.clock)
    command = SurveySceneSkillCommand(command_id="survey-1", issued_ms=1)

    observation = transport.read_observation(objective="survey", readiness_timeout_s=1)
    transport.bind_observation(observation)
    transport.dispatch(command)
    terminal = transport.wait_for_terminal_result(command, timeout_ms=1000)

    node = fake.rclpy.nodes[0]
    assert _publisher_payloads(node, "/survey/goal") == [
        {
            "command_id": "survey-1",
            "duration_s": 5.0,
            "ttl_ms": 250,
            "yaw_span_deg": 180.0,
        }
    ]
    assert terminal.status is CommandStatus.OK
    assert terminal.message == "success"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"success": False, "reason": "bad_goal"}, CommandStatus.REJECTED),
        ({"success": False, "reason": "stale_telemetry"}, CommandStatus.STALE),
        (
            {"success": False, "reason": "bridge_fault", "fault": "bridge_fault"},
            CommandStatus.FAILED,
        ),
    ],
)
def test_survey_terminal_payload_status_normalization(
    payload: dict[str, Any],
    expected: CommandStatus,
) -> None:
    fake = FakeRosFactory([{}, {"/survey/result": json.dumps(payload)}])
    transport = ros_execution.PM4HardwareTransport(fake.runtime(), clock=fake.clock)
    command = SurveySceneSkillCommand(command_id="survey-2", issued_ms=1)

    terminal = transport.wait_for_terminal_result(command, timeout_ms=1000)

    assert terminal.status is expected


def test_survey_timeout_publishes_cancel_without_fallback_motion() -> None:
    fake = FakeRosFactory([{}])
    transport = ros_execution.PM4HardwareTransport(fake.runtime(), clock=fake.clock)
    command = SurveySceneSkillCommand(command_id="survey-timeout", issued_ms=1)

    with pytest.raises(TimeoutError):
        transport.wait_for_terminal_result(command, timeout_ms=50)
    transport.cancel(command, reason="timeout")

    node = fake.rclpy.nodes[0]
    assert _publisher_payloads(node, "/survey/cancel") == [
        {"command_id": "survey-timeout", "reason": "timeout"}
    ]
    assert node.publishers["/operator/command"].messages == []


def test_claw_open_and_close_use_operator_command_surface() -> None:
    fake = FakeRosFactory(
        [
            {
                "/operator/results": json.dumps(
                    {"outcome": {"method": "release", "success": True, "reason": "released"}}
                )
            },
            {
                "/operator/results": json.dumps(
                    {"outcome": {"method": "grab", "success": True, "reason": "grabbed"}}
                )
            },
        ]
    )
    transport = ros_execution.PM4HardwareTransport(fake.runtime(), clock=fake.clock)
    open_command = ClawOpenSkillCommand(command_id="open-1", issued_ms=1)
    close_command = ClawCloseSkillCommand(command_id="close-1", issued_ms=1)

    transport.dispatch(open_command)
    open_terminal = transport.wait_for_terminal_result(open_command, timeout_ms=1000)
    transport.dispatch(close_command)
    close_terminal = transport.wait_for_terminal_result(close_command, timeout_ms=1000)

    node = fake.rclpy.nodes[0]
    payloads = _publisher_payloads(node, "/operator/command")
    assert [payload["action"] for payload in payloads] == ["release", "grab"]
    assert open_terminal.status is CommandStatus.OK
    assert close_terminal.status is CommandStatus.OK


def test_unavailable_operator_surface_rejects_before_publish() -> None:
    fake = FakeRosFactory([])
    transport = ros_execution.PM4HardwareTransport(
        fake.runtime(),
        clock=fake.clock,
        operator_surface_available=False,
    )
    command = ClawOpenSkillCommand(command_id="open-unavailable", issued_ms=1)

    terminal = transport.preflight_terminal_outcome(command, _healthy_observation())

    assert terminal is not None
    assert terminal.status is CommandStatus.REJECTED
    assert "unavailable" in (terminal.message or "")
    node = fake.rclpy.nodes[0]
    assert node.publishers["/operator/command"].messages == []


def test_verify_skills_are_read_only_terminal_checks() -> None:
    fake = FakeRosFactory([])
    transport = ros_execution.PM4HardwareTransport(fake.runtime(), clock=fake.clock)
    grasp = VerifyGraspSkillCommand(command_id="verify-grasp", issued_ms=1)
    drop = VerifyDropSkillCommand(command_id="verify-drop", issued_ms=1)

    transport.dispatch(grasp)
    grasp_terminal = transport.wait_for_terminal_result(grasp, timeout_ms=100)
    transport.dispatch(drop)
    drop_terminal = transport.wait_for_terminal_result(drop, timeout_ms=100)

    node = fake.rclpy.nodes[0]
    assert grasp_terminal.status is CommandStatus.OK
    assert drop_terminal.status is CommandStatus.OK
    assert node.publishers["/survey/goal"].messages == []
    assert node.publishers["/survey/cancel"].messages == []
    assert node.publishers["/operator/command"].messages == []
