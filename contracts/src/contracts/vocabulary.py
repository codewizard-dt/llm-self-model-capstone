"""Config-axis vocabulary — one StrEnum per axis, seeded verbatim from the
MASTER_REQUIREMENTS Parts Catalog Grammar.

This module is the single source of truth for the legal per-axis config values.
F2 (self-model) types `SelfModelConfig` against these enums, and F3
(parts-catalog-grammar) will import them rather than redefine the value sets.
"""

from __future__ import annotations

from enum import StrEnum


class MotorAllocation(StrEnum):
    DRIVE2_ARM1_CLAW1 = "2drive+1arm+1claw"
    DRIVE2_FREE2 = "2drive+2free"
    DRIVE4 = "4drive"
    DRIVE3_MANIP1 = "3drive+1manip"


class ArmPosition(StrEnum):
    FRONT = "front"
    REAR = "rear"
    SIDE = "side"
    ABSENT = "absent"


class EndEffector(StrEnum):
    CLAW_GRASPER = "claw_grasper"
    BARE_ARM = "bare_arm"
    NONE = "none"


class WheelConfig(StrEnum):
    FRONT_OMNI_REAR_STANDARD = "front_omni+rear_standard"


class ArmGearRatio(StrEnum):
    SEVEN_TO_ONE = "7:1"
    ONE_TO_ONE = "1:1"


class Cartridge(StrEnum):
    RPM_200 = "200rpm"
