from __future__ import annotations

import builtins
import dataclasses
import importlib
import sys

import pytest
from contracts import (
    AssertionState,
    BridgeHealth,
    CommandStatus,
    LocalizationState,
    ManipulatorState,
    PilotAssertion,
    PilotDecision,
    PilotDecisionAction,
    PilotObservation,
    PilotSkillName,
    PilotSkillResult,
    PilotTaskPhase,
    PilotTraceRecord,
    SurveySceneSkillCommand,
)
from pydantic import TypeAdapter

from pilot.run_logger import (
    STOP_REASONS,
    RunLogger,
    RunLoggerConfig,
    RunLoggerError,
    default_session_id,
)

TRACE_RECORD_ADAPTER = TypeAdapter(PilotTraceRecord)


def _observation() -> PilotObservation:
    return PilotObservation(
        observed_ms=100,
        task_phase=PilotTaskPhase.SURVEY,
        objective="deliver the yellow ball",
        localization=LocalizationState(pose=None, confidence=0.75, age_ms=20),
        manipulator=ManipulatorState(arm_deg=None, claw_state="unknown", held_object_id=None),
        bridge=BridgeHealth(state="ok", last_heartbeat_age_ms=10),
    )


def _command(command_id: str = "cmd-survey") -> SurveySceneSkillCommand:
    return SurveySceneSkillCommand(command_id=command_id, issued_ms=110)


def _decision() -> PilotDecision:
    return PilotDecision(
        decision_id="decision-1",
        decided_ms=120,
        action=PilotDecisionAction.CONTINUE,
        rationale="survey first",
        confidence=0.82,
        command=_command(),
    )


def _result() -> PilotSkillResult:
    return PilotSkillResult(
        command_id="cmd-survey",
        skill=PilotSkillName.SURVEY_SCENE,
        status=CommandStatus.OK,
        completed_ms=140,
        message="survey complete",
    )


def _assertion() -> PilotAssertion:
    return PilotAssertion(
        assertion_id="target-visible",
        predicate="target is visible",
        state=AssertionState.TRUE,
        confidence=0.9,
        observed_ms=150,
    )


def test_run_logger_module_imports_without_ros_packages_and_exports_public_api(monkeypatch) -> None:
    ros_roots = {"rclpy", "std_msgs", "sensor_msgs", "geometry_msgs"}

    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            root = fullname.split(".", maxsplit=1)[0]
            if root in ros_roots:
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.run_logger", None)

    module = importlib.import_module("pilot.run_logger")
    import pilot

    assert module.RunLogger is not None
    assert module.RunLoggerConfig is not None
    assert "RunLogger" in pilot.__all__
    assert "RunLoggerConfig" in pilot.__all__
    assert ros_roots.isdisjoint(sys.modules)


def test_config_session_ids_are_stable_defaultable_and_immutable() -> None:
    generated = default_session_id()
    logger = RunLogger()
    explicit = RunLogger(RunLoggerConfig(session_id="session-explicit"))
    config = RunLoggerConfig(session_id="session-frozen", start_seq=3)

    assert generated.startswith("run-")
    assert generated.strip()
    assert logger.session_id.startswith("run-")
    assert logger.session_id == logger.session_id
    assert explicit.session_id == "session-explicit"
    assert dataclasses.is_dataclass(config)
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.start_seq = 4


def test_sequence_starts_from_config_and_advances_only_after_validated_record() -> None:
    logger = RunLogger(RunLoggerConfig(session_id="session-seq", start_seq=7))

    first = logger.append_stop("operator", monotonic_ms=50)
    second = logger.append_stop("success", monotonic_ms=55)

    assert first.session_id == "session-seq"
    assert first.seq == 7
    assert second.seq == 8
    assert logger.next_seq == 9


def test_deterministic_clock_and_explicit_timestamp_are_used_without_hidden_time() -> None:
    clock_values = iter([10, 20])
    logger = RunLogger(
        RunLoggerConfig(session_id="session-clock", monotonic_clock=lambda: next(clock_values))
    )

    explicit = logger.append_stop("operator", monotonic_ms=99)
    from_clock = logger.append_stop("success")
    no_clock_logger = RunLogger(RunLoggerConfig(session_id="session-no-clock"))

    assert explicit.monotonic_ms == 99
    assert from_clock.monotonic_ms == 10
    with pytest.raises(RunLoggerError, match="monotonic_ms requires"):
        no_clock_logger.append_stop("operator")
    assert no_clock_logger.next_seq == 0


def test_all_six_variants_validate_through_contract_union() -> None:
    clock_values = iter([10, 20, 30, 40, 50, 60])
    logger = RunLogger(
        RunLoggerConfig(session_id="session-variants", monotonic_clock=lambda: next(clock_values))
    )

    records = [
        logger.append_observation(_observation()),
        logger.append_decision(_decision()),
        logger.append_command(_command()),
        logger.append_result(_result()),
        logger.append_assertion(_assertion()),
        logger.append_stop("request_human", message="operator review requested"),
    ]

    assert [record.event for record in records] == [
        "observation",
        "decision",
        "command",
        "result",
        "assertion",
        "stop",
    ]
    assert [record.seq for record in records] == list(range(6))
    assert [record.monotonic_ms for record in records] == [10, 20, 30, 40, 50, 60]
    assert logger.next_seq == 6
    for record in records:
        assert TRACE_RECORD_ADAPTER.validate_python(record.model_dump()) == record


def test_invalid_payloads_stop_reasons_and_metadata_raise_without_consuming_sequence() -> None:
    logger = RunLogger(RunLoggerConfig(session_id="session-invalid"))

    with pytest.raises(RunLoggerError, match="invalid observation trace record"):
        logger.append_observation({"objective": "missing required fields"}, monotonic_ms=1)
    assert logger.next_seq == 0

    with pytest.raises(RunLoggerError, match="invalid stop trace record"):
        logger.append_stop("not-a-stop-reason", monotonic_ms=2)
    assert logger.next_seq == 0

    with pytest.raises(RunLoggerError, match="monotonic_ms"):
        logger.append_stop("operator", monotonic_ms=-1)
    assert logger.next_seq == 0

    valid = logger.append_stop("operator", monotonic_ms=3)
    assert valid.seq == 0
    assert logger.next_seq == 1


@pytest.mark.parametrize(
    ("factory", "match"),
    [
        (lambda: RunLoggerConfig(session_id=""), "session_id"),
        (lambda: RunLoggerConfig(session_id="x" * 81), "session_id"),
        (lambda: RunLoggerConfig(start_seq=-1), "start_seq"),
        (lambda: RunLoggerConfig(start_seq=True), "start_seq"),
        (lambda: RunLoggerConfig(monotonic_clock=object()), "monotonic_clock"),
    ],
)
def test_invalid_configuration_is_a_logger_error(factory: object, match: str) -> None:
    with pytest.raises(RunLoggerError, match=match):
        factory()


def test_append_skeleton_does_not_open_or_write_files(monkeypatch) -> None:
    def reject_file_io(*args: object, **kwargs: object) -> object:
        raise AssertionError("run logger core API must not open files")

    monkeypatch.setattr(builtins, "open", reject_file_io)
    logger = RunLogger(RunLoggerConfig(session_id="session-memory-only"))

    record = logger.append_stop("success", monotonic_ms=1)

    assert record.reason == "success"
    assert STOP_REASONS == ("success", "failure", "operator", "fault", "request_human")
