"""Online pilot loop scaffolding."""

from pilot.observation import (
    ObservationCache,
    assertion_sort_key,
    failure_sort_key,
    sorted_assertions,
    sorted_failures,
    sorted_visible_objects,
    sorted_visible_tags,
    stale_bridge,
    unknown_localization,
    unknown_manipulator,
    visible_object_sort_key,
    visible_tag_sort_key,
)
from pilot.decision import (
    PROMPT_SECTION_ORDER,
    build_decision_prompt,
    build_prompt_payload,
    render_prompt,
)
from pilot.skills import (
    BoundReference,
    MovementEnvelope,
    SkillDefault,
    SkillDefinition,
    SkillInput,
    SkillSuccessAssertion,
    get_skill_definition,
    list_skill_definitions,
)

__all__ = [
    "BoundReference",
    "MovementEnvelope",
    "ObservationCache",
    "PROMPT_SECTION_ORDER",
    "SkillDefault",
    "SkillDefinition",
    "SkillInput",
    "SkillSuccessAssertion",
    "assertion_sort_key",
    "failure_sort_key",
    "get_skill_definition",
    "build_decision_prompt",
    "build_prompt_payload",
    "list_skill_definitions",
    "render_prompt",
    "sorted_assertions",
    "sorted_failures",
    "sorted_visible_objects",
    "sorted_visible_tags",
    "stale_bridge",
    "unknown_localization",
    "unknown_manipulator",
    "visible_object_sort_key",
    "visible_tag_sort_key",
]
