from __future__ import annotations

import importlib
import io
import json
import sys
from dataclasses import dataclass, field

import pytest
from contracts import (
    ApproachTargetParams,
    ApproachTargetSkillCommand,
    BridgeHealth,
    CommandStatus,
    LocalizationState,
    ManipulatorState,
    PilotObservation,
    PilotSkillResult,
    PilotTaskPhase,
    PilotTraceRecord,
    Pose2D,
    VisibleObject,
)
from pydantic import TypeAdapter

from pilot.execution import (
    ExecutionStatus,
    TransportTerminalOutcome,
    execute_one_skill,
    normalize_skill_result,
)
from pilot.safety import ValidationMode, ValidationReasonCode
from pilot.trace import PilotTraceWriter


TRACE_RECORD_TA = TypeAdapter(PilotTraceRecord)


@dataclass(slots=True)
class FakeTransport:
    terminal: object | None = None
    raises: BaseException | None = None
    dispatched: list[object] = field(default_factory=list)
    cancelled: list[tuple[object, str]] = field(default_factory=list)
    waits: list[tuple[object, int]] = field(default_factory=list)

    def dispatch(self, command: object) -> None:
        self.dispatched.append(command)

    def wait_for_terminal_result(self, command: object, *, timeout_ms: int) -> object:
        self.waits.append((command, timeout_ms))
        if self.raises is not None:
            raise self.raises
        assert self.terminal is not None
        return self.terminal

    def cancel(self, command: object, *, reason: str) -> None:
        self.cancelled.append((command, reason))


def _command(command_id: str = "cmd-approach") -> ApproachTargetSkillCommand:
    return ApproachTargetSkillCommand(
        command_id=command_id,
        issued_ms=100,
        params=ApproachTargetParams(target_id="block-1"),
    )


def _observation(
    *,
    bridge: BridgeHealth | None = None,
    localization: LocalizationState | None = None,
    visible_objects: list[VisibleObject] | None = None,
) -> PilotObservation:
    pose = Pose2D(x_m=0.4, y_m=0.2, heading_rad=0.1)
    return PilotObservation(
        observed_ms=120,
        task_phase=PilotTaskPhase.MANIPULATE,
        objective="pick up block-1",
        robot_pose=pose,
        localization=localization or LocalizationState(pose=pose, confidence=0.8, age_ms=25),
        visible_objects=visible_objects
        if visible_objects is not None
        else [VisibleObject(object_id="block-1", label="block", confidence=0.9)],
        visible_tags=[],
        manipulator=ManipulatorState(arm_deg=20.0, claw_state="open"),
        bridge=bridge
        or BridgeHealth(
            state="ok",
            last_heartbeat_age_ms=25,
            estop=False,
            battery_pct=80.0,
        ),
        recent_failures=[],
        current_assertions=[],
    )


def _trace_writer() -> tuple[PilotTraceWriter, io.StringIO]:
    sink = io.StringIO()
    ticks = iter([10, 20, 30, 40, 50])
    return PilotTraceWriter(sink, session_id="session-1", clock_ms=lambda: next(ticks)), sink


def _trace_records(sink: io.StringIO) -> list[object]:
    return [
        TRACE_RECORD_TA.validate_python(json.loads(line)) for line in sink.getvalue().splitlines()
    ]


def test_execution_module_and_pilot_package_import_without_ros_packages(monkeypatch) -> None:
    ros_roots = {"rclpy", "std_msgs", "sensor_msgs", "geometry_msgs"}

    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            root = fullname.split(".", maxsplit=1)[0]
            if root in ros_roots:
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.execution", None)
    sys.modules.pop("pilot.trace", None)

    execution = importlib.import_module("pilot.execution")
    trace = importlib.import_module("pilot.trace")
    import pilot

    assert execution.execute_one_skill is not None
    assert trace.PilotTraceWriter is not None
    assert "execute_one_skill" in pilot.__all__
    assert "PilotTraceWriter" in pilot.__all__
    assert ros_roots.isdisjoint(sys.modules)


def test_validation_failure_rejects_without_dispatch_and_writes_stop_record() -> None:
    writer, sink = _trace_writer()
    transport = FakeTransport()

    outcome = execute_one_skill(
        _command(),
        _observation(visible_objects=[]),
        mode=ValidationMode.REPLAY,
        human_supervised=True,
        timeout_ms=500,
        session_id="session-1",
        trace_sink=writer,
        transport=transport,
    )

    assert outcome.status is ExecutionStatus.REJECTED
    assert outcome.validation.reason_code is ValidationReasonCode.TARGET_EVIDENCE
    assert transport.dispatched == []
    records = _trace_records(sink)
    assert [(record.event, record.seq, record.session_id) for record in records] == [
        ("stop", 0, "session-1")
    ]
    assert records[0].reason == "failure"
    assert "target_evidence" in records[0].message


def test_hardware_mode_requires_supervision_before_dispatch() -> None:
    writer, sink = _trace_writer()
    transport = FakeTransport()

    outcome = execute_one_skill(
        _command(),
        _observation(),
        mode=ValidationMode.HARDWARE,
        human_supervised=False,
        timeout_ms=500,
        session_id="session-1",
        trace_sink=writer,
        transport=transport,
    )

    assert outcome.status is ExecutionStatus.REJECTED
    assert outcome.validation.reason_code is ValidationReasonCode.HUMAN_SUPERVISION_REQUIRED
    assert transport.dispatched == []
    records = _trace_records(sink)
    assert records[0].event == "stop"
    assert records[0].reason == "request_human"


@pytest.mark.parametrize(
    "bridge,expected",
    [
        (
            BridgeHealth(state="stale", last_heartbeat_age_ms=25, estop=False),
            ValidationReasonCode.BRIDGE_STALE,
        ),
        (
            BridgeHealth(state="ok", last_heartbeat_age_ms=25, estop=True),
            ValidationReasonCode.ESTOP_ACTIVE,
        ),
    ],
)
def test_faulted_observation_rejects_before_dispatch(
    bridge: BridgeHealth,
    expected: ValidationReasonCode,
) -> None:
    writer, _sink = _trace_writer()
    transport = FakeTransport()

    outcome = execute_one_skill(
        _command(),
        _observation(bridge=bridge),
        mode=ValidationMode.REPLAY,
        human_supervised=True,
        timeout_ms=500,
        session_id="session-1",
        trace_sink=writer,
        transport=transport,
    )

    assert outcome.status is ExecutionStatus.REJECTED
    assert outcome.validation.reason_code is expected
    assert transport.dispatched == []


def test_invalid_command_and_observation_reject_before_dispatch() -> None:
    transport = FakeTransport()
    writer, _sink = _trace_writer()

    bad_command_outcome = execute_one_skill(
        {"skill": "drive"},
        _observation(),
        mode=ValidationMode.REPLAY,
        human_supervised=True,
        timeout_ms=500,
        session_id="session-1",
        trace_sink=writer,
        transport=transport,
    )
    writer, _sink = _trace_writer()
    bad_observation_outcome = execute_one_skill(
        _command(),
        {"observed_ms": 120},
        mode=ValidationMode.REPLAY,
        human_supervised=True,
        timeout_ms=500,
        session_id="session-1",
        trace_sink=writer,
        transport=transport,
    )

    assert bad_command_outcome.validation.reason_code is ValidationReasonCode.INVALID_COMMAND
    assert (
        bad_observation_outcome.validation.reason_code is ValidationReasonCode.INVALID_OBSERVATION
    )
    assert transport.dispatched == []


def test_success_dispatches_once_normalizes_result_and_writes_trace_records() -> None:
    command = _command()
    writer, sink = _trace_writer()
    transport = FakeTransport(
        terminal={
            "status": "success",
            "completed_ms": 180,
            "message": "approach complete",
        }
    )

    outcome = execute_one_skill(
        command,
        _observation(),
        mode=ValidationMode.REPLAY,
        human_supervised=False,
        timeout_ms=500,
        session_id="session-1",
        trace_sink=writer,
        transport=transport,
    )

    assert outcome.status is ExecutionStatus.SUCCEEDED
    assert outcome.result == PilotSkillResult(
        command_id=command.command_id,
        skill="approach_target",
        status=CommandStatus.OK,
        completed_ms=180,
        message="approach complete",
    )
    assert transport.dispatched == [command]
    assert transport.waits == [(command, 500)]
    assert transport.cancelled == []
    records = _trace_records(sink)
    assert [(record.event, record.seq, record.session_id) for record in records] == [
        ("command", 0, "session-1"),
        ("result", 1, "session-1"),
        ("stop", 2, "session-1"),
    ]
    assert records[0].command == command
    assert records[1].result == outcome.result
    assert records[2].reason == "success"


def test_executor_accepts_raw_trace_sink_with_session_and_clock() -> None:
    sink = io.StringIO()
    command = _command()
    transport = FakeTransport(terminal={"status": "ok", "completed_ms": 180})

    outcome = execute_one_skill(
        command,
        _observation(),
        mode=ValidationMode.REPLAY,
        human_supervised=False,
        timeout_ms=500,
        session_id="session-1",
        trace_sink=sink,
        start_seq=7,
        clock_ms=lambda: 90,
        transport=transport,
    )

    assert outcome.status is ExecutionStatus.SUCCEEDED
    records = _trace_records(sink)
    assert [(record.event, record.seq, record.monotonic_ms) for record in records] == [
        ("command", 7, 90),
        ("result", 8, 90),
        ("stop", 9, 90),
    ]


@pytest.mark.parametrize(
    "terminal,expected_status,expected_execution_status",
    [
        (
            TransportTerminalOutcome(
                status="failed",
                completed_ms=190,
                message="blocked",
                fault="path_blocked",
            ),
            CommandStatus.FAILED,
            ExecutionStatus.FAILED,
        ),
        (
            TransportTerminalOutcome(status="rejected", completed_ms=190, message="unsafe"),
            CommandStatus.REJECTED,
            ExecutionStatus.REJECTED,
        ),
        (
            TransportTerminalOutcome(status="timeout", completed_ms=190, message="stale result"),
            CommandStatus.STALE,
            ExecutionStatus.STALE,
        ),
    ],
)
def test_failure_rejection_and_timeout_like_terminal_results_normalize(
    terminal: TransportTerminalOutcome,
    expected_status: CommandStatus,
    expected_execution_status: ExecutionStatus,
) -> None:
    command = _command()
    writer, sink = _trace_writer()
    transport = FakeTransport(terminal=terminal)

    outcome = execute_one_skill(
        command,
        _observation(),
        mode=ValidationMode.REPLAY,
        human_supervised=False,
        timeout_ms=500,
        session_id="session-1",
        trace_sink=writer,
        transport=transport,
    )

    assert outcome.status is expected_execution_status
    assert outcome.result is not None
    assert outcome.result.status is expected_status
    assert outcome.result.command_id == command.command_id
    assert outcome.result.skill.value == command.skill
    records = _trace_records(sink)
    assert records[-1].event == "stop"
    assert records[-1].reason == "failure"


def test_normalize_preserves_contract_result_fields() -> None:
    command = _command()
    result = normalize_skill_result(
        PilotSkillResult(
            command_id=command.command_id,
            skill="approach_target",
            status=CommandStatus.OK,
            completed_ms=220,
            message="done",
            fault=None,
        ),
        command=command,
    )

    assert result.command_id == command.command_id
    assert result.skill.value == command.skill
    assert result.status is CommandStatus.OK
    assert result.completed_ms == 220
    assert result.message == "done"


def test_timeout_cancels_without_extra_dispatch_and_writes_explanatory_stop() -> None:
    command = _command()
    writer, sink = _trace_writer()
    transport = FakeTransport(raises=TimeoutError())

    outcome = execute_one_skill(
        command,
        _observation(),
        mode=ValidationMode.REPLAY,
        human_supervised=False,
        timeout_ms=500,
        session_id="session-1",
        trace_sink=writer,
        transport=transport,
    )

    assert outcome.status is ExecutionStatus.TIMED_OUT
    assert transport.dispatched == [command]
    assert transport.cancelled == [(command, "timeout")]
    records = _trace_records(sink)
    assert [record.event for record in records] == ["command", "stop"]
    assert records[-1].reason == "failure"
    assert "500 ms" in records[-1].message


def test_interrupt_cancels_without_extra_dispatch_and_writes_operator_stop() -> None:
    command = _command()
    writer, sink = _trace_writer()
    transport = FakeTransport(raises=KeyboardInterrupt())

    outcome = execute_one_skill(
        command,
        _observation(),
        mode=ValidationMode.REPLAY,
        human_supervised=False,
        timeout_ms=500,
        session_id="session-1",
        trace_sink=writer,
        transport=transport,
    )

    assert outcome.status is ExecutionStatus.INTERRUPTED
    assert transport.dispatched == [command]
    assert transport.cancelled == [(command, "interrupt")]
    records = _trace_records(sink)
    assert [record.event for record in records] == ["command", "stop"]
    assert records[-1].reason == "operator"
