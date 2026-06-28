from __future__ import annotations

import dataclasses
import importlib
from io import StringIO
import json
from pathlib import Path
import sys

import pytest
from contracts import (
    AssertionState,
    AssertionTraceRecord,
    BridgeHealth,
    CommandTraceRecord,
    CommandStatus,
    DecisionTraceRecord,
    LocalizationState,
    ManipulatorState,
    ObservationTraceRecord,
    PilotAssertion,
    PilotDecision,
    PilotDecisionAction,
    PilotFailure,
    PilotObservation,
    PilotSkillName,
    PilotSkillResult,
    PilotTaskPhase,
    PilotTraceRecord,
    ResultTraceRecord,
    StopTraceRecord,
    SurveySceneSkillCommand,
)
from pydantic import TypeAdapter

from pilot.run_logger import (
    STOP_REASONS,
    RunLogger,
    RunLoggerConfig,
    RunLoggerError,
    RunLoggerReadbackError,
    default_session_id,
    default_trace_path,
    format_recent_history,
    read_trace_records,
)

TRACE_RECORD_ADAPTER = TypeAdapter(PilotTraceRecord)
TRACE_RECORD_TYPES = (
    ObservationTraceRecord,
    DecisionTraceRecord,
    CommandTraceRecord,
    ResultTraceRecord,
    AssertionTraceRecord,
    StopTraceRecord,
)
PROMPT_UNSAFE_MARKERS = (
    "data:image",
    "base64,",
    "BEGIN PRIVATE KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "os.environ",
    "\x00",
    "Human:",
    "full provider transcript",
)


def _observation() -> PilotObservation:
    return PilotObservation(
        observed_ms=100,
        task_phase=PilotTaskPhase.SURVEY,
        objective="deliver the yellow ball",
        localization=LocalizationState(pose=None, confidence=0.75, age_ms=20),
        manipulator=ManipulatorState(arm_deg=None, claw_state="unknown", held_object_id=None),
        bridge=BridgeHealth(state="ok", last_heartbeat_age_ms=10),
    )


def _observation_with_history() -> PilotObservation:
    return _observation().model_copy(
        update={
            "last_command": _command("cmd-failed"),
            "last_result": PilotSkillResult(
                command_id="cmd-failed",
                skill=PilotSkillName.SURVEY_SCENE,
                status=CommandStatus.FAILED,
                completed_ms=130,
                message='raw tail {"event":"result","fault":"bad"}',
                fault="OPENAI_API_KEY=secret-value bridge timeout",
            ),
            "recent_failures": [
                PilotFailure(
                    failed_ms=131,
                    source="vision",
                    summary="target lost OPENAI_API_KEY=secret-value",
                    command_id="cmd-failed",
                    recovery_hint="resurvey before continuing",
                )
            ],
            "current_assertions": [_assertion()],
        }
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


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


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
    assert pilot.RunLogger.__name__ == module.RunLogger.__name__
    assert pilot.RunLoggerConfig.__name__ == module.RunLoggerConfig.__name__
    assert pilot.RunLoggerReadbackError.__name__ == module.RunLoggerReadbackError.__name__
    assert callable(pilot.default_trace_path)
    assert callable(pilot.format_recent_history)
    assert callable(pilot.read_trace_records)
    for export in (
        "RunLogger",
        "RunLoggerConfig",
        "RunLoggerReadbackError",
        "default_trace_path",
        "format_recent_history",
        "read_trace_records",
    ):
        assert export in pilot.__all__
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


def test_sequence_starts_from_config_and_advances_only_after_validated_record(
    tmp_path: Path,
) -> None:
    logger = RunLogger(
        RunLoggerConfig(session_id="session-seq", start_seq=7, trace_path=tmp_path / "trace.jsonl")
    )

    first = logger.append_stop("operator", monotonic_ms=50)
    second = logger.append_stop("success", monotonic_ms=55)

    assert first.session_id == "session-seq"
    assert first.seq == 7
    assert second.seq == 8
    assert logger.next_seq == 9


def test_deterministic_clock_and_explicit_timestamp_are_used_without_hidden_time(
    tmp_path: Path,
) -> None:
    clock_values = iter([10, 20])
    logger = RunLogger(
        RunLoggerConfig(
            session_id="session-clock",
            monotonic_clock=lambda: next(clock_values),
            trace_path=tmp_path / "clock.jsonl",
        )
    )

    explicit = logger.append_stop("operator", monotonic_ms=99)
    from_clock = logger.append_stop("success")
    no_clock_logger = RunLogger(
        RunLoggerConfig(session_id="session-no-clock", trace_path=tmp_path / "no-clock.jsonl")
    )

    assert explicit.monotonic_ms == 99
    assert from_clock.monotonic_ms == 10
    with pytest.raises(RunLoggerError, match="monotonic_ms requires"):
        no_clock_logger.append_stop("operator")
    assert no_clock_logger.next_seq == 0


def test_all_six_variants_write_in_order_as_contract_valid_compact_jsonl(tmp_path: Path) -> None:
    trace_path = tmp_path / "nested" / "pilot-trace.jsonl"
    clock_values = iter([10, 20, 30, 40, 50, 60])
    logger = RunLogger(
        RunLoggerConfig(
            session_id="session-variants",
            monotonic_clock=lambda: next(clock_values),
            trace_path=trace_path,
        )
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
    assert trace_path.parent.is_dir()
    text = trace_path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert "\n\n" not in text
    assert all(line.startswith("{") and line.endswith("}") for line in text.splitlines())
    assert all(": " not in line for line in text.splitlines())

    written = _read_jsonl(trace_path)
    assert [line["event"] for line in written] == [
        "observation",
        "decision",
        "command",
        "result",
        "assertion",
        "stop",
    ]
    assert [line["seq"] for line in written] == list(range(6))
    for line, record in zip(written, records, strict=True):
        assert TRACE_RECORD_ADAPTER.validate_python(line) == record

    readback = read_trace_records(trace_path)

    assert readback == records
    assert all(isinstance(record, TRACE_RECORD_TYPES) for record in readback)
    assert [type(record) for record in readback] == [
        ObservationTraceRecord,
        DecisionTraceRecord,
        CommandTraceRecord,
        ResultTraceRecord,
        AssertionTraceRecord,
        StopTraceRecord,
    ]


@pytest.mark.parametrize("reason", STOP_REASONS)
def test_all_stop_reasons_round_trip_as_contract_values(tmp_path: Path, reason: str) -> None:
    trace_path = tmp_path / f"{reason}.jsonl"
    logger = RunLogger(RunLoggerConfig(session_id=f"session-{reason}", trace_path=trace_path))

    record = logger.append_stop(reason, message=f"{reason} stop", monotonic_ms=10)
    logger.close()

    assert record.reason == reason
    assert logger.next_seq == 1
    assert read_trace_records(trace_path) == [record]


def test_unsupported_stop_reason_rejects_before_writing_or_consuming_sequence(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "unsupported-stop.jsonl"
    logger = RunLogger(
        RunLoggerConfig(session_id="session-unsupported-stop", trace_path=trace_path)
    )

    with pytest.raises(RunLoggerError, match="invalid stop trace record"):
        logger.append_stop("unsafe", monotonic_ms=1)

    assert logger.next_seq == 0
    assert not trace_path.exists()


def test_invalid_payloads_stop_reasons_and_metadata_raise_without_writing_or_consuming_sequence(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "invalid.jsonl"
    logger = RunLogger(RunLoggerConfig(session_id="session-invalid", trace_path=trace_path))

    first = logger.append_stop("operator", monotonic_ms=0)
    before = trace_path.read_bytes()
    assert first.seq == 0
    assert logger.next_seq == 1

    with pytest.raises(RunLoggerError, match="invalid observation trace record"):
        logger.append_observation({"objective": "missing required fields"}, monotonic_ms=1)
    assert logger.next_seq == 1
    assert trace_path.read_bytes() == before

    with pytest.raises(RunLoggerError, match="invalid stop trace record"):
        logger.append_stop("not-a-stop-reason", monotonic_ms=2)
    assert logger.next_seq == 1
    assert trace_path.read_bytes() == before

    with pytest.raises(RunLoggerError, match="monotonic_ms"):
        logger.append_stop("operator", monotonic_ms=-1)
    assert logger.next_seq == 1
    assert trace_path.read_bytes() == before

    valid = logger.append_stop("operator", monotonic_ms=3)
    assert valid.seq == 1
    assert logger.next_seq == 2
    assert [line["seq"] for line in _read_jsonl(trace_path)] == [0, 1]


@pytest.mark.parametrize(
    ("factory", "match"),
    [
        (lambda: RunLoggerConfig(session_id=""), "session_id"),
        (lambda: RunLoggerConfig(session_id="x" * 81), "session_id"),
        (lambda: RunLoggerConfig(trace_path=""), "trace_path"),
        (lambda: RunLoggerConfig(start_seq=-1), "start_seq"),
        (lambda: RunLoggerConfig(start_seq=True), "start_seq"),
        (lambda: RunLoggerConfig(flush_after_append=1), "flush_after_append"),
        (lambda: RunLoggerConfig(monotonic_clock=object()), "monotonic_clock"),
    ],
)
def test_invalid_configuration_is_a_logger_error(factory: object, match: str) -> None:
    with pytest.raises(RunLoggerError, match=match):
        factory()


def test_explicit_path_parent_dirs_flush_close_and_context_manager(tmp_path: Path) -> None:
    trace_path = tmp_path / "a" / "b" / "explicit.jsonl"
    logger = RunLogger(RunLoggerConfig(session_id="session-explicit", trace_path=trace_path))

    record = logger.append_stop("success", monotonic_ms=1)

    assert record.reason == "success"
    assert STOP_REASONS == ("success", "failure", "operator", "fault", "request_human")
    assert logger.trace_path == trace_path
    assert trace_path.exists()
    assert _read_jsonl(trace_path)[0]["reason"] == "success"

    logger.close()
    logger.close()
    logger.append_stop("operator", monotonic_ms=2)
    logger.close()
    assert [line["seq"] for line in _read_jsonl(trace_path)] == [0, 1]

    context_path = tmp_path / "context" / "trace.jsonl"
    with RunLogger(RunLoggerConfig(session_id="session-context", trace_path=context_path)) as ctx:
        ctx.append_stop("operator", monotonic_ms=3)
    assert _read_jsonl(context_path)[0]["session_id"] == "session-context"


def test_default_path_uses_ignored_pilot_runs_directory_and_session_filename() -> None:
    session_id = "session-default-path"
    trace_path = default_trace_path(session_id)
    if trace_path.exists():
        trace_path.unlink()

    logger = RunLogger(RunLoggerConfig(session_id=session_id))

    try:
        assert logger.trace_path == trace_path
        assert trace_path.parent.name == "runs"
        assert trace_path.parent.parent.name == "pilot"
        assert trace_path.name == f"{session_id}.jsonl"

        logger.append_stop("operator", monotonic_ms=1)

        assert trace_path.exists()
        assert _read_jsonl(trace_path)[0]["session_id"] == session_id
    finally:
        logger.close()
        if trace_path.exists():
            trace_path.unlink()


def test_read_trace_records_returns_typed_records_from_path_and_stream_in_file_order(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "readback.jsonl"
    logger = RunLogger(RunLoggerConfig(session_id="session-readback", trace_path=trace_path))

    logger.append_stop("operator", monotonic_ms=30)
    logger.append_decision(_decision(), monotonic_ms=10)
    logger.append_result(_result(), monotonic_ms=20)
    logger.close()

    path_records = read_trace_records(trace_path)
    stream_records = read_trace_records(StringIO(trace_path.read_text(encoding="utf-8")))

    assert [record.event for record in path_records] == ["stop", "decision", "result"]
    assert [record.seq for record in path_records] == [0, 1, 2]
    assert [record.monotonic_ms for record in path_records] == [30, 10, 20]
    assert path_records == stream_records
    assert path_records[0] is not stream_records[0]
    assert all(isinstance(record, TRACE_RECORD_TYPES) for record in path_records)
    assert all(not isinstance(record, dict) for record in path_records)
    assert all(
        TRACE_RECORD_ADAPTER.validate_python(record.model_dump()) == record
        for record in path_records
    )


def test_read_trace_records_reports_malformed_json_with_line_number() -> None:
    source = StringIO(
        '{"v":1,"session_id":"s","seq":0,"monotonic_ms":0,"event":"stop","reason":"operator"}\n'
        '{"v":1,"event":'
    )

    with pytest.raises(RunLoggerReadbackError, match=r"line 2: malformed JSON") as exc_info:
        read_trace_records(source)

    assert exc_info.value.line_number == 2


@pytest.mark.parametrize("line", ['"not an object"\n', '["not", "an", "object"]\n'])
def test_read_trace_records_reports_non_object_json_with_line_number(line: str) -> None:
    with pytest.raises(RunLoggerReadbackError, match=r"line 1: trace record must be a JSON object"):
        read_trace_records(StringIO(line))


def test_read_trace_records_reports_schema_invalid_json_with_line_number() -> None:
    source = StringIO(
        '{"v":1,"session_id":"s","seq":0,"monotonic_ms":0,"event":"stop","reason":"operator"}\n'
        '{"v":1,"session_id":"s","seq":1,"monotonic_ms":1,"event":"not-real"}\n'
    )

    with pytest.raises(
        RunLoggerReadbackError, match=r"line 2: schema-invalid trace record"
    ) as exc_info:
        read_trace_records(source)

    assert "event" in str(exc_info.value)


def test_format_recent_history_is_bounded_deterministic_and_count_limited() -> None:
    records = [
        TRACE_RECORD_ADAPTER.validate_python(
            {
                "v": 1,
                "session_id": "session-history",
                "seq": index,
                "monotonic_ms": index,
                "event": "stop",
                "reason": "operator",
                "message": f"message {index} " + ("x" * 200),
            }
        )
        for index in range(8)
    ]

    first = format_recent_history(records, max_records=3, max_chars=160)
    second = format_recent_history(records, max_records=3, max_chars=160)
    wide = format_recent_history(records, max_records=3, max_chars=1_000)

    assert first == second
    assert len(first) <= 160
    assert "seq=7" in first
    assert "seq=5" in wide
    assert "seq=7" in wide
    assert "seq=4" not in first
    assert "seq=4" not in wide
    assert first.endswith("[truncated]")


def test_format_recent_history_summarizes_relevant_events_without_raw_prompt_unsafe_data(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "history.jsonl"
    logger = RunLogger(RunLoggerConfig(session_id="session-history", trace_path=trace_path))

    logger.append_observation(_observation_with_history(), monotonic_ms=1)
    logger.append_decision(
        _decision().model_copy(
            update={"rationale": "Human: full provider transcript OPENAI_API_KEY=secret-value"}
        ),
        monotonic_ms=2,
    )
    logger.append_command(_command("cmd-next"), monotonic_ms=3)
    logger.append_result(
        _result().model_copy(
            update={
                "status": CommandStatus.FAILED,
                "message": 'command log tail {"raw":"jsonl"} \x00 OPENAI_API_KEY=secret-value',
                "fault": "motor stalled",
            }
        ),
        monotonic_ms=4,
    )
    logger.append_assertion(
        _assertion().model_copy(
            update={"state": AssertionState.FALSE, "recovery_hint": "resurvey"}
        ),
        monotonic_ms=5,
    )
    logger.append_stop("failure", message="policy stop after failed command", monotonic_ms=6)
    logger.close()

    history = format_recent_history(read_trace_records(trace_path), max_records=6, max_chars=1_200)

    assert "seq=0 observation" in history
    assert "phase=survey" in history
    assert "failures=vision:" in history
    assert "assertions=target-visible" in history
    assert "seq=1 decision" in history
    assert "decision-1" in history
    assert "cmd-next/survey_scene" in history
    assert "status=failed" in history
    assert "seq=4 assertion" in history
    assert "state=false" in history
    assert "seq=5 stop: reason=failure" in history
    assert "secret-value" not in history
    assert "OPENAI_API_KEY" not in history
    assert '{"' not in history
    assert "\x00" not in history
    assert "Human:" not in history


def test_recent_history_feeds_decision_prompt_without_ros_hardware_or_provider(
    tmp_path: Path,
) -> None:
    import pilot

    trace_path = tmp_path / "prompt-history.jsonl"
    logger = RunLogger(RunLoggerConfig(session_id="session-prompt-history", trace_path=trace_path))
    logger.append_observation(_observation(), monotonic_ms=1)
    logger.append_decision(_decision(), monotonic_ms=2)
    logger.append_command(_command(), monotonic_ms=3)
    logger.append_result(_result(), monotonic_ms=4)
    logger.close()

    recent_history = pilot.format_recent_history(pilot.read_trace_records(trace_path))
    payload = pilot.build_prompt_payload(
        _observation(),
        recent_history=recent_history,
        allowed_skills=[],
    )
    prompt = pilot.render_prompt(payload)

    assert payload["recent_history"] == recent_history
    assert "## recent history" in prompt
    assert "seq=0 observation" in prompt
    assert "\\nseq=1 decision" in prompt
    assert all(root not in sys.modules for root in ("rclpy", "openai", "anthropic"))


def test_logger_derived_surfaces_are_bounded_temporary_and_prompt_safe(tmp_path: Path) -> None:
    trace_path = tmp_path / "safe-surfaces.jsonl"
    logger = RunLogger(RunLoggerConfig(session_id="session-safe-surfaces", trace_path=trace_path))
    logger.append_result(
        _result().model_copy(
            update={
                "message": "provider summary stored without raw image bytes or transcript",
                "fault": "operator-visible fault summary",
            }
        ),
        monotonic_ms=1,
    )
    logger.append_stop("failure", message="bounded stop summary", monotonic_ms=2)
    logger.close()

    raw_trace = trace_path.read_text(encoding="utf-8")
    readback = read_trace_records(trace_path)
    history = format_recent_history(readback, max_records=10, max_chars=400)

    assert trace_path.is_relative_to(tmp_path)
    assert len(raw_trace) < 2_000
    assert len(history) <= 400
    assert all(isinstance(record, TRACE_RECORD_TYPES) for record in readback)
    for surface in (raw_trace, history):
        for marker in PROMPT_UNSAFE_MARKERS:
            assert marker not in surface
