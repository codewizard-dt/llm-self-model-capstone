"""Validator matrix for the SelfModel (F2) and its layered sub-models."""

from __future__ import annotations

import json
import typing
from pathlib import Path

import pytest
from pydantic import ValidationError

from contracts import SelfModel
from contracts import vocabulary as vocab
from contracts.self_model import CapabilityLayer, SelfModelConfig


# contracts/tests/test_self_model.py -> parents[1] is the contracts root where
# fixtures/ lives (same resolution validate.py uses, robust to cwd).
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


VALID_CONFIG = {
    "motor_allocation": "2drive+1arm+1claw",
    "arm_position": "front",
    "end_effector": "claw_grasper",
    "wheel_config": "front_omni+rear_standard",
    "arm_gear_ratio": "7:1",
    "cartridge": "200rpm",
}


def minimal_self_model(**overrides) -> dict:
    doc = {
        "generation": 0,
        "parent_generation": None,
        "config": dict(VALID_CONFIG),
        "structural": {"parts": [], "connections": []},
        "capability": {},
        "predictive": {},
        "gap_model": {},
        "reasoning": "initial design",
    }
    doc.update(overrides)
    return doc


def test_minimal_valid_round_trip() -> None:
    model = SelfModel(**minimal_self_model())
    assert model.schema_version == "1.0"
    assert model.generation == 0
    assert model.parent_generation is None
    # round-trip through dict
    again = SelfModel(**model.model_dump())
    assert again.config.cartridge == vocab.Cartridge.RPM_200


def test_gen0_with_parent_raises() -> None:
    with pytest.raises(ValidationError):
        SelfModel(**minimal_self_model(generation=0, parent_generation=0))


def test_gen1_with_null_parent_raises() -> None:
    with pytest.raises(ValidationError):
        SelfModel(**minimal_self_model(generation=1, parent_generation=None))


def test_parent_ge_generation_raises() -> None:
    with pytest.raises(ValidationError):
        SelfModel(**minimal_self_model(generation=2, parent_generation=2))
    with pytest.raises(ValidationError):
        SelfModel(**minimal_self_model(generation=2, parent_generation=3))


def test_gen1_with_valid_parent_ok() -> None:
    model = SelfModel(**minimal_self_model(generation=2, parent_generation=1))
    assert model.parent_generation == 1


def test_negative_generation_raises() -> None:
    with pytest.raises(ValidationError):
        SelfModel(**minimal_self_model(generation=-1))


def test_empty_reasoning_raises() -> None:
    with pytest.raises(ValidationError):
        SelfModel(**minimal_self_model(reasoning=""))


@pytest.mark.parametrize("missing", ["config", "capability", "generation"])
def test_missing_required_field_raises(missing: str) -> None:
    doc = minimal_self_model()
    del doc[missing]
    with pytest.raises(ValidationError):
        SelfModel(**doc)


def test_out_of_vocabulary_config_raises() -> None:
    bad = dict(VALID_CONFIG, cartridge="999rpm")
    with pytest.raises(ValidationError):
        SelfModel(**minimal_self_model(config=bad))


def test_config_annotations_are_shared_vocabulary_enums() -> None:
    hints = typing.get_type_hints(SelfModelConfig)
    assert hints["motor_allocation"] is vocab.MotorAllocation
    assert hints["arm_position"] is vocab.ArmPosition
    assert hints["end_effector"] is vocab.EndEffector
    assert hints["wheel_config"] is vocab.WheelConfig
    assert hints["arm_gear_ratio"] is vocab.ArmGearRatio
    assert hints["cartridge"] is vocab.Cartridge


def test_predictive_and_gap_model_accept_arbitrary_task_keys() -> None:
    model = SelfModel(
        **minimal_self_model(
            predictive={"score": {"reach_ok": True, "note": "x", "value": 1.5}},
            gap_model={"score": {"force_error_N": 0.5, "duration_error_s": 0.1}},
        )
    )
    assert model.predictive["score"]["reach_ok"] is True
    assert model.gap_model["score"]["force_error_N"] == 0.5


def test_extra_field_on_strict_config_raises() -> None:
    bad = dict(VALID_CONFIG, bogus="x")
    with pytest.raises(ValidationError):
        SelfModelConfig(**bad)


def test_extra_field_on_capability_raises() -> None:
    with pytest.raises(ValidationError):
        CapabilityLayer(reach_mm=1.0, bogus="x")


# F1's frozen grab residual keys (force_error_N / duration_error_s), taken from the
# session_example.jsonl grab `gap` block; gen1's gap_model.grab must be a subset.
F1_GRAB_GAP_KEYS = {"force_error_N", "duration_error_s"}


@pytest.mark.parametrize("name", ["self_model_gen0.json", "self_model_gen1.json"])
def test_self_model_fixture_round_trips(name: str) -> None:
    raw = (FIXTURES_DIR / name).read_text()
    model = SelfModel.model_validate_json(raw)
    # round-trips: re-serialize and re-parse yields an equal document
    again = SelfModel.model_validate_json(model.model_dump_json())
    assert again.model_dump() == model.model_dump()


def test_gen1_revision_closes_the_grab_gap() -> None:
    gen0 = _load_fixture("self_model_gen0.json")
    gen1 = _load_fixture("self_model_gen1.json")

    assert gen1["generation"] == 1
    assert gen1["parent_generation"] == 0

    # At least one capability field OR predictive.grab value moved vs Gen-0.
    capability_changed = gen0["capability"] != gen1["capability"]
    predicted_grab_changed = gen0["predictive"]["grab"] != gen1["predictive"]["grab"]
    assert capability_changed or predicted_grab_changed

    # gap_model.grab keyed only with F1's frozen grab residual keys.
    assert set(gen1["gap_model"]["grab"].keys()) <= F1_GRAB_GAP_KEYS

    # The residual shrank toward 0 vs Gen-0 (the gap closing).
    assert abs(gen1["gap_model"]["grab"]["force_error_N"]) < abs(
        gen0["gap_model"]["grab"]["force_error_N"]
    )
