from __future__ import annotations

from dataclasses import dataclass

from .align_to_tag import BridgeHealth, VexCommand
from .bridge_protocol import clamp


@dataclass(frozen=True)
class SurveyScanGoal:
    duration_s: float = 14.5
    omega_rad_s: float = 0.45
    max_step_ms: int = 180
    ack_stale_s: float = 0.8
    telemetry_stale_s: float = 1.0


@dataclass(frozen=True)
class SurveyTelemetry:
    stamp_s: float | None
    motion_enabled: bool = False
    estop: bool = False
    drive_ports_ok: bool = False
    left_pos_deg: float | None = None
    right_pos_deg: float | None = None
    left_vel_rpm: float | None = None
    right_vel_rpm: float | None = None


@dataclass(frozen=True)
class SurveyFeedback:
    active: bool
    reason: str
    elapsed_s: float | None
    observed_tag_ids: list[int]
    last_ack_seq: int | None
    telemetry_seen: bool
    fault: str | None = None


@dataclass(frozen=True)
class SurveyResult:
    success: bool
    reason: str
    duration_s: float
    observed_tag_ids: list[int]
    final_left_pos_deg: float | None = None
    final_right_pos_deg: float | None = None
    fault: str | None = None


@dataclass(frozen=True)
class SurveyDecision:
    feedback: SurveyFeedback
    command: VexCommand | None = None
    result: SurveyResult | None = None


def bounded_goal(goal: SurveyScanGoal) -> SurveyScanGoal:
    omega = clamp(float(goal.omega_rad_s), -0.5, 0.5)
    if abs(omega) < 0.02:
        omega = -0.02 if omega < 0.0 else 0.02
    return SurveyScanGoal(
        duration_s=clamp(float(goal.duration_s), 0.2, 20.0),
        omega_rad_s=omega,
        max_step_ms=int(clamp(int(goal.max_step_ms), 20, 250)),
        ack_stale_s=clamp(float(goal.ack_stale_s), 0.05, 3.0),
        telemetry_stale_s=clamp(float(goal.telemetry_stale_s), 0.05, 3.0),
    )


class SurveyScanController:
    def __init__(self) -> None:
        self.goal: SurveyScanGoal | None = None
        self.started_at_s: float | None = None
        self.observed_tag_ids: set[int] = set()

    @property
    def active(self) -> bool:
        return self.goal is not None and self.started_at_s is not None

    def start(
        self,
        goal: SurveyScanGoal,
        *,
        now_s: float,
        bridge: BridgeHealth,
        telemetry: SurveyTelemetry,
        observed_tag_ids: list[int] | None = None,
    ) -> SurveyDecision:
        bounded = bounded_goal(goal)
        was_active = self.active
        self.observed_tag_ids = set(observed_tag_ids or [])
        readiness = self._readiness_result(bounded, now_s, bridge, telemetry)
        if readiness is not None:
            self.goal = None
            self.started_at_s = None
            return SurveyDecision(
                feedback=self._feedback(
                    bounded,
                    now_s,
                    bridge,
                    telemetry,
                    readiness.reason,
                    active=False,
                    fault=readiness.fault,
                ),
                command=VexCommand(
                    "stop",
                    ttl_ms=min(bounded.max_step_ms, 250),
                    reason=readiness.reason,
                )
                if was_active
                else None,
                result=readiness,
            )

        self.goal = bounded
        self.started_at_s = now_s
        return SurveyDecision(
            feedback=self._feedback(
                bounded, now_s, bridge, telemetry, "started", active=True
            )
        )

    def step(
        self,
        *,
        now_s: float,
        bridge: BridgeHealth,
        telemetry: SurveyTelemetry,
        observed_tag_ids: list[int] | None = None,
        cancel: bool = False,
    ) -> SurveyDecision:
        if observed_tag_ids:
            self.observed_tag_ids.update(observed_tag_ids)

        if not self.active or self.goal is None or self.started_at_s is None:
            return SurveyDecision(
                feedback=SurveyFeedback(
                    active=False,
                    reason="idle",
                    elapsed_s=None,
                    observed_tag_ids=sorted(self.observed_tag_ids),
                    last_ack_seq=bridge.last_ack_seq,
                    telemetry_seen=telemetry.stamp_s is not None,
                    fault=bridge.fault,
                )
            )

        goal = self.goal
        if cancel:
            return self._finish(
                goal, now_s, bridge, telemetry, reason="cancelled", success=False
            )

        readiness = self._readiness_result(goal, now_s, bridge, telemetry)
        if readiness is not None:
            return self._finish(
                goal,
                now_s,
                bridge,
                telemetry,
                reason=readiness.reason,
                success=False,
                fault=readiness.fault,
            )

        elapsed_s = now_s - self.started_at_s
        if elapsed_s >= goal.duration_s:
            return self._finish(
                goal, now_s, bridge, telemetry, reason="success", success=True
            )

        return SurveyDecision(
            feedback=self._feedback(goal, now_s, bridge, telemetry, "running", True),
            command=VexCommand("turn", ttl_ms=goal.max_step_ms, omega=goal.omega_rad_s),
        )

    def _readiness_result(
        self,
        goal: SurveyScanGoal,
        now_s: float,
        bridge: BridgeHealth,
        telemetry: SurveyTelemetry,
    ) -> SurveyResult | None:
        if bridge.fault:
            return self._result(goal, telemetry, "bridge_fault", False, bridge.fault)
        if bridge.stamp_s is None or now_s - bridge.stamp_s > goal.ack_stale_s:
            return self._result(goal, telemetry, "stale_ack", False, "stale_ack")
        if (
            telemetry.stamp_s is None
            or now_s - telemetry.stamp_s > goal.telemetry_stale_s
        ):
            return self._result(
                goal, telemetry, "stale_telemetry", False, "stale_telemetry"
            )
        if telemetry.estop:
            return self._result(goal, telemetry, "estop", False, "estop")
        if not telemetry.motion_enabled:
            return self._result(
                goal, telemetry, "motion_disabled", False, "motion_disabled"
            )
        if not telemetry.drive_ports_ok:
            return self._result(goal, telemetry, "drive_fault", False, "drive_fault")
        return None

    def _finish(
        self,
        goal: SurveyScanGoal,
        now_s: float,
        bridge: BridgeHealth,
        telemetry: SurveyTelemetry,
        *,
        reason: str,
        success: bool,
        fault: str | None = None,
    ) -> SurveyDecision:
        self.goal = None
        self.started_at_s = None
        return SurveyDecision(
            feedback=self._feedback(
                goal, now_s, bridge, telemetry, reason, active=False, fault=fault
            ),
            command=VexCommand(
                "stop", ttl_ms=min(goal.max_step_ms, 250), reason=reason
            ),
            result=self._result(goal, telemetry, reason, success, fault),
        )

    def _feedback(
        self,
        goal: SurveyScanGoal,
        now_s: float,
        bridge: BridgeHealth,
        telemetry: SurveyTelemetry,
        reason: str,
        active: bool,
        fault: str | None = None,
    ) -> SurveyFeedback:
        elapsed_s = (
            None if self.started_at_s is None else max(0.0, now_s - self.started_at_s)
        )
        return SurveyFeedback(
            active=active,
            reason=reason,
            elapsed_s=elapsed_s,
            observed_tag_ids=sorted(self.observed_tag_ids),
            last_ack_seq=bridge.last_ack_seq,
            telemetry_seen=telemetry.stamp_s is not None,
            fault=fault or bridge.fault,
        )

    def _result(
        self,
        goal: SurveyScanGoal,
        telemetry: SurveyTelemetry,
        reason: str,
        success: bool,
        fault: str | None,
    ) -> SurveyResult:
        return SurveyResult(
            success=success,
            reason=reason,
            duration_s=goal.duration_s,
            observed_tag_ids=sorted(self.observed_tag_ids),
            final_left_pos_deg=telemetry.left_pos_deg,
            final_right_pos_deg=telemetry.right_pos_deg,
            fault=fault,
        )
