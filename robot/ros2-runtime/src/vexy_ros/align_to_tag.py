from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .bridge_protocol import clamp

STOP_REASONS = {
    "success",
    "timeout",
    "cancelled",
    "stale_tag",
    "stale_ack",
    "bridge_fault",
}


@dataclass(frozen=True)
class AlignToTagGoal:
    tag_id: int = 0
    target_distance_m: float = 0.45
    yaw_tolerance_rad: float = 0.05
    lateral_tolerance_m: float = 0.03
    distance_tolerance_m: float = 0.05
    timeout_s: float = 8.0
    max_step_ms: int = 150
    max_vx: float = 0.12
    max_vy: float = 0.08
    max_omega: float = 0.25
    tag_stale_s: float = 0.5
    ack_stale_s: float = 0.8


@dataclass(frozen=True)
class TagObservation:
    tag_id: int
    stamp_s: float
    yaw_error_rad: float
    lateral_error_m: float
    distance_m: float
    confidence: float | None = None


@dataclass(frozen=True)
class BridgeHealth:
    stamp_s: float | None
    last_ack_seq: int | None = None
    fault: str | None = None
    status: str = "unknown"


@dataclass(frozen=True)
class VexCommand:
    cmd: Literal["drive", "turn", "stop"]
    ttl_ms: int
    vx: float = 0.0
    vy: float = 0.0
    omega: float = 0.0
    reason: str | None = None


@dataclass(frozen=True)
class AlignFeedback:
    active: bool
    reason: str
    tag_visible: bool
    yaw_error_rad: float | None
    lateral_error_m: float | None
    distance_error_m: float | None
    last_ack_seq: int | None
    fault: str | None


@dataclass(frozen=True)
class AlignResult:
    success: bool
    reason: str
    final_yaw_error_rad: float | None = None
    final_lateral_error_m: float | None = None
    final_distance_error_m: float | None = None
    fault: str | None = None


@dataclass(frozen=True)
class AlignDecision:
    feedback: AlignFeedback
    command: VexCommand | None = None
    result: AlignResult | None = None


def bounded_goal(goal: AlignToTagGoal) -> AlignToTagGoal:
    return AlignToTagGoal(
        tag_id=max(0, int(goal.tag_id)),
        target_distance_m=clamp(float(goal.target_distance_m), 0.1, 2.0),
        yaw_tolerance_rad=clamp(float(goal.yaw_tolerance_rad), 0.01, 0.5),
        lateral_tolerance_m=clamp(float(goal.lateral_tolerance_m), 0.005, 0.5),
        distance_tolerance_m=clamp(float(goal.distance_tolerance_m), 0.01, 0.75),
        timeout_s=clamp(float(goal.timeout_s), 0.5, 30.0),
        max_step_ms=int(clamp(int(goal.max_step_ms), 20, 500)),
        max_vx=clamp(abs(float(goal.max_vx)), 0.01, 0.25),
        max_vy=clamp(abs(float(goal.max_vy)), 0.01, 0.20),
        max_omega=clamp(abs(float(goal.max_omega)), 0.02, 0.6),
        tag_stale_s=clamp(float(goal.tag_stale_s), 0.05, 2.0),
        ack_stale_s=clamp(float(goal.ack_stale_s), 0.05, 3.0),
    )


class AlignToTagController:
    def __init__(self) -> None:
        self.goal: AlignToTagGoal | None = None
        self.started_at_s: float | None = None

    @property
    def active(self) -> bool:
        return self.goal is not None and self.started_at_s is not None

    def start(
        self,
        goal: AlignToTagGoal,
        *,
        now_s: float,
        tag: TagObservation | None,
        bridge: BridgeHealth,
    ) -> AlignDecision:
        bounded = bounded_goal(goal)
        readiness = self._readiness_result(bounded, now_s, tag, bridge)
        if readiness is not None:
            return AlignDecision(
                feedback=self._feedback(
                    bounded, tag, bridge, readiness.reason, active=False
                ),
                result=readiness,
            )

        self.goal = bounded
        self.started_at_s = now_s
        return AlignDecision(
            feedback=self._feedback(bounded, tag, bridge, "started", active=True)
        )

    def step(
        self,
        *,
        now_s: float,
        tag: TagObservation | None,
        bridge: BridgeHealth,
        cancel: bool = False,
    ) -> AlignDecision:
        if not self.active or self.goal is None or self.started_at_s is None:
            return AlignDecision(
                feedback=AlignFeedback(
                    active=False,
                    reason="idle",
                    tag_visible=False,
                    yaw_error_rad=None,
                    lateral_error_m=None,
                    distance_error_m=None,
                    last_ack_seq=bridge.last_ack_seq,
                    fault=bridge.fault,
                )
            )

        goal = self.goal
        if cancel:
            return self._finish(goal, tag, bridge, reason="cancelled", success=False)

        readiness = self._readiness_result(goal, now_s, tag, bridge)
        if readiness is not None:
            return self._finish(
                goal,
                tag,
                bridge,
                reason=readiness.reason,
                success=False,
                fault=readiness.fault,
            )

        if now_s - self.started_at_s >= goal.timeout_s:
            return self._finish(goal, tag, bridge, reason="timeout", success=False)

        assert tag is not None
        distance_error_m = tag.distance_m - goal.target_distance_m
        if (
            abs(tag.yaw_error_rad) <= goal.yaw_tolerance_rad
            and abs(tag.lateral_error_m) <= goal.lateral_tolerance_m
            and abs(distance_error_m) <= goal.distance_tolerance_m
        ):
            return self._finish(goal, tag, bridge, reason="success", success=True)

        command = self._movement_command(goal, tag, distance_error_m)
        return AlignDecision(
            feedback=self._feedback(goal, tag, bridge, "running", active=True),
            command=command,
        )

    def _readiness_result(
        self,
        goal: AlignToTagGoal,
        now_s: float,
        tag: TagObservation | None,
        bridge: BridgeHealth,
    ) -> AlignResult | None:
        if bridge.fault:
            return AlignResult(False, "bridge_fault", fault=bridge.fault)
        if bridge.stamp_s is None or now_s - bridge.stamp_s > goal.ack_stale_s:
            return AlignResult(False, "stale_ack", fault="stale_ack")
        if tag is None or tag.tag_id != goal.tag_id:
            return AlignResult(False, "stale_tag", fault="tag_not_visible")
        if now_s - tag.stamp_s > goal.tag_stale_s:
            return AlignResult(False, "stale_tag", fault="tag_stale")
        return None

    def _movement_command(
        self, goal: AlignToTagGoal, tag: TagObservation, distance_error_m: float
    ) -> VexCommand:
        vx = clamp(0.45 * distance_error_m, -goal.max_vx, goal.max_vx)
        vy = clamp(-0.6 * tag.lateral_error_m, -goal.max_vy, goal.max_vy)
        omega = clamp(0.9 * tag.yaw_error_rad, -goal.max_omega, goal.max_omega)
        return VexCommand("drive", ttl_ms=goal.max_step_ms, vx=vx, vy=vy, omega=omega)

    def _finish(
        self,
        goal: AlignToTagGoal,
        tag: TagObservation | None,
        bridge: BridgeHealth,
        *,
        reason: str,
        success: bool,
        fault: str | None = None,
    ) -> AlignDecision:
        self.goal = None
        self.started_at_s = None
        final = self._result(goal, tag, reason=reason, success=success, fault=fault)
        return AlignDecision(
            feedback=self._feedback(
                goal, tag, bridge, reason, active=False, fault=fault
            ),
            command=VexCommand(
                "stop", ttl_ms=min(goal.max_step_ms, 250), reason=reason
            ),
            result=final,
        )

    def _feedback(
        self,
        goal: AlignToTagGoal,
        tag: TagObservation | None,
        bridge: BridgeHealth,
        reason: str,
        *,
        active: bool,
        fault: str | None = None,
    ) -> AlignFeedback:
        return AlignFeedback(
            active=active,
            reason=reason,
            tag_visible=tag is not None and tag.tag_id == goal.tag_id,
            yaw_error_rad=None if tag is None else tag.yaw_error_rad,
            lateral_error_m=None if tag is None else tag.lateral_error_m,
            distance_error_m=None
            if tag is None
            else tag.distance_m - goal.target_distance_m,
            last_ack_seq=bridge.last_ack_seq,
            fault=fault or bridge.fault,
        )

    def _result(
        self,
        goal: AlignToTagGoal,
        tag: TagObservation | None,
        *,
        reason: str,
        success: bool,
        fault: str | None,
    ) -> AlignResult:
        return AlignResult(
            success=success,
            reason=reason,
            final_yaw_error_rad=None if tag is None else tag.yaw_error_rad,
            final_lateral_error_m=None if tag is None else tag.lateral_error_m,
            final_distance_error_m=None
            if tag is None
            else tag.distance_m - goal.target_distance_m,
            fault=fault,
        )
