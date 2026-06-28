"""ROS-free normalized inputs for later pilot observation construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

from contracts import (
    BridgeHealth,
    ImageBox,
    LocalizationState,
    ManipulatorState,
    PilotAssertion,
    PilotFailure,
    PilotSkillCommand,
    PilotSkillResult,
    PilotTaskPhase,
    Pose2D,
    VisibleObject,
    VisibleTag,
)
from contracts import PilotObservation
from contracts.pilot import (
    MAX_ASSERTIONS,
    MAX_RECENT_FAILURES,
    MAX_VISIBLE_OBJECTS,
    MAX_VISIBLE_TAGS,
)

Objective: TypeAlias = str | None


def unknown_localization(age_ms: int = 0) -> LocalizationState:
    """Return an explicit unknown localization state without fabricating a pose."""
    return LocalizationState(pose=None, confidence=0.0, age_ms=age_ms)


def unknown_manipulator() -> ManipulatorState:
    """Return an explicit unknown manipulator state."""
    return ManipulatorState(arm_deg=None, claw_state="unknown", held_object_id=None)


def stale_bridge(age_ms: int | None = None, fault: str | None = None) -> BridgeHealth:
    """Return an explicit stale bridge state for missing or expired telemetry."""
    return BridgeHealth(state="stale", last_heartbeat_age_ms=age_ms, fault=fault)


@dataclass(frozen=True, slots=True)
class ObservationCache:
    """Normalized in-process inputs for a future bounded PilotObservation builder.

    The cache stores contract-owned component models and keeps missing optional inputs explicit.
    It is intentionally not a schema model and does not construct a final PilotObservation.
    """

    objective: Objective = None
    task_phase: PilotTaskPhase = PilotTaskPhase.IDLE
    robot_pose: Pose2D | None = None
    localization: LocalizationState = field(default_factory=unknown_localization)
    visible_objects: tuple[VisibleObject, ...] = field(default_factory=tuple)
    visible_tags: tuple[VisibleTag, ...] = field(default_factory=tuple)
    manipulator: ManipulatorState = field(default_factory=unknown_manipulator)
    bridge: BridgeHealth = field(default_factory=stale_bridge)
    last_command: PilotSkillCommand | None = None
    last_result: PilotSkillResult | None = None
    recent_failures: tuple[PilotFailure, ...] = field(default_factory=tuple)
    current_assertions: tuple[PilotAssertion, ...] = field(default_factory=tuple)

    @classmethod
    def from_inputs(
        cls,
        *,
        objective: Objective = None,
        task_phase: PilotTaskPhase = PilotTaskPhase.IDLE,
        robot_pose: Pose2D | None = None,
        localization: LocalizationState | None = None,
        visible_objects: list[VisibleObject] | tuple[VisibleObject, ...] = (),
        visible_tags: list[VisibleTag] | tuple[VisibleTag, ...] = (),
        manipulator: ManipulatorState | None = None,
        bridge: BridgeHealth | None = None,
        last_command: PilotSkillCommand | None = None,
        last_result: PilotSkillResult | None = None,
        recent_failures: list[PilotFailure] | tuple[PilotFailure, ...] = (),
        current_assertions: list[PilotAssertion] | tuple[PilotAssertion, ...] = (),
    ) -> ObservationCache:
        """Normalize optional inputs into immutable cache tuples and explicit unknown states."""
        return cls(
            objective=objective,
            task_phase=task_phase,
            robot_pose=robot_pose,
            localization=localization or unknown_localization(),
            visible_objects=tuple(visible_objects),
            visible_tags=tuple(visible_tags),
            manipulator=manipulator or unknown_manipulator(),
            bridge=bridge or stale_bridge(),
            last_command=last_command,
            last_result=last_result,
            recent_failures=tuple(recent_failures),
            current_assertions=tuple(current_assertions),
        )


def build_observation_snapshot(
    cache: ObservationCache,
    *,
    observed_ms: int,
) -> PilotObservation:
    """Compact normalized cache state into a contract-valid pilot observation."""
    if observed_ms < 0:
        raise ValueError("observed_ms must be non-negative")
    if cache.objective is None or not cache.objective.strip():
        raise ValueError("ObservationCache.objective is required")

    return PilotObservation.model_validate(
        {
            "observed_ms": observed_ms,
            "task_phase": cache.task_phase,
            "objective": cache.objective,
            "robot_pose": cache.robot_pose,
            "localization": cache.localization,
            "visible_objects": list(
                sorted_visible_objects(cache.visible_objects)[:MAX_VISIBLE_OBJECTS]
            ),
            "visible_tags": list(sorted_visible_tags(cache.visible_tags)[:MAX_VISIBLE_TAGS]),
            "manipulator": cache.manipulator,
            "bridge": cache.bridge,
            "last_command": cache.last_command,
            "last_result": cache.last_result,
            "recent_failures": list(sorted_failures(cache.recent_failures)[:MAX_RECENT_FAILURES]),
            "current_assertions": list(
                sorted_assertions(cache.current_assertions)[:MAX_ASSERTIONS]
            ),
        }
    )


def _box_sort_key(box: ImageBox | None) -> tuple[int, int, int, int]:
    if box is None:
        return (-1, -1, -1, -1)
    return (box.x_px, box.y_px, box.width_px, box.height_px)


def _pose_sort_key(pose: Pose2D | None) -> tuple[float, float, float]:
    if pose is None:
        return (float("inf"), float("inf"), float("inf"))
    return (pose.x_m, pose.y_m, pose.heading_rad)


def visible_object_sort_key(
    obj: VisibleObject,
) -> tuple[float, str, str, tuple[int, int, int, int]]:
    """Sort high-confidence objects first, then by stable semantic identifiers."""
    return (-obj.confidence, obj.label.casefold(), obj.object_id, _box_sort_key(obj.bbox))


def visible_tag_sort_key(tag: VisibleTag) -> tuple[str, int, float, tuple[float, float, float]]:
    """Sort tags by stable map identity before confidence or pose details."""
    return (tag.family.casefold(), tag.tag_id, -tag.confidence, _pose_sort_key(tag.pose))


def failure_sort_key(failure: PilotFailure) -> tuple[int, str, str, str, str]:
    """Sort recent failures first with stable tie-breakers."""
    return (
        -failure.failed_ms,
        failure.source,
        failure.command_id or "",
        failure.summary,
        failure.recovery_hint or "",
    )


def assertion_sort_key(assertion: PilotAssertion) -> tuple[str, str, str, int, int]:
    """Sort assertions by stable identity, then by caller-provided timing metadata."""
    return (
        assertion.assertion_id,
        assertion.predicate,
        assertion.state,
        assertion.observed_ms if assertion.observed_ms is not None else -1,
        assertion.age_ms if assertion.age_ms is not None else -1,
    )


def sorted_visible_objects(
    objects: list[VisibleObject] | tuple[VisibleObject, ...],
) -> tuple[VisibleObject, ...]:
    return tuple(sorted(objects, key=visible_object_sort_key))


def sorted_visible_tags(tags: list[VisibleTag] | tuple[VisibleTag, ...]) -> tuple[VisibleTag, ...]:
    return tuple(sorted(tags, key=visible_tag_sort_key))


def sorted_failures(
    failures: list[PilotFailure] | tuple[PilotFailure, ...],
) -> tuple[PilotFailure, ...]:
    return tuple(sorted(failures, key=failure_sort_key))


def sorted_assertions(
    assertions: list[PilotAssertion] | tuple[PilotAssertion, ...],
) -> tuple[PilotAssertion, ...]:
    return tuple(sorted(assertions, key=assertion_sort_key))
