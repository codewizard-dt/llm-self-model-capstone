"""Pilot-loop contracts for bounded online LLM decisions and trace records."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import ConfigDict, Field, model_validator

from contracts.control_command import (
    ARM_DEG_MAX,
    ARM_DEG_MIN,
    MAX_ARM_RPM,
    MAX_CLAW_GRIP_FORCE_N,
    MAX_LINEAR,
    MAX_OMEGA,
)
from contracts.motor_telemetry import StrictModel

COMMAND_ID_MAX_LENGTH = 80
TEXT_MAX_LENGTH = 512
TARGET_ID_MAX_LENGTH = 80
PILOT_TIMEOUT_MS_MAX = 30_000
MAX_VISIBLE_OBJECTS = 32
MAX_VISIBLE_TAGS = 32
MAX_RECENT_FAILURES = 12
MAX_ASSERTIONS = 32
MAX_EVIDENCE_ENTRIES = 12


class PilotModel(StrictModel):
    """Base for pilot contracts: closed shape, JSON-friendly scalar coercion."""

    model_config = ConfigDict(extra="forbid", strict=False)


class PilotSkillName(StrEnum):
    """Closed MVP pilot skill vocabulary."""

    STOP = "stop"
    SURVEY_SCENE = "survey_scene"
    FACE_TARGET = "face_target"
    APPROACH_TARGET = "approach_target"
    CENTER_OBJECT_IN_GRIPPER = "center_object_in_gripper"
    ARM_TO_ANGLE = "arm_to_angle"
    CLAW_OPEN = "claw_open"
    CLAW_CLOSE = "claw_close"
    VERIFY_GRASP = "verify_grasp"
    GO_TO_DESTINATION = "go_to_destination"
    VERIFY_DROP = "verify_drop"


class AssertionState(StrEnum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


class PilotDecisionAction(StrEnum):
    CONTINUE = "continue"
    RETRY = "retry"
    STOP_SUCCESS = "stop_success"
    STOP_FAILURE = "stop_failure"
    REQUEST_HUMAN = "request_human"


class PilotTaskPhase(StrEnum):
    IDLE = "idle"
    SURVEY = "survey"
    NAVIGATE = "navigate"
    MANIPULATE = "manipulate"
    VERIFY = "verify"
    COMPLETE = "complete"
    FAILED = "failed"


class CommandStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    OK = "ok"
    REJECTED = "rejected"
    FAILED = "failed"
    STALE = "stale"


class Pose2D(PilotModel):
    x_m: float
    y_m: float
    heading_rad: float


class ImageBox(PilotModel):
    x_px: int = Field(ge=0)
    y_px: int = Field(ge=0)
    width_px: int = Field(gt=0)
    height_px: int = Field(gt=0)


class StopSkillParams(PilotModel):
    reason: Literal["operator", "task_complete", "fault", "unsafe", "policy"]


class SurveySceneParams(PilotModel):
    yaw_span_deg: float = Field(default=180.0, ge=0.0, le=360.0)
    timeout_ms: int = Field(default=5000, ge=1, le=PILOT_TIMEOUT_MS_MAX)


class FaceTargetParams(PilotModel):
    target_id: str = Field(min_length=1, max_length=TARGET_ID_MAX_LENGTH)
    max_turn_rad_s: float = Field(default=MAX_OMEGA, ge=0.0, le=MAX_OMEGA)
    timeout_ms: int = Field(default=4000, ge=1, le=PILOT_TIMEOUT_MS_MAX)


class ApproachTargetParams(PilotModel):
    target_id: str = Field(min_length=1, max_length=TARGET_ID_MAX_LENGTH)
    standoff_m: float = Field(default=0.20, ge=0.0, le=5.0)
    max_speed_mps: float = Field(default=MAX_LINEAR, ge=0.0, le=MAX_LINEAR)
    timeout_ms: int = Field(default=10_000, ge=1, le=PILOT_TIMEOUT_MS_MAX)


class CenterObjectInGripperParams(PilotModel):
    object_id: str = Field(min_length=1, max_length=TARGET_ID_MAX_LENGTH)
    image_tolerance_px: int = Field(default=16, ge=0, le=320)
    timeout_ms: int = Field(default=6000, ge=1, le=PILOT_TIMEOUT_MS_MAX)


class ArmToAngleParams(PilotModel):
    deg: float = Field(ge=ARM_DEG_MIN, le=ARM_DEG_MAX)
    vel_rpm: float | None = Field(default=None, ge=0.0, le=MAX_ARM_RPM)


class ClawOpenParams(PilotModel):
    opening_pct: float | None = Field(default=None, ge=0.0, le=100.0)


class ClawCloseParams(PilotModel):
    grip_force_n: float | None = Field(default=None, ge=0.0, le=MAX_CLAW_GRIP_FORCE_N)


class VerifyGraspParams(PilotModel):
    object_id: str | None = Field(default=None, min_length=1, max_length=TARGET_ID_MAX_LENGTH)
    min_confidence: float = Field(default=0.65, ge=0.0, le=1.0)


class GoToDestinationParams(PilotModel):
    destination_id: str | None = Field(default=None, min_length=1, max_length=TARGET_ID_MAX_LENGTH)
    x_m: float | None = None
    y_m: float | None = None
    heading_rad: float | None = None
    position_tolerance_m: float = Field(default=0.10, ge=0.0, le=2.0)
    max_speed_mps: float = Field(default=MAX_LINEAR, ge=0.0, le=MAX_LINEAR)
    timeout_ms: int = Field(default=15_000, ge=1, le=PILOT_TIMEOUT_MS_MAX)

    @model_validator(mode="after")
    def _require_destination_or_coordinates(self) -> GoToDestinationParams:
        if self.destination_id is None and (self.x_m is None or self.y_m is None):
            raise ValueError("go_to_destination requires destination_id or x_m/y_m coordinates")
        return self


class VerifyDropParams(PilotModel):
    destination_id: str | None = Field(default=None, min_length=1, max_length=TARGET_ID_MAX_LENGTH)
    min_confidence: float = Field(default=0.65, ge=0.0, le=1.0)


class PilotCommandBase(PilotModel):
    v: Literal[1] = 1
    command_id: str = Field(min_length=1, max_length=COMMAND_ID_MAX_LENGTH)
    issued_ms: int = Field(ge=0)


class StopSkillCommand(PilotCommandBase):
    skill: Literal["stop"] = "stop"
    params: StopSkillParams


class SurveySceneSkillCommand(PilotCommandBase):
    skill: Literal["survey_scene"] = "survey_scene"
    params: SurveySceneParams = Field(default_factory=SurveySceneParams)


class FaceTargetSkillCommand(PilotCommandBase):
    skill: Literal["face_target"] = "face_target"
    params: FaceTargetParams


class ApproachTargetSkillCommand(PilotCommandBase):
    skill: Literal["approach_target"] = "approach_target"
    params: ApproachTargetParams


class CenterObjectInGripperSkillCommand(PilotCommandBase):
    skill: Literal["center_object_in_gripper"] = "center_object_in_gripper"
    params: CenterObjectInGripperParams


class ArmToAngleSkillCommand(PilotCommandBase):
    skill: Literal["arm_to_angle"] = "arm_to_angle"
    params: ArmToAngleParams


class ClawOpenSkillCommand(PilotCommandBase):
    skill: Literal["claw_open"] = "claw_open"
    params: ClawOpenParams = Field(default_factory=ClawOpenParams)


class ClawCloseSkillCommand(PilotCommandBase):
    skill: Literal["claw_close"] = "claw_close"
    params: ClawCloseParams = Field(default_factory=ClawCloseParams)


class VerifyGraspSkillCommand(PilotCommandBase):
    skill: Literal["verify_grasp"] = "verify_grasp"
    params: VerifyGraspParams = Field(default_factory=VerifyGraspParams)


class GoToDestinationSkillCommand(PilotCommandBase):
    skill: Literal["go_to_destination"] = "go_to_destination"
    params: GoToDestinationParams


class VerifyDropSkillCommand(PilotCommandBase):
    skill: Literal["verify_drop"] = "verify_drop"
    params: VerifyDropParams = Field(default_factory=VerifyDropParams)


PilotSkillCommand = Annotated[
    Union[
        StopSkillCommand,
        SurveySceneSkillCommand,
        FaceTargetSkillCommand,
        ApproachTargetSkillCommand,
        CenterObjectInGripperSkillCommand,
        ArmToAngleSkillCommand,
        ClawOpenSkillCommand,
        ClawCloseSkillCommand,
        VerifyGraspSkillCommand,
        GoToDestinationSkillCommand,
        VerifyDropSkillCommand,
    ],
    Field(discriminator="skill"),
]


class AssertionEvidence(PilotModel):
    source: Literal["telemetry", "vision", "bridge", "planner", "operator", "replay"]
    summary: str = Field(min_length=1, max_length=TEXT_MAX_LENGTH)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    observed_ms: int | None = Field(default=None, ge=0)
    age_ms: int | None = Field(default=None, ge=0)


class PilotAssertion(PilotModel):
    v: Literal[1] = 1
    assertion_id: str = Field(min_length=1, max_length=COMMAND_ID_MAX_LENGTH)
    predicate: str = Field(min_length=1, max_length=TEXT_MAX_LENGTH)
    state: AssertionState
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[AssertionEvidence] = Field(default_factory=list, max_length=MAX_EVIDENCE_ENTRIES)
    observed_ms: int | None = Field(default=None, ge=0)
    age_ms: int | None = Field(default=None, ge=0)
    recovery_hint: str | None = Field(default=None, min_length=1, max_length=TEXT_MAX_LENGTH)

    @model_validator(mode="after")
    def _require_time_or_age(self) -> PilotAssertion:
        if self.observed_ms is None and self.age_ms is None:
            raise ValueError("pilot assertion requires observed_ms or age_ms")
        return self


class LocalizationState(PilotModel):
    pose: Pose2D | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    age_ms: int = Field(ge=0)


class VisibleObject(PilotModel):
    object_id: str = Field(min_length=1, max_length=TARGET_ID_MAX_LENGTH)
    label: str = Field(min_length=1, max_length=80)
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: ImageBox | None = None


class VisibleTag(PilotModel):
    tag_id: int = Field(ge=0)
    family: str = Field(default="tag36h11", min_length=1, max_length=40)
    confidence: float = Field(ge=0.0, le=1.0)
    pose: Pose2D | None = None


class ManipulatorState(PilotModel):
    arm_deg: float | None = Field(default=None, ge=ARM_DEG_MIN, le=ARM_DEG_MAX)
    claw_state: Literal["open", "closed", "holding", "unknown"]
    held_object_id: str | None = Field(default=None, min_length=1, max_length=TARGET_ID_MAX_LENGTH)


class BridgeHealth(PilotModel):
    state: Literal["ok", "degraded", "fault", "stale"]
    last_heartbeat_age_ms: int | None = Field(default=None, ge=0)
    estop: bool = False
    battery_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    fault: str | None = Field(default=None, min_length=1, max_length=TEXT_MAX_LENGTH)


class PilotSkillResult(PilotModel):
    v: Literal[1] = 1
    command_id: str = Field(min_length=1, max_length=COMMAND_ID_MAX_LENGTH)
    skill: PilotSkillName
    status: CommandStatus
    completed_ms: int | None = Field(default=None, ge=0)
    message: str | None = Field(default=None, min_length=1, max_length=TEXT_MAX_LENGTH)
    fault: str | None = Field(default=None, min_length=1, max_length=TEXT_MAX_LENGTH)


class PilotFailure(PilotModel):
    failed_ms: int = Field(ge=0)
    source: Literal["command", "assertion", "bridge", "localization", "vision", "policy"]
    summary: str = Field(min_length=1, max_length=TEXT_MAX_LENGTH)
    command_id: str | None = Field(default=None, min_length=1, max_length=COMMAND_ID_MAX_LENGTH)
    recovery_hint: str | None = Field(default=None, min_length=1, max_length=TEXT_MAX_LENGTH)


class PilotObservation(PilotModel):
    v: Literal[1] = 1
    observed_ms: int = Field(ge=0)
    task_phase: PilotTaskPhase
    objective: str = Field(min_length=1, max_length=TEXT_MAX_LENGTH)
    robot_pose: Pose2D | None = None
    localization: LocalizationState
    visible_objects: list[VisibleObject] = Field(
        default_factory=list, max_length=MAX_VISIBLE_OBJECTS
    )
    visible_tags: list[VisibleTag] = Field(default_factory=list, max_length=MAX_VISIBLE_TAGS)
    manipulator: ManipulatorState
    bridge: BridgeHealth
    last_command: PilotSkillCommand | None = None
    last_result: PilotSkillResult | None = None
    recent_failures: list[PilotFailure] = Field(
        default_factory=list, max_length=MAX_RECENT_FAILURES
    )
    current_assertions: list[PilotAssertion] = Field(
        default_factory=list, max_length=MAX_ASSERTIONS
    )


class PilotDecision(PilotModel):
    v: Literal[1] = 1
    decision_id: str = Field(min_length=1, max_length=COMMAND_ID_MAX_LENGTH)
    decided_ms: int = Field(ge=0)
    action: PilotDecisionAction
    rationale: str = Field(min_length=1, max_length=TEXT_MAX_LENGTH)
    confidence: float = Field(ge=0.0, le=1.0)
    command: PilotSkillCommand | None = None
    retry_of_command_id: str | None = Field(
        default=None, min_length=1, max_length=COMMAND_ID_MAX_LENGTH
    )
    stop_reason: str | None = Field(default=None, min_length=1, max_length=TEXT_MAX_LENGTH)


class TraceRecordBase(PilotModel):
    v: Literal[1] = 1
    session_id: str = Field(min_length=1, max_length=COMMAND_ID_MAX_LENGTH)
    seq: int = Field(ge=0)
    monotonic_ms: int = Field(ge=0)


class ObservationTraceRecord(TraceRecordBase):
    event: Literal["observation"] = "observation"
    observation: PilotObservation


class DecisionTraceRecord(TraceRecordBase):
    event: Literal["decision"] = "decision"
    decision: PilotDecision


class CommandTraceRecord(TraceRecordBase):
    event: Literal["command"] = "command"
    command: PilotSkillCommand


class ResultTraceRecord(TraceRecordBase):
    event: Literal["result"] = "result"
    result: PilotSkillResult


class AssertionTraceRecord(TraceRecordBase):
    event: Literal["assertion"] = "assertion"
    assertion: PilotAssertion


class StopTraceRecord(TraceRecordBase):
    event: Literal["stop"] = "stop"
    reason: Literal["success", "failure", "operator", "fault", "request_human"]
    message: str | None = Field(default=None, min_length=1, max_length=TEXT_MAX_LENGTH)


PilotTraceRecord = Annotated[
    Union[
        ObservationTraceRecord,
        DecisionTraceRecord,
        CommandTraceRecord,
        ResultTraceRecord,
        AssertionTraceRecord,
        StopTraceRecord,
    ],
    Field(discriminator="event"),
]
