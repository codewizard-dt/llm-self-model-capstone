"""The control grammar (F19): wire models for the online control loop.

Defines the closed 6-verb `ControlCommand` discriminated union
(stop/drive/turn/arm/claw/flywheel), `HeartbeatLine`, the outer `ControlLine`
wire union (keyed on `type`), and `AckLine` carrying a closed-set `FaultCode`
`StrEnum`. The module-level wire-limit constants (`MAX_LINEAR`, `MAX_OMEGA`,
`MAX_FLYWHEEL_RPM`, `ARM_DEG_MIN`, `ARM_DEG_MAX`, `TTL_MS_MAX`) are the Pi-side
envelope accepted by the online controller. Brain physical clamps are exported
separately because the guarded V5 firmware intentionally narrows the wire
envelope at the hardware boundary.

Strictly additive to F1+F2+F3+F4: nothing here touches the frozen telemetry
schemas. `ControlLine` carries `type ∈ {"cmd", "heartbeat"}` and `AckLine`
carries `type == "ack"` — the closed `type` discriminator is the single
demultiplexer for the Pi reader thread (D2 / BRAIN_INTERFACE §3.3).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import ConfigDict, Discriminator, Field, Tag, model_validator

from contracts.motor_telemetry import StrictModel


# --- Wire limits + Brain physical clamps ------------------------------------

MAX_LINEAR = 0.35  # m/s   — ROS/Pi command-envelope maximum.
MAX_OMEGA = 0.60  # rad/s — ROS/Pi command-envelope maximum.
MAX_FLYWHEEL_RPM = 3600.0  # output shaft RPM — proposed default; F20 may narrow
MAX_ARM_RPM = 600.0  # V5 motor cartridge upper envelope; F20 may narrow.
MAX_CLAW_GRIP_FORCE_N = 100.0  # permissive target envelope; F20 may narrow.
# `deg` is the *physical arm-joint angle* in degrees (NOT encoder counts): 0° is
# the stowed/down home (claw at the floor), increasing toward a raised claw. The
# as-built claw arm sweeps ~90° (a min/max stall calibration measured encoder
# -125..+1667 motor counts at ~0.05°/enc ≈ -6..+83° of joint travel, ~19:1 geared
# — O1 resolved). The Brain (F20) converts `deg`→encoder target with the
# precise per-build °/enc and clamps physically; F19 only range-checks the wire.
ARM_DEG_MIN = 0.0
ARM_DEG_MAX = 90.0  # measured joint travel (~90° sweep); F20 holds the exact °/enc
TTL_MS_MAX = 5000  # ROS bridge envelope; Brain motion commands narrow this.
BRAIN_MAX_LINEAR = 0.18  # guarded PROS drive clamp for physical Clawbot motion.
BRAIN_TTL_MS_MAX = 500  # guarded PROS per-motion TTL clamp.


# --- FaultCode (D7) — exactly 8 values, closed StrEnum -----------------------


class FaultCode(StrEnum):
    """Closed receipt-fault vocabulary (D7). F20 emits; F19 ships the values."""

    MALFORMED_JSON = "malformed_json"
    UNKNOWN_COMMAND = "unknown_command"
    TTL_EXPIRED = "ttl_expired"
    WATCHDOG = "watchdog"
    ESTOP_LATCHED = "estop_latched"
    OUT_OF_RANGE = "out_of_range"
    OVERSIZED_PACKET = "oversized_packet"
    NOT_ASSEMBLED = "not_assembled"


# --- Envelope (shared by every cmd line + the heartbeat) ---------------------


class ControlEnvelope(StrictModel):
    """Shared envelope for ControlLine lines (commands + heartbeat).

    `type` is the outer discriminator and lives on the wire-line models below,
    not here — keeping the envelope discriminator-free lets pydantic v2's
    discriminated union route cleanly without ambiguity (D4).
    """

    model_config = ConfigDict(extra="forbid", strict=False)

    v: Literal[1] = 1
    seq: int = Field(ge=0, lt=2**32)
    sent_ms: int = Field(ge=0)
    ttl_ms: int = Field(ge=1, le=TTL_MS_MAX)


# --- 6 command bodies (every one is a `type == "cmd"` wire line) -------------


class StopCommand(ControlEnvelope):
    """Stop verb — graceful halt with a structured reason."""

    type: Literal["cmd"] = "cmd"
    cmd: Literal["stop"] = "stop"
    reason: Literal["operator_estop", "operator", "watchdog_self", "fault"]


class DriveCommand(ControlEnvelope):
    """Drive verb — planar velocity command.

    `vy` is wire-locked to 0 (D12): every post-PR-#18 buildable config uses
    `front_omni+rear_standard`, so a holonomic axis is structurally inapplicable
    today. Keeping the field forward-compats a future holonomic kit — drop the
    `le=0` bound, no wire addition.
    """

    type: Literal["cmd"] = "cmd"
    cmd: Literal["drive"] = "drive"
    vx: float = Field(ge=-MAX_LINEAR, le=MAX_LINEAR)
    vy: float = Field(default=0.0, ge=0.0, le=0.0)
    omega: float = Field(ge=-MAX_OMEGA, le=MAX_OMEGA)


class TurnCommand(ControlEnvelope):
    """Turn verb — yaw-rate command (no linear component)."""

    type: Literal["cmd"] = "cmd"
    cmd: Literal["turn"] = "turn"
    omega: float = Field(ge=-MAX_OMEGA, le=MAX_OMEGA)


class ArmCommand(ControlEnvelope):
    """Arm verb — absolute physical joint angle in degrees, optional vel_rpm.

    `deg` is the arm-joint angle (0° stowed/down, ~90° raised), not a motor
    encoder count; the Brain maps it to encoder targets per build. See the
    ARM_DEG_MIN/MAX note above for the as-built calibration.
    """

    type: Literal["cmd"] = "cmd"
    cmd: Literal["arm"] = "arm"
    deg: float = Field(ge=ARM_DEG_MIN, le=ARM_DEG_MAX)
    vel_rpm: float | None = Field(default=None, ge=0.0, le=MAX_ARM_RPM)


class ClawCommand(ControlEnvelope):
    """Claw verb — open/close, optional grip force."""

    type: Literal["cmd"] = "cmd"
    cmd: Literal["claw"] = "claw"
    state: Literal["open", "close"]
    grip_force_N: float | None = Field(default=None, ge=0.0, le=MAX_CLAW_GRIP_FORCE_N)


class FlywheelCommand(ControlEnvelope):
    """Flywheel verb — target output-shaft RPM (non-negative)."""

    type: Literal["cmd"] = "cmd"
    cmd: Literal["flywheel"] = "flywheel"
    rpm: float = Field(ge=0.0, le=MAX_FLYWHEEL_RPM)


# --- Inner discriminated union (cmd-keyed, the 6 verbs) ----------------------

ControlCommand = Annotated[
    Union[
        StopCommand,
        DriveCommand,
        TurnCommand,
        ArmCommand,
        ClawCommand,
        FlywheelCommand,
    ],
    Field(discriminator="cmd"),
]


# --- Heartbeat (the second `type` value on the command stream) ---------------


class HeartbeatLine(ControlEnvelope):
    """Heartbeat line — envelope-only, no `cmd` field."""

    type: Literal["heartbeat"] = "heartbeat"


# --- Outer discriminated union (type-keyed, the wire shape) ------------------
#
# The 6 command bodies all share `type: Literal["cmd"]`, which collides on a
# flat type-keyed union. Per D4, we use pydantic v2's callable-Discriminator +
# Tag pattern: route on `type` to either the inner cmd-keyed ControlCommand
# union (for `type == "cmd"`) or to HeartbeatLine (for `type == "heartbeat"`).
# The wire shape stays exactly `{v, seq, type, sent_ms, ttl_ms, cmd, ...body}`
# for cmd lines and `{v, seq, type='heartbeat', sent_ms, ttl_ms}` for the
# heartbeat — no internal wrapper key surfaces on the wire.


def _control_line_discriminator(value: object) -> str | None:
    """Return the outer-union tag for a candidate wire line.

    Handles both raw dicts (from `validate_python` / `validate_json`) and
    already-validated model instances (from `model_dump` / passthrough).
    """

    if isinstance(value, dict):
        return value.get("type")
    return getattr(value, "type", None)


ControlLine = Annotated[
    Union[
        Annotated[ControlCommand, Tag("cmd")],
        Annotated[HeartbeatLine, Tag("heartbeat")],
    ],
    Discriminator(_control_line_discriminator),
]


# --- AckLine — receipt + lightweight bridge health ---------------------------


class AckLine(StrictModel):
    """Brain → Pi receipt for a single command seq.

    `state` is the closed set {ok, rejected, stale} (D6); the model validator
    enforces `fault is None iff state == "ok"`, `state == "rejected"` requires
    a non-null fault, and `state == "stale"` accepts either (typical fault is
    `ttl_expired`). The optional health fields match the guarded V5 Brain
    firmware proven in PR #21; streaming motor samples remain on telemetry.
    """

    model_config = ConfigDict(extra="forbid", strict=False)

    v: Literal[1] = 1
    type: Literal["ack"] = "ack"
    ack: int = Field(ge=0, lt=2**32)
    state: Literal["ok", "rejected", "stale"]
    recv_ms: int = Field(ge=0)
    fault: FaultCode | None = None
    battery_mv: int | None = Field(default=None, ge=0)
    battery_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    watchdog_age_ms: int | None = Field(default=None, ge=0)
    estop: bool | None = None
    motion_enabled: bool | None = None
    drive_ports_ok: bool | None = None
    motor_ports: list[int] | None = None

    @model_validator(mode="after")
    def _enforce_state_fault_invariants(self) -> AckLine:
        if self.state == "ok" and self.fault is not None:
            raise ValueError("state='ok' requires fault is None")
        if self.state == "rejected" and self.fault is None:
            raise ValueError("state='rejected' requires a non-null fault")
        # state == "stale" accepts either (typical: fault == "ttl_expired")
        return self
