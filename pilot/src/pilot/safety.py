"""ROS-free safety validation for pilot skill commands."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from pydantic import TypeAdapter, ValidationError

from contracts import AssertionState, PilotObservation, PilotSkillCommand, PilotSkillName
from pilot.skills import SkillDefinition, get_skill_definition


class ValidationMode(StrEnum):
    """Execution context for safety policy."""

    REPLAY = "replay"
    HARDWARE = "hardware"


class ValidationStatus(StrEnum):
    """Deterministic validator outcome."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    STOPPED = "stopped"


class ValidationReasonCode(StrEnum):
    """Stable reason codes for executor, logger, replay, and tests."""

    OK = "ok"
    INVALID_COMMAND = "invalid_command"
    INVALID_OBSERVATION = "invalid_observation"
    UNKNOWN_SKILL = "unknown_skill"
    REGISTRY_MISSING = "registry_missing"
    HUMAN_SUPERVISION_REQUIRED = "human_supervision_required"
    BRIDGE_STALE = "bridge_stale"
    BRIDGE_FAULT = "bridge_fault"
    ESTOP_ACTIVE = "estop_active"
    HEARTBEAT_MISSING = "heartbeat_missing"
    HEARTBEAT_STALE = "heartbeat_stale"
    DURATION_ENVELOPE = "duration_envelope"
    MOVEMENT_ENVELOPE = "movement_envelope"
    TARGET_EVIDENCE = "target_evidence"
    DESTINATION_EVIDENCE = "destination_evidence"
    LOCALIZATION_MISSING = "localization_missing"
    LOCALIZATION_STALE = "localization_stale"
    LOCALIZATION_LOW_CONFIDENCE = "localization_low_confidence"
    VERIFICATION_EVIDENCE = "verification_evidence"


@dataclass(frozen=True, slots=True)
class SafetyPolicy:
    """Policy thresholds for core command safety gates."""

    heartbeat_stale_after_ms: int = 500
    localization_stale_after_ms: int = 250
    localization_min_confidence: float = 0.60
    evidence_stale_after_ms: int = 1000
    require_hardware_supervision: bool = True

    def __post_init__(self) -> None:
        if self.heartbeat_stale_after_ms < 0:
            raise ValueError("heartbeat_stale_after_ms must be non-negative")
        if self.localization_stale_after_ms < 0:
            raise ValueError("localization_stale_after_ms must be non-negative")
        if not 0.0 <= self.localization_min_confidence <= 1.0:
            raise ValueError("localization_min_confidence must be between 0.0 and 1.0")
        if self.evidence_stale_after_ms < 0:
            raise ValueError("evidence_stale_after_ms must be non-negative")


@dataclass(frozen=True, slots=True)
class ValidationReason:
    """Machine-readable reason with a concise human-readable message."""

    code: ValidationReasonCode
    message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Safety validation result for a normalized pilot skill command."""

    status: ValidationStatus
    command: PilotSkillCommand | None
    mode: ValidationMode | None
    skill: PilotSkillName | None
    reasons: tuple[ValidationReason, ...]

    @property
    def accepted(self) -> bool:
        return self.status is ValidationStatus.ACCEPTED

    @property
    def reason(self) -> ValidationReason:
        return self.reasons[0]

    @property
    def reason_code(self) -> ValidationReasonCode:
        return self.reason.code

    @property
    def message(self) -> str:
        return self.reason.message


DEFAULT_SAFETY_POLICY: Final = SafetyPolicy()
_SKILL_COMMAND_ADAPTER: Final[TypeAdapter[PilotSkillCommand]] = TypeAdapter(PilotSkillCommand)


def validate_skill_command(
    command: object,
    observation: object,
    *,
    mode: ValidationMode | str,
    policy: SafetyPolicy = DEFAULT_SAFETY_POLICY,
    human_supervised: bool = False,
) -> ValidationResult:
    """Validate a contract command against core pilot safety policy."""

    validation_mode = ValidationMode(mode)
    normalized_command = _normalize_command(command)
    if normalized_command is None:
        return _result(
            ValidationStatus.REJECTED,
            command=None,
            mode=validation_mode,
            skill=None,
            reasons=(
                ValidationReason(
                    ValidationReasonCode.INVALID_COMMAND,
                    "command is not a contract-valid pilot skill command",
                ),
            ),
        )

    try:
        normalized_observation = PilotObservation.model_validate(observation)
    except ValidationError:
        return _result(
            ValidationStatus.REJECTED,
            command=normalized_command,
            mode=validation_mode,
            skill=_skill_name(normalized_command),
            reasons=(
                ValidationReason(
                    ValidationReasonCode.INVALID_OBSERVATION,
                    "observation is not a contract-valid pilot observation",
                ),
            ),
        )

    try:
        skill = _skill_name(normalized_command)
        definition = get_skill_definition(skill)
    except (KeyError, ValueError):
        return _result(
            ValidationStatus.REJECTED,
            command=normalized_command,
            mode=validation_mode,
            skill=skill if "skill" in locals() else None,
            reasons=(
                ValidationReason(
                    ValidationReasonCode.REGISTRY_MISSING,
                    "pilot skill is not registered",
                ),
            ),
        )
    if definition.name is not skill:
        return _result(
            ValidationStatus.REJECTED,
            command=normalized_command,
            mode=validation_mode,
            skill=skill,
            reasons=(
                ValidationReason(
                    ValidationReasonCode.REGISTRY_MISSING,
                    "pilot skill registry returned a mismatched definition",
                ),
            ),
        )

    health_reasons = _bridge_health_reasons(normalized_observation, policy=policy)
    if skill is PilotSkillName.STOP:
        return _result(
            ValidationStatus.ACCEPTED,
            command=normalized_command,
            mode=validation_mode,
            skill=skill,
            reasons=health_reasons or (_ok_reason(),),
        )

    gate_reasons: list[ValidationReason] = []
    if (
        validation_mode is ValidationMode.HARDWARE
        and policy.require_hardware_supervision
        and not human_supervised
    ):
        gate_reasons.append(
            ValidationReason(
                ValidationReasonCode.HUMAN_SUPERVISION_REQUIRED,
                "hardware mode requires human supervision",
            )
        )
    gate_reasons.extend(health_reasons)

    if gate_reasons:
        return _result(
            ValidationStatus.REJECTED,
            command=normalized_command,
            mode=validation_mode,
            skill=skill,
            reasons=tuple(gate_reasons),
        )

    skill_reasons = _skill_rule_reasons(
        normalized_command,
        normalized_observation,
        definition=definition,
        policy=policy,
    )
    if skill_reasons:
        return _result(
            ValidationStatus.REJECTED,
            command=normalized_command,
            mode=validation_mode,
            skill=skill,
            reasons=skill_reasons,
        )

    return _result(
        ValidationStatus.ACCEPTED,
        command=normalized_command,
        mode=validation_mode,
        skill=skill,
        reasons=(_ok_reason(),),
    )


def _normalize_command(command: object) -> PilotSkillCommand | None:
    try:
        return _SKILL_COMMAND_ADAPTER.validate_python(command)
    except ValidationError:
        return None


def _skill_name(command: PilotSkillCommand) -> PilotSkillName:
    return PilotSkillName(str(command.skill))


def _bridge_health_reasons(
    observation: PilotObservation,
    *,
    policy: SafetyPolicy,
) -> tuple[ValidationReason, ...]:
    bridge = observation.bridge
    reasons: list[ValidationReason] = []

    if bridge.state == "stale":
        reasons.append(ValidationReason(ValidationReasonCode.BRIDGE_STALE, "bridge state is stale"))
    elif bridge.state == "fault":
        reasons.append(ValidationReason(ValidationReasonCode.BRIDGE_FAULT, "bridge state is fault"))

    if bridge.estop:
        reasons.append(ValidationReason(ValidationReasonCode.ESTOP_ACTIVE, "estop is active"))

    if bridge.last_heartbeat_age_ms is None:
        reasons.append(
            ValidationReason(
                ValidationReasonCode.HEARTBEAT_MISSING,
                "bridge heartbeat age is missing",
            )
        )
    elif bridge.last_heartbeat_age_ms > policy.heartbeat_stale_after_ms:
        reasons.append(
            ValidationReason(
                ValidationReasonCode.HEARTBEAT_STALE,
                "bridge heartbeat is stale",
            )
        )

    return tuple(reasons)


def _skill_rule_reasons(
    command: PilotSkillCommand,
    observation: PilotObservation,
    *,
    definition: SkillDefinition,
    policy: SafetyPolicy,
) -> tuple[ValidationReason, ...]:
    reasons: list[ValidationReason] = []
    reasons.extend(_duration_reasons(command, definition))
    reasons.extend(_movement_reasons(command, definition))

    if reasons:
        return tuple(reasons)

    skill = definition.name
    match skill:
        case PilotSkillName.STOP:
            return ()
        case PilotSkillName.SURVEY_SCENE:
            return ()
        case PilotSkillName.FACE_TARGET:
            return _face_target_reasons(command, observation, policy=policy)
        case PilotSkillName.APPROACH_TARGET:
            return _approach_target_reasons(command, observation, policy=policy)
        case PilotSkillName.CENTER_OBJECT_IN_GRIPPER:
            return _center_object_reasons(command, observation)
        case PilotSkillName.ARM_TO_ANGLE:
            return ()
        case PilotSkillName.CLAW_OPEN:
            return ()
        case PilotSkillName.CLAW_CLOSE:
            return ()
        case PilotSkillName.VERIFY_GRASP:
            return _verify_grasp_reasons(command, observation, policy=policy)
        case PilotSkillName.GO_TO_DESTINATION:
            return _go_to_destination_reasons(command, observation, policy=policy)
        case PilotSkillName.VERIFY_DROP:
            return _verify_drop_reasons(command, observation, policy=policy)


def _duration_reasons(
    command: PilotSkillCommand,
    definition: SkillDefinition,
) -> tuple[ValidationReason, ...]:
    timeout_ms = getattr(command.params, "timeout_ms", None)
    if timeout_ms is not None and timeout_ms > definition.max_duration_ms:
        return (
            ValidationReason(
                ValidationReasonCode.DURATION_ENVELOPE,
                f"{definition.name.value} timeout exceeds registry max duration",
            ),
        )
    return ()


def _movement_reasons(
    command: PilotSkillCommand,
    definition: SkillDefinition,
) -> tuple[ValidationReason, ...]:
    movement = definition.movement
    params = command.params
    reasons: list[ValidationReason] = []

    max_speed_mps = getattr(params, "max_speed_mps", None)
    if max_speed_mps is not None and max_speed_mps > movement.linear_mps:
        reasons.append(
            ValidationReason(
                ValidationReasonCode.MOVEMENT_ENVELOPE,
                f"{definition.name.value} speed exceeds registry movement envelope",
            )
        )

    max_turn_rad_s = getattr(params, "max_turn_rad_s", None)
    if max_turn_rad_s is not None and max_turn_rad_s > movement.omega_rad_s:
        reasons.append(
            ValidationReason(
                ValidationReasonCode.MOVEMENT_ENVELOPE,
                f"{definition.name.value} turn rate exceeds registry movement envelope",
            )
        )

    deg = getattr(params, "deg", None)
    if deg is not None and (
        movement.arm_deg_min is None
        or movement.arm_deg_max is None
        or not movement.arm_deg_min <= deg <= movement.arm_deg_max
    ):
        reasons.append(
            ValidationReason(
                ValidationReasonCode.MOVEMENT_ENVELOPE,
                f"{definition.name.value} arm angle exceeds registry movement envelope",
            )
        )

    vel_rpm = getattr(params, "vel_rpm", None)
    if vel_rpm is not None and (movement.arm_rpm is None or vel_rpm > movement.arm_rpm):
        reasons.append(
            ValidationReason(
                ValidationReasonCode.MOVEMENT_ENVELOPE,
                f"{definition.name.value} arm velocity exceeds registry movement envelope",
            )
        )

    grip_force_n = getattr(params, "grip_force_n", None)
    if grip_force_n is not None and (
        movement.claw_grip_force_n is None or grip_force_n > movement.claw_grip_force_n
    ):
        reasons.append(
            ValidationReason(
                ValidationReasonCode.MOVEMENT_ENVELOPE,
                f"{definition.name.value} claw force exceeds registry movement envelope",
            )
        )

    opening_pct = getattr(params, "opening_pct", None)
    if opening_pct is not None and not 0.0 <= opening_pct <= 100.0:
        reasons.append(
            ValidationReason(
                ValidationReasonCode.MOVEMENT_ENVELOPE,
                f"{definition.name.value} claw opening exceeds registry movement envelope",
            )
        )

    return tuple(reasons)


def _face_target_reasons(
    command: PilotSkillCommand,
    observation: PilotObservation,
    *,
    policy: SafetyPolicy,
) -> tuple[ValidationReason, ...]:
    target_id = command.params.target_id
    if not _has_named_target_evidence(observation, target_id, policy=policy):
        return (
            ValidationReason(
                ValidationReasonCode.TARGET_EVIDENCE,
                "face_target requires current target evidence",
            ),
        )
    return ()


def _approach_target_reasons(
    command: PilotSkillCommand,
    observation: PilotObservation,
    *,
    policy: SafetyPolicy,
) -> tuple[ValidationReason, ...]:
    localization_reasons = _localization_reasons(observation, policy=policy)
    if localization_reasons:
        return localization_reasons

    target_id = command.params.target_id
    if not _has_named_target_evidence(observation, target_id, policy=policy):
        return (
            ValidationReason(
                ValidationReasonCode.TARGET_EVIDENCE,
                "approach_target requires current target evidence",
            ),
        )
    return ()


def _center_object_reasons(
    command: PilotSkillCommand,
    observation: PilotObservation,
) -> tuple[ValidationReason, ...]:
    object_id = command.params.object_id
    if not any(visible.object_id == object_id for visible in observation.visible_objects):
        return (
            ValidationReason(
                ValidationReasonCode.TARGET_EVIDENCE,
                "center_object_in_gripper requires the named visible object",
            ),
        )
    return ()


def _go_to_destination_reasons(
    command: PilotSkillCommand,
    observation: PilotObservation,
    *,
    policy: SafetyPolicy,
) -> tuple[ValidationReason, ...]:
    params = command.params
    localization_reasons = _localization_reasons(observation, policy=policy)
    if localization_reasons:
        return localization_reasons

    if params.destination_id is not None and not _has_named_destination_evidence(
        observation,
        params.destination_id,
        policy=policy,
    ):
        return (
            ValidationReason(
                ValidationReasonCode.DESTINATION_EVIDENCE,
                "go_to_destination requires destination evidence or coordinates",
            ),
        )
    return ()


def _verify_grasp_reasons(
    command: PilotSkillCommand,
    observation: PilotObservation,
    *,
    policy: SafetyPolicy,
) -> tuple[ValidationReason, ...]:
    params = command.params
    held_object_id = observation.manipulator.held_object_id
    manipulator_matches = observation.manipulator.claw_state == "holding" and (
        params.object_id is None or held_object_id == params.object_id
    )
    if manipulator_matches:
        return ()

    if _has_success_assertion(
        observation,
        "assert.object_held",
        min_confidence=params.min_confidence,
        policy=policy,
    ):
        return ()

    return (
        ValidationReason(
            ValidationReasonCode.VERIFICATION_EVIDENCE,
            "verify_grasp requires manipulator or assertion evidence for a held object",
        ),
    )


def _verify_drop_reasons(
    command: PilotSkillCommand,
    observation: PilotObservation,
    *,
    policy: SafetyPolicy,
) -> tuple[ValidationReason, ...]:
    params = command.params
    manipulator_released = (
        observation.manipulator.claw_state in {"open", "unknown"}
        and observation.manipulator.held_object_id is None
    )
    if params.destination_id is not None and not _has_named_destination_evidence(
        observation,
        params.destination_id,
        policy=policy,
        min_confidence=params.min_confidence,
    ):
        return (
            ValidationReason(
                ValidationReasonCode.VERIFICATION_EVIDENCE,
                "verify_drop requires current destination evidence for destination-specific release",
            ),
        )

    if manipulator_released:
        return ()

    if _has_success_assertion(
        observation,
        "assert.object_dropped",
        min_confidence=params.min_confidence,
        policy=policy,
    ):
        return ()

    return (
        ValidationReason(
            ValidationReasonCode.VERIFICATION_EVIDENCE,
            "verify_drop requires manipulator or assertion evidence for a released object",
        ),
    )


def _localization_reasons(
    observation: PilotObservation,
    *,
    policy: SafetyPolicy,
) -> tuple[ValidationReason, ...]:
    localization = observation.localization
    if localization.pose is None and observation.robot_pose is None:
        return (
            ValidationReason(
                ValidationReasonCode.LOCALIZATION_MISSING,
                "navigation requires a localized robot pose",
            ),
        )
    if localization.age_ms > policy.localization_stale_after_ms:
        return (
            ValidationReason(
                ValidationReasonCode.LOCALIZATION_STALE,
                "navigation localization is stale",
            ),
        )
    if localization.confidence < policy.localization_min_confidence:
        return (
            ValidationReason(
                ValidationReasonCode.LOCALIZATION_LOW_CONFIDENCE,
                "navigation localization confidence is too low",
            ),
        )
    return ()


def _has_named_target_evidence(
    observation: PilotObservation,
    name: str,
    *,
    policy: SafetyPolicy,
) -> bool:
    return (
        any(visible.object_id == name for visible in observation.visible_objects)
        or any(_tag_matches(visible.tag_id, name) for visible in observation.visible_tags)
        or _has_named_assertion_evidence(observation, name, policy=policy)
    )


def _has_named_destination_evidence(
    observation: PilotObservation,
    destination_id: str,
    *,
    policy: SafetyPolicy,
    min_confidence: float = 0.0,
) -> bool:
    return any(
        _tag_matches(visible.tag_id, destination_id) and visible.confidence >= min_confidence
        for visible in observation.visible_tags
    ) or (
        _has_named_assertion_evidence(
            observation,
            destination_id,
            policy=policy,
            min_confidence=min_confidence,
        )
    )


def _has_named_assertion_evidence(
    observation: PilotObservation,
    name: str,
    *,
    policy: SafetyPolicy,
    min_confidence: float = 0.0,
) -> bool:
    needle = name.casefold()
    for assertion in observation.current_assertions:
        if assertion.state is not AssertionState.TRUE:
            continue
        if assertion.confidence < min_confidence:
            continue
        if assertion.age_ms is not None and assertion.age_ms > policy.evidence_stale_after_ms:
            continue
        haystack = " ".join(
            (
                assertion.assertion_id,
                assertion.predicate,
                *(evidence.summary for evidence in assertion.evidence),
            )
        ).casefold()
        if needle in haystack:
            return True
    return False


def _has_success_assertion(
    observation: PilotObservation,
    assertion_id: str,
    *,
    min_confidence: float,
    policy: SafetyPolicy,
) -> bool:
    for assertion in observation.current_assertions:
        if assertion.assertion_id != assertion_id:
            continue
        if assertion.state is not AssertionState.TRUE:
            continue
        if assertion.confidence < min_confidence:
            continue
        if assertion.age_ms is not None and assertion.age_ms > policy.evidence_stale_after_ms:
            continue
        return True
    return False


def _tag_matches(tag_id: int, requested_id: str) -> bool:
    return requested_id in {str(tag_id), f"tag-{tag_id}", f"apriltag-{tag_id}"}


def _ok_reason() -> ValidationReason:
    return ValidationReason(ValidationReasonCode.OK, "command accepted")


def _result(
    status: ValidationStatus,
    *,
    command: PilotSkillCommand | None,
    mode: ValidationMode | None,
    skill: PilotSkillName | None,
    reasons: tuple[ValidationReason, ...],
) -> ValidationResult:
    return ValidationResult(
        status=status,
        command=command,
        mode=mode,
        skill=skill,
        reasons=reasons,
    )


__all__ = [
    "DEFAULT_SAFETY_POLICY",
    "SafetyPolicy",
    "ValidationMode",
    "ValidationReason",
    "ValidationReasonCode",
    "ValidationResult",
    "ValidationStatus",
    "validate_skill_command",
]
