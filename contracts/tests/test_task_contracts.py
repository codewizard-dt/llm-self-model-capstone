"""Typed task-block contracts and the score enforcement on ContractLine.

These restore the field-level guarantees the flexible `dict` edges dropped
(PR #9 review): the `score` task must carry `ball_in_bin` and friends, typed.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from contracts import (
    ContractLine,
    ScoreContractLine,
    ScoreGap,
    ScoreObserved,
    ScorePredicted,
)

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "session_example.jsonl"


def _score_line() -> dict:
    for raw in FIXTURE_PATH.read_text().splitlines():
        if raw.strip():
            data = json.loads(raw)
            if data["task"] == "score":
                return data
    raise AssertionError("no score line in fixture")


# --- the typed blocks themselves ------------------------------------------------


def test_score_blocks_round_trip_from_fixture() -> None:
    line = _score_line()
    assert ScorePredicted.model_validate(line["predicted"]).success is True
    assert ScoreObserved.model_validate(line["outcome"]).ball_in_bin is True
    assert ScoreGap.model_validate(line["gap"]).distance_error_m == -0.05


def test_score_observed_requires_ball_in_bin() -> None:
    with pytest.raises(ValidationError):
        ScoreObserved.model_validate({"score_value": 1.0, "success": True})


def test_score_observed_forbids_unknown_field() -> None:
    with pytest.raises(ValidationError):
        ScoreObserved.model_validate(
            {"ball_in_bin": True, "score_value": 1.0, "success": True, "bonus": 9}
        )


def test_ball_in_bin_must_be_a_real_bool() -> None:
    # strict bool: a string must not silently coerce to True.
    with pytest.raises(ValidationError):
        ScoreObserved.model_validate({"ball_in_bin": "yes", "score_value": 1.0, "success": True})


# --- enforcement through the ContractLine envelope ------------------------------


def test_score_line_parses_and_carries_ball_in_bin() -> None:
    model = ContractLine.model_validate(_score_line())
    assert model.task == "score"
    assert model.outcome is not None and model.outcome["ball_in_bin"] is True


def test_score_line_missing_ball_in_bin_raises() -> None:
    line = _score_line()
    del line["outcome"]["ball_in_bin"]
    with pytest.raises(ValidationError):
        ContractLine.model_validate(line)


def test_score_line_typo_in_outcome_raises() -> None:
    line = _score_line()
    line["outcome"]["bal_in_bin"] = line["outcome"].pop("ball_in_bin")
    with pytest.raises(ValidationError):
        ContractLine.model_validate(line)


def test_score_line_missing_outcome_raises() -> None:
    line = _score_line()
    line["outcome"] = None
    with pytest.raises(ValidationError):
        ContractLine.model_validate(line)


def test_score_predicted_extra_field_raises() -> None:
    line = _score_line()
    line["predicted"]["mystery"] = 1.0
    with pytest.raises(ValidationError):
        ContractLine.model_validate(line)


def test_non_score_task_keeps_flexible_dicts() -> None:
    # A score-shaped outcome typo only fails for task == "score"; other tasks
    # remain free-form, so adding a typed task never constrains existing ones.
    line = _score_line()
    line["task"] = "grab"
    line["outcome"]["bal_in_bin"] = line["outcome"].pop("ball_in_bin")
    model = ContractLine.model_validate(line)
    assert model.task == "grab"


# --- the typed ScoreContractLine successor --------------------------------------


def test_score_contract_line_gives_typed_attribute_access() -> None:
    typed = ScoreContractLine.model_validate(_score_line())
    assert typed.outcome.ball_in_bin is True
    assert typed.predicted.success is True
    assert typed.gap.distance_error_m == -0.05
