"""ROS-free assertion context and foundation builders for the pilot loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Literal, TypeAlias

from contracts import (
    AssertionEvidence,
    AssertionState,
    PilotAssertion,
    PilotObservation,
    VisibleObject,
)

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


_IMAGE_CENTER_X_PX = 320.0
_BBOX_DISTANCE_SCALE_M_PX = 24.0
_DESTINATION_TOLERANCE_M = 0.15

_PREDICATES: dict[AssertionId, str] = {
    "target_ball_visible": "target ball is visible with configured confidence",
    "robot_pose_reliable": "robot pose is reliable for bounded pilot decisions",
    "ball_reachable": "target ball is within configured grasp reach",
    "ball_centered_for_grasp": "target ball is centered in the grasp corridor",
    "grasp_likely": "recent grasp likely secured the target ball",
    "carrying_ball": "robot is carrying the target ball",
    "at_destination": "robot is at the configured destination",
    "drop_likely": "recent release likely dropped the target ball",
    "ball_at_destination": "target ball is at the configured destination",
}


@dataclass(frozen=True, slots=True)
class _Signal:
    """Internal evaluator signal before conversion to a contract assertion."""

    state: AssertionState
    confidence: float
    evidence: tuple[AssertionEvidence, ...]
    recovery_hint: str | None = None


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
    """Build an explicit unknown assertion for missing evaluator evidence."""
    if assertion_id not in _REQUIRED_ASSERTION_ID_SET:
        raise ValueError(f"unknown required assertion id: {assertion_id}")

    evidence = AssertionEvidence.model_validate(
        {
            "source": "planner",
            "summary": (
                f"insufficient evaluator evidence for {assertion_id}; "
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
        predicate=f"unknown whether {_PREDICATES[assertion_id]}",
        state=AssertionState.UNKNOWN,
        confidence=0.0,
        evidence=(evidence,),
        observed_ms=observation.observed_ms,
        age_ms=0,
        recovery_hint="Collect fresh telemetry and vision evidence before marking true or false.",
    )


def evaluate_assertions(
    observation: PilotObservation,
    context: AssertionContext | None = None,
) -> tuple[PilotAssertion, ...]:
    """Return deterministic assertion evaluations in the required stable order."""
    resolved_context = context or AssertionContext()
    evaluators = {
        "target_ball_visible": _evaluate_target_ball_visible,
        "robot_pose_reliable": _evaluate_robot_pose_reliable,
        "ball_reachable": _evaluate_ball_reachable,
        "ball_centered_for_grasp": _evaluate_ball_centered_for_grasp,
        "grasp_likely": _evaluate_grasp_likely,
        "carrying_ball": _evaluate_carrying_ball,
        "at_destination": _evaluate_at_destination,
        "drop_likely": _evaluate_drop_likely,
        "ball_at_destination": _evaluate_ball_at_destination,
    }
    return tuple(
        _assertion_from_signal(
            assertion_id,
            evaluators[assertion_id](observation, resolved_context),
            observation=observation,
        )
        for assertion_id in REQUIRED_ASSERTION_IDS
    )


def _target_description(target: AssertionTarget) -> str:
    if target.object_id is None:
        return f"label:{target.label}"
    return f"id:{target.object_id};label:{target.label}"


def _assertion_from_signal(
    assertion_id: AssertionId,
    signal: _Signal,
    *,
    observation: PilotObservation,
) -> PilotAssertion:
    return build_assertion(
        assertion_id=assertion_id,
        predicate=_PREDICATES[assertion_id],
        state=signal.state,
        confidence=_bounded_confidence(signal.confidence),
        evidence=signal.evidence,
        observed_ms=observation.observed_ms,
        age_ms=_max_evidence_age(signal.evidence),
        recovery_hint=signal.recovery_hint,
    )


def _evaluate_target_ball_visible(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal:
    unsafe = _unsafe_bridge_signal(observation, context)
    if unsafe is not None:
        return unsafe

    if not observation.visible_objects:
        return _unknown(
            _vision_evidence(observation, "no visible object evidence in the observation", 0.0),
            "survey_scene to collect object detections",
        )

    target = _target_object(observation, context)
    if target is not None and target.confidence >= context.config.visible_confidence_min:
        return _Signal(
            AssertionState.TRUE,
            target.confidence,
            (
                _object_evidence(
                    observation,
                    target,
                    f"matched {_target_description(context.target)} at confidence "
                    f"{target.confidence:.2f}",
                ),
            ),
        )
    if target is not None:
        return _unknown(
            _object_evidence(
                observation,
                target,
                f"matched {_target_description(context.target)} below confidence threshold "
                f"{context.config.visible_confidence_min:.2f}",
            ),
            "survey_scene or face_target until target confidence is high enough",
        )

    return _Signal(
        AssertionState.FALSE,
        _max_object_confidence(observation),
        (
            _vision_evidence(
                observation,
                f"{len(observation.visible_objects)} visible object(s) exclude "
                f"{_target_description(context.target)}",
                _max_object_confidence(observation),
            ),
        ),
        "survey_scene or update the target id/label if the task target changed",
    )


def _evaluate_robot_pose_reliable(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal:
    bridge = observation.bridge
    bridge_evidence = _bridge_evidence(
        observation,
        f"bridge state={bridge.state}; heartbeat_age={bridge.last_heartbeat_age_ms}; "
        f"estop={bridge.estop}; fault={bridge.fault}",
        1.0 if bridge.state == "ok" and not bridge.estop and bridge.fault is None else 0.2,
    )
    if bridge.estop or bridge.fault is not None or bridge.state in {"fault", "stale"}:
        return _Signal(
            AssertionState.FALSE,
            0.95,
            (bridge_evidence,),
            "clear bridge fault or estop before trusting localization",
        )
    if bridge.last_heartbeat_age_ms is None:
        return _unknown(bridge_evidence, "wait for bridge heartbeat before using robot pose")
    if bridge.last_heartbeat_age_ms > context.config.bridge_max_age_ms:
        return _Signal(
            AssertionState.FALSE,
            0.9,
            (bridge_evidence,),
            "restore fresh bridge heartbeat before moving",
        )
    if bridge.state != "ok":
        return _unknown(bridge_evidence, "wait for bridge state ok before trusting localization")

    pose = observation.localization.pose or observation.robot_pose
    loc = observation.localization
    loc_evidence = _telemetry_evidence(
        observation,
        f"localization pose_present={pose is not None}; confidence={loc.confidence:.2f}; "
        f"age_ms={loc.age_ms}",
        loc.confidence,
        age_ms=loc.age_ms,
    )
    if pose is None:
        return _unknown(loc_evidence, "collect localization pose before planning movement")
    if loc.age_ms > context.config.localization_max_age_ms:
        return _Signal(
            AssertionState.FALSE,
            0.9,
            (bridge_evidence, loc_evidence),
            "refresh localization before planning movement",
        )
    if loc.confidence < context.config.pose_confidence_min:
        return _Signal(
            AssertionState.FALSE,
            1.0 - loc.confidence,
            (bridge_evidence, loc_evidence),
            "relocalize until pose confidence meets the configured threshold",
        )
    return _Signal(
        AssertionState.TRUE,
        min(loc.confidence, 0.99),
        (bridge_evidence, loc_evidence),
    )


def _evaluate_ball_reachable(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal:
    target_signal = _usable_target_signal(observation, context)
    if target_signal.state is not AssertionState.TRUE:
        return target_signal

    target = _target_object(observation, context)
    if target is None or target.bbox is None:
        return _unknown(
            _vision_evidence(
                observation,
                "target object lacks bbox evidence for reachability heuristic",
                target.confidence if target else 0.0,
            ),
            "face_target or survey_scene until target bbox evidence is available",
        )

    estimated_distance_m = _estimated_distance_m(target)
    state = (
        AssertionState.TRUE
        if estimated_distance_m <= context.config.reachability_distance_m
        else AssertionState.FALSE
    )
    return _Signal(
        state,
        target.confidence,
        (
            _object_evidence(
                observation,
                target,
                f"bbox max span estimates distance {estimated_distance_m:.2f} m; threshold "
                f"{context.config.reachability_distance_m:.2f} m",
            ),
        ),
        None if state is AssertionState.TRUE else "approach_target until the target bbox is larger",
    )


def _evaluate_ball_centered_for_grasp(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal:
    target_signal = _usable_target_signal(observation, context)
    if target_signal.state is not AssertionState.TRUE:
        return target_signal

    target = _target_object(observation, context)
    if target is None or target.bbox is None:
        return _unknown(
            _vision_evidence(
                observation,
                "target object lacks bbox evidence for grasp centering",
                target.confidence if target else 0.0,
            ),
            "center_object_in_gripper after target bbox evidence is available",
        )

    offset_px = _bbox_center_x(target) - _IMAGE_CENTER_X_PX
    tolerance_px = min(
        context.config.image_center_tolerance_px,
        context.config.grasp_corridor_tolerance_px,
    )
    state = AssertionState.TRUE if abs(offset_px) <= tolerance_px else AssertionState.FALSE
    return _Signal(
        state,
        target.confidence,
        (
            _object_evidence(
                observation,
                target,
                f"bbox center offset {offset_px:.1f} px; image tolerance "
                f"{context.config.image_center_tolerance_px} px; grasp tolerance "
                f"{context.config.grasp_corridor_tolerance_px} px",
            ),
        ),
        None
        if state is AssertionState.TRUE
        else "center_object_in_gripper until the target is inside the grasp corridor",
    )


def _evaluate_grasp_likely(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal:
    return _fused_grasp_or_carry(
        observation,
        context,
        assertion="grasp",
        true_hint="verify_grasp if the grasp was not just confirmed",
        false_hint="open, recenter, and retry claw_close",
    )


def _evaluate_carrying_ball(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal:
    return _fused_grasp_or_carry(
        observation,
        context,
        assertion="carry",
        true_hint="verify_grasp before navigating if carry evidence is incomplete",
        false_hint="recover the target before navigating to the destination",
    )


def _evaluate_at_destination(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal:
    unsafe = _unsafe_bridge_signal(observation, context)
    if unsafe is not None:
        return unsafe

    signal = _destination_signal(observation, context)
    if signal is not None:
        return signal
    return _unknown(
        _planner_evidence(
            observation,
            f"destination {context.destination.destination_id} lacks x/y coordinates or tag id",
            0.0,
        ),
        "configure destination coordinates or a destination tag",
    )


def _evaluate_drop_likely(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal:
    destination = _destination_signal(observation, context)
    manipulator = _drop_manipulator_signal(observation, context)
    skill = _last_result_signal(
        observation,
        positive_skills={"claw_open", "verify_drop"},
        negative_skills={"claw_open", "verify_drop"},
    )
    object_signal = _target_at_destination_signal(observation, context)
    return _combine_drop_signals(
        destination=destination,
        manipulator=manipulator,
        skill=skill,
        object_signal=object_signal,
        true_hint="verify_drop with fresh destination and manipulator evidence",
        false_hint="open claw at the destination and verify the drop again",
        require_object=True,
    )


def _evaluate_ball_at_destination(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal:
    destination = _destination_signal(observation, context)
    manipulator = _drop_manipulator_signal(observation, context)
    skill = _last_result_signal(
        observation,
        positive_skills={"verify_drop"},
        negative_skills={"verify_drop"},
    )
    object_signal = _target_at_destination_signal(observation, context)
    return _combine_drop_signals(
        destination=destination,
        manipulator=manipulator,
        skill=skill,
        object_signal=object_signal,
        true_hint="survey the destination and run verify_drop",
        false_hint="retry delivery after reacquiring the target ball",
        require_object=True,
    )


def _combine_drop_signals(
    *,
    destination: _Signal | None,
    manipulator: _Signal | None,
    skill: _Signal | None,
    object_signal: _Signal | None,
    true_hint: str,
    false_hint: str,
    require_object: bool = False,
) -> _Signal:
    signals = [signal for signal in (destination, manipulator, skill, object_signal) if signal]
    if not signals:
        return _unknown(
            AssertionEvidence(
                source="planner",
                summary="no drop or destination evidence classes available",
                confidence=0.0,
                age_ms=0,
            ),
            true_hint,
        )

    evidence = tuple(evidence for signal in signals for evidence in signal.evidence)
    completion_signals = [signal for signal in (manipulator, skill, object_signal) if signal]
    positives = [signal for signal in completion_signals if signal.state is AssertionState.TRUE]
    negatives = [signal for signal in completion_signals if signal.state is AssertionState.FALSE]
    destination_ready = destination is not None and destination.state is AssertionState.TRUE
    destination_failed = destination is not None and destination.state is AssertionState.FALSE

    if positives and negatives:
        return _Signal(
            AssertionState.UNKNOWN,
            0.0,
            evidence,
            "resolve conflicting drop evidence before declaring delivery complete",
        )
    if destination_failed and not positives:
        return _Signal(AssertionState.FALSE, destination.confidence, evidence, "go_to_destination")
    if negatives:
        return _Signal(AssertionState.FALSE, _mean_confidence(negatives), evidence, false_hint)

    object_ready = object_signal is not None and object_signal.state is AssertionState.TRUE
    enough_completion = len(positives) >= 2 and (object_ready or not require_object)
    if destination_ready and enough_completion:
        return _Signal(AssertionState.TRUE, _mean_confidence(positives), evidence)

    return _Signal(AssertionState.UNKNOWN, 0.0, evidence, true_hint)


def _fused_grasp_or_carry(
    observation: PilotObservation,
    context: AssertionContext,
    *,
    assertion: Literal["grasp", "carry"],
    true_hint: str,
    false_hint: str,
) -> _Signal:
    manipulator = _grasp_manipulator_signal(observation, context)
    skill = _last_result_signal(
        observation,
        positive_skills={"claw_close", "verify_grasp"},
        negative_skills={"claw_close", "verify_grasp"},
    )
    object_signal = _held_object_signal(observation, context)
    signals = [signal for signal in (manipulator, skill, object_signal) if signal]
    return _combine_grasp_signals(
        signals=signals,
        manipulator=manipulator,
        skill=skill,
        object_signal=object_signal,
        unknown_hint=true_hint,
        false_hint=false_hint,
        conflict_hint=f"resolve conflicting {assertion} evidence before continuing",
    )


def _combine_grasp_signals(
    *,
    signals: list[_Signal],
    manipulator: _Signal | None,
    skill: _Signal | None,
    object_signal: _Signal | None,
    unknown_hint: str,
    false_hint: str,
    conflict_hint: str,
) -> _Signal:
    if not signals:
        return _unknown(
            AssertionEvidence(
                source="planner",
                summary="no fused evidence classes available",
                confidence=0.0,
                age_ms=0,
            ),
            unknown_hint,
        )

    positives = [signal for signal in signals if signal.state is AssertionState.TRUE]
    negatives = [signal for signal in signals if signal.state is AssertionState.FALSE]
    evidence = tuple(evidence for signal in signals for evidence in signal.evidence)
    if positives and negatives:
        return _Signal(AssertionState.UNKNOWN, 0.0, evidence, conflict_hint)
    if len(negatives) >= 2:
        return _Signal(AssertionState.FALSE, _mean_confidence(negatives), evidence, false_hint)

    has_action_evidence = any(
        signal is not None and signal.state is AssertionState.TRUE
        for signal in (manipulator, skill)
    )
    has_object_evidence = object_signal is not None and object_signal.state is AssertionState.TRUE
    if has_action_evidence and has_object_evidence:
        return _Signal(AssertionState.TRUE, _mean_confidence(positives), evidence)

    return _Signal(AssertionState.UNKNOWN, 0.0, evidence, unknown_hint)


def _combine_fused_signals(
    signals: list[_Signal],
    *,
    true_min_positive: int,
    false_min_negative: int,
    unknown_hint: str,
    false_hint: str,
    conflict_hint: str | None = None,
) -> _Signal:
    if not signals:
        return _unknown(
            AssertionEvidence(
                source="planner",
                summary="no fused evidence classes available",
                confidence=0.0,
                age_ms=0,
            ),
            unknown_hint,
        )

    positives = [signal for signal in signals if signal.state is AssertionState.TRUE]
    negatives = [signal for signal in signals if signal.state is AssertionState.FALSE]
    evidence = tuple(evidence for signal in signals for evidence in signal.evidence)
    if positives and negatives:
        return _Signal(
            AssertionState.UNKNOWN,
            0.0,
            evidence,
            conflict_hint or "collect fresh evidence because current signals conflict",
        )
    if len(positives) >= true_min_positive:
        return _Signal(AssertionState.TRUE, _mean_confidence(positives), evidence)
    if len(negatives) >= false_min_negative:
        return _Signal(AssertionState.FALSE, _mean_confidence(negatives), evidence, false_hint)
    return _Signal(AssertionState.UNKNOWN, 0.0, evidence, unknown_hint)


def _usable_target_signal(observation: PilotObservation, context: AssertionContext) -> _Signal:
    visible = _evaluate_target_ball_visible(observation, context)
    if visible.state is AssertionState.TRUE:
        return visible
    if visible.state is AssertionState.FALSE:
        return _Signal(
            AssertionState.UNKNOWN,
            0.0,
            visible.evidence,
            "required target evidence is absent for this evaluator",
        )
    return visible


def _target_object(
    observation: PilotObservation,
    context: AssertionContext,
) -> VisibleObject | None:
    matches = [obj for obj in observation.visible_objects if _matches_target(obj, context.target)]
    if not matches:
        return None
    return max(matches, key=lambda obj: (obj.confidence, obj.object_id))


def _matches_target(obj: VisibleObject, target: AssertionTarget) -> bool:
    return (
        target.object_id is not None and obj.object_id == target.object_id
    ) or obj.label.casefold() == target.label.casefold()


def _unsafe_bridge_signal(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal | None:
    bridge = observation.bridge
    if bridge.estop or bridge.fault is not None or bridge.state in {"fault", "stale"}:
        return _unknown(
            _bridge_evidence(
                observation,
                f"bridge unsafe to trust: state={bridge.state}; estop={bridge.estop}; "
                f"fault={bridge.fault}",
                0.0,
            ),
            "clear bridge fault or estop before evaluating task progress",
        )
    if (
        bridge.last_heartbeat_age_ms is not None
        and bridge.last_heartbeat_age_ms > context.config.bridge_max_age_ms
    ):
        return _unknown(
            _bridge_evidence(
                observation,
                f"bridge heartbeat age {bridge.last_heartbeat_age_ms} ms exceeds "
                f"{context.config.bridge_max_age_ms} ms",
                0.0,
            ),
            "restore a fresh bridge heartbeat before evaluating task progress",
        )
    return None


def _grasp_manipulator_signal(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal | None:
    manipulator = observation.manipulator
    summary = (
        f"claw_state={manipulator.claw_state}; held_object_id={manipulator.held_object_id}; "
        f"target={_target_description(context.target)}"
    )
    if manipulator.claw_state in {"holding", "closed"}:
        return _Signal(
            AssertionState.TRUE,
            0.8,
            (_telemetry_evidence(observation, summary, 0.8),),
        )
    if manipulator.claw_state == "open":
        return _Signal(
            AssertionState.FALSE,
            0.85,
            (_telemetry_evidence(observation, summary, 0.85),),
            "close the claw on a centered target before verifying grasp",
        )
    return None


def _held_object_signal(observation: PilotObservation, context: AssertionContext) -> _Signal | None:
    manipulator = observation.manipulator
    held_object_id = manipulator.held_object_id
    if held_object_id is None:
        return None
    summary = f"held_object_id={held_object_id}; target={_target_description(context.target)}"
    if context.target.object_id is None or held_object_id == context.target.object_id:
        return _Signal(
            AssertionState.TRUE,
            0.95,
            (_telemetry_evidence(observation, summary, 0.95),),
        )
    return _Signal(
        AssertionState.FALSE,
        0.95,
        (_telemetry_evidence(observation, summary, 0.95),),
        "release the wrong held object and reacquire the target",
    )


def _drop_manipulator_signal(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal | None:
    manipulator = observation.manipulator
    summary = (
        f"drop manipulator state claw={manipulator.claw_state}; "
        f"held_object_id={manipulator.held_object_id}"
    )
    if manipulator.claw_state == "open" and manipulator.held_object_id is None:
        return _Signal(
            AssertionState.TRUE,
            0.85,
            (_telemetry_evidence(observation, summary, 0.85),),
        )
    if manipulator.held_object_id is not None and (
        context.target.object_id is None or manipulator.held_object_id == context.target.object_id
    ):
        return _Signal(
            AssertionState.FALSE,
            0.9,
            (_telemetry_evidence(observation, summary, 0.9),),
            "open the claw before verifying delivery",
        )
    if manipulator.claw_state in {"closed", "holding"}:
        return _Signal(
            AssertionState.FALSE,
            0.75,
            (_telemetry_evidence(observation, summary, 0.75),),
            "open the claw before verifying delivery",
        )
    return None


def _last_result_signal(
    observation: PilotObservation,
    *,
    positive_skills: set[str],
    negative_skills: set[str],
) -> _Signal | None:
    result = observation.last_result
    if result is None:
        return None
    skill = str(result.skill)
    if skill.startswith("PilotSkillName."):
        skill = result.skill.value
    summary = f"last_result skill={skill}; status={result.status}; message={result.message}"
    if skill in positive_skills and str(result.status) == "ok":
        return _Signal(
            AssertionState.TRUE,
            0.85,
            (_telemetry_evidence(observation, summary, 0.85, observed_ms=result.completed_ms),),
        )
    if skill in negative_skills and str(result.status) in {"failed", "rejected", "stale"}:
        return _Signal(
            AssertionState.FALSE,
            0.85,
            (_telemetry_evidence(observation, summary, 0.85, observed_ms=result.completed_ms),),
            "recover from the failed skill before treating the assertion as complete",
        )
    return None


def _destination_signal(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal | None:
    destination = context.destination
    if destination.x_m is not None and destination.y_m is not None:
        pose = observation.localization.pose or observation.robot_pose
        if pose is None:
            return _unknown(
                _telemetry_evidence(observation, "destination check lacks robot pose", 0.0),
                "localize before checking destination arrival",
            )
        if observation.localization.age_ms > context.config.localization_max_age_ms:
            return _unknown(
                _telemetry_evidence(
                    observation,
                    f"destination pose age {observation.localization.age_ms} ms is stale",
                    0.0,
                    age_ms=observation.localization.age_ms,
                ),
                "refresh localization before checking destination arrival",
            )
        distance = hypot(pose.x_m - destination.x_m, pose.y_m - destination.y_m)
        state = (
            AssertionState.TRUE if distance <= _DESTINATION_TOLERANCE_M else AssertionState.FALSE
        )
        return _Signal(
            state,
            max(observation.localization.confidence, 0.1),
            (
                _telemetry_evidence(
                    observation,
                    f"robot pose is {distance:.2f} m from destination {destination.destination_id}",
                    observation.localization.confidence,
                    age_ms=observation.localization.age_ms,
                ),
            ),
            None if state is AssertionState.TRUE else "go_to_destination before verifying drop",
        )

    if destination.tag_id is not None:
        tag = next(
            (
                visible
                for visible in observation.visible_tags
                if visible.tag_id == destination.tag_id
            ),
            None,
        )
        if tag is None:
            return _unknown(
                _vision_evidence(
                    observation,
                    f"destination tag {destination.tag_id} not visible",
                    0.0,
                ),
                "survey_scene until the destination tag is visible",
            )
        if tag.confidence < context.config.delivery_confidence_min:
            return _unknown(
                _vision_evidence(
                    observation,
                    f"destination tag {destination.tag_id} below confidence threshold "
                    f"{context.config.delivery_confidence_min:.2f}",
                    tag.confidence,
                ),
                "face the destination tag until confidence improves",
            )
        if tag.pose is None:
            return _Signal(
                AssertionState.TRUE,
                tag.confidence,
                (
                    _vision_evidence(
                        observation,
                        f"destination tag {destination.tag_id} is visible without metric pose",
                        tag.confidence,
                    ),
                ),
            )
        distance = hypot(tag.pose.x_m, tag.pose.y_m)
        state = (
            AssertionState.TRUE
            if distance <= context.config.reachability_distance_m
            else AssertionState.FALSE
        )
        return _Signal(
            state,
            tag.confidence,
            (
                _vision_evidence(
                    observation,
                    f"destination tag {destination.tag_id} relative distance {distance:.2f} m",
                    tag.confidence,
                ),
            ),
            None if state is AssertionState.TRUE else "go_to_destination until tag is near",
        )

    return None


def _target_at_destination_signal(
    observation: PilotObservation,
    context: AssertionContext,
) -> _Signal | None:
    target = _target_object(observation, context)
    if target is None:
        if observation.visible_objects:
            return _Signal(
                AssertionState.FALSE,
                _max_object_confidence(observation),
                (
                    _vision_evidence(
                        observation,
                        f"visible objects exclude target at destination "
                        f"{_target_description(context.target)}",
                        _max_object_confidence(observation),
                    ),
                ),
                "survey destination until the target ball is visible",
            )
        return None
    if target.confidence < context.config.delivery_confidence_min:
        return _unknown(
            _object_evidence(
                observation,
                target,
                f"target visible at destination below delivery confidence "
                f"{context.config.delivery_confidence_min:.2f}",
            ),
            "survey destination until target confidence improves",
        )
    return _Signal(
        AssertionState.TRUE,
        target.confidence,
        (
            _object_evidence(
                observation,
                target,
                f"target object visible while checking destination {context.destination.destination_id}",
            ),
        ),
    )


def _estimated_distance_m(obj: VisibleObject) -> float:
    if obj.bbox is None:
        return float("inf")
    return _BBOX_DISTANCE_SCALE_M_PX / max(obj.bbox.width_px, obj.bbox.height_px)


def _bbox_center_x(obj: VisibleObject) -> float:
    if obj.bbox is None:
        return float("inf")
    return obj.bbox.x_px + (obj.bbox.width_px / 2.0)


def _max_object_confidence(observation: PilotObservation) -> float:
    if not observation.visible_objects:
        return 0.0
    return max(obj.confidence for obj in observation.visible_objects)


def _mean_confidence(signals: list[_Signal]) -> float:
    return sum(signal.confidence for signal in signals) / len(signals)


def _unknown(evidence: AssertionEvidence, recovery_hint: str) -> _Signal:
    return _Signal(AssertionState.UNKNOWN, 0.0, (evidence,), recovery_hint)


def _object_evidence(
    observation: PilotObservation,
    obj: VisibleObject,
    summary: str,
) -> AssertionEvidence:
    bbox_summary = ""
    if obj.bbox is not None:
        bbox_summary = (
            f"; bbox={obj.bbox.x_px},{obj.bbox.y_px},{obj.bbox.width_px},{obj.bbox.height_px}"
        )
    return _vision_evidence(
        observation,
        f"{summary}; object_id={obj.object_id}; label={obj.label}{bbox_summary}",
        obj.confidence,
    )


def _bridge_evidence(
    observation: PilotObservation,
    summary: str,
    confidence: float,
) -> AssertionEvidence:
    age_ms = observation.bridge.last_heartbeat_age_ms
    return AssertionEvidence(
        source="bridge",
        summary=summary,
        confidence=_bounded_confidence(confidence),
        observed_ms=_observed_at(observation, age_ms),
        age_ms=age_ms,
    )


def _telemetry_evidence(
    observation: PilotObservation,
    summary: str,
    confidence: float,
    *,
    observed_ms: int | None = None,
    age_ms: int | None = 0,
) -> AssertionEvidence:
    return AssertionEvidence(
        source="telemetry",
        summary=summary,
        confidence=_bounded_confidence(confidence),
        observed_ms=observed_ms if observed_ms is not None else _observed_at(observation, age_ms),
        age_ms=age_ms,
    )


def _vision_evidence(
    observation: PilotObservation,
    summary: str,
    confidence: float,
) -> AssertionEvidence:
    return AssertionEvidence(
        source="vision",
        summary=summary,
        confidence=_bounded_confidence(confidence),
        observed_ms=observation.observed_ms,
        age_ms=0,
    )


def _planner_evidence(
    observation: PilotObservation,
    summary: str,
    confidence: float,
) -> AssertionEvidence:
    return AssertionEvidence(
        source="planner",
        summary=summary,
        confidence=_bounded_confidence(confidence),
        observed_ms=observation.observed_ms,
        age_ms=0,
    )


def _observed_at(observation: PilotObservation, age_ms: int | None) -> int:
    if age_ms is None:
        return observation.observed_ms
    return max(0, observation.observed_ms - age_ms)


def _max_evidence_age(evidence: tuple[AssertionEvidence, ...]) -> int:
    ages = [item.age_ms for item in evidence if item.age_ms is not None]
    return max(ages, default=0)


def _bounded_confidence(value: float) -> float:
    return min(1.0, max(0.0, value))


def _require_confidence(field_name: str, value: float) -> None:
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _require_non_blank(field_name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must be non-blank")


def _require_non_negative_int(field_name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
