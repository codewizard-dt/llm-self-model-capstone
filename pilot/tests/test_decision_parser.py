from __future__ import annotations

import json
from copy import deepcopy

from contracts import PilotDecision, PilotDecisionAction
from pilot.decision import DecisionParseResult, parse_decision_response

_DEFAULT_COMMAND = object()


def _command(
    skill: str = "face_target", params: dict[str, object] | None = None
) -> dict[str, object]:
    return {
        "v": 1,
        "command_id": f"cmd-{skill}-1",
        "issued_ms": 1000,
        "skill": skill,
        "params": {"target_id": "obj-1"} if params is None else params,
    }


def _decision(
    *,
    action: str = "continue",
    command: dict[str, object] | None | object = _DEFAULT_COMMAND,
) -> dict[str, object]:
    return {
        "v": 1,
        "decision_id": "decision-1",
        "decided_ms": 1200,
        "action": action,
        "rationale": "target remains visible",
        "confidence": 0.82,
        "command": _command() if command is _DEFAULT_COMMAND else command,
    }


def _parse(payload: dict[str, object]) -> DecisionParseResult:
    return parse_decision_response(json.dumps(payload))


def _assert_invalid(result: DecisionParseResult, code: str) -> None:
    assert not result.ok
    assert result.decision is None
    assert result.command is None
    assert result.error is not None
    assert result.error.code == code
    assert result.error.message


def test_parse_valid_continue_and_retry_with_registry_known_commands() -> None:
    continue_result = _parse(_decision(action="continue", command=_command("face_target")))
    retry_payload = _decision(action="retry", command=_command("survey_scene", {}))
    retry_payload["retry_of_command_id"] = "cmd-survey-scene-previous"
    retry_result = _parse(retry_payload)

    assert continue_result.ok
    assert isinstance(continue_result.decision, PilotDecision)
    assert continue_result.decision.action is PilotDecisionAction.CONTINUE
    assert continue_result.command is continue_result.decision.command
    assert continue_result.command is not None
    assert continue_result.command.skill == "face_target"

    assert retry_result.ok
    assert isinstance(retry_result.decision, PilotDecision)
    assert retry_result.decision.action is PilotDecisionAction.RETRY
    assert retry_result.command is not None
    assert retry_result.command.skill == "survey_scene"


def test_parse_valid_stop_decisions_with_null_or_stop_command_only() -> None:
    stop_success_without_command = _decision(action="stop_success", command=None)
    stop_success_without_command["stop_reason"] = "task complete"
    stop_failure_with_stop = _decision(
        action="stop_failure",
        command=_command("stop", {"reason": "fault"}),
    )
    stop_failure_with_stop["stop_reason"] = "bridge fault"

    success_result = _parse(stop_success_without_command)
    failure_result = _parse(stop_failure_with_stop)
    non_stop_result = _parse(_decision(action="stop_success", command=_command("face_target")))

    assert success_result.ok
    assert success_result.decision is not None
    assert success_result.decision.action is PilotDecisionAction.STOP_SUCCESS
    assert success_result.command is None

    assert failure_result.ok
    assert failure_result.decision is not None
    assert failure_result.decision.action is PilotDecisionAction.STOP_FAILURE
    assert failure_result.command is not None
    assert failure_result.command.skill == "stop"

    _assert_invalid(non_stop_result, "action_command_mismatch")


def test_parse_valid_request_human_returns_no_executable_command() -> None:
    payload = _decision(action="request_human", command=None)
    payload["rationale"] = "operator judgment required"

    result = _parse(payload)

    assert result.ok
    assert result.decision is not None
    assert result.decision.action is PilotDecisionAction.REQUEST_HUMAN
    assert result.decision.command is None
    assert result.command is None


def test_parse_malformed_json_and_non_object_json_return_structured_errors() -> None:
    malformed = parse_decision_response('{"v": 1')
    prose_wrapped = parse_decision_response(f"prose {json.dumps(_decision())}")
    array_response = parse_decision_response("[]")
    string_response = parse_decision_response('"continue"')

    _assert_invalid(malformed, "malformed_json")
    assert malformed.error is not None
    assert malformed.error.details["line"] == 1

    _assert_invalid(prose_wrapped, "malformed_json")
    _assert_invalid(array_response, "non_object_json")
    assert array_response.error is not None
    assert array_response.error.details["parsed_type"] == "array"
    _assert_invalid(string_response, "non_object_json")


def test_parse_rejects_non_standard_json_constants_before_validation() -> None:
    payload = _decision(
        command=_command(
            "go_to_destination",
            {
                "x_m": "__NON_STANDARD_JSON_CONSTANT__",
                "y_m": 1.0,
            },
        )
    )

    for constant in ("NaN", "Infinity", "-Infinity"):
        raw_response = json.dumps(payload).replace(
            '"__NON_STANDARD_JSON_CONSTANT__"',
            constant,
        )

        result = parse_decision_response(raw_response)

        _assert_invalid(result, "malformed_json")
        assert result.error is not None
        assert result.error.details["constant"] == constant


def test_parse_unknown_action_and_unknown_skill_have_distinct_errors() -> None:
    unknown_action_payload = _decision(action="dance")
    unknown_skill_payload = _decision(command=_command("fly_to_goal", {"target_id": "obj-1"}))

    unknown_action = _parse(unknown_action_payload)
    unknown_skill = _parse(unknown_skill_payload)

    _assert_invalid(unknown_action, "unknown_action")
    assert unknown_action.error is not None
    assert "dance" in unknown_action.error.message
    assert "allowed_actions" in unknown_action.error.details

    _assert_invalid(unknown_skill, "unknown_skill")
    assert unknown_skill.error is not None
    assert "fly_to_goal" in unknown_skill.error.message
    assert "allowed_skills" in unknown_skill.error.details


def test_parse_schema_invalid_command_parameters_use_contract_validation() -> None:
    payload = _decision(command=_command("arm_to_angle", {"deg": 10_000.0}))

    result = _parse(payload)

    _assert_invalid(result, "schema_validation")
    assert result.error is not None
    assert "PilotDecision contract" in result.error.message
    assert result.error.details["errors"]


def test_parse_invalid_action_command_consistency_returns_no_executable_objects() -> None:
    missing_continue_command = _decision(action="continue", command=None)
    request_human_with_command = _decision(
        action="request_human",
        command=_command("stop", {"reason": "operator"}),
    )
    retry_without_command = _decision(action="retry", command=None)

    for result in (
        _parse(missing_continue_command),
        _parse(request_human_with_command),
        _parse(retry_without_command),
    ):
        _assert_invalid(result, "action_command_mismatch")


def test_parse_trims_whitespace_but_rejects_non_object_values() -> None:
    payload = _decision()

    result = parse_decision_response(f"\n\t{json.dumps(payload)}  \n")
    null_result = parse_decision_response(" null ")
    number_result = parse_decision_response(" 1 ")

    assert result.ok
    assert result.decision is not None
    assert result.decision.command is not None
    _assert_invalid(null_result, "non_object_json")
    _assert_invalid(number_result, "non_object_json")


def test_parse_does_not_mutate_input_payload() -> None:
    payload = _decision(command=_command("go_to_destination", {"destination_id": "drop-zone"}))
    original = deepcopy(payload)

    result = _parse(payload)

    assert result.ok
    assert payload == original
