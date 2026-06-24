"""Config-axis vocabulary — one StrEnum per active config axis.

Seeded from the MASTER_REQUIREMENTS Parts Catalog Grammar, revised per the PR #13
review, and narrowed again per the PR #16 post-merge review to match what the V5
Starter Kit can actually build. The active axes are the three the design space
turns on:

- ``MotorAllocation`` is **effector-encoded**: each value names a concrete build
  (claw / scoop / flywheel) rather than an abstract motor budget. ``4drive``,
  ``2drive+2free``, and ``3drive+1manip`` are gone — no `4drive` config is
  buildable (no manipulator motor), and the `+free` / `+manip` labels collapsed
  once each effector pinned its own allocation.
- ``EndEffector`` keeps the three real ball-manipulation mechanisms.
- ``Cartridge`` drops ``100rpm`` (not in inventory); only ``200rpm`` and
  ``600rpm`` remain.

The previous ``ArmPosition``, ``ArmGearRatio``, and ``WheelConfig`` enums were
removed: arm position is fixed to rear (moving it is infeasible), the arm gear
ratio is fixed at 7:1 mechanical (the configurable knob is the cartridge), and
the wheel config was already single-valued — none of them carry a design choice.

This module is the single source of truth for the legal per-axis config values.
F2 (self-model) types ``SelfModelConfig`` against these enums, and F3
(parts-catalog-grammar) imports them rather than redefining the value sets.
"""

from __future__ import annotations

from enum import StrEnum


class MotorAllocation(StrEnum):
    DRIVE2_ARM1_CLAW1 = "2drive+1arm+1claw"
    DRIVE2_ARM1 = "2drive+1arm"
    DRIVE2_FLYWHEEL1 = "2drive+1flywheel"


class EndEffector(StrEnum):
    CLAW_GRASPER = "claw_grasper"
    SCOOP = "scoop"
    FLYWHEEL = "flywheel"


class Cartridge(StrEnum):
    RPM_200 = "200rpm"
    RPM_600 = "600rpm"
