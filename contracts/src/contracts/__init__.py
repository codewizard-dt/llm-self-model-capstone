"""Public API for the contracts vertical — the single source of truth for schemas."""

from contracts.adapters import TelemetrySource, VisionSource
from contracts.contract_line import (
    AprilTagPose,
    ContractLine,
    ScoreContractLine,
    VisionBlock,
)
from contracts.control_command import (
    ARM_DEG_MAX,
    ARM_DEG_MIN,
    MAX_FLYWHEEL_RPM,
    MAX_LINEAR,
    MAX_OMEGA,
    TTL_MS_MAX,
    AckLine,
    ArmCommand,
    ClawCommand,
    ControlCommand,
    ControlEnvelope,
    ControlLine,
    DriveCommand,
    FaultCode,
    FlywheelCommand,
    HeartbeatLine,
    StopCommand,
    TurnCommand,
)
from contracts.motor_telemetry import (
    ContractSource,
    MotorApiSample,
    MotorApiValues,
    motor_sample_from_pros,
    motor_sample_from_vexcode,
    vexcode_motor_source_api,
)
from contracts.parts_catalog import PartsCatalog, validate_config
from contracts.self_model import SelfModel, SelfModelConfig
from contracts.task_contracts import ScoreGap, ScoreObserved, ScorePredicted
from contracts.vocabulary import Cartridge, EndEffector, MotorAllocation

__all__ = [
    "TelemetrySource",
    "VisionSource",
    "ContractLine",
    "ScoreContractLine",
    "ScorePredicted",
    "ScoreObserved",
    "ScoreGap",
    "VisionBlock",
    "AprilTagPose",
    "MotorApiSample",
    "MotorApiValues",
    "ContractSource",
    "motor_sample_from_vexcode",
    "motor_sample_from_pros",
    "vexcode_motor_source_api",
    "SelfModel",
    "SelfModelConfig",
    "PartsCatalog",
    "validate_config",
    "MotorAllocation",
    "EndEffector",
    "Cartridge",
    "ControlEnvelope",
    "ControlLine",
    "ControlCommand",
    "HeartbeatLine",
    "AckLine",
    "StopCommand",
    "DriveCommand",
    "TurnCommand",
    "ArmCommand",
    "ClawCommand",
    "FlywheelCommand",
    "FaultCode",
    "MAX_LINEAR",
    "MAX_OMEGA",
    "MAX_FLYWHEEL_RPM",
    "ARM_DEG_MIN",
    "ARM_DEG_MAX",
    "TTL_MS_MAX",
]
