from __future__ import annotations

import dataclasses
import importlib
import sys

import pytest
from contracts import (
    AssertionEvidence,
    AssertionState,
    BridgeHealth,
    CommandStatus,
    ImageBox,
    LocalizationState,
    ManipulatorState,
    PilotAssertion,
    PilotObservation,
    PilotSkillResult,
    PilotTaskPhase,
    Pose2D,
    VisibleObject,
    VisibleTag,
)
from pydantic import ValidationError

from pilot.assertions import (
    REQUIRED_ASSERTION_IDS,
    AssertionConfig,
    AssertionContext,
    AssertionDestination,
    AssertionTarget,
    build_assertion,
    build_unknown_assertion,
    evaluate_assertions,
)


def _observation(
    observed_ms: int = 1200,
    *,
    pose: Pose2D | None = None,
    localization: LocalizationState | None = None,
    visible_objects: list[VisibleObject] | None = None,
    visible_tags: list[VisibleTag] | None = None,
    manipulator: ManipulatorState | None = None,
    bridge: BridgeHealth | None = None,
    last_result: PilotSkillResult | None = None,
) -> PilotObservation:
    return PilotObservation(
        observed_ms=observed_ms,
        task_phase=PilotTaskPhase.SURVEY,
        objective="deliver the yellow ball",
        robot_pose=pose,
        localization=localization or LocalizationState(pose=pose, confidence=0.0, age_ms=50),
        visible_objects=visible_objects or [],
        visible_tags=visible_tags or [],
        manipulator=manipulator
        or ManipulatorState(arm_deg=None, claw_state="unknown", held_object_id=None),
        bridge=bridge or BridgeHealth(state="ok", last_heartbeat_age_ms=25),
        last_result=last_result,
    )


def _target_object(
    *,
    object_id: str = "ball-yellow-1",
    label: str = "yellow_ball",
    confidence: float = 0.9,
    x_px: int = 296,
    width_px: int = 48,
) -> VisibleObject:
    return VisibleObject(
        object_id=object_id,
        label=label,
        confidence=confidence,
        bbox=ImageBox(x_px=x_px, y_px=120, width_px=width_px, height_px=48),
    )


def _context() -> AssertionContext:
    return AssertionContext(
        target=AssertionTarget(label="yellow_ball", object_id="ball-yellow-1"),
        destination=AssertionDestination(destination_id="goal-blue-1", x_m=1.0, y_m=2.0),
    )


def _assertion_by_id(assertions: tuple[PilotAssertion, ...], assertion_id: str) -> PilotAssertion:
    return next(assertion for assertion in assertions if assertion.assertion_id == assertion_id)


def test_default_context_is_deterministic_and_immutable() -> None:
    context = AssertionContext()

    assert dataclasses.is_dataclass(context)
    assert context.target == AssertionTarget(label="ball", object_id=None)
    assert context.destination == AssertionDestination(destination_id="destination")
    assert context.config == AssertionConfig()
    assert context.config.visible_confidence_min == 0.65
    assert context.config.pose_confidence_min == 0.70
    assert context.config.localization_max_age_ms == 500
    assert context.config.reachability_distance_m == 0.45
    assert context.config.image_center_tolerance_px == 24
    assert context.config.grasp_corridor_tolerance_px == 32

    with pytest.raises(dataclasses.FrozenInstanceError):
        context.target = AssertionTarget(label="cube")
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.config.reachability_distance_m = 2.0


def test_explicit_context_values_are_task_configurable() -> None:
    context = AssertionContext(
        target=AssertionTarget(label="yellow_ball", object_id="ball-yellow-1"),
        destination=AssertionDestination(
            destination_id="goal-blue-1",
            tag_id=12,
            x_m=1.4,
            y_m=0.8,
        ),
        config=AssertionConfig(
            visible_confidence_min=0.75,
            pose_confidence_min=0.8,
            grasp_confidence_min=0.7,
            delivery_confidence_min=0.72,
            localization_max_age_ms=250,
            bridge_max_age_ms=300,
            reachability_distance_m=0.3,
            image_center_tolerance_px=12,
            grasp_corridor_tolerance_px=18,
        ),
    )

    assert context.target.object_id == "ball-yellow-1"
    assert context.target.label == "yellow_ball"
    assert context.destination.destination_id == "goal-blue-1"
    assert context.destination.tag_id == 12
    assert context.destination.x_m == 1.4
    assert context.destination.y_m == 0.8
    assert context.config.visible_confidence_min == 0.75
    assert context.config.localization_max_age_ms == 250
    assert context.config.bridge_max_age_ms == 300


@pytest.mark.parametrize(
    ("factory", "match"),
    [
        (lambda: AssertionTarget(label=" "), "label must be non-blank"),
        (lambda: AssertionTarget(label="ball", object_id=" "), "object_id must be non-blank"),
        (
            lambda: AssertionDestination(destination_id="goal", tag_id=-1),
            "tag_id must be non-negative",
        ),
        (
            lambda: AssertionConfig(visible_confidence_min=1.1),
            "visible_confidence_min must be between",
        ),
        (
            lambda: AssertionConfig(localization_max_age_ms=-1),
            "localization_max_age_ms must be non-negative",
        ),
        (
            lambda: AssertionConfig(reachability_distance_m=-0.1),
            "reachability_distance_m must be non-negative",
        ),
    ],
)
def test_context_rejects_invalid_configuration(factory: object, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        factory()


def test_required_assertion_ids_are_exact_and_stable() -> None:
    assert REQUIRED_ASSERTION_IDS == (
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
    assert len(REQUIRED_ASSERTION_IDS) == len(set(REQUIRED_ASSERTION_IDS))


def test_build_assertion_returns_contract_valid_record() -> None:
    evidence = AssertionEvidence(
        source="vision",
        summary="target not evaluated yet",
        confidence=0.2,
        observed_ms=900,
        age_ms=25,
    )

    assertion = build_assertion(
        assertion_id="target_ball_visible",
        predicate="target visibility is pending",
        state=AssertionState.UNKNOWN,
        confidence=0.2,
        evidence=(evidence,),
        observed_ms=900,
        age_ms=25,
        recovery_hint="wait for vision evaluator",
    )

    assert isinstance(assertion, PilotAssertion)
    assert PilotAssertion.model_validate(assertion.model_dump()) == assertion
    assert assertion.assertion_id == "target_ball_visible"
    assert assertion.evidence == [evidence]
    assert assertion.confidence == 0.2
    assert assertion.observed_ms == 900
    assert assertion.age_ms == 25


def test_build_assertion_requires_required_id_and_evidence() -> None:
    evidence = AssertionEvidence(source="planner", summary="placeholder", observed_ms=1)

    with pytest.raises(ValueError, match="unknown required assertion id"):
        build_assertion(
            assertion_id="not_required",
            predicate="invalid",
            state=AssertionState.UNKNOWN,
            confidence=0.0,
            evidence=(evidence,),
            observed_ms=1,
        )
    with pytest.raises(ValueError, match="at least one evidence"):
        build_assertion(
            assertion_id="target_ball_visible",
            predicate="missing evidence",
            state=AssertionState.UNKNOWN,
            confidence=0.0,
            evidence=(),
            observed_ms=1,
        )
    with pytest.raises(ValidationError):
        build_assertion(
            assertion_id="target_ball_visible",
            predicate="unbounded confidence",
            state=AssertionState.UNKNOWN,
            confidence=1.1,
            evidence=(evidence,),
            observed_ms=1,
        )


def test_build_unknown_assertion_makes_uncertainty_explicit() -> None:
    observation = _observation(observed_ms=5000)
    context = AssertionContext(
        target=AssertionTarget(label="yellow_ball", object_id="ball-yellow-1"),
        destination=AssertionDestination(destination_id="goal-blue-1"),
    )

    assertion = build_unknown_assertion(
        "target_ball_visible",
        observation=observation,
        context=context,
    )

    assert assertion.state is AssertionState.UNKNOWN
    assert assertion.confidence == 0.0
    assert assertion.observed_ms == 5000
    assert assertion.age_ms == 0
    assert assertion.recovery_hint is not None
    assert "true or false" in assertion.recovery_hint
    assert "unknown whether" in assertion.predicate
    assert len(assertion.evidence) == 1
    assert assertion.evidence[0].source == "planner"
    assert assertion.evidence[0].confidence == 0.0
    assert assertion.evidence[0].observed_ms == 5000
    assert assertion.evidence[0].age_ms == 0
    assert "insufficient evaluator evidence" in assertion.evidence[0].summary
    assert "ball-yellow-1" in assertion.evidence[0].summary
    assert PilotAssertion.model_validate(assertion.model_dump()) == assertion


def test_evaluate_assertions_returns_contract_valid_assertions_in_required_order() -> None:
    observation = _observation(observed_ms=300)

    assertions = evaluate_assertions(observation, AssertionContext())

    assert isinstance(assertions, tuple)
    assert [assertion.assertion_id for assertion in assertions] == list(REQUIRED_ASSERTION_IDS)
    assert len(assertions) == len(REQUIRED_ASSERTION_IDS)
    for assertion in assertions:
        assert assertion.evidence
        assert 0.0 <= assertion.confidence <= 1.0
        assert assertion.observed_ms == observation.observed_ms
        assert PilotAssertion.model_validate(assertion.model_dump()) == assertion


def test_evaluate_assertions_defaults_context() -> None:
    assertions = evaluate_assertions(_observation())

    assert [assertion.assertion_id for assertion in assertions] == list(REQUIRED_ASSERTION_IDS)


def test_target_visibility_true_false_unknown_and_unsafe_cases() -> None:
    context = _context()

    visible = _assertion_by_id(
        evaluate_assertions(_observation(visible_objects=[_target_object()]), context),
        "target_ball_visible",
    )
    label_fallback = _assertion_by_id(
        evaluate_assertions(
            _observation(
                visible_objects=[
                    _target_object(object_id="ball-yellow-renumbered", label="yellow_ball")
                ]
            ),
            context,
        ),
        "target_ball_visible",
    )
    excluded = _assertion_by_id(
        evaluate_assertions(
            _observation(visible_objects=[_target_object(object_id="cube-1", label="red_cube")]),
            context,
        ),
        "target_ball_visible",
    )
    weak = _assertion_by_id(
        evaluate_assertions(
            _observation(visible_objects=[_target_object(confidence=0.4)]),
            context,
        ),
        "target_ball_visible",
    )
    unsafe = _assertion_by_id(
        evaluate_assertions(
            _observation(
                visible_objects=[_target_object()],
                bridge=BridgeHealth(state="fault", last_heartbeat_age_ms=20, fault="serial fault"),
            ),
            context,
        ),
        "target_ball_visible",
    )

    assert visible.state is AssertionState.TRUE
    assert visible.evidence[0].source == "vision"
    assert label_fallback.state is AssertionState.TRUE
    assert excluded.state is AssertionState.FALSE
    assert "exclude" in excluded.evidence[0].summary
    assert weak.state is AssertionState.UNKNOWN
    assert weak.recovery_hint is not None
    assert unsafe.state is AssertionState.UNKNOWN
    assert unsafe.evidence[0].source == "bridge"


def test_pose_reliability_uses_pose_bridge_confidence_and_age() -> None:
    pose = Pose2D(x_m=1.0, y_m=2.0, heading_rad=0.0)

    reliable = _assertion_by_id(
        evaluate_assertions(
            _observation(
                pose=pose,
                localization=LocalizationState(pose=pose, confidence=0.91, age_ms=45),
            ),
            _context(),
        ),
        "robot_pose_reliable",
    )
    stale = _assertion_by_id(
        evaluate_assertions(
            _observation(
                pose=pose,
                localization=LocalizationState(pose=pose, confidence=0.91, age_ms=900),
            ),
            _context(),
        ),
        "robot_pose_reliable",
    )
    missing = _assertion_by_id(
        evaluate_assertions(_observation(), _context()),
        "robot_pose_reliable",
    )

    assert reliable.state is AssertionState.TRUE
    assert {evidence.source for evidence in reliable.evidence} == {"bridge", "telemetry"}
    assert stale.state is AssertionState.FALSE
    assert "refresh localization" in (stale.recovery_hint or "")
    assert missing.state is AssertionState.UNKNOWN


def test_reachable_and_centered_use_bbox_heuristics_with_missing_evidence_unknown() -> None:
    context = _context()

    close_centered = evaluate_assertions(
        _observation(visible_objects=[_target_object(width_px=96, x_px=272)]),
        context,
    )
    far_offset = evaluate_assertions(
        _observation(visible_objects=[_target_object(width_px=24, x_px=230)]),
        context,
    )
    missing_bbox = evaluate_assertions(
        _observation(
            visible_objects=[
                VisibleObject(
                    object_id="ball-yellow-1",
                    label="yellow_ball",
                    confidence=0.9,
                    bbox=None,
                )
            ]
        ),
        context,
    )

    assert _assertion_by_id(close_centered, "ball_reachable").state is AssertionState.TRUE
    assert _assertion_by_id(close_centered, "ball_centered_for_grasp").state is AssertionState.TRUE
    assert _assertion_by_id(far_offset, "ball_reachable").state is AssertionState.FALSE
    assert _assertion_by_id(far_offset, "ball_centered_for_grasp").state is AssertionState.FALSE
    assert _assertion_by_id(missing_bbox, "ball_reachable").state is AssertionState.UNKNOWN
    assert _assertion_by_id(missing_bbox, "ball_centered_for_grasp").state is AssertionState.UNKNOWN


def test_grasp_likely_requires_fused_evidence_and_conflicts_return_unknown() -> None:
    context = _context()

    likely = _assertion_by_id(
        evaluate_assertions(
            _observation(
                manipulator=ManipulatorState(
                    arm_deg=10.0,
                    claw_state="closed",
                    held_object_id="ball-yellow-1",
                ),
                last_result=PilotSkillResult(
                    command_id="cmd-verify",
                    skill="verify_grasp",
                    status=CommandStatus.OK,
                    completed_ms=1190,
                ),
            ),
            context,
        ),
        "grasp_likely",
    )
    failed = _assertion_by_id(
        evaluate_assertions(
            _observation(
                manipulator=ManipulatorState(
                    arm_deg=10.0,
                    claw_state="open",
                    held_object_id=None,
                ),
                last_result=PilotSkillResult(
                    command_id="cmd-verify",
                    skill="verify_grasp",
                    status=CommandStatus.FAILED,
                    completed_ms=1190,
                    fault="no contact",
                ),
            ),
            context,
        ),
        "grasp_likely",
    )
    single_class = _assertion_by_id(
        evaluate_assertions(
            _observation(
                last_result=PilotSkillResult(
                    command_id="cmd-verify",
                    skill="verify_grasp",
                    status=CommandStatus.OK,
                    completed_ms=1190,
                ),
            ),
            context,
        ),
        "grasp_likely",
    )
    no_object_evidence = _assertion_by_id(
        evaluate_assertions(
            _observation(
                manipulator=ManipulatorState(
                    arm_deg=10.0,
                    claw_state="closed",
                    held_object_id=None,
                ),
                last_result=PilotSkillResult(
                    command_id="cmd-verify",
                    skill="verify_grasp",
                    status=CommandStatus.OK,
                    completed_ms=1190,
                ),
            ),
            context,
        ),
        "grasp_likely",
    )
    conflict = _assertion_by_id(
        evaluate_assertions(
            _observation(
                manipulator=ManipulatorState(
                    arm_deg=10.0,
                    claw_state="open",
                    held_object_id=None,
                ),
                last_result=PilotSkillResult(
                    command_id="cmd-verify",
                    skill="verify_grasp",
                    status=CommandStatus.OK,
                    completed_ms=1190,
                ),
            ),
            context,
        ),
        "grasp_likely",
    )

    assert likely.state is AssertionState.TRUE
    assert len(likely.evidence) >= 2
    assert failed.state is AssertionState.FALSE
    assert single_class.state is AssertionState.UNKNOWN
    assert no_object_evidence.state is AssertionState.UNKNOWN
    assert conflict.state is AssertionState.UNKNOWN
    assert "conflicting" in (conflict.recovery_hint or "")


def test_carrying_ball_requires_compatible_manipulator_and_object_state() -> None:
    context = _context()

    carrying = _assertion_by_id(
        evaluate_assertions(
            _observation(
                manipulator=ManipulatorState(
                    arm_deg=20.0,
                    claw_state="holding",
                    held_object_id="ball-yellow-1",
                )
            ),
            context,
        ),
        "carrying_ball",
    )
    not_carrying = _assertion_by_id(
        evaluate_assertions(
            _observation(
                manipulator=ManipulatorState(
                    arm_deg=20.0,
                    claw_state="open",
                    held_object_id=None,
                ),
                last_result=PilotSkillResult(
                    command_id="cmd-verify",
                    skill="verify_grasp",
                    status=CommandStatus.FAILED,
                    completed_ms=1190,
                ),
            ),
            context,
        ),
        "carrying_ball",
    )

    assert carrying.state is AssertionState.TRUE
    assert not_carrying.state is AssertionState.FALSE


def test_destination_arrival_uses_configured_pose_and_tag_context() -> None:
    context = _context()
    near_pose = Pose2D(x_m=1.05, y_m=2.04, heading_rad=0.0)
    far_pose = Pose2D(x_m=2.0, y_m=2.0, heading_rad=0.0)
    tag_context = AssertionContext(
        target=context.target,
        destination=AssertionDestination(destination_id="goal-blue-1", tag_id=7),
    )

    near = _assertion_by_id(
        evaluate_assertions(
            _observation(
                pose=near_pose,
                localization=LocalizationState(pose=near_pose, confidence=0.9, age_ms=20),
            ),
            context,
        ),
        "at_destination",
    )
    far = _assertion_by_id(
        evaluate_assertions(
            _observation(
                pose=far_pose,
                localization=LocalizationState(pose=far_pose, confidence=0.9, age_ms=20),
            ),
            context,
        ),
        "at_destination",
    )
    tag = _assertion_by_id(
        evaluate_assertions(
            _observation(
                visible_tags=[
                    VisibleTag(
                        tag_id=7,
                        confidence=0.92,
                        pose=Pose2D(x_m=0.2, y_m=0.1, heading_rad=0.0),
                    )
                ]
            ),
            tag_context,
        ),
        "at_destination",
    )

    assert near.state is AssertionState.TRUE
    assert far.state is AssertionState.FALSE
    assert tag.state is AssertionState.TRUE


def test_drop_likely_and_ball_at_destination_fuse_destination_drop_and_object_evidence() -> None:
    context = _context()
    pose = Pose2D(x_m=1.02, y_m=2.03, heading_rad=0.0)
    observation = _observation(
        pose=pose,
        localization=LocalizationState(pose=pose, confidence=0.9, age_ms=20),
        visible_objects=[_target_object(width_px=72)],
        manipulator=ManipulatorState(arm_deg=18.0, claw_state="open", held_object_id=None),
        last_result=PilotSkillResult(
            command_id="cmd-drop",
            skill="verify_drop",
            status=CommandStatus.OK,
            completed_ms=1195,
        ),
    )

    assertions = evaluate_assertions(observation, context)

    assert _assertion_by_id(assertions, "drop_likely").state is AssertionState.TRUE
    assert _assertion_by_id(assertions, "ball_at_destination").state is AssertionState.TRUE


def test_drop_likely_requires_target_object_evidence_at_destination() -> None:
    context = _context()
    pose = Pose2D(x_m=1.02, y_m=2.03, heading_rad=0.0)
    observation = _observation(
        pose=pose,
        localization=LocalizationState(pose=pose, confidence=0.9, age_ms=20),
        manipulator=ManipulatorState(arm_deg=18.0, claw_state="open", held_object_id=None),
        last_result=PilotSkillResult(
            command_id="cmd-drop",
            skill="verify_drop",
            status=CommandStatus.OK,
            completed_ms=1195,
        ),
    )

    drop = _assertion_by_id(evaluate_assertions(observation, context), "drop_likely")

    assert drop.state is AssertionState.UNKNOWN


def test_drop_and_final_delivery_conflicts_return_unknown_with_recovery_hint() -> None:
    context = _context()
    pose = Pose2D(x_m=1.02, y_m=2.03, heading_rad=0.0)
    observation = _observation(
        pose=pose,
        localization=LocalizationState(pose=pose, confidence=0.9, age_ms=20),
        visible_objects=[_target_object(width_px=72)],
        manipulator=ManipulatorState(
            arm_deg=18.0,
            claw_state="holding",
            held_object_id="ball-yellow-1",
        ),
        last_result=PilotSkillResult(
            command_id="cmd-drop",
            skill="verify_drop",
            status=CommandStatus.OK,
            completed_ms=1195,
        ),
    )

    assertions = evaluate_assertions(observation, context)
    drop = _assertion_by_id(assertions, "drop_likely")
    final = _assertion_by_id(assertions, "ball_at_destination")

    assert drop.state is AssertionState.UNKNOWN
    assert final.state is AssertionState.UNKNOWN
    assert "conflicting" in (drop.recovery_hint or "")
    assert "conflicting" in (final.recovery_hint or "")


def test_package_assertion_exports_import_without_ros_packages(monkeypatch) -> None:
    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            if fullname == "rclpy" or fullname.startswith(("rclpy.", "std_msgs.", "sensor_msgs.")):
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.assertions", None)
    sys.modules.pop("pilot", None)

    module = importlib.import_module("pilot")
    assertions = module.evaluate_assertions(_observation(observed_ms=1), module.AssertionContext())

    assert module.REQUIRED_ASSERTION_IDS == REQUIRED_ASSERTION_IDS
    assert [assertion.assertion_id for assertion in assertions] == list(REQUIRED_ASSERTION_IDS)
    assert "rclpy" not in sys.modules
