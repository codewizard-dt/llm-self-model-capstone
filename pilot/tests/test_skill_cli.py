from __future__ import annotations

import importlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from contracts import (
    BridgeHealth,
    CommandStatus,
    LocalizationState,
    ManipulatorState,
    PilotObservation,
    PilotTaskPhase,
    PilotTraceRecord,
)
from pydantic import TypeAdapter

from pilot import observe, skill_cli
from pilot.execution import TransportTerminalOutcome

_TRACE_ADAPTER = TypeAdapter(PilotTraceRecord)


def _healthy_observation(*, holding: bool = False) -> PilotObservation:
    return PilotObservation(
        observed_ms=1000,
        task_phase=PilotTaskPhase.IDLE,
        objective="pm4 proof",
        localization=LocalizationState(pose=None, confidence=0.0, age_ms=0),
        manipulator=ManipulatorState(
            claw_state="holding" if holding else "open",
            held_object_id="ball-1" if holding else None,
        ),
        bridge=BridgeHealth(state="ok", last_heartbeat_age_ms=10),
    )


@dataclass
class FakeTransport:
    observation: PilotObservation = field(default_factory=_healthy_observation)
    terminal_status: CommandStatus = CommandStatus.OK
    preflight: object | None = None
    dispatched: list[object] = field(default_factory=list)
    bound: list[object] = field(default_factory=list)
    closed: bool = False

    def read_observation(self, *, objective: str, readiness_timeout_s: float) -> PilotObservation:
        assert objective
        assert readiness_timeout_s > 0
        return self.observation

    def bind_observation(self, observation: object) -> None:
        self.bound.append(observation)

    def preflight_terminal_outcome(self, command: object, observation: object) -> object | None:
        assert observation is self.observation
        return self.preflight

    def dispatch(self, command: object) -> None:
        self.dispatched.append(command)

    def wait_for_terminal_result(self, command: object, *, timeout_ms: int) -> object:
        assert timeout_ms > 0
        return TransportTerminalOutcome(status=self.terminal_status, message="terminal")

    def cancel(self, command: object, *, reason: str) -> None:
        raise AssertionError(f"unexpected cancel: {reason}")

    def close(self) -> None:
        self.closed = True


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_skill_cli_imports_without_ros_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            if fullname == "rclpy" or fullname.startswith(("rclpy.", "std_msgs.")):
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.skill_cli", None)

    module = importlib.import_module("pilot.skill_cli")

    assert module.APPROVED_PM4_SKILL_VALUES == (
        "survey_scene",
        "claw_open",
        "claw_close",
        "verify_grasp",
        "verify_drop",
    )
    assert "rclpy" not in sys.modules


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (
            ["skill", "--human-supervised", "--skill", "survey_scene", "--out", "trace.jsonl"],
            "--hardware",
        ),
        (
            ["skill", "--hardware", "--skill", "survey_scene", "--out", "trace.jsonl"],
            "--human-supervised",
        ),
        (
            ["skill", "--hardware", "--human-supervised", "--skill", "survey_scene"],
            "--out",
        ),
        (
            [
                "skill",
                "--hardware",
                "--human-supervised",
                "--skill",
                "face_target",
                "--out",
                "trace.jsonl",
            ],
            "unsupported PM4 hardware skill",
        ),
    ],
)
def test_hardware_gates_fail_before_transport_construction(
    argv: list[str],
    message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    constructed = False

    def factory() -> FakeTransport:
        nonlocal constructed
        constructed = True
        return FakeTransport()

    code = skill_cli.main(argv, transport_factory=factory, clock_ms=lambda: 1000)

    assert code == skill_cli.EXIT_USAGE
    assert message in capsys.readouterr().err
    assert constructed is False


def test_command_construction_covers_exact_approved_skill_set() -> None:
    parser = skill_cli.build_parser()
    built = []
    for skill in skill_cli.APPROVED_PM4_SKILL_VALUES:
        args = parser.parse_args(
            [
                "skill",
                "--hardware",
                "--human-supervised",
                "--skill",
                skill,
                "--out",
                "trace.jsonl",
            ]
        )
        built.append(skill_cli.build_skill_command(args, issued_ms=1234).skill)

    assert tuple(str(skill) for skill in built) == skill_cli.APPROVED_PM4_SKILL_VALUES


def test_command_json_is_normalized_and_checked_against_pm4_scope(tmp_path: Path) -> None:
    command_json = tmp_path / "command.json"
    command_json.write_text(
        json.dumps(
            {
                "v": 1,
                "command_id": "json-survey",
                "issued_ms": 42,
                "skill": "survey_scene",
                "params": {"yaw_span_deg": 90, "timeout_ms": 3000},
            }
        ),
        encoding="utf-8",
    )
    args = skill_cli.build_parser().parse_args(
        [
            "skill",
            "--hardware",
            "--human-supervised",
            "--command-json",
            str(command_json),
            "--out",
            str(tmp_path / "trace.jsonl"),
        ]
    )

    command = skill_cli.build_skill_command(args, issued_ms=9999)

    assert command.command_id == "json-survey"
    assert command.issued_ms == 42
    assert command.skill == "survey_scene"


def test_successful_skill_run_writes_contract_trace_and_closes_transport(tmp_path: Path) -> None:
    out = tmp_path / "trace.jsonl"
    transport = FakeTransport()

    code = skill_cli.main(
        [
            "skill",
            "--hardware",
            "--human-supervised",
            "--skill",
            "survey_scene",
            "--duration-s",
            "3.0",
            "--out",
            str(out),
        ],
        transport_factory=lambda: transport,
        clock_ms=lambda: 555,
    )

    assert code == skill_cli.EXIT_OK
    assert transport.closed
    assert len(transport.dispatched) == 1
    command = transport.dispatched[0]
    assert command.command_id == "pm4-survey_scene-555"
    assert command.params.timeout_ms == 3000
    rows = _jsonl(out)
    assert [row["event"] for row in rows] == ["command", "result", "stop"]
    for row in rows:
        _TRACE_ADAPTER.validate_python(row)


def test_preflight_rejection_writes_result_and_stop_without_dispatch(tmp_path: Path) -> None:
    out = tmp_path / "trace.jsonl"
    transport = FakeTransport(
        preflight=TransportTerminalOutcome(
            status=CommandStatus.REJECTED,
            message="operator claw surface is unavailable",
            fault="operator_surface_unavailable",
        )
    )

    code = skill_cli.main(
        [
            "skill",
            "--hardware",
            "--human-supervised",
            "--skill",
            "claw_open",
            "--out",
            str(out),
        ],
        transport_factory=lambda: transport,
        clock_ms=lambda: 777,
    )

    assert code == skill_cli.EXIT_REJECTED
    assert transport.dispatched == []
    rows = _jsonl(out)
    assert [row["event"] for row in rows] == ["result", "stop"]
    assert rows[0]["result"]["status"] == "rejected"
    assert "unavailable" in rows[1]["message"]


def test_validation_rejection_writes_stop_before_dispatch(tmp_path: Path) -> None:
    out = tmp_path / "trace.jsonl"
    stale_observation = _healthy_observation().model_copy(
        update={"bridge": BridgeHealth(state="stale", last_heartbeat_age_ms=10)}
    )
    transport = FakeTransport(observation=stale_observation)

    code = skill_cli.main(
        [
            "skill",
            "--hardware",
            "--human-supervised",
            "--skill",
            "survey_scene",
            "--out",
            str(out),
        ],
        transport_factory=lambda: transport,
        clock_ms=lambda: 888,
    )

    assert code == skill_cli.EXIT_REJECTED
    assert transport.dispatched == []
    rows = _jsonl(out)
    assert [row["event"] for row in rows] == ["stop"]
    assert "bridge_stale" in rows[0]["message"]


def test_observe_subcommand_is_preserved_under_pilot_entrypoint(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def missing_ros() -> observe.RosRuntime:
        raise observe.ObserveCliError("delegated observe", observe.EXIT_ROS_DEPENDENCY)

    code = skill_cli.main(
        ["observe", "--objective", "collect", "--duration-s", "1"],
        observe_ros_loader=missing_ros,
    )

    assert code == observe.EXIT_ROS_DEPENDENCY
    assert "delegated observe" in capsys.readouterr().err


def test_parser_rejects_unknown_skill_before_transport(capsys: pytest.CaptureFixture[str]) -> None:
    constructed = False

    def factory() -> FakeTransport:
        nonlocal constructed
        constructed = True
        return FakeTransport()

    code = skill_cli.main(
        [
            "skill",
            "--hardware",
            "--human-supervised",
            "--skill",
            "not_a_skill",
            "--out",
            "trace.jsonl",
        ],
        transport_factory=factory,
    )

    assert code == skill_cli.EXIT_USAGE
    assert "unknown pilot skill" in capsys.readouterr().err
    assert constructed is False
