"""Tests for the control grammar (F19): envelope, 7-verb union, heartbeat, ack.

Covers every acceptance id in `.ai-sdd/artifacts/feature-plan.v1.yaml` for the
models-and-schemas slice: round-trip parse of every wire-line shape, the
discriminated-union failure modes, the per-command range bounds (incl. the
`vy == 0` lock — D12), envelope shape, ack invariants, clamp-constant identity,
the FaultCode closed-set check, and the cross-contract demux invariant against
F1's ContractLine on the shared USB user-port stream.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from contracts import (
    ARM_DEG_MAX,
    ARM_DEG_MIN,
    BRAIN_MAX_LINEAR,
    BRAIN_TTL_MS_MAX,
    MAX_ARM_RPM,
    MAX_CLAW_GRIP_FORCE_N,
    MAX_FLYWHEEL_RPM,
    MAX_LINEAR,
    MAX_OMEGA,
    ROUTINE_SLOT_MAX,
    ROUTINE_SLOT_MIN,
    TTL_MS_MAX,
    AckLine,
    ArmCommand,
    ClawCommand,
    ContractLine,
    ControlLine,
    DriveCommand,
    FaultCode,
    FlywheelCommand,
    HeartbeatLine,
    RoutineCommand,
    StopCommand,
    TurnCommand,
)

CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
SESSION_EXAMPLE = CONTRACTS_ROOT / "fixtures" / "session_example.jsonl"

CONTROL_LINE_TA = TypeAdapter(ControlLine)


# --- envelope template -------------------------------------------------------


def _env(**overrides) -> dict:
    base = {"v": 1, "seq": 7, "sent_ms": 1000, "ttl_ms": 500}
    base.update(overrides)
    return base


# --- acc-test-roundtrip-commands --------------------------------------------


@pytest.mark.parametrize(
    "payload,expected_cls",
    [
        (_env(type="cmd", cmd="stop", reason="operator_estop"), StopCommand),
        (_env(type="cmd", cmd="drive", vx=0.1, omega=0.2), DriveCommand),
        (_env(type="cmd", cmd="turn", omega=-0.3), TurnCommand),
        (_env(type="cmd", cmd="arm", deg=45.0), ArmCommand),
        (_env(type="cmd", cmd="arm", deg=45.0, vel_rpm=30.0), ArmCommand),
        (_env(type="cmd", cmd="claw", state="open"), ClawCommand),
        (_env(type="cmd", cmd="claw", state="close", grip_force_N=12.0), ClawCommand),
        (_env(type="cmd", cmd="flywheel", rpm=1800.0), FlywheelCommand),
        (_env(type="cmd", cmd="routine", slot=2), RoutineCommand),
        (_env(type="cmd", cmd="routine", slot=4), RoutineCommand),
    ],
)
def test_roundtrip_each_command_verb(payload, expected_cls):
    parsed = CONTROL_LINE_TA.validate_python(payload)
    assert isinstance(parsed, expected_cls)
    dumped = parsed.model_dump()
    # Wire shape preserved: every input key round-trips intact.
    for key, value in payload.items():
        assert dumped[key] == value
    # JSON-string parse path round-trips too.
    parsed_json = CONTROL_LINE_TA.validate_json(json.dumps(payload))
    assert isinstance(parsed_json, expected_cls)


# --- acc-test-roundtrip-heartbeat -------------------------------------------


def test_roundtrip_heartbeat():
    payload = _env(type="heartbeat")
    parsed = CONTROL_LINE_TA.validate_python(payload)
    assert isinstance(parsed, HeartbeatLine)
    dumped = parsed.model_dump()
    assert dumped == {"v": 1, "seq": 7, "sent_ms": 1000, "ttl_ms": 500, "type": "heartbeat"}
    assert "cmd" not in dumped


# --- acc-test-roundtrip-ack -------------------------------------------------


def test_roundtrip_ack_ok():
    payload = {"v": 1, "type": "ack", "ack": 42, "state": "ok", "recv_ms": 1234}
    ack = AckLine.model_validate(payload)
    assert ack.state == "ok"
    assert ack.fault is None
    dumped = ack.model_dump(exclude_none=True)
    assert dumped == {
        "v": 1,
        "type": "ack",
        "ack": 42,
        "state": "ok",
        "recv_ms": 1234,
    }


# --- acc-test-discriminator-unknown-cmd -------------------------------------


def test_unknown_cmd_rejected():
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="fly"))


# --- acc-test-discriminator-unknown-type ------------------------------------


def test_unknown_type_rejected():
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="telemetry"))


# --- acc-test-discriminator-missing-cmd -------------------------------------


def test_missing_cmd_on_cmd_line_rejected():
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd"))


# --- acc-test-discriminator-missing-body-field ------------------------------


def test_drive_missing_vx_rejected():
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="drive", omega=0.2))


def test_drive_missing_omega_rejected():
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="drive", vx=0.1))


# --- acc-test-range-vx ------------------------------------------------------


@pytest.mark.parametrize("vx", [MAX_LINEAR + 1e-6, -MAX_LINEAR - 1e-6, 1.0, -1.0])
def test_drive_vx_out_of_range_rejected(vx):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="drive", vx=vx, omega=0.0))


# --- acc-test-vy-locked (D12) -----------------------------------------------


@pytest.mark.parametrize("vy", [0.01, -0.01, 0.1, -0.1])
def test_drive_vy_must_be_zero(vy):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="drive", vx=0.1, vy=vy, omega=0.0))


# --- acc-test-range-omega ---------------------------------------------------


@pytest.mark.parametrize("omega", [MAX_OMEGA + 1e-6, -MAX_OMEGA - 1e-6])
def test_drive_omega_out_of_range_rejected(omega):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="drive", vx=0.0, omega=omega))


@pytest.mark.parametrize("omega", [MAX_OMEGA + 1e-6, -MAX_OMEGA - 1e-6])
def test_turn_omega_out_of_range_rejected(omega):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="turn", omega=omega))


# --- acc-test-range-arm -----------------------------------------------------


@pytest.mark.parametrize("deg", [ARM_DEG_MIN - 1e-6, ARM_DEG_MAX + 1e-6, -1.0, 91.0])
def test_arm_deg_out_of_range_rejected(deg):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="arm", deg=deg))


@pytest.mark.parametrize("vel_rpm", [-0.1, MAX_ARM_RPM + 0.1, 999999.0])
def test_arm_vel_rpm_out_of_range_rejected(vel_rpm):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="arm", deg=45.0, vel_rpm=vel_rpm))


def test_arm_vel_rpm_boundaries_accepted():
    CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="arm", deg=45.0, vel_rpm=0.0))
    CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="arm", deg=45.0, vel_rpm=MAX_ARM_RPM))


@pytest.mark.parametrize("grip_force_N", [-0.1, MAX_CLAW_GRIP_FORCE_N + 0.1, 999999999.0])
def test_claw_grip_force_out_of_range_rejected(grip_force_N):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(
            _env(type="cmd", cmd="claw", state="close", grip_force_N=grip_force_N)
        )


def test_claw_grip_force_boundaries_accepted():
    CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="claw", state="close", grip_force_N=0.0))
    CONTROL_LINE_TA.validate_python(
        _env(type="cmd", cmd="claw", state="close", grip_force_N=MAX_CLAW_GRIP_FORCE_N)
    )


# --- acc-test-range-flywheel ------------------------------------------------


@pytest.mark.parametrize("rpm", [-0.1, MAX_FLYWHEEL_RPM + 0.1, -1.0])
def test_flywheel_rpm_out_of_range_rejected(rpm):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="flywheel", rpm=rpm))


# --- acc-test-range-routine-slot --------------------------------------------


@pytest.mark.parametrize(
    "slot",
    [
        ROUTINE_SLOT_MIN - 1,
        ROUTINE_SLOT_MAX + 1,
        -1,
        0,
        99,
    ],
)
def test_routine_slot_out_of_range_rejected(slot):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="routine", slot=slot))


# --- acc-test-range-ttl -----------------------------------------------------


@pytest.mark.parametrize("ttl_ms", [0, -1, TTL_MS_MAX + 1])
def test_ttl_ms_out_of_range_rejected(ttl_ms):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(
            _env(ttl_ms=ttl_ms, type="cmd", cmd="stop", reason="operator")
        )


def test_ttl_ms_boundaries_accepted():
    CONTROL_LINE_TA.validate_python(_env(ttl_ms=1, type="cmd", cmd="stop", reason="operator"))
    CONTROL_LINE_TA.validate_python(
        _env(ttl_ms=TTL_MS_MAX, type="cmd", cmd="stop", reason="operator")
    )


# --- acc-test-envelope-v ----------------------------------------------------


def test_v_must_be_one():
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(v=2, type="cmd", cmd="stop", reason="operator"))
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(v=0, type="heartbeat"))
    with pytest.raises(ValidationError):
        AckLine.model_validate({"v": 2, "type": "ack", "ack": 1, "state": "ok", "recv_ms": 1})


# --- acc-test-envelope-extras -----------------------------------------------


def test_extras_forbidden_on_every_model():
    # Envelope-level extras
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(
            _env(type="cmd", cmd="stop", reason="operator", extra_key="bad")
        )
    # Heartbeat extras
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="heartbeat", extra_key="bad"))
    # Body-level extras on drive
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(type="cmd", cmd="drive", vx=0.0, omega=0.0, junk=1))
    # AckLine extras
    with pytest.raises(ValidationError):
        AckLine.model_validate(
            {
                "v": 1,
                "type": "ack",
                "ack": 1,
                "state": "ok",
                "recv_ms": 1,
                "extra_key": "bad",
            }
        )


# --- acc-test-envelope-seq --------------------------------------------------


@pytest.mark.parametrize("seq", [-1, 2**32, 2**32 + 1])
def test_seq_out_of_range_rejected(seq):
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(_env(seq=seq, type="cmd", cmd="stop", reason="operator"))


def test_seq_boundaries_accepted():
    CONTROL_LINE_TA.validate_python(_env(seq=0, type="cmd", cmd="stop", reason="operator"))
    CONTROL_LINE_TA.validate_python(_env(seq=2**32 - 1, type="cmd", cmd="stop", reason="operator"))


# --- acc-test-ack-ok-with-fault ---------------------------------------------


def test_ack_ok_with_fault_rejected():
    with pytest.raises(ValidationError):
        AckLine.model_validate(
            {
                "v": 1,
                "type": "ack",
                "ack": 1,
                "state": "ok",
                "recv_ms": 1,
                "fault": "ttl_expired",
            }
        )


# --- acc-test-ack-rejected-without-fault ------------------------------------


def test_ack_rejected_without_fault_rejected():
    with pytest.raises(ValidationError):
        AckLine.model_validate({"v": 1, "type": "ack", "ack": 1, "state": "rejected", "recv_ms": 1})
    with pytest.raises(ValidationError):
        AckLine.model_validate(
            {
                "v": 1,
                "type": "ack",
                "ack": 1,
                "state": "rejected",
                "recv_ms": 1,
                "fault": None,
            }
        )


# --- acc-test-ack-stale-with-fault ------------------------------------------


def test_ack_stale_with_fault_accepted():
    ack = AckLine.model_validate(
        {
            "v": 1,
            "type": "ack",
            "ack": 1,
            "state": "stale",
            "recv_ms": 1,
            "fault": "ttl_expired",
        }
    )
    assert ack.state == "stale"
    assert ack.fault is FaultCode.TTL_EXPIRED


def test_ack_stale_without_fault_accepted():
    # D6: stale accepts either; the model validator does not require a fault.
    ack = AckLine.model_validate({"v": 1, "type": "ack", "ack": 1, "state": "stale", "recv_ms": 1})
    assert ack.state == "stale"
    assert ack.fault is None


# --- acc-test-ack-ok-no-fault -----------------------------------------------


def test_ack_ok_no_fault_accepted():
    ack = AckLine.model_validate(
        {"v": 1, "type": "ack", "ack": 1, "state": "ok", "recv_ms": 1, "fault": None}
    )
    assert ack.state == "ok"
    assert ack.fault is None


def test_ack_rejected_with_fault_accepted():
    ack = AckLine.model_validate(
        {
            "v": 1,
            "type": "ack",
            "ack": 1,
            "state": "rejected",
            "recv_ms": 1,
            "fault": "out_of_range",
        }
    )
    assert ack.fault is FaultCode.OUT_OF_RANGE


def test_live_guarded_brain_ack_shape_accepted():
    ack = AckLine.model_validate(
        {
            "v": 1,
            "ack": 120,
            "battery_mv": 13421,
            "battery_pct": 34.0,
            "arm_port_ok": True,
            "drive_ports_ok": True,
            "estop": False,
            "fault": None,
            "motion_enabled": True,
            "motor_ports": [1, 3, 8, 10],
            "recv_ms": 20407,
            "routine_active": False,
            "state": "ok",
            "type": "ack",
            "watchdog_age_ms": 0,
        }
    )

    assert ack.state == "ok"
    assert ack.battery_mv == 13421
    assert ack.arm_port_ok is True
    assert ack.motion_enabled is True
    assert ack.routine_active is False
    assert ack.motor_ports == [1, 3, 8, 10]


# --- acc-test-clamp-identity (D10/C1) ---------------------------------------


def test_clamp_constants_bit_for_bit():
    assert MAX_LINEAR == 0.35
    assert MAX_OMEGA == 0.60
    assert MAX_FLYWHEEL_RPM == 3600.0
    assert MAX_ARM_RPM == 600.0
    assert MAX_CLAW_GRIP_FORCE_N == 100.0
    assert ROUTINE_SLOT_MIN == 2
    assert ROUTINE_SLOT_MAX == 4
    assert ARM_DEG_MIN == 0.0
    assert ARM_DEG_MAX == 90.0
    assert TTL_MS_MAX == 5000
    assert BRAIN_MAX_LINEAR == 0.18
    assert BRAIN_TTL_MS_MAX == 500


# --- acc-test-faultcode-closed (D7) -----------------------------------------


def test_faultcode_is_closed_9_value_strenum():
    expected = {
        "malformed_json",
        "unknown_command",
        "ttl_expired",
        "watchdog",
        "estop_latched",
        "out_of_range",
        "oversized_packet",
        "not_assembled",
        "busy",
    }
    assert {member.value for member in FaultCode} == expected
    # str-subclass semantics — StrEnum members compare equal to their string value.
    assert FaultCode.NOT_ASSEMBLED == "not_assembled"
    assert FaultCode.MALFORMED_JSON == "malformed_json"


# --- acc-test-cross-contract-demux (D2 invariant) ---------------------------


def test_cross_contract_demux_against_contract_line():
    """A ContractLine fixture MUST parse as ContractLine and FAIL as ControlLine.

    Proves the `type` discriminator is mutually exclusive across the F1
    telemetry and F19 control streams on the shared USB user-port stream.
    """

    line = next(L for L in SESSION_EXAMPLE.read_text().splitlines() if L.strip())
    payload = json.loads(line)
    # Regression sanity: ContractLine still parses.
    ContractLine.model_validate(payload)
    # ControlLine MUST reject — no `type` collision.
    with pytest.raises(ValidationError):
        CONTROL_LINE_TA.validate_python(payload)


# --- additional sanity: closed type discriminator on AckLine ---------------


def test_ack_type_locked_to_ack():
    with pytest.raises(ValidationError):
        AckLine.model_validate({"v": 1, "type": "cmd", "ack": 1, "state": "ok", "recv_ms": 1})
