"""ROS-free safety validation for pilot skill commands."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from pydantic import TypeAdapter, ValidationError

from contracts import PilotObservation, PilotSkillCommand, PilotSkillName
from pilot.skills import get_skill_definition


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
    HUMAN_SUPERVISION_REQUIRED = "human_supervision_required"
    BRIDGE_STALE = "bridge_stale"
    BRIDGE_FAULT = "bridge_fault"
    ESTOP_ACTIVE = "estop_active"
    HEARTBEAT_MISSING = "heartbeat_missing"
    HEARTBEAT_STALE = "heartbeat_stale"


@dataclass(frozen=True, slots=True)
class SafetyPolicy:
    """Policy thresholds for core command safety gates."""

    heartbeat_stale_after_ms: int = 500
    require_hardware_supervision: bool = True

    def __post_init__(self) -> None:
        if self.heartbeat_stale_after_ms < 0:
            raise ValueError("heartbeat_stale_after_ms must be non-negative")


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
        get_skill_definition(skill)
    except (KeyError, ValueError):
        return _result(
            ValidationStatus.REJECTED,
            command=normalized_command,
            mode=validation_mode,
            skill=None,
            reasons=(
                ValidationReason(
                    ValidationReasonCode.UNKNOWN_SKILL,
                    "pilot skill is not registered",
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
