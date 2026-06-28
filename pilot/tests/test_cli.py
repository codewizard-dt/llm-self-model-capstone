from __future__ import annotations

import importlib
import io
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

from contracts import CommandStatus, PilotObservation, PilotSkillName, SurveySceneSkillCommand

from pilot.cli import CliDependencies, run
from pilot.executor import ExecutionResult
from pilot.safety import (
    ValidationMode,
    ValidationReason,
    ValidationReasonCode,
    ValidationResult,
    ValidationStatus,
    validate_skill_command,
)


ROOT = Path(__file__).resolve().parents[1]


def _accepted(command: object) -> ValidationResult:
    return ValidationResult(
        status=ValidationStatus.ACCEPTED,
        command=command,
        mode=ValidationMode.HARDWARE,
        skill=PilotSkillName.SURVEY_SCENE,
        reasons=(ValidationReason(ValidationReasonCode.OK, "command accepted"),),
    )


def _execution_result(command_id: str = "pilot-survey_scene-123456") -> ExecutionResult:
    return ExecutionResult(
        command_id=command_id,
        skill=PilotSkillName.SURVEY_SCENE,
        status=CommandStatus.OK,
        reason_code="terminal_ok",
        message="terminal transport result ok: survey complete",
        issued_ms=123456,
        completed_ms=124000,
    )


def _run_cli(args: list[str], deps: CliDependencies) -> tuple[int, dict[str, object], str]:
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = run(args, deps=deps, stdout=stdout, stderr=stderr)

    payload = json.loads(stdout.getvalue()) if stdout.getvalue() else {}
    return code, payload, stderr.getvalue()


def test_cli_module_imports_without_ros_packages() -> None:
    ros_roots = {"rclpy", "std_msgs", "sensor_msgs", "geometry_msgs"}

    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            root = fullname.split(".", maxsplit=1)[0]
            if root in ros_roots:
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    original_meta_path = list(sys.meta_path)
    try:
        sys.meta_path = [RejectRosImports(), *sys.meta_path]
        sys.modules.pop("pilot.cli", None)

        module = importlib.import_module("pilot.cli")
    finally:
        sys.meta_path = original_meta_path

    assert module.main is not None
    assert module.run is not None
    assert ros_roots.isdisjoint(sys.modules)


def test_pyproject_exposes_pilot_console_script() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert pyproject["project"]["scripts"]["pilot"] == "pilot.cli:main"


def test_packaged_console_command_imports_contracts_without_pythonpath() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["UV_NO_PROGRESS"] = "1"

    completed = subprocess.run(
        [
            "uv",
            "run",
            "--frozen",
            "pilot",
            "skill",
            "--hardware",
            "--skill",
            "survey_scene",
            "--duration-s",
            "3.0",
        ],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert "Traceback" not in completed.stderr
    assert "ModuleNotFoundError" not in completed.stderr
    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert str(payload["command_id"]).startswith("pilot-survey_scene-")
    assert payload["skill"] == "survey_scene"
    assert payload["status"] == "failed"
    assert payload["reason_code"] == "transport_failed"
    assert (
        payload["message"]
        == "transport boundary failed: hardware transport is not configured for the pilot CLI"
    )


def test_hardware_survey_cli_constructs_contract_command_and_executes_accepted_validation() -> None:
    validator_calls: list[dict[str, object]] = []
    executor_calls: list[ValidationResult] = []

    def validator(command: object, observation: object, **kwargs: object) -> ValidationResult:
        validator_calls.append(
            {
                "command": command,
                "observation": observation,
                **kwargs,
            }
        )
        return _accepted(command)

    def executor(validation: ValidationResult) -> ExecutionResult:
        executor_calls.append(validation)
        assert validation.command is not None
        return _execution_result(validation.command.command_id)

    code, payload, stderr = _run_cli(
        ["skill", "--hardware", "--skill", "survey_scene", "--duration-s", "3.0"],
        CliDependencies(clock_ms=lambda: 123456, validator=validator, executor=executor),
    )

    assert code == 0
    assert stderr == ""
    assert len(validator_calls) == 1
    command = validator_calls[0]["command"]
    observation = validator_calls[0]["observation"]
    assert isinstance(command, SurveySceneSkillCommand)
    assert command.command_id == "pilot-survey_scene-123456"
    assert command.issued_ms == 123456
    assert command.params.timeout_ms == 3000
    assert command.params.yaw_span_deg == 180.0
    assert isinstance(observation, PilotObservation)
    assert observation.bridge.state == "ok"
    assert validator_calls[0]["mode"] is ValidationMode.HARDWARE
    assert validator_calls[0]["human_supervised"] is True
    assert len(executor_calls) == 1
    assert executor_calls[0].command == command
    assert payload == {
        "command_id": "pilot-survey_scene-123456",
        "skill": "survey_scene",
        "status": "ok",
        "reason_code": "terminal_ok",
        "message": "terminal transport result ok: survey complete",
    }


def test_replay_survey_cli_uses_replay_mode_without_hardware_supervision() -> None:
    validator_calls: list[dict[str, object]] = []

    def validator(command: object, observation: object, **kwargs: object) -> ValidationResult:
        validator_calls.append(kwargs)
        return _accepted(command)

    code, payload, _stderr = _run_cli(
        ["skill", "--skill", "survey_scene", "--duration-s", "3"],
        CliDependencies(
            clock_ms=lambda: 123456,
            validator=validator,
            executor=lambda _validation: _execution_result(),
        ),
    )

    assert code == 0
    assert payload["status"] == "ok"
    assert validator_calls == [{"mode": ValidationMode.REPLAY, "human_supervised": False}]


def test_missing_hardware_supervision_refuses_before_executor() -> None:
    executor_calls: list[ValidationResult] = []

    code, payload, stderr = _run_cli(
        [
            "skill",
            "--hardware",
            "--no-supervision",
            "--skill",
            "survey_scene",
            "--duration-s",
            "3.0",
        ],
        CliDependencies(
            clock_ms=lambda: 123456,
            validator=validate_skill_command,
            executor=executor_calls.append,
        ),
    )

    assert code == 1
    assert stderr == ""
    assert executor_calls == []
    assert payload == {
        "command_id": "pilot-survey_scene-123456",
        "skill": "survey_scene",
        "status": "rejected",
        "reason_code": "human_supervision_required",
        "message": "hardware mode requires human supervision",
    }


def test_validation_refusal_reports_reason_and_does_not_execute() -> None:
    executor_calls: list[ValidationResult] = []

    def validator(command: object, observation: object, **kwargs: object) -> ValidationResult:
        return ValidationResult(
            status=ValidationStatus.STOPPED,
            command=command,
            mode=kwargs["mode"],
            skill=PilotSkillName.SURVEY_SCENE,
            reasons=(ValidationReason(ValidationReasonCode.BRIDGE_STALE, "bridge state is stale"),),
        )

    code, payload, stderr = _run_cli(
        ["skill", "--hardware", "--skill", "survey_scene", "--duration-s", "3"],
        CliDependencies(
            clock_ms=lambda: 123456, validator=validator, executor=executor_calls.append
        ),
    )

    assert code == 1
    assert stderr == ""
    assert executor_calls == []
    assert payload["command_id"] == "pilot-survey_scene-123456"
    assert payload["skill"] == "survey_scene"
    assert payload["status"] == "stopped"
    assert payload["reason_code"] == "bridge_stale"
    assert payload["message"] == "bridge state is stale"


def test_unsupported_skill_fails_in_parser_before_validation_or_execution() -> None:
    calls: list[object] = []
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = run(
        ["skill", "--hardware", "--skill", "face_target", "--duration-s", "3"],
        deps=CliDependencies(
            validator=lambda *args, **kwargs: calls.append(args),  # type: ignore[arg-type]
            executor=lambda validation: calls.append(validation),  # type: ignore[arg-type]
        ),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 2
    assert stdout.getvalue() == ""
    assert "invalid choice" in stderr.getvalue()
    assert calls == []


def test_invalid_duration_reports_deterministic_argument_error() -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = run(
        ["skill", "--hardware", "--skill", "survey_scene", "--duration-s", "0"],
        deps=CliDependencies(clock_ms=lambda: 123456),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 2
    assert stdout.getvalue() == ""
    assert "--duration-s must be greater than zero" in stderr.getvalue()
