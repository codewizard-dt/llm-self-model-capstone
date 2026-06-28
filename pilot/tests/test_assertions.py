from __future__ import annotations

import dataclasses
import importlib
import sys

import pytest
from contracts import (
    AssertionEvidence,
    AssertionState,
    BridgeHealth,
    LocalizationState,
    ManipulatorState,
    PilotAssertion,
    PilotObservation,
    PilotTaskPhase,
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


def _observation(observed_ms: int = 1200) -> PilotObservation:
    return PilotObservation(
        observed_ms=observed_ms,
        task_phase=PilotTaskPhase.SURVEY,
        objective="deliver the yellow ball",
        localization=LocalizationState(pose=None, confidence=0.0, age_ms=50),
        manipulator=ManipulatorState(arm_deg=None, claw_state="unknown", held_object_id=None),
        bridge=BridgeHealth(state="ok", last_heartbeat_age_ms=25),
    )


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
    assert "deferred heuristics" in assertion.predicate
    assert len(assertion.evidence) == 1
    assert assertion.evidence[0].source == "planner"
    assert assertion.evidence[0].confidence == 0.0
    assert assertion.evidence[0].observed_ms == 5000
    assert assertion.evidence[0].age_ms == 0
    assert "deferred heuristics" in assertion.evidence[0].summary
    assert "ball-yellow-1" in assertion.evidence[0].summary
    assert PilotAssertion.model_validate(assertion.model_dump()) == assertion


def test_evaluate_assertions_returns_unknown_assertions_in_required_order() -> None:
    observation = _observation(observed_ms=300)

    assertions = evaluate_assertions(observation, AssertionContext())

    assert isinstance(assertions, tuple)
    assert [assertion.assertion_id for assertion in assertions] == list(REQUIRED_ASSERTION_IDS)
    assert len(assertions) == len(REQUIRED_ASSERTION_IDS)
    for assertion in assertions:
        assert assertion.state is AssertionState.UNKNOWN
        assert assertion.confidence == 0.0
        assert assertion.evidence
        assert assertion.observed_ms == observation.observed_ms
        assert PilotAssertion.model_validate(assertion.model_dump()) == assertion


def test_evaluate_assertions_defaults_context() -> None:
    assertions = evaluate_assertions(_observation())

    assert [assertion.assertion_id for assertion in assertions] == list(REQUIRED_ASSERTION_IDS)


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
