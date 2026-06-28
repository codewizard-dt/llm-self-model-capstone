"""Online pilot loop scaffolding."""

from pathlib import Path
import sys


def _ensure_repo_contracts_importable() -> None:
    contracts_src = Path(__file__).resolve().parents[3] / "contracts" / "src"
    if not (contracts_src / "contracts").is_dir():
        return

    contracts_path = str(contracts_src)
    if contracts_path not in sys.path:
        sys.path.insert(0, contracts_path)


_ensure_repo_contracts_importable()

from pilot.assertions import (  # noqa: E402
    REQUIRED_ASSERTION_IDS,
    AssertionConfig,
    AssertionContext,
    AssertionDestination,
    AssertionId,
    AssertionTarget,
    build_assertion,
    build_unknown_assertion,
    evaluate_assertions,
)
from pilot.observation import (  # noqa: E402
    ObservationCache,
    assertion_sort_key,
    build_observation_snapshot,
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
from pilot.decision import (  # noqa: E402
    DecisionAdapterError,
    DecisionAdapterResult,
    DecisionPromptClient,
    PROMPT_SECTION_ORDER,
    build_decision_prompt,
    build_prompt_payload,
    render_prompt,
    request_pilot_decision,
)
from pilot.executor import (  # noqa: E402
    DEFAULT_EXECUTOR_POLICY,
    ExecutionResult,
    ExecutorDeadline,
    ExecutorPolicy,
    ExecutorReasonCode,
    ExecutorRoute,
    ExecutorTransport,
    SkillExecutor,
    TransportBoundary,
    TransportRequest,
    execute_validated_command,
)
from pilot.safety import (  # noqa: E402
    DEFAULT_SAFETY_POLICY,
    SafetyPolicy,
    ValidationMode,
    ValidationReason,
    ValidationReasonCode,
    ValidationResult,
    ValidationStatus,
    validate_skill_command,
)
from pilot.skills import (  # noqa: E402
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
    "REQUIRED_ASSERTION_IDS",
    "AssertionConfig",
    "AssertionContext",
    "AssertionDestination",
    "AssertionId",
    "AssertionTarget",
    "BoundReference",
    "DEFAULT_EXECUTOR_POLICY",
    "DEFAULT_SAFETY_POLICY",
    "DecisionAdapterError",
    "DecisionAdapterResult",
    "DecisionPromptClient",
    "ExecutionResult",
    "ExecutorDeadline",
    "ExecutorPolicy",
    "ExecutorReasonCode",
    "ExecutorRoute",
    "ExecutorTransport",
    "MovementEnvelope",
    "ObservationCache",
    "PROMPT_SECTION_ORDER",
    "SafetyPolicy",
    "SkillDefault",
    "SkillDefinition",
    "SkillExecutor",
    "SkillInput",
    "SkillSuccessAssertion",
    "TransportBoundary",
    "TransportRequest",
    "ValidationMode",
    "ValidationReason",
    "ValidationReasonCode",
    "ValidationResult",
    "ValidationStatus",
    "assertion_sort_key",
    "build_assertion",
    "build_observation_snapshot",
    "build_unknown_assertion",
    "execute_validated_command",
    "evaluate_assertions",
    "failure_sort_key",
    "get_skill_definition",
    "build_decision_prompt",
    "build_prompt_payload",
    "list_skill_definitions",
    "request_pilot_decision",
    "render_prompt",
    "sorted_assertions",
    "sorted_failures",
    "sorted_visible_objects",
    "sorted_visible_tags",
    "stale_bridge",
    "unknown_localization",
    "unknown_manipulator",
    "validate_skill_command",
    "visible_object_sort_key",
    "visible_tag_sort_key",
]
