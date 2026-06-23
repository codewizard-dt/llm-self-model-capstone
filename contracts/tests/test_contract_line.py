"""Envelope round-trip and edge-case tests for ContractLine."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from contracts import ContractLine

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "session_example.jsonl"


def _fixture_lines() -> list[str]:
    return [line for line in FIXTURE_PATH.read_text().splitlines() if line.strip()]


def test_fixture_has_four_lines() -> None:
    assert len(_fixture_lines()) == 4


@pytest.mark.parametrize("line", _fixture_lines())
def test_fixture_lines_round_trip(line: str) -> None:
    model = ContractLine.model_validate_json(line)
    reparsed = ContractLine.model_validate_json(model.model_dump_json())
    assert reparsed == model


def test_motor_only_line_without_vision_parses() -> None:
    pull_line = next(
        line for line in _fixture_lines() if ContractLine.model_validate_json(line).task == "pull"
    )
    model = ContractLine.model_validate_json(pull_line)
    assert model.vision is None
    assert model.motor_samples[0].subsystem == "drivetrain"


def test_line_with_outcome_none_parses() -> None:
    model = ContractLine(
        session_id="session_20260624_141200",
        generation=0,
        round=1,
        task="grab",
        motor_samples=ContractLine.model_validate_json(_fixture_lines()[0]).motor_samples,
        predicted={"success": True},
        gap={"force_error_N": 0.0},
        outcome=None,
    )
    assert model.outcome is None


def test_missing_session_id_raises() -> None:
    with pytest.raises(ValidationError):
        ContractLine(
            generation=0,
            round=1,
            task="grab",
            motor_samples=ContractLine.model_validate_json(_fixture_lines()[0]).motor_samples,
            predicted={"success": True},
            gap={"force_error_N": 0.0},
        )


def test_task_accepts_arbitrary_string() -> None:
    model = ContractLine(
        session_id="session_20260624_141200",
        generation=0,
        round=1,
        task="custom_task",
        motor_samples=ContractLine.model_validate_json(_fixture_lines()[0]).motor_samples,
        predicted={"success": True},
        gap={"force_error_N": 0.0},
    )
    assert model.task == "custom_task"


def test_score_fixture_carries_ball_in_bin_in_flexible_outcome() -> None:
    score_line = next(
        line for line in _fixture_lines() if ContractLine.model_validate_json(line).task == "score"
    )
    model = ContractLine.model_validate_json(score_line)
    assert model.outcome is not None
    assert model.outcome["ball_in_bin"] is True
