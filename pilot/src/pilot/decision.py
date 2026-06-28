"""Deterministic prompt construction and parsing for pilot LLM decisions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import json
from json import JSONDecodeError
from typing import Literal, Protocol, TypeAlias

from pydantic import ValidationError

from contracts import PilotDecision, PilotDecisionAction, PilotObservation
import pilot.skills as skill_registry
from pilot.skills import JsonValue

PromptPayload: TypeAlias = dict[str, JsonValue]
DecisionParseErrorCode: TypeAlias = Literal[
    "malformed_json",
    "non_object_json",
    "unknown_action",
    "unknown_skill",
    "schema_validation",
    "action_command_mismatch",
]

PROMPT_SECTION_ORDER: tuple[str, ...] = (
    "objective",
    "current_phase",
    "observation_snapshot",
    "assertions",
    "last_skill_result",
    "recent_history",
    "allowed_skills",
    "safety_constraints",
    "output_schema",
)

_PROMPT_SECTION_LABELS: dict[str, str] = {
    "objective": "objective",
    "current_phase": "current phase",
    "observation_snapshot": "observation snapshot",
    "assertions": "assertions",
    "last_skill_result": "last skill/result",
    "recent_history": "recent history",
    "allowed_skills": "allowed skills",
    "safety_constraints": "safety constraints",
    "output_schema": "output schema",
}

_OUTPUT_SCHEMA: PromptPayload = {
    "format": "json",
    "required_fields": [
        "v",
        "decision_id",
        "decided_ms",
        "action",
        "rationale",
        "confidence",
    ],
    "optional_fields": [
        "command",
        "retry_of_command_id",
        "stop_reason",
    ],
    "action_values": [action.value for action in PilotDecisionAction],
    "command": {
        "description": "Use one contract-owned pilot skill command from allowed_skills, or null.",
        "required_when_action": ["continue", "retry"],
    },
}


@dataclass(frozen=True, slots=True)
class DecisionParseError:
    """Structured, retry-prompt-friendly parser failure data."""

    code: DecisionParseErrorCode
    message: str
    details: dict[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DecisionParseResult:
    """Result of parsing one raw LLM response."""

    decision: PilotDecision | None = None
    error: DecisionParseError | None = None

    def __post_init__(self) -> None:
        has_decision = self.decision is not None
        has_error = self.error is not None
        if has_decision == has_error:
            raise ValueError("decision parse result must contain exactly one of decision or error")

    @property
    def ok(self) -> bool:
        return self.decision is not None

    @property
    def command(self) -> object | None:
        if self.decision is None:
            return None
        return self.decision.command


class DecisionPromptClient(Protocol):
    """Provider boundary for submitting one rendered prompt and receiving one raw response."""

    def complete(self, prompt: str) -> str:
        """Submit one rendered prompt string and return the provider's raw response text."""


@dataclass(frozen=True, slots=True)
class DecisionAdapterError:
    """Final adapter failure after bounded provider attempts are exhausted."""

    attempt_count: int
    max_attempts: int
    final_error: DecisionParseError

    @property
    def code(self) -> DecisionParseErrorCode:
        return self.final_error.code

    @property
    def message(self) -> str:
        return self.final_error.message

    @property
    def details(self) -> dict[str, JsonValue]:
        return dict(self.final_error.details)


@dataclass(frozen=True, slots=True)
class DecisionAdapterResult:
    """Result of invoking the LLM decision adapter."""

    decision: PilotDecision | None = None
    error: DecisionAdapterError | None = None
    attempt_count: int = 0

    def __post_init__(self) -> None:
        has_decision = self.decision is not None
        has_error = self.error is not None
        if has_decision == has_error:
            raise ValueError(
                "decision adapter result must contain exactly one of decision or error"
            )
        if self.attempt_count < 1:
            raise ValueError("decision adapter result attempt_count must be at least 1")

    @property
    def ok(self) -> bool:
        return self.decision is not None

    @property
    def command(self) -> object | None:
        if self.decision is None:
            return None
        return self.decision.command


class _NonStandardJsonConstant(ValueError):
    def __init__(self, constant: str) -> None:
        super().__init__(f"non-standard JSON constant is not allowed: {constant}")
        self.constant = constant


def parse_decision_response(response_text: str) -> DecisionParseResult:
    """Parse and validate a strict JSON LLM decision response.

    Ordinary malformed model output is returned as structured parser errors. Only successful
    results carry a contract-owned ``PilotDecision`` and executable command object.
    """

    try:
        parsed = json.loads(
            response_text.strip(),
            parse_constant=_reject_non_standard_json_constant,
        )
    except _NonStandardJsonConstant as exc:
        return _failure(
            "malformed_json",
            "response must be strict whole-response JSON",
            {
                "constant": exc.constant,
                "reason": "non-standard JSON constants are not valid JSON",
            },
        )
    except JSONDecodeError as exc:
        return _failure(
            "malformed_json",
            "response must be strict whole-response JSON",
            {
                "line": exc.lineno,
                "column": exc.colno,
                "position": exc.pos,
                "reason": exc.msg,
            },
        )

    if not isinstance(parsed, dict):
        return _failure(
            "non_object_json",
            "response JSON must be an object",
            {"parsed_type": _json_type(parsed)},
        )

    action_error = _validate_action_value(parsed)
    if action_error is not None:
        return _failure_from_error(action_error)

    skill_error = _validate_command_skill(parsed)
    if skill_error is not None:
        return _failure_from_error(skill_error)

    try:
        decision = PilotDecision.model_validate(parsed)
    except ValidationError as exc:
        return _failure(
            "schema_validation",
            "response does not match the PilotDecision contract",
            {"errors": _json_safe(exc.errors(include_url=False))},
        )

    consistency_error = _validate_action_command_consistency(decision)
    if consistency_error is not None:
        return _failure_from_error(consistency_error)

    return DecisionParseResult(decision=decision)


def request_pilot_decision(
    observation: PilotObservation,
    *,
    client: DecisionPromptClient,
    recent_history: str = "",
    safety_constraints: Sequence[str] = (),
    allowed_skills: Sequence[Mapping[str, JsonValue]] | None = None,
    max_attempts: int = 1,
) -> DecisionAdapterResult:
    """Invoke an injected prompt client until a valid pilot decision or bounded exhaustion.

    ``max_attempts`` is the total provider submission limit, including the first prompt. Failed
    parser/contract validations are retryable; only a successful final parse exposes a
    ``PilotDecision`` or command object.
    """

    if type(max_attempts) is not int or max_attempts < 1:
        raise ValueError("max_attempts must be an integer greater than or equal to 1")

    base_payload = build_prompt_payload(
        observation,
        recent_history=recent_history,
        safety_constraints=safety_constraints,
        allowed_skills=allowed_skills,
    )
    previous_error: DecisionParseError | None = None

    for attempt_number in range(1, max_attempts + 1):
        payload = _payload_for_attempt(base_payload, attempt_number, previous_error)
        raw_response = client.complete(render_prompt(payload))
        parse_result = parse_decision_response(raw_response)

        if parse_result.decision is not None:
            return DecisionAdapterResult(
                decision=parse_result.decision,
                attempt_count=attempt_number,
            )

        if parse_result.error is None:  # Defensive guard; DecisionParseResult prevents this.
            raise RuntimeError("parser returned neither decision nor error")
        previous_error = parse_result.error

    if previous_error is None:  # Defensive guard; max_attempts validation prevents this.
        raise RuntimeError("adapter exhausted without recording a parser error")

    return DecisionAdapterResult(
        error=DecisionAdapterError(
            attempt_count=max_attempts,
            max_attempts=max_attempts,
            final_error=previous_error,
        ),
        attempt_count=max_attempts,
    )


def build_prompt_payload(
    observation: PilotObservation,
    *,
    recent_history: str = "",
    safety_constraints: Sequence[str] = (),
    allowed_skills: Sequence[Mapping[str, JsonValue]] | None = None,
) -> PromptPayload:
    """Build the JSON-compatible decision prompt payload.

    By default, allowed skill metadata is sourced from the public pilot skill registry summary API.
    The optional override exists for deterministic replay fixtures that have already captured those
    registry summaries.
    """

    observation_snapshot = _json_clone(observation.model_dump(mode="json"))
    skill_summaries = allowed_skills
    if skill_summaries is None:
        skill_summaries = skill_registry.list_skill_summaries()

    return {
        "objective": observation.objective,
        "current_phase": observation.task_phase.value,
        "observation_snapshot": observation_snapshot,
        "assertions": _json_clone(observation_snapshot["current_assertions"]),
        "last_skill_result": {
            "last_command": _json_clone(observation_snapshot["last_command"]),
            "last_result": _json_clone(observation_snapshot["last_result"]),
        },
        "recent_history": recent_history,
        "allowed_skills": _json_clone(list(skill_summaries)),
        "safety_constraints": [str(constraint) for constraint in safety_constraints],
        "output_schema": _json_clone(_OUTPUT_SCHEMA),
    }


def render_prompt(payload: Mapping[str, JsonValue]) -> str:
    """Render a stable text prompt from a prompt payload."""

    rendered_sections: list[str] = ["Pilot decision prompt"]
    emitted: set[str] = set()

    for section in PROMPT_SECTION_ORDER:
        if section in payload:
            rendered_sections.append(_render_section(section, payload[section]))
            emitted.add(section)

    for section in sorted(set(payload) - emitted):
        rendered_sections.append(_render_section(section, payload[section]))

    return "\n\n".join(rendered_sections)


def build_decision_prompt(
    observation: PilotObservation,
    *,
    recent_history: str = "",
    safety_constraints: Sequence[str] = (),
    allowed_skills: Sequence[Mapping[str, JsonValue]] | None = None,
) -> tuple[PromptPayload, str]:
    """Build both the prompt payload and its deterministic rendered text."""

    payload = build_prompt_payload(
        observation,
        recent_history=recent_history,
        safety_constraints=safety_constraints,
        allowed_skills=allowed_skills,
    )
    return payload, render_prompt(payload)


def _payload_for_attempt(
    base_payload: Mapping[str, JsonValue],
    attempt_number: int,
    previous_error: DecisionParseError | None,
) -> PromptPayload:
    payload = _json_clone(base_payload)
    if not isinstance(payload, dict):
        raise TypeError("prompt payload must be a JSON object")

    if previous_error is not None:
        payload["retry_context"] = {
            "previous_attempt": {
                "attempt_number": attempt_number - 1,
                "error": {
                    "code": previous_error.code,
                    "message": previous_error.message,
                    "details": _json_safe(previous_error.details),
                },
            }
        }
    return payload


def _render_section(section: str, value: JsonValue) -> str:
    label = _PROMPT_SECTION_LABELS.get(section, section.replace("_", " "))
    return f"## {label}\n{_canonical_json(value)}"


def _canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True)


def _json_clone(value: object) -> JsonValue:
    return json.loads(_canonical_json(value))


def _reject_non_standard_json_constant(constant: str) -> object:
    raise _NonStandardJsonConstant(constant)


def _validate_action_value(parsed: Mapping[str, object]) -> DecisionParseError | None:
    action = parsed.get("action")
    if not isinstance(action, str):
        return None

    try:
        PilotDecisionAction(action)
    except ValueError:
        return DecisionParseError(
            code="unknown_action",
            message=f"unknown decision action: {action}",
            details={
                "action": action,
                "allowed_actions": [allowed.value for allowed in PilotDecisionAction],
            },
        )
    return None


def _validate_command_skill(parsed: Mapping[str, object]) -> DecisionParseError | None:
    command = parsed.get("command")
    if command is None or not isinstance(command, dict):
        return None

    skill = command.get("skill")
    if not isinstance(skill, str):
        return None

    try:
        skill_registry.get_skill_definition(skill)
    except (KeyError, ValueError):
        return DecisionParseError(
            code="unknown_skill",
            message=f"unknown command skill: {skill}",
            details={
                "skill": skill,
                "allowed_skills": [
                    str(summary["name"]) for summary in skill_registry.list_skill_summaries()
                ],
            },
        )
    return None


def _validate_action_command_consistency(
    decision: PilotDecision,
) -> DecisionParseError | None:
    action = decision.action
    command = decision.command

    if action in (PilotDecisionAction.CONTINUE, PilotDecisionAction.RETRY):
        if command is None:
            return DecisionParseError(
                code="action_command_mismatch",
                message=f"{action.value} decisions require a validated command",
                details={"action": action.value, "required_command": True},
            )
        return None

    if action is PilotDecisionAction.REQUEST_HUMAN:
        if command is not None:
            return DecisionParseError(
                code="action_command_mismatch",
                message="request_human decisions must not include a command",
                details={"action": action.value, "allowed_command": None},
            )
        return None

    if action in (PilotDecisionAction.STOP_SUCCESS, PilotDecisionAction.STOP_FAILURE):
        if command is not None and command.skill != "stop":
            return DecisionParseError(
                code="action_command_mismatch",
                message=f"{action.value} decisions may only include a stop command",
                details={
                    "action": action.value,
                    "received_skill": str(command.skill),
                    "allowed_skill": "stop",
                },
            )
    return None


def _failure(
    code: DecisionParseErrorCode,
    message: str,
    details: Mapping[str, JsonValue] | None = None,
) -> DecisionParseResult:
    return DecisionParseResult(
        error=DecisionParseError(code=code, message=message, details=dict(details or {}))
    )


def _failure_from_error(error: DecisionParseError) -> DecisionParseResult:
    return DecisionParseResult(error=error)


def _json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int | float):
        return "number"
    return type(value).__name__


def _json_safe(value: object) -> JsonValue:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return str(value)


__all__ = [
    "DecisionAdapterError",
    "DecisionAdapterResult",
    "DecisionParseError",
    "DecisionParseErrorCode",
    "DecisionParseResult",
    "DecisionPromptClient",
    "PROMPT_SECTION_ORDER",
    "PromptPayload",
    "build_decision_prompt",
    "build_prompt_payload",
    "parse_decision_response",
    "render_prompt",
    "request_pilot_decision",
]
