from __future__ import annotations

import dataclasses
import importlib
import sys

import pytest
from contracts import (
    ApproachTargetParams,
    ApproachTargetSkillCommand,
    BridgeHealth,
    LocalizationState,
    ManipulatorState,
    PilotObservation,
    PilotTaskPhase,
    StopSkillCommand,
    StopSkillParams,
)

from pilot.safety import (
    SafetyPolicy,
    ValidationMode,
    ValidationReasonCode,
    ValidationStatus,
    validate_skill_command,
)
from pilot.skills import get_skill_definition


def _motion_command() -> ApproachTargetSkillCommand:
    return ApproachTargetSkillCommand(
        command_id="cmd-approach",
        issued_ms=100,
        params=ApproachTargetParams(target_id="block-1"),
    )


def _stop_command() -> StopSkillCommand:
    return StopSkillCommand(
        command_id="cmd-stop",
        issued_ms=100,
        params=StopSkillParams(reason="unsafe"),
    )


def _observation(*, bridge: BridgeHealth | None = None) -> PilotObservation:
    return PilotObservation(
        observed_ms=120,
        task_phase=PilotTaskPhase.MANIPULATE,
        objective="pick up block-1",
        localization=LocalizationState(pose=None, confidence=0.8, age_ms=25),
        manipulator=ManipulatorState(arm_deg=20.0, claw_state="open"),
        bridge=bridge
        or BridgeHealth(
            state="ok",
            last_heartbeat_age_ms=25,
            estop=False,
            battery_pct=80.0,
        ),
    )


def _reason_codes(result: object) -> tuple[ValidationReasonCode, ...]:
    return tuple(reason.code for reason in result.reasons)


def test_safety_module_imports_without_ros_packages_and_exports_public_api(monkeypatch) -> None:
    ros_roots = {"rclpy", "std_msgs", "sensor_msgs", "geometry_msgs"}

    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            root = fullname.split(".", maxsplit=1)[0]
            if root in ros_roots:
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.safety", None)

    module = importlib.import_module("pilot.safety")
    import pilot

    assert module.validate_skill_command is not None
    assert module.ValidationMode.REPLAY.value == "replay"
    assert "validate_skill_command" in pilot.__all__
    assert "SafetyPolicy" in pilot.__all__
    assert ros_roots.isdisjoint(sys.modules)


def test_policy_reason_and_result_types_are_immutable() -> None:
    policy = SafetyPolicy(heartbeat_stale_after_ms=100)
    result = validate_skill_command(
        _motion_command(),
        _observation(),
        mode=ValidationMode.REPLAY,
        policy=policy,
    )

    assert dataclasses.is_dataclass(policy)
    assert dataclasses.is_dataclass(result)
    assert dataclasses.is_dataclass(result.reason)
    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.heartbeat_stale_after_ms = 200
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.status = ValidationStatus.REJECTED
    with pytest.raises(ValueError, match="heartbeat_stale_after_ms"):
        SafetyPolicy(heartbeat_stale_after_ms=-1)


def test_replay_mode_accepts_healthy_known_contract_command() -> None:
    command = _motion_command()
    observation = _observation()

    result = validate_skill_command(command, observation, mode="replay")

    assert get_skill_definition(command.skill).name.value == command.skill
    assert result.status is ValidationStatus.ACCEPTED
    assert result.accepted is True
    assert result.command == command
    assert result.mode is ValidationMode.REPLAY
    assert result.reason_code is ValidationReasonCode.OK
    assert result.message == "command accepted"


def test_hardware_mode_rejects_non_stop_without_human_supervision() -> None:
    result = validate_skill_command(
        _motion_command(),
        _observation(),
        mode=ValidationMode.HARDWARE,
        human_supervised=False,
    )

    assert result.status is ValidationStatus.REJECTED
    assert result.reason_code is ValidationReasonCode.HUMAN_SUPERVISION_REQUIRED
    assert result.message == "hardware mode requires human supervision"


def test_hardware_mode_accepts_non_stop_with_human_supervision() -> None:
    result = validate_skill_command(
        _motion_command(),
        _observation(),
        mode=ValidationMode.HARDWARE,
        human_supervised=True,
    )

    assert result.status is ValidationStatus.ACCEPTED
    assert result.reason_code is ValidationReasonCode.OK


@pytest.mark.parametrize(
    "bridge,expected_code",
    [
        (
            BridgeHealth(state="stale", last_heartbeat_age_ms=25),
            ValidationReasonCode.BRIDGE_STALE,
        ),
        (
            BridgeHealth(state="fault", last_heartbeat_age_ms=25, fault="serial fault"),
            ValidationReasonCode.BRIDGE_FAULT,
        ),
        (
            BridgeHealth(state="ok", last_heartbeat_age_ms=25, estop=True),
            ValidationReasonCode.ESTOP_ACTIVE,
        ),
        (
            BridgeHealth(state="ok", last_heartbeat_age_ms=None),
            ValidationReasonCode.HEARTBEAT_MISSING,
        ),
        (
            BridgeHealth(state="ok", last_heartbeat_age_ms=501),
            ValidationReasonCode.HEARTBEAT_STALE,
        ),
    ],
)
def test_non_stop_commands_reject_unsafe_bridge_health(
    bridge: BridgeHealth,
    expected_code: ValidationReasonCode,
) -> None:
    result = validate_skill_command(
        _motion_command(),
        _observation(bridge=bridge),
        mode=ValidationMode.REPLAY,
    )

    assert result.status is ValidationStatus.REJECTED
    assert expected_code in _reason_codes(result)


def test_heartbeat_threshold_uses_policy_value() -> None:
    observation = _observation(bridge=BridgeHealth(state="ok", last_heartbeat_age_ms=101))

    fresh = validate_skill_command(
        _motion_command(),
        observation,
        mode=ValidationMode.REPLAY,
        policy=SafetyPolicy(heartbeat_stale_after_ms=101),
    )
    stale = validate_skill_command(
        _motion_command(),
        observation,
        mode=ValidationMode.REPLAY,
        policy=SafetyPolicy(heartbeat_stale_after_ms=100),
    )

    assert fresh.status is ValidationStatus.ACCEPTED
    assert stale.status is ValidationStatus.REJECTED
    assert stale.reason_code is ValidationReasonCode.HEARTBEAT_STALE


def test_stop_remains_admissible_and_reports_unsafe_health() -> None:
    bridge = BridgeHealth(
        state="fault",
        last_heartbeat_age_ms=800,
        estop=True,
        fault="operator estop",
    )

    result = validate_skill_command(
        _stop_command(),
        _observation(bridge=bridge),
        mode=ValidationMode.HARDWARE,
        human_supervised=False,
    )

    assert result.status is ValidationStatus.ACCEPTED
    assert result.command == _stop_command()
    assert result.reason_code is ValidationReasonCode.BRIDGE_FAULT
    assert _reason_codes(result) == (
        ValidationReasonCode.BRIDGE_FAULT,
        ValidationReasonCode.ESTOP_ACTIVE,
        ValidationReasonCode.HEARTBEAT_STALE,
    )


def test_invalid_command_returns_stable_rejection_reason() -> None:
    result = validate_skill_command(
        {"v": 1, "command_id": "bad", "issued_ms": 1, "skill": "fly", "params": {}},
        _observation(),
        mode=ValidationMode.REPLAY,
    )

    assert result.status is ValidationStatus.REJECTED
    assert result.command is None
    assert result.reason_code is ValidationReasonCode.INVALID_COMMAND
