"""ROS-free assertion context and foundation builders for the pilot loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from contracts import AssertionEvidence, AssertionState, PilotAssertion, PilotObservation

AssertionId: TypeAlias = Literal[
    "target_ball_visible",
    "robot_pose_reliable",
    "ball_reachable",
    "ball_centered_for_grasp",
    "grasp_likely",
    "carrying_ball",
    "at_destination",
    "drop_likely",
    "ball_at_destination",
]

REQUIRED_ASSERTION_IDS: tuple[AssertionId, ...] = (
    "target_ball_visible",
    "robot_pose_reliable",
    "ball_reachable",
    "ball_centered_for_grasp",
    "grasp_likely",
    "carrying_ball",
    "at_destination",
    "drop_likely",
    "ball_at_destination",
)

_REQUIRED_ASSERTION_ID_SET = frozenset(REQUIRED_ASSERTION_IDS)


@dataclass(frozen=True, slots=True)
class AssertionTarget:
    """Task target selection for assertion evaluation."""

    label: str = "ball"
    object_id: str | None = None

    def __post_init__(self) -> None:
        _require_non_blank("label", self.label)
        if self.object_id is not None:
            _require_non_blank("object_id", self.object_id)


@dataclass(frozen=True, slots=True)
class AssertionDestination:
    """Task destination selection for assertion evaluation."""

    destination_id: str = "destination"
    tag_id: int | None = None
    x_m: float | None = None
    y_m: float | None = None

    def __post_init__(self) -> None:
        _require_non_blank("destination_id", self.destination_id)
        if self.tag_id is not None and self.tag_id < 0:
            raise ValueError("tag_id must be non-negative")


@dataclass(frozen=True, slots=True)
class AssertionConfig:
    """Pilot-local thresholds for future assertion heuristics."""

    visible_confidence_min: float = 0.65
    pose_confidence_min: float = 0.70
    grasp_confidence_min: float = 0.65
    delivery_confidence_min: float = 0.65
    localization_max_age_ms: int = 500
    bridge_max_age_ms: int = 500
    reachability_distance_m: float = 0.45
    image_center_tolerance_px: int = 24
    grasp_corridor_tolerance_px: int = 32

    def __post_init__(self) -> None:
        for field_name in (
            "visible_confidence_min",
            "pose_confidence_min",
            "grasp_confidence_min",
            "delivery_confidence_min",
        ):
            _require_confidence(field_name, getattr(self, field_name))
        _require_non_negative_int("localization_max_age_ms", self.localization_max_age_ms)
        _require_non_negative_int("bridge_max_age_ms", self.bridge_max_age_ms)
        if self.reachability_distance_m < 0.0:
            raise ValueError("reachability_distance_m must be non-negative")
        _require_non_negative_int("image_center_tolerance_px", self.image_center_tolerance_px)
        _require_non_negative_int("grasp_corridor_tolerance_px", self.grasp_corridor_tolerance_px)


@dataclass(frozen=True, slots=True)
class AssertionContext:
    """Immutable task context for deterministic assertion evaluation."""

    target: AssertionTarget = field(default_factory=AssertionTarget)
    destination: AssertionDestination = field(default_factory=AssertionDestination)
    config: AssertionConfig = field(default_factory=AssertionConfig)


_UNKNOWN_PREDICATES: dict[AssertionId, str] = {
    "target_ball_visible": "unknown whether target ball is visible; deferred heuristics",
    "robot_pose_reliable": "unknown whether robot pose is reliable; deferred heuristics",
    "ball_reachable": "unknown whether target ball is reachable; deferred heuristics",
    "ball_centered_for_grasp": (
        "unknown whether target ball is centered for grasp; deferred heuristics"
    ),
    "grasp_likely": "unknown whether grasp is likely; deferred heuristics",
    "carrying_ball": "unknown whether robot is carrying the ball; deferred heuristics",
    "at_destination": "unknown whether robot is at destination; deferred heuristics",
    "drop_likely": "unknown whether drop is likely; deferred heuristics",
    "ball_at_destination": "unknown whether ball is at destination; deferred heuristics",
}


def build_assertion(
    *,
    assertion_id: AssertionId,
    predicate: str,
    state: AssertionState,
    confidence: float,
    evidence: tuple[AssertionEvidence, ...] | list[AssertionEvidence],
    observed_ms: int | None = None,
    age_ms: int | None = None,
    recovery_hint: str | None = None,
) -> PilotAssertion:
    """Create and validate a contract-owned pilot assertion."""
    if assertion_id not in _REQUIRED_ASSERTION_ID_SET:
        raise ValueError(f"unknown required assertion id: {assertion_id}")
    if not evidence:
        raise ValueError("pilot assertion requires at least one evidence entry")

    return PilotAssertion.model_validate(
        {
            "assertion_id": assertion_id,
            "predicate": predicate,
            "state": state,
            "confidence": confidence,
            "evidence": list(evidence),
            "observed_ms": observed_ms,
            "age_ms": age_ms,
            "recovery_hint": recovery_hint,
        }
    )


def build_unknown_assertion(
    assertion_id: AssertionId,
    *,
    observation: PilotObservation,
    context: AssertionContext,
) -> PilotAssertion:
    """Build an explicit unknown placeholder until fused heuristics are implemented."""
    if assertion_id not in _REQUIRED_ASSERTION_ID_SET:
        raise ValueError(f"unknown required assertion id: {assertion_id}")

    evidence = AssertionEvidence.model_validate(
        {
            "source": "planner",
            "summary": (
                f"assertion foundation only; deferred heuristics for {assertion_id}; "
                f"target={_target_description(context.target)}; "
                f"destination={context.destination.destination_id}"
            ),
            "confidence": 0.0,
            "observed_ms": observation.observed_ms,
            "age_ms": 0,
        }
    )
    return build_assertion(
        assertion_id=assertion_id,
        predicate=_UNKNOWN_PREDICATES[assertion_id],
        state=AssertionState.UNKNOWN,
        confidence=0.0,
        evidence=(evidence,),
        observed_ms=observation.observed_ms,
        age_ms=0,
        recovery_hint="Collect fused telemetry and vision evidence before marking true or false.",
    )


def evaluate_assertions(
    observation: PilotObservation,
    context: AssertionContext | None = None,
) -> tuple[PilotAssertion, ...]:
    """Return the required assertion vocabulary in stable order.

    This foundation slice intentionally emits explicit unknown assertions; later evaluator slices
    replace the placeholder state with fused telemetry and vision heuristics.
    """
    resolved_context = context or AssertionContext()
    return tuple(
        build_unknown_assertion(assertion_id, observation=observation, context=resolved_context)
        for assertion_id in REQUIRED_ASSERTION_IDS
    )


def _target_description(target: AssertionTarget) -> str:
    if target.object_id is None:
        return f"label:{target.label}"
    return f"id:{target.object_id};label:{target.label}"


def _require_confidence(field_name: str, value: float) -> None:
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _require_non_blank(field_name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must be non-blank")


def _require_non_negative_int(field_name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
