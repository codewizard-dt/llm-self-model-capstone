"""Static pilot skill registry for the closed MVP command vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from contracts.control_command import (
    ARM_DEG_MAX,
    ARM_DEG_MIN,
    MAX_ARM_RPM,
    MAX_CLAW_GRIP_FORCE_N,
    MAX_LINEAR,
    MAX_OMEGA,
)
from contracts.pilot import (
    PILOT_TIMEOUT_MS_MAX,
    ApproachTargetParams,
    ApproachTargetSkillCommand,
    ArmToAngleParams,
    ArmToAngleSkillCommand,
    CenterObjectInGripperParams,
    CenterObjectInGripperSkillCommand,
    ClawCloseParams,
    ClawCloseSkillCommand,
    ClawOpenParams,
    ClawOpenSkillCommand,
    FaceTargetParams,
    FaceTargetSkillCommand,
    GoToDestinationParams,
    GoToDestinationSkillCommand,
    PilotCommandBase,
    PilotModel,
    PilotSkillName,
    StopSkillCommand,
    StopSkillParams,
    SurveySceneParams,
    SurveySceneSkillCommand,
    VerifyDropParams,
    VerifyDropSkillCommand,
    VerifyGraspParams,
    VerifyGraspSkillCommand,
)

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
SkillSummary: TypeAlias = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class SkillInput:
    """Descriptive input metadata for one contract-owned skill parameter."""

    name: str
    description: str
    required: bool
    bound: str | None = None


@dataclass(frozen=True, slots=True)
class SkillDefault:
    """Default value advertised by the registry for omitted optional intent."""

    name: str
    value: object


@dataclass(frozen=True, slots=True)
class BoundReference:
    """A named bound imported from the contracts vertical."""

    source: str
    name: str
    value: float | int


@dataclass(frozen=True, slots=True)
class MovementEnvelope:
    """Maximum motion a skill may request through the contract command grammar."""

    linear_mps: float = 0.0
    omega_rad_s: float = 0.0
    arm_deg_min: float | None = None
    arm_deg_max: float | None = None
    arm_rpm: float | None = None
    claw_grip_force_n: float | None = None


@dataclass(frozen=True, slots=True)
class SkillSuccessAssertion:
    """Observation assertion expected to prove a skill succeeded."""

    assertion_id: str
    name: str


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    """Immutable static metadata for one pilot skill."""

    name: PilotSkillName
    params_model: type[PilotModel]
    command_model: type[PilotCommandBase]
    inputs: tuple[SkillInput, ...]
    defaults: tuple[SkillDefault, ...]
    preconditions: tuple[str, ...]
    max_duration_ms: int
    movement: MovementEnvelope
    command_path: str
    expected_result_source: str
    success_assertion: SkillSuccessAssertion
    failure_reasons: tuple[str, ...]
    recovery_hints: tuple[str, ...]
    bound_references: tuple[BoundReference, ...]


_PILOT_TIMEOUT_BOUND = BoundReference(
    source="contracts.pilot",
    name="PILOT_TIMEOUT_MS_MAX",
    value=PILOT_TIMEOUT_MS_MAX,
)
_MAX_LINEAR_BOUND = BoundReference(
    source="contracts.control_command",
    name="MAX_LINEAR",
    value=MAX_LINEAR,
)
_MAX_OMEGA_BOUND = BoundReference(
    source="contracts.control_command",
    name="MAX_OMEGA",
    value=MAX_OMEGA,
)
_ARM_DEG_MIN_BOUND = BoundReference(
    source="contracts.control_command",
    name="ARM_DEG_MIN",
    value=ARM_DEG_MIN,
)
_ARM_DEG_MAX_BOUND = BoundReference(
    source="contracts.control_command",
    name="ARM_DEG_MAX",
    value=ARM_DEG_MAX,
)
_MAX_ARM_RPM_BOUND = BoundReference(
    source="contracts.control_command",
    name="MAX_ARM_RPM",
    value=MAX_ARM_RPM,
)
_MAX_CLAW_GRIP_FORCE_BOUND = BoundReference(
    source="contracts.control_command",
    name="MAX_CLAW_GRIP_FORCE_N",
    value=MAX_CLAW_GRIP_FORCE_N,
)

_NO_MOVEMENT = MovementEnvelope()
_DRIVE_TURN_MOVEMENT = MovementEnvelope(linear_mps=MAX_LINEAR, omega_rad_s=MAX_OMEGA)
_TURN_MOVEMENT = MovementEnvelope(omega_rad_s=MAX_OMEGA)
_ARM_MOVEMENT = MovementEnvelope(
    arm_deg_min=ARM_DEG_MIN,
    arm_deg_max=ARM_DEG_MAX,
    arm_rpm=MAX_ARM_RPM,
)
_CLAW_MOVEMENT = MovementEnvelope(claw_grip_force_n=MAX_CLAW_GRIP_FORCE_N)

_COMMON_FAILURES = (
    "command rejected",
    "command timed out",
    "bridge stale",
    "operator interrupted",
)
_COMMON_RECOVERY = (
    "stop if state is unsafe",
    "refresh observation before retry",
)

_REGISTRY: dict[PilotSkillName, SkillDefinition] = {
    PilotSkillName.STOP: SkillDefinition(
        name=PilotSkillName.STOP,
        params_model=StopSkillParams,
        command_model=StopSkillCommand,
        inputs=(
            SkillInput(
                name="reason",
                description="Structured reason for halting the pilot loop and robot motion.",
                required=True,
            ),
        ),
        defaults=(SkillDefault(name="reason", value="operator"),),
        preconditions=("bridge accepts command grammar",),
        max_duration_ms=500,
        movement=_NO_MOVEMENT,
        command_path="pilot.skill.stop -> control.stop",
        expected_result_source="pilot_observation.last_result",
        success_assertion=SkillSuccessAssertion("assert.robot_stopped", "robot stopped"),
        failure_reasons=("bridge stale", "estop already latched", "operator interrupted"),
        recovery_hints=("hold stopped state", "request human if stop is not acknowledged"),
        bound_references=(_PILOT_TIMEOUT_BOUND,),
    ),
    PilotSkillName.SURVEY_SCENE: SkillDefinition(
        name=PilotSkillName.SURVEY_SCENE,
        params_model=SurveySceneParams,
        command_model=SurveySceneSkillCommand,
        inputs=(
            SkillInput(
                name="yaw_span_deg",
                description="Total yaw sweep used to refresh visible objects and tags.",
                required=False,
            ),
            SkillInput(
                name="timeout_ms",
                description="Observation sweep timeout.",
                required=False,
                bound="PILOT_TIMEOUT_MS_MAX",
            ),
        ),
        defaults=(
            SkillDefault(name="yaw_span_deg", value=180.0),
            SkillDefault(name="timeout_ms", value=5000),
        ),
        preconditions=("bridge healthy", "operator has not interrupted the run"),
        max_duration_ms=5000,
        movement=_TURN_MOVEMENT,
        command_path="pilot.skill.survey_scene -> control.turn",
        expected_result_source="pilot_observation.visible_objects|visible_tags",
        success_assertion=SkillSuccessAssertion("assert.scene_surveyed", "scene surveyed"),
        failure_reasons=(*_COMMON_FAILURES, "localization stale"),
        recovery_hints=(*_COMMON_RECOVERY, "retry with a narrower yaw span"),
        bound_references=(_PILOT_TIMEOUT_BOUND, _MAX_OMEGA_BOUND),
    ),
    PilotSkillName.FACE_TARGET: SkillDefinition(
        name=PilotSkillName.FACE_TARGET,
        params_model=FaceTargetParams,
        command_model=FaceTargetSkillCommand,
        inputs=(
            SkillInput(
                name="target_id",
                description="Visible object or tag identifier to face.",
                required=True,
            ),
            SkillInput(
                name="max_turn_rad_s",
                description="Maximum yaw rate while turning toward the target.",
                required=False,
                bound="MAX_OMEGA",
            ),
            SkillInput(
                name="timeout_ms",
                description="Maximum time allowed for target alignment.",
                required=False,
                bound="PILOT_TIMEOUT_MS_MAX",
            ),
        ),
        defaults=(
            SkillDefault(name="max_turn_rad_s", value=MAX_OMEGA),
            SkillDefault(name="timeout_ms", value=4000),
        ),
        preconditions=("target is visible or recently localized", "bridge healthy"),
        max_duration_ms=4000,
        movement=_TURN_MOVEMENT,
        command_path="pilot.skill.face_target -> control.turn",
        expected_result_source="pilot_observation.current_assertions",
        success_assertion=SkillSuccessAssertion("assert.target_faced", "target faced"),
        failure_reasons=(*_COMMON_FAILURES, "target lost", "heading confidence too low"),
        recovery_hints=(*_COMMON_RECOVERY, "survey scene to reacquire the target"),
        bound_references=(_PILOT_TIMEOUT_BOUND, _MAX_OMEGA_BOUND),
    ),
    PilotSkillName.APPROACH_TARGET: SkillDefinition(
        name=PilotSkillName.APPROACH_TARGET,
        params_model=ApproachTargetParams,
        command_model=ApproachTargetSkillCommand,
        inputs=(
            SkillInput(
                name="target_id",
                description="Visible object or destination identifier to approach.",
                required=True,
            ),
            SkillInput(
                name="standoff_m",
                description="Distance to stop short of the target.",
                required=False,
            ),
            SkillInput(
                name="max_speed_mps",
                description="Maximum forward speed while approaching.",
                required=False,
                bound="MAX_LINEAR",
            ),
            SkillInput(
                name="timeout_ms",
                description="Maximum time allowed for the approach.",
                required=False,
                bound="PILOT_TIMEOUT_MS_MAX",
            ),
        ),
        defaults=(
            SkillDefault(name="standoff_m", value=0.20),
            SkillDefault(name="max_speed_mps", value=MAX_LINEAR),
            SkillDefault(name="timeout_ms", value=10_000),
        ),
        preconditions=("target is localized", "drive path is not known blocked", "bridge healthy"),
        max_duration_ms=10_000,
        movement=_DRIVE_TURN_MOVEMENT,
        command_path="pilot.skill.approach_target -> control.drive",
        expected_result_source="pilot_observation.localization|visible_objects",
        success_assertion=SkillSuccessAssertion(
            "assert.target_standoff", "target standoff reached"
        ),
        failure_reasons=(*_COMMON_FAILURES, "target lost", "path blocked", "standoff not reached"),
        recovery_hints=(*_COMMON_RECOVERY, "face target before retrying approach"),
        bound_references=(_PILOT_TIMEOUT_BOUND, _MAX_LINEAR_BOUND, _MAX_OMEGA_BOUND),
    ),
    PilotSkillName.CENTER_OBJECT_IN_GRIPPER: SkillDefinition(
        name=PilotSkillName.CENTER_OBJECT_IN_GRIPPER,
        params_model=CenterObjectInGripperParams,
        command_model=CenterObjectInGripperSkillCommand,
        inputs=(
            SkillInput(
                name="object_id",
                description="Visible object identifier to center in the gripper.",
                required=True,
            ),
            SkillInput(
                name="image_tolerance_px",
                description="Accepted pixel error from gripper centerline.",
                required=False,
            ),
            SkillInput(
                name="timeout_ms",
                description="Maximum time allowed for centering.",
                required=False,
                bound="PILOT_TIMEOUT_MS_MAX",
            ),
        ),
        defaults=(
            SkillDefault(name="image_tolerance_px", value=16),
            SkillDefault(name="timeout_ms", value=6000),
        ),
        preconditions=("object is visible", "gripper is open or ready", "bridge healthy"),
        max_duration_ms=6000,
        movement=_DRIVE_TURN_MOVEMENT,
        command_path="pilot.skill.center_object_in_gripper -> control.drive",
        expected_result_source="pilot_observation.visible_objects",
        success_assertion=SkillSuccessAssertion("assert.object_centered", "object centered"),
        failure_reasons=(*_COMMON_FAILURES, "object lost", "centering tolerance not reached"),
        recovery_hints=(*_COMMON_RECOVERY, "survey or face the object before retrying"),
        bound_references=(_PILOT_TIMEOUT_BOUND, _MAX_LINEAR_BOUND, _MAX_OMEGA_BOUND),
    ),
    PilotSkillName.ARM_TO_ANGLE: SkillDefinition(
        name=PilotSkillName.ARM_TO_ANGLE,
        params_model=ArmToAngleParams,
        command_model=ArmToAngleSkillCommand,
        inputs=(
            SkillInput(
                name="deg",
                description="Absolute arm joint angle in degrees.",
                required=True,
                bound="ARM_DEG_MIN..ARM_DEG_MAX",
            ),
            SkillInput(
                name="vel_rpm",
                description="Optional maximum arm motor velocity.",
                required=False,
                bound="MAX_ARM_RPM",
            ),
        ),
        defaults=(SkillDefault(name="vel_rpm", value=None),),
        preconditions=(
            "arm port is available",
            "requested angle is contract-valid",
            "bridge healthy",
        ),
        max_duration_ms=3000,
        movement=_ARM_MOVEMENT,
        command_path="pilot.skill.arm_to_angle -> control.arm",
        expected_result_source="pilot_observation.manipulator",
        success_assertion=SkillSuccessAssertion("assert.arm_at_angle", "arm at requested angle"),
        failure_reasons=(*_COMMON_FAILURES, "arm not assembled", "angle not reached"),
        recovery_hints=(*_COMMON_RECOVERY, "use a conservative angle within the contract range"),
        bound_references=(
            _PILOT_TIMEOUT_BOUND,
            _ARM_DEG_MIN_BOUND,
            _ARM_DEG_MAX_BOUND,
            _MAX_ARM_RPM_BOUND,
        ),
    ),
    PilotSkillName.CLAW_OPEN: SkillDefinition(
        name=PilotSkillName.CLAW_OPEN,
        params_model=ClawOpenParams,
        command_model=ClawOpenSkillCommand,
        inputs=(
            SkillInput(
                name="opening_pct",
                description="Optional target claw opening percentage.",
                required=False,
            ),
        ),
        defaults=(SkillDefault(name="opening_pct", value=None),),
        preconditions=("claw port is available", "bridge healthy"),
        max_duration_ms=1500,
        movement=_CLAW_MOVEMENT,
        command_path="pilot.skill.claw_open -> control.claw",
        expected_result_source="pilot_observation.manipulator",
        success_assertion=SkillSuccessAssertion("assert.claw_open", "claw open"),
        failure_reasons=(*_COMMON_FAILURES, "claw not assembled", "object still held"),
        recovery_hints=(*_COMMON_RECOVERY, "stop before requesting human assistance"),
        bound_references=(_PILOT_TIMEOUT_BOUND, _MAX_CLAW_GRIP_FORCE_BOUND),
    ),
    PilotSkillName.CLAW_CLOSE: SkillDefinition(
        name=PilotSkillName.CLAW_CLOSE,
        params_model=ClawCloseParams,
        command_model=ClawCloseSkillCommand,
        inputs=(
            SkillInput(
                name="grip_force_n",
                description="Optional grip-force target.",
                required=False,
                bound="MAX_CLAW_GRIP_FORCE_N",
            ),
        ),
        defaults=(SkillDefault(name="grip_force_n", value=None),),
        preconditions=(
            "object is centered or graspable",
            "claw port is available",
            "bridge healthy",
        ),
        max_duration_ms=1500,
        movement=_CLAW_MOVEMENT,
        command_path="pilot.skill.claw_close -> control.claw",
        expected_result_source="pilot_observation.manipulator",
        success_assertion=SkillSuccessAssertion("assert.claw_closed", "claw closed"),
        failure_reasons=(*_COMMON_FAILURES, "claw not assembled", "object slipped"),
        recovery_hints=(*_COMMON_RECOVERY, "verify grasp before navigating away"),
        bound_references=(_PILOT_TIMEOUT_BOUND, _MAX_CLAW_GRIP_FORCE_BOUND),
    ),
    PilotSkillName.VERIFY_GRASP: SkillDefinition(
        name=PilotSkillName.VERIFY_GRASP,
        params_model=VerifyGraspParams,
        command_model=VerifyGraspSkillCommand,
        inputs=(
            SkillInput(
                name="object_id",
                description="Optional object identifier expected to be held.",
                required=False,
            ),
            SkillInput(
                name="min_confidence",
                description="Minimum confidence for grasp verification.",
                required=False,
            ),
        ),
        defaults=(
            SkillDefault(name="object_id", value=None),
            SkillDefault(name="min_confidence", value=0.65),
        ),
        preconditions=("recent close command or held-object evidence exists",),
        max_duration_ms=1000,
        movement=_NO_MOVEMENT,
        command_path="pilot.skill.verify_grasp -> observation.assertion",
        expected_result_source="pilot_observation.manipulator|current_assertions",
        success_assertion=SkillSuccessAssertion("assert.object_held", "object held"),
        failure_reasons=("object absent", "confidence below threshold", "observation stale"),
        recovery_hints=(
            "center object and close claw again",
            "request human if repeated grasp fails",
        ),
        bound_references=(_PILOT_TIMEOUT_BOUND,),
    ),
    PilotSkillName.GO_TO_DESTINATION: SkillDefinition(
        name=PilotSkillName.GO_TO_DESTINATION,
        params_model=GoToDestinationParams,
        command_model=GoToDestinationSkillCommand,
        inputs=(
            SkillInput(
                name="destination_id",
                description="Optional symbolic destination identifier.",
                required=False,
            ),
            SkillInput(
                name="x_m", description="Optional destination x coordinate.", required=False
            ),
            SkillInput(
                name="y_m", description="Optional destination y coordinate.", required=False
            ),
            SkillInput(
                name="heading_rad",
                description="Optional desired final heading.",
                required=False,
            ),
            SkillInput(
                name="position_tolerance_m",
                description="Accepted destination position tolerance.",
                required=False,
            ),
            SkillInput(
                name="max_speed_mps",
                description="Maximum forward speed while navigating.",
                required=False,
                bound="MAX_LINEAR",
            ),
            SkillInput(
                name="timeout_ms",
                description="Maximum time allowed for navigation.",
                required=False,
                bound="PILOT_TIMEOUT_MS_MAX",
            ),
        ),
        defaults=(
            SkillDefault(name="destination_id", value=None),
            SkillDefault(name="heading_rad", value=None),
            SkillDefault(name="position_tolerance_m", value=0.10),
            SkillDefault(name="max_speed_mps", value=MAX_LINEAR),
            SkillDefault(name="timeout_ms", value=15_000),
        ),
        preconditions=("destination is known or coordinates are provided", "bridge healthy"),
        max_duration_ms=15_000,
        movement=_DRIVE_TURN_MOVEMENT,
        command_path="pilot.skill.go_to_destination -> control.drive",
        expected_result_source="pilot_observation.localization",
        success_assertion=SkillSuccessAssertion(
            "assert.destination_reached", "destination reached"
        ),
        failure_reasons=(*_COMMON_FAILURES, "destination unknown", "path blocked"),
        recovery_hints=(*_COMMON_RECOVERY, "survey scene or choose a nearer destination"),
        bound_references=(_PILOT_TIMEOUT_BOUND, _MAX_LINEAR_BOUND, _MAX_OMEGA_BOUND),
    ),
    PilotSkillName.VERIFY_DROP: SkillDefinition(
        name=PilotSkillName.VERIFY_DROP,
        params_model=VerifyDropParams,
        command_model=VerifyDropSkillCommand,
        inputs=(
            SkillInput(
                name="destination_id",
                description="Optional destination where the object should have been dropped.",
                required=False,
            ),
            SkillInput(
                name="min_confidence",
                description="Minimum confidence for drop verification.",
                required=False,
            ),
        ),
        defaults=(
            SkillDefault(name="destination_id", value=None),
            SkillDefault(name="min_confidence", value=0.65),
        ),
        preconditions=("recent open command or release evidence exists",),
        max_duration_ms=1000,
        movement=_NO_MOVEMENT,
        command_path="pilot.skill.verify_drop -> observation.assertion",
        expected_result_source="pilot_observation.manipulator|visible_objects|current_assertions",
        success_assertion=SkillSuccessAssertion("assert.object_dropped", "object dropped"),
        failure_reasons=(
            "object still held",
            "destination not visible",
            "confidence below threshold",
        ),
        recovery_hints=("open claw again", "survey destination before retrying verification"),
        bound_references=(_PILOT_TIMEOUT_BOUND,),
    ),
}


def list_skill_definitions() -> tuple[SkillDefinition, ...]:
    """Return registry definitions in contract enum declaration order."""

    return tuple(_REGISTRY[name] for name in PilotSkillName)


def get_skill_definition(name: PilotSkillName | str) -> SkillDefinition:
    """Return one registry definition or raise a clear error for unknown names."""

    try:
        skill_name = name if isinstance(name, PilotSkillName) else PilotSkillName(str(name))
    except ValueError as exc:
        raise ValueError(f"unknown pilot skill: {name!r}") from exc

    try:
        return _REGISTRY[skill_name]
    except KeyError as exc:
        raise KeyError(f"missing pilot skill definition: {skill_name.value}") from exc


def list_skill_summaries() -> list[SkillSummary]:
    """Return compact JSON-compatible skill metadata in contract enum order."""

    return [_summarize_skill_definition(definition) for definition in list_skill_definitions()]


def get_skill_summary(name: PilotSkillName | str) -> SkillSummary:
    """Return one compact JSON-compatible skill summary."""

    return _summarize_skill_definition(get_skill_definition(name))


def _summarize_skill_definition(definition: SkillDefinition) -> SkillSummary:
    return {
        "name": definition.name.value,
        "params_model": _qualified_name(definition.params_model),
        "command_model": _qualified_name(definition.command_model),
        "inputs": [
            {
                "name": input_metadata.name,
                "description": input_metadata.description,
                "required": input_metadata.required,
                "bound": input_metadata.bound,
            }
            for input_metadata in definition.inputs
        ],
        "defaults": [
            {
                "name": default.name,
                "value": default.value,
            }
            for default in definition.defaults
        ],
        "preconditions": list(definition.preconditions),
        "max_duration_ms": definition.max_duration_ms,
        "movement": {
            "linear_mps": definition.movement.linear_mps,
            "omega_rad_s": definition.movement.omega_rad_s,
            "arm_deg_min": definition.movement.arm_deg_min,
            "arm_deg_max": definition.movement.arm_deg_max,
            "arm_rpm": definition.movement.arm_rpm,
            "claw_grip_force_n": definition.movement.claw_grip_force_n,
        },
        "command_path": definition.command_path,
        "expected_result_source": definition.expected_result_source,
        "success_assertion": {
            "assertion_id": definition.success_assertion.assertion_id,
            "name": definition.success_assertion.name,
        },
        "failure_reasons": list(definition.failure_reasons),
        "recovery_hints": list(definition.recovery_hints),
        "bound_references": [
            {
                "source": bound.source,
                "name": bound.name,
                "value": bound.value,
            }
            for bound in definition.bound_references
        ],
    }


def _qualified_name(model: type[object]) -> str:
    return f"{model.__module__}.{model.__qualname__}"


__all__ = [
    "BoundReference",
    "JsonScalar",
    "JsonValue",
    "MovementEnvelope",
    "SkillDefault",
    "SkillDefinition",
    "SkillInput",
    "SkillSummary",
    "SkillSuccessAssertion",
    "get_skill_definition",
    "get_skill_summary",
    "list_skill_definitions",
    "list_skill_summaries",
]
