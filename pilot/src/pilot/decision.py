"""Deterministic prompt construction for pilot LLM decisions."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TypeAlias

from contracts import PilotDecisionAction, PilotObservation
import pilot.skills as skill_registry
from pilot.skills import JsonValue

PromptPayload: TypeAlias = dict[str, JsonValue]

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


def _render_section(section: str, value: JsonValue) -> str:
    label = _PROMPT_SECTION_LABELS.get(section, section.replace("_", " "))
    return f"## {label}\n{_canonical_json(value)}"


def _canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True)


def _json_clone(value: object) -> JsonValue:
    return json.loads(_canonical_json(value))


__all__ = [
    "PROMPT_SECTION_ORDER",
    "PromptPayload",
    "build_decision_prompt",
    "build_prompt_payload",
    "render_prompt",
]
