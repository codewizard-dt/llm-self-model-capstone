from __future__ import annotations

import dataclasses
import importlib
import sys
from dataclasses import replace

import pytest
from contracts import (
    ApproachTargetParams,
    ApproachTargetSkillCommand,
    ArmToAngleParams,
    ArmToAngleSkillCommand,
    AssertionEvidence,
    AssertionState,
    BridgeHealth,
    CenterObjectInGripperParams,
    CenterObjectInGripperSkillCommand,
    ClawCloseParams,
    ClawCloseSkillCommand,
    ClawOpenSkillCommand,
    CommandStatus,
    FaceTargetParams,
    FaceTargetSkillCommand,
    GoToDestinationParams,
    GoToDestinationSkillCommand,
    LocalizationState,
    ManipulatorState,
    MAX_ARM_RPM,
    MAX_CLAW_GRIP_FORCE_N,
    MAX_LINEAR,
    MAX_OMEGA,
    PilotAssertion,
    PilotFailure,
    PilotObservation,
    PilotSkillResult,
    PilotSkillName,
    PilotTaskPhase,
    Pose2D,
    StopSkillCommand,
    StopSkillParams,
    SurveySceneSkillCommand,
    VisibleObject,
    VisibleTag,
    VerifyDropParams,
    VerifyDropSkillCommand,
    VerifyGraspParams,
    VerifyGraspSkillCommand,
)

from pilot.safety import (
    SafetyPolicy,
    ValidationMode,
    ValidationReasonCode,
    ValidationStatus,
    validate_skill_command,
)
from pilot.skills import MovementEnvelope, get_skill_definition


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


def _observation(
    *,
    bridge: BridgeHealth | None = None,
    localization: LocalizationState | None = None,
    robot_pose: Pose2D | None = None,
    include_robot_pose: bool = True,
    visible_objects: list[VisibleObject] | None = None,
    visible_tags: list[VisibleTag] | None = None,
    manipulator: ManipulatorState | None = None,
    last_result: PilotSkillResult | None = None,
    recent_failures: list[PilotFailure] | None = None,
    current_assertions: list[PilotAssertion] | None = None,
) -> PilotObservation:
    pose = robot_pose or Pose2D(x_m=0.4, y_m=0.2, heading_rad=0.1)
    return PilotObservation(
        observed_ms=120,
        task_phase=PilotTaskPhase.MANIPULATE,
        objective="pick up block-1",
        robot_pose=pose if include_robot_pose else None,
        localization=localization or LocalizationState(pose=pose, confidence=0.8, age_ms=25),
        visible_objects=visible_objects
        if visible_objects is not None
        else [VisibleObject(object_id="block-1", label="block", confidence=0.9)],
        visible_tags=visible_tags if visible_tags is not None else [],
        manipulator=manipulator or ManipulatorState(arm_deg=20.0, claw_state="open"),
        bridge=bridge
        or BridgeHealth(
            state="ok",
            last_heartbeat_age_ms=25,
            estop=False,
            battery_pct=80.0,
        ),
        last_result=last_result,
        recent_failures=recent_failures if recent_failures is not None else [],
        current_assertions=current_assertions if current_assertions is not None else [],
    )


def _reason_codes(result: object) -> tuple[ValidationReasonCode, ...]:
    return tuple(reason.code for reason in result.reasons)


def _assertion(
    assertion_id: str,
    *,
    predicate: str,
    confidence: float = 0.9,
    age_ms: int = 25,
    summary: str | None = None,
) -> PilotAssertion:
    return PilotAssertion(
        assertion_id=assertion_id,
        predicate=predicate,
        state=AssertionState.TRUE,
        confidence=confidence,
        age_ms=age_ms,
        evidence=[
            AssertionEvidence(
                source="vision",
                summary=summary or predicate,
                confidence=confidence,
                age_ms=age_ms,
            )
        ],
    )


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


def test_pilot_package_exports_complete_safety_observation_and_registry_api() -> None:
    import pilot

    expected_exports = {
        "DEFAULT_SAFETY_POLICY",
        "SafetyPolicy",
        "ValidationMode",
        "ValidationReason",
        "ValidationReasonCode",
        "ValidationResult",
        "ValidationStatus",
        "validate_skill_command",
        "ObservationCache",
        "sorted_visible_objects",
        "get_skill_definition",
        "list_skill_definitions",
    }

    assert expected_exports <= set(pilot.__all__)
    for name in expected_exports:
        assert getattr(pilot, name) is not None


def test_validation_reason_code_values_are_stable() -> None:
    assert {code.value for code in ValidationReasonCode} == {
        "ok",
        "invalid_command",
        "invalid_observation",
        "unknown_skill",
        "registry_missing",
        "human_supervision_required",
        "bridge_stale",
        "bridge_fault",
        "estop_active",
        "heartbeat_missing",
        "heartbeat_stale",
        "command_rejected",
        "command_failed",
        "command_stale",
        "duration_envelope",
        "movement_envelope",
        "target_evidence",
        "destination_evidence",
        "localization_missing",
        "localization_stale",
        "localization_low_confidence",
        "verification_evidence",
    }


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


def test_replay_mode_accepts_raw_contract_mapping_without_supervision() -> None:
    command = _motion_command()

    result = validate_skill_command(
        command.model_dump(),
        _observation(),
        mode=ValidationMode.REPLAY,
        human_supervised=False,
    )

    assert result.status is ValidationStatus.ACCEPTED
    assert result.command == command
    assert result.reason_code is ValidationReasonCode.OK


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
    command = _motion_command()

    result = validate_skill_command(
        command.model_dump(),
        _observation(),
        mode=ValidationMode.HARDWARE,
        human_supervised=True,
    )

    assert result.status is ValidationStatus.ACCEPTED
    assert result.command == command
    assert result.mode is ValidationMode.HARDWARE
    assert result.skill is PilotSkillName.APPROACH_TARGET
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


@pytest.mark.parametrize(
    "last_result_status,expected_code",
    [
        (CommandStatus.REJECTED, ValidationReasonCode.COMMAND_REJECTED),
        (CommandStatus.FAILED, ValidationReasonCode.COMMAND_FAILED),
        (CommandStatus.STALE, ValidationReasonCode.COMMAND_STALE),
    ],
)
def test_non_stop_commands_reject_unsafe_command_result_health(
    last_result_status: CommandStatus,
    expected_code: ValidationReasonCode,
) -> None:
    result = validate_skill_command(
        _motion_command(),
        _observation(
            last_result=PilotSkillResult(
                command_id="cmd-previous",
                skill=PilotSkillName.APPROACH_TARGET,
                status=last_result_status,
                fault="bridge rejected command"
                if last_result_status is CommandStatus.REJECTED
                else None,
            )
        ),
        mode=ValidationMode.REPLAY,
    )

    assert result.status is ValidationStatus.REJECTED
    assert result.reason_code is expected_code


def test_non_stop_commands_reject_recent_command_failure_health() -> None:
    result = validate_skill_command(
        _motion_command(),
        _observation(
            recent_failures=[
                PilotFailure(
                    failed_ms=110,
                    source="command",
                    summary="previous command fault",
                    command_id="cmd-previous",
                )
            ]
        ),
        mode=ValidationMode.REPLAY,
    )

    assert result.status is ValidationStatus.REJECTED
    assert result.reason_code is ValidationReasonCode.COMMAND_FAILED


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


def test_stop_remains_admissible_and_reports_command_health() -> None:
    result = validate_skill_command(
        _stop_command(),
        _observation(
            last_result=PilotSkillResult(
                command_id="cmd-previous",
                skill=PilotSkillName.APPROACH_TARGET,
                status=CommandStatus.FAILED,
                fault="motor fault",
            )
        ),
        mode=ValidationMode.HARDWARE,
        human_supervised=False,
    )

    assert result.status is ValidationStatus.ACCEPTED
    assert result.reason_code is ValidationReasonCode.COMMAND_FAILED


def test_invalid_command_returns_stable_rejection_reason() -> None:
    result = validate_skill_command(
        {"v": 1, "command_id": "bad", "issued_ms": 1, "skill": "fly", "params": {}},
        _observation(),
        mode=ValidationMode.REPLAY,
    )

    assert result.status is ValidationStatus.REJECTED
    assert result.command is None
    assert result.reason_code is ValidationReasonCode.INVALID_COMMAND


def test_contract_invalid_oversized_raw_command_stays_invalid_command() -> None:
    oversized_commands = [
        {
            "v": 1,
            "command_id": "bad-speed",
            "issued_ms": 1,
            "skill": "approach_target",
            "params": {"target_id": "block-1", "max_speed_mps": MAX_LINEAR + 1.0},
        },
        {
            "v": 1,
            "command_id": "bad-opening",
            "issued_ms": 1,
            "skill": "claw_open",
            "params": {"opening_pct": 101.0},
        },
    ]

    for command in oversized_commands:
        result = validate_skill_command(command, _observation(), mode=ValidationMode.REPLAY)
        assert result.status is ValidationStatus.REJECTED
        assert result.reason_code is ValidationReasonCode.INVALID_COMMAND


def test_missing_registry_definition_returns_stable_registry_reason(monkeypatch) -> None:
    def missing_definition(name: PilotSkillName | str) -> object:
        raise KeyError(name)

    monkeypatch.setitem(
        validate_skill_command.__globals__, "get_skill_definition", missing_definition
    )

    result = validate_skill_command(_motion_command(), _observation(), mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.REJECTED
    assert result.skill is PilotSkillName.APPROACH_TARGET
    assert result.reason_code is ValidationReasonCode.REGISTRY_MISSING


def test_mismatched_registry_definition_returns_stable_registry_reason(monkeypatch) -> None:
    wrong_definition = get_skill_definition(PilotSkillName.STOP)
    monkeypatch.setitem(
        validate_skill_command.__globals__,
        "get_skill_definition",
        lambda name: wrong_definition,
    )

    result = validate_skill_command(_motion_command(), _observation(), mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.REJECTED
    assert result.skill is PilotSkillName.APPROACH_TARGET
    assert result.reason_code is ValidationReasonCode.REGISTRY_MISSING


def test_timeout_above_registry_duration_rejects_with_duration_reason() -> None:
    command = FaceTargetSkillCommand(
        command_id="cmd-face",
        issued_ms=100,
        params=FaceTargetParams(target_id="block-1", timeout_ms=4001),
    )

    result = validate_skill_command(command, _observation(), mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.REJECTED
    assert result.reason_code is ValidationReasonCode.DURATION_ENVELOPE


@pytest.mark.parametrize(
    "command,strict_movement",
    [
        (
            FaceTargetSkillCommand(
                command_id="cmd-turn",
                issued_ms=100,
                params=FaceTargetParams(target_id="block-1", max_turn_rad_s=MAX_OMEGA),
            ),
            MovementEnvelope(omega_rad_s=MAX_OMEGA / 2),
        ),
        (
            ApproachTargetSkillCommand(
                command_id="cmd-drive",
                issued_ms=100,
                params=ApproachTargetParams(target_id="block-1", max_speed_mps=MAX_LINEAR),
            ),
            MovementEnvelope(linear_mps=MAX_LINEAR / 2, omega_rad_s=MAX_OMEGA),
        ),
        (
            ArmToAngleSkillCommand(
                command_id="cmd-arm-angle",
                issued_ms=100,
                params=ArmToAngleParams(deg=40.0),
            ),
            MovementEnvelope(arm_deg_min=0.0, arm_deg_max=30.0, arm_rpm=MAX_ARM_RPM),
        ),
        (
            ArmToAngleSkillCommand(
                command_id="cmd-arm-velocity",
                issued_ms=100,
                params=ArmToAngleParams(deg=20.0, vel_rpm=MAX_ARM_RPM),
            ),
            MovementEnvelope(arm_deg_min=0.0, arm_deg_max=90.0, arm_rpm=MAX_ARM_RPM / 2),
        ),
        (
            ClawCloseSkillCommand(
                command_id="cmd-claw-force",
                issued_ms=100,
                params=ClawCloseParams(grip_force_n=MAX_CLAW_GRIP_FORCE_N),
            ),
            MovementEnvelope(claw_grip_force_n=MAX_CLAW_GRIP_FORCE_N / 2),
        ),
    ],
)
def test_registry_stricter_movement_envelopes_reject(
    monkeypatch,
    command: object,
    strict_movement: MovementEnvelope,
) -> None:
    base_definition = get_skill_definition(command.skill)
    strict_definition = replace(base_definition, movement=strict_movement)
    monkeypatch.setitem(
        validate_skill_command.__globals__,
        "get_skill_definition",
        lambda name: strict_definition,
    )

    result = validate_skill_command(command, _observation(), mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.REJECTED
    assert result.reason_code is ValidationReasonCode.MOVEMENT_ENVELOPE


@pytest.mark.parametrize(
    "command,observation,expected_code",
    [
        (
            FaceTargetSkillCommand(
                command_id="cmd-face-missing",
                issued_ms=100,
                params=FaceTargetParams(target_id="missing-block"),
            ),
            _observation(),
            ValidationReasonCode.TARGET_EVIDENCE,
        ),
        (
            CenterObjectInGripperSkillCommand(
                command_id="cmd-center-missing",
                issued_ms=100,
                params=CenterObjectInGripperParams(object_id="missing-block"),
            ),
            _observation(),
            ValidationReasonCode.TARGET_EVIDENCE,
        ),
        (
            GoToDestinationSkillCommand(
                command_id="cmd-dest-missing",
                issued_ms=100,
                params=GoToDestinationParams(destination_id="drop-zone"),
            ),
            _observation(),
            ValidationReasonCode.DESTINATION_EVIDENCE,
        ),
    ],
)
def test_target_and_destination_skills_require_current_evidence(
    command: object,
    observation: PilotObservation,
    expected_code: ValidationReasonCode,
) -> None:
    result = validate_skill_command(command, observation, mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.REJECTED
    assert result.reason_code is expected_code


def test_target_skill_rejects_stale_assertion_evidence() -> None:
    command = FaceTargetSkillCommand(
        command_id="cmd-face-stale-assertion",
        issued_ms=100,
        params=FaceTargetParams(target_id="block-2"),
    )
    observation = _observation(
        visible_objects=[],
        current_assertions=[
            _assertion(
                "assert.target.visible",
                predicate="block-2 target is visible",
                age_ms=1001,
            )
        ],
    )

    result = validate_skill_command(command, observation, mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.REJECTED
    assert result.reason_code is ValidationReasonCode.TARGET_EVIDENCE


def test_destination_id_accepts_current_assertion_evidence() -> None:
    command = GoToDestinationSkillCommand(
        command_id="cmd-dest",
        issued_ms=100,
        params=GoToDestinationParams(destination_id="drop-zone"),
    )
    observation = _observation(
        current_assertions=[
            _assertion(
                "assert.destination.visible",
                predicate="drop-zone destination is visible",
            )
        ]
    )

    result = validate_skill_command(command, observation, mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.ACCEPTED
    assert result.reason_code is ValidationReasonCode.OK


def test_symbolic_destination_navigation_rejects_stale_localization() -> None:
    pose = Pose2D(x_m=0.4, y_m=0.2, heading_rad=0.1)
    command = GoToDestinationSkillCommand(
        command_id="cmd-dest-stale-localization",
        issued_ms=100,
        params=GoToDestinationParams(destination_id="drop-zone"),
    )
    observation = _observation(
        localization=LocalizationState(pose=pose, confidence=0.9, age_ms=251),
        robot_pose=pose,
        current_assertions=[
            _assertion(
                "assert.destination.visible",
                predicate="drop-zone destination is visible",
            )
        ],
    )

    result = validate_skill_command(command, observation, mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.REJECTED
    assert result.reason_code is ValidationReasonCode.LOCALIZATION_STALE


@pytest.mark.parametrize(
    "localization,expected_code",
    [
        (
            LocalizationState(pose=None, confidence=0.9, age_ms=20),
            ValidationReasonCode.LOCALIZATION_MISSING,
        ),
        (
            LocalizationState(
                pose=Pose2D(x_m=0.4, y_m=0.2, heading_rad=0.1),
                confidence=0.9,
                age_ms=251,
            ),
            ValidationReasonCode.LOCALIZATION_STALE,
        ),
        (
            LocalizationState(
                pose=Pose2D(x_m=0.4, y_m=0.2, heading_rad=0.1),
                confidence=0.59,
                age_ms=20,
            ),
            ValidationReasonCode.LOCALIZATION_LOW_CONFIDENCE,
        ),
    ],
)
def test_coordinate_navigation_rejects_bad_localization(
    localization: LocalizationState,
    expected_code: ValidationReasonCode,
) -> None:
    command = GoToDestinationSkillCommand(
        command_id="cmd-coordinates",
        issued_ms=100,
        params=GoToDestinationParams(x_m=1.0, y_m=1.5),
    )
    observation = _observation(localization=localization, include_robot_pose=False)

    result = validate_skill_command(command, observation, mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.REJECTED
    assert result.reason_code is expected_code


def test_policy_controls_localization_thresholds() -> None:
    pose = Pose2D(x_m=0.4, y_m=0.2, heading_rad=0.1)
    command = GoToDestinationSkillCommand(
        command_id="cmd-coordinates",
        issued_ms=100,
        params=GoToDestinationParams(x_m=1.0, y_m=1.5),
    )
    observation = _observation(
        localization=LocalizationState(pose=pose, confidence=0.65, age_ms=300),
        robot_pose=pose,
    )

    accepted = validate_skill_command(
        command,
        observation,
        mode=ValidationMode.REPLAY,
        policy=SafetyPolicy(localization_stale_after_ms=300, localization_min_confidence=0.65),
    )
    stale = validate_skill_command(
        command,
        observation,
        mode=ValidationMode.REPLAY,
        policy=SafetyPolicy(localization_stale_after_ms=299, localization_min_confidence=0.65),
    )

    assert accepted.status is ValidationStatus.ACCEPTED
    assert stale.status is ValidationStatus.REJECTED
    assert stale.reason_code is ValidationReasonCode.LOCALIZATION_STALE


def test_verification_skills_use_manipulator_and_assertion_evidence_only() -> None:
    grasp = VerifyGraspSkillCommand(
        command_id="cmd-verify-grasp",
        issued_ms=100,
        params=VerifyGraspParams(object_id="block-1", min_confidence=0.7),
    )
    holding_observation = _observation(
        manipulator=ManipulatorState(
            arm_deg=20.0,
            claw_state="holding",
            held_object_id="block-1",
        )
    )
    missing_observation = _observation(
        manipulator=ManipulatorState(arm_deg=20.0, claw_state="closed")
    )
    assertion_observation = _observation(
        manipulator=ManipulatorState(arm_deg=20.0, claw_state="closed"),
        current_assertions=[
            _assertion(
                "assert.object_held",
                predicate="object is held",
                confidence=0.8,
            )
        ],
    )

    assert validate_skill_command(grasp, holding_observation, mode=ValidationMode.REPLAY).accepted
    assert validate_skill_command(grasp, assertion_observation, mode=ValidationMode.REPLAY).accepted

    rejected = validate_skill_command(grasp, missing_observation, mode=ValidationMode.REPLAY)
    assert rejected.status is ValidationStatus.REJECTED
    assert rejected.reason_code is ValidationReasonCode.VERIFICATION_EVIDENCE


def test_verify_drop_rejects_held_object_and_accepts_release_evidence() -> None:
    command = VerifyDropSkillCommand(command_id="cmd-verify-drop", issued_ms=100)
    holding_observation = _observation(
        manipulator=ManipulatorState(
            arm_deg=20.0,
            claw_state="holding",
            held_object_id="block-1",
        )
    )
    released_observation = _observation(
        manipulator=ManipulatorState(arm_deg=20.0, claw_state="open")
    )

    rejected = validate_skill_command(command, holding_observation, mode=ValidationMode.REPLAY)
    accepted = validate_skill_command(command, released_observation, mode=ValidationMode.REPLAY)

    assert rejected.status is ValidationStatus.REJECTED
    assert rejected.reason_code is ValidationReasonCode.VERIFICATION_EVIDENCE
    assert accepted.status is ValidationStatus.ACCEPTED


@pytest.mark.parametrize(
    "current_assertions",
    [
        [],
        [
            _assertion(
                "assert.destination.visible",
                predicate="drop-zone destination is visible",
                age_ms=1001,
            )
        ],
        [
            _assertion(
                "assert.destination.visible",
                predicate="drop-zone destination is visible",
                confidence=0.6,
            )
        ],
    ],
)
def test_destination_specific_verify_drop_requires_current_destination_evidence(
    current_assertions: list[PilotAssertion],
) -> None:
    command = VerifyDropSkillCommand(
        command_id="cmd-verify-drop-destination",
        issued_ms=100,
        params=VerifyDropParams(destination_id="drop-zone", min_confidence=0.7),
    )
    observation = _observation(
        manipulator=ManipulatorState(arm_deg=20.0, claw_state="open"),
        current_assertions=current_assertions,
    )

    result = validate_skill_command(command, observation, mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.REJECTED
    assert result.reason_code is ValidationReasonCode.VERIFICATION_EVIDENCE


def test_destination_specific_verify_drop_accepts_current_destination_evidence() -> None:
    command = VerifyDropSkillCommand(
        command_id="cmd-verify-drop-destination-ok",
        issued_ms=100,
        params=VerifyDropParams(destination_id="drop-zone", min_confidence=0.7),
    )
    observation = _observation(
        manipulator=ManipulatorState(arm_deg=20.0, claw_state="open"),
        current_assertions=[
            _assertion(
                "assert.destination.visible",
                predicate="drop-zone destination is visible",
                confidence=0.8,
            )
        ],
    )

    result = validate_skill_command(command, observation, mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.ACCEPTED
    assert result.reason_code is ValidationReasonCode.OK


@pytest.mark.parametrize(
    "command,observation",
    [
        (
            StopSkillCommand(
                command_id="cmd-stop-ok",
                issued_ms=100,
                params=StopSkillParams(reason="operator"),
            ),
            _observation(),
        ),
        (SurveySceneSkillCommand(command_id="cmd-survey", issued_ms=100), _observation()),
        (
            FaceTargetSkillCommand(
                command_id="cmd-face-ok",
                issued_ms=100,
                params=FaceTargetParams(target_id="tag-3"),
            ),
            _observation(
                visible_objects=[],
                visible_tags=[VisibleTag(tag_id=3, confidence=0.95)],
            ),
        ),
        (_motion_command(), _observation()),
        (
            CenterObjectInGripperSkillCommand(
                command_id="cmd-center-ok",
                issued_ms=100,
                params=CenterObjectInGripperParams(object_id="block-1"),
            ),
            _observation(),
        ),
        (
            ArmToAngleSkillCommand(
                command_id="cmd-arm-ok",
                issued_ms=100,
                params=ArmToAngleParams(deg=20.0),
            ),
            _observation(),
        ),
        (ClawOpenSkillCommand(command_id="cmd-open-ok", issued_ms=100), _observation()),
        (ClawCloseSkillCommand(command_id="cmd-close-ok", issued_ms=100), _observation()),
        (
            VerifyGraspSkillCommand(command_id="cmd-grasp-ok", issued_ms=100),
            _observation(
                manipulator=ManipulatorState(
                    arm_deg=20.0,
                    claw_state="holding",
                    held_object_id="block-1",
                )
            ),
        ),
        (
            GoToDestinationSkillCommand(
                command_id="cmd-go-ok",
                issued_ms=100,
                params=GoToDestinationParams(x_m=1.0, y_m=1.5),
            ),
            _observation(),
        ),
        (
            VerifyDropSkillCommand(command_id="cmd-drop-ok", issued_ms=100),
            _observation(manipulator=ManipulatorState(arm_deg=20.0, claw_state="open")),
        ),
    ],
)
def test_every_pilot_skill_has_an_accepting_validation_path(
    command: object,
    observation: PilotObservation,
) -> None:
    result = validate_skill_command(command, observation, mode=ValidationMode.REPLAY)

    assert result.status is ValidationStatus.ACCEPTED
    assert result.reason_code is ValidationReasonCode.OK
