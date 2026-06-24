"""Config-axis vocabulary — one StrEnum per axis.

Seeded from the MASTER_REQUIREMENTS Parts Catalog Grammar, then revised per the
PR #13 review to keep only realistically feasible options: end effectors are the
real ball-manipulation mechanisms (claw / scoop / flywheel), arm position is
trimmed to the two feasible mounts, and the cartridge axis carries all three VEX
V5 gear cartridges (100 / 200 / 600 rpm).

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


class EndEffector(StrEnum):
    CLAW_GRASPER = "claw_grasper"
    SCOOP = "scoop"
    FLYWHEEL = "flywheel"


class WheelConfig(StrEnum):
    FRONT_OMNI_REAR_STANDARD = "front_omni+rear_standard"


class ArmGearRatio(StrEnum):
    SEVEN_TO_ONE = "7:1"
    ONE_TO_ONE = "1:1"


class Cartridge(StrEnum):
    RPM_100 = "100rpm"
    RPM_200 = "200rpm"
    RPM_600 = "600rpm"
