from __future__ import annotations

import importlib
import json
import sys

from contracts import (
    AssertionState,
    BridgeHealth,
    ClawCloseParams,
    ClawCloseSkillCommand,
    CommandStatus,
    LocalizationState,
    ManipulatorState,
    PilotAssertion,
    PilotDecision,
    PilotDecisionAction,
    PilotObservation,
    PilotSkillResult,
    PilotTaskPhase,
    Pose2D,
    VisibleObject,
)
from pilot.decision import (
    DecisionAdapterResult,
    DecisionPromptClient,
    request_pilot_decision,
)


_DEFAULT_COMMAND = object()


class SequencedPromptClient:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []
        self.responses_returned: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self._responses:
            raise AssertionError("adapter submitted more prompts than expected")
        response = self._responses.pop(0)
        self.responses_returned.append(response)
        return response


def _observation() -> PilotObservation:
    command = ClawCloseSkillCommand(
        command_id="cmd-close-1",
        issued_ms=1000,
        params=ClawCloseParams(grip_force_n=3.0),
    )
    return PilotObservation(
        observed_ms=1250,
        task_phase=PilotTaskPhase.MANIPULATE,
        objective="pick up the yellow ball",
        robot_pose=Pose2D(x_m=1.0, y_m=0.5, heading_rad=0.2),
        localization=LocalizationState(
            pose=Pose2D(x_m=1.0, y_m=0.5, heading_rad=0.2),
            confidence=0.83,
            age_ms=30,
        ),
        visible_objects=[
            VisibleObject(object_id="obj-yellow-1", label="yellow_ball", confidence=0.91)
        ],
        manipulator=ManipulatorState(
            arm_deg=35.0,
            claw_state="holding",
            held_object_id="obj-yellow-1",
        ),
        bridge=BridgeHealth(state="ok", last_heartbeat_age_ms=12, battery_pct=88.0),
        last_command=command,
        last_result=PilotSkillResult(
            command_id="cmd-close-1",
            skill="claw_close",
            status=CommandStatus.OK,
            completed_ms=1200,
            message="grip verified",
        ),
        current_assertions=[
            PilotAssertion(
                assertion_id="assert-grasp",
                predicate="object held",
                state=AssertionState.TRUE,
                confidence=0.86,
                observed_ms=1230,
            )
        ],
    )


def _command(
    skill: str = "face_target", params: dict[str, object] | None = None
) -> dict[str, object]:
    return {
        "v": 1,
        "command_id": f"cmd-{skill}-1",
        "issued_ms": 1300,
        "skill": skill,
        "params": {"target_id": "obj-yellow-1"} if params is None else params,
    }


def _decision(
    *,
    action: str = "continue",
    command: dict[str, object] | None | object = _DEFAULT_COMMAND,
    decision_id: str = "decision-1",
) -> dict[str, object]:
    return {
        "v": 1,
        "decision_id": decision_id,
        "decided_ms": 1350,
        "action": action,
        "rationale": "target remains visible",
        "confidence": 0.82,
        "command": _command() if command is _DEFAULT_COMMAND else command,
    }


def _valid_response(decision_id: str = "decision-valid") -> str:
    return json.dumps(_decision(decision_id=decision_id))


def _retry_context(prompt: str) -> dict[str, object]:
    marker = "## retry context\n"
    assert marker in prompt
    section = prompt.split(marker, maxsplit=1)[1].split("\n\n## ", maxsplit=1)[0]
    context = json.loads(section)
    assert isinstance(context, dict)
    return context


def test_adapter_returns_valid_first_response_without_retry() -> None:
    client: DecisionPromptClient = SequencedPromptClient([_valid_response()])

    result = request_pilot_decision(
        _observation(),
        client=client,
        recent_history="cmd-close-1 completed",
        safety_constraints=["ttl_ms must remain bounded"],
        max_attempts=3,
    )

    assert isinstance(result, DecisionAdapterResult)
    assert result.ok
    assert isinstance(result.decision, PilotDecision)
    assert result.decision.action is PilotDecisionAction.CONTINUE
    assert result.command is result.decision.command
    assert result.command is not None
    assert result.attempt_count == 1
    assert len(client.prompts) == 1
    assert "## retry context" not in client.prompts[0]


def test_malformed_json_retries_with_structured_failure_context() -> None:
    client = SequencedPromptClient(['{"v": 1', _valid_response("decision-after-malformed")])

    result = request_pilot_decision(_observation(), client=client, max_attempts=2)

    context = _retry_context(client.prompts[1])
    previous = context["previous_attempt"]
    assert result.ok
    assert result.attempt_count == 2
    assert len(client.prompts) == 2
    assert previous["attempt_number"] == 1
    assert previous["error"]["code"] == "malformed_json"
    assert previous["error"]["message"] == "response must be strict whole-response JSON"
    assert previous["error"]["details"]["line"] == 1


def test_unknown_skill_retries_without_exposing_failed_command() -> None:
    invalid = json.dumps(_decision(command=_command("fly_to_goal", {"target_id": "obj-yellow-1"})))
    client = SequencedPromptClient([invalid, _valid_response("decision-after-skill")])

    result = request_pilot_decision(_observation(), client=client, max_attempts=2)

    context = _retry_context(client.prompts[1])
    assert result.ok
    assert result.decision is not None
    assert result.decision.decision_id == "decision-after-skill"
    assert result.command is not None
    assert result.command.skill == "face_target"
    assert result.command.command_id == "cmd-face_target-1"
    assert context["previous_attempt"]["error"]["code"] == "unknown_skill"
    assert context["previous_attempt"]["error"]["details"]["skill"] == "fly_to_goal"


def test_unknown_action_retries_and_returns_only_final_valid_decision() -> None:
    invalid = json.dumps(_decision(action="hover"))
    client = SequencedPromptClient([invalid, _valid_response("decision-after-action")])

    result = request_pilot_decision(_observation(), client=client, max_attempts=2)

    context = _retry_context(client.prompts[1])
    assert result.ok
    assert result.decision is not None
    assert result.decision.decision_id == "decision-after-action"
    assert result.decision.action is PilotDecisionAction.CONTINUE
    assert result.command is not None
    assert context["previous_attempt"]["error"]["code"] == "unknown_action"
    assert context["previous_attempt"]["error"]["details"]["action"] == "hover"


def test_retry_exhaustion_returns_error_without_decision_or_command() -> None:
    client = SequencedPromptClient(["not json", "[]"])

    result = request_pilot_decision(_observation(), client=client, max_attempts=2)

    assert not result.ok
    assert result.decision is None
    assert result.command is None
    assert result.error is not None
    assert result.error.attempt_count == 2
    assert result.error.max_attempts == 2
    assert result.error.code == "non_object_json"
    assert result.error.details["parsed_type"] == "array"
    assert len(client.prompts) == 2
    assert client.responses_returned == ["not json", "[]"]


def test_mock_client_response_order_and_prompt_count_for_success_and_exhaustion() -> None:
    success_client = SequencedPromptClient(["bad", _valid_response("decision-in-order")])
    exhausted_client = SequencedPromptClient(["bad", "worse", "still bad"])

    success = request_pilot_decision(_observation(), client=success_client, max_attempts=3)
    exhausted = request_pilot_decision(_observation(), client=exhausted_client, max_attempts=2)

    assert success.ok
    assert success.attempt_count == 2
    assert success_client.responses_returned == ["bad", _valid_response("decision-in-order")]
    assert len(success_client.prompts) == 2

    assert not exhausted.ok
    assert exhausted.attempt_count == 2
    assert exhausted_client.responses_returned == ["bad", "worse"]
    assert len(exhausted_client.prompts) == 2


def test_retry_prompt_context_is_deterministic_and_json_compatible() -> None:
    invalid = json.dumps(_decision(action="hover"))
    first_client = SequencedPromptClient([invalid, _valid_response()])
    second_client = SequencedPromptClient([invalid, _valid_response()])

    first = request_pilot_decision(_observation(), client=first_client, max_attempts=2)
    second = request_pilot_decision(_observation(), client=second_client, max_attempts=2)

    first_context = _retry_context(first_client.prompts[1])
    assert first.ok and second.ok
    assert first_client.prompts[1] == second_client.prompts[1]
    assert json.loads(json.dumps(first_context, sort_keys=True)) == first_context
    assert first_context == {
        "previous_attempt": {
            "attempt_number": 1,
            "error": {
                "code": "unknown_action",
                "message": "unknown decision action: hover",
                "details": {
                    "action": "hover",
                    "allowed_actions": [
                        "continue",
                        "retry",
                        "stop_success",
                        "stop_failure",
                        "request_human",
                    ],
                },
            },
        }
    }


def test_adapter_import_and_execution_remain_ros_free_and_provider_sdk_free(monkeypatch) -> None:
    forbidden_roots = {
        "anthropic",
        "geometry_msgs",
        "google_genai",
        "openai",
        "rclpy",
        "sensor_msgs",
        "std_msgs",
    }

    class RejectForbiddenImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            root = fullname.split(".", maxsplit=1)[0]
            if root in forbidden_roots:
                raise AssertionError(f"unexpected runtime/provider import: {fullname}")
            return None

    for root in forbidden_roots:
        sys.modules.pop(root, None)
    monkeypatch.setattr(sys, "meta_path", [RejectForbiddenImports(), *sys.meta_path])
    sys.modules.pop("pilot.decision", None)

    module = importlib.import_module("pilot.decision")
    client = SequencedPromptClient([_valid_response()])
    result = module.request_pilot_decision(_observation(), client=client, max_attempts=1)

    assert result.ok
    assert len(client.prompts) == 1
    assert forbidden_roots.isdisjoint(sys.modules)


def test_package_exports_adapter_api_additively() -> None:
    import pilot

    assert pilot.request_pilot_decision is request_pilot_decision
    assert pilot.DecisionAdapterResult is DecisionAdapterResult
    assert pilot.DecisionPromptClient is DecisionPromptClient
    assert pilot.build_decision_prompt is not None
    assert pilot.render_prompt is not None


def test_max_attempts_must_be_positive_integer_before_provider_call() -> None:
    client = SequencedPromptClient([_valid_response()])

    for max_attempts in (0, -1, True):
        try:
            request_pilot_decision(_observation(), client=client, max_attempts=max_attempts)
        except ValueError as exc:
            assert "max_attempts" in str(exc)
        else:
            raise AssertionError("invalid max_attempts should fail before provider submission")

    assert client.prompts == []
