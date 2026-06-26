"""Task file envelope for offline self-model to operator handoff."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

from contracts.contract_line import ContractLine

MIN_TAG_ID = 0
MAX_TAG_ID = 14
OPERATOR_METHOD_NAMES = {
    "locate_nearest_apriltag",
    "orient_to_tag",
    "move_to_tag",
    "pickup_ball",
    "grab",
    "lift",
    "release",
}

OperatorMethodName = Literal[
    "locate_nearest_apriltag",
    "orient_to_tag",
    "move_to_tag",
    "pickup_ball",
    "grab",
    "lift",
    "release",
]
OperatorMethodCall = tuple[OperatorMethodName, tuple[Any, ...], Mapping[str, Any]]


class TaskOutline(RootModel[list[Any]]):
    """Operator method-call outline emitted by the offline loop."""

    model_config = ConfigDict(
        json_schema_extra={
            "minItems": 1,
            "items": {
                "oneOf": [
                    {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "prefixItems": [
                            {"const": "locate_nearest_apriltag"},
                            {"type": "array", "maxItems": 0},
                        ],
                    },
                    {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "prefixItems": [
                            {"const": "orient_to_tag"},
                            {
                                "type": "array",
                                "minItems": 1,
                                "maxItems": 1,
                                "items": {
                                    "type": "integer",
                                    "minimum": MIN_TAG_ID,
                                    "maximum": MAX_TAG_ID,
                                },
                            },
                        ],
                    },
                    {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 3,
                        "prefixItems": [
                            {"const": "move_to_tag"},
                            {
                                "type": "array",
                                "minItems": 1,
                                "maxItems": 1,
                                "items": {
                                    "type": "integer",
                                    "minimum": MIN_TAG_ID,
                                    "maximum": MAX_TAG_ID,
                                },
                            },
                            {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "target_distance_m": {
                                        "type": "number",
                                        "minimum": 0,
                                    }
                                },
                            },
                        ],
                    },
                    {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 3,
                        "prefixItems": [
                            {"enum": ["pickup_ball", "grab", "lift", "release"]},
                            {"type": "array", "maxItems": 0},
                            {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "duration_ms": {
                                        "type": "integer",
                                        "minimum": 1,
                                    }
                                },
                            },
                        ],
                    },
                ]
            },
        }
    )

    @model_validator(mode="after")
    def _validate_outline(self) -> TaskOutline:
        if not self.root:
            raise ValueError("task outline requires at least one operator method")
        for item in self.root:
            _parse_operator_method_call(item)
        return self

    def method_plan(self) -> tuple[OperatorMethodCall, ...]:
        return tuple(_parse_operator_method_call(item) for item in self.root)


class TaskEnvelope(BaseModel):
    """Task file dropped onto the Pi for the operator to consume."""

    model_config = ConfigDict(extra="forbid")

    contract: ContractLine
    outline: TaskOutline = Field(
        description="List of operator method-call tuples: [method, args, kwargs?]."
    )


def _parse_operator_method_call(raw: Any) -> OperatorMethodCall:
    if not isinstance(raw, (list, tuple)) or len(raw) not in {2, 3}:
        raise ValueError(
            "operator method calls must be [method_name, args] or [method_name, args, kwargs]"
        )
    method_name = str(raw[0])
    if method_name not in OPERATOR_METHOD_NAMES:
        raise ValueError(f"unsupported operator method: {method_name}")
    args = _args_tuple(raw[1])
    kwargs = _kwargs_mapping({} if len(raw) == 2 else raw[2])
    _validate_operator_method_call(method_name, args, kwargs)
    return method_name, args, kwargs  # type: ignore[return-value]


def _args_tuple(raw: Any) -> tuple[Any, ...]:
    if not isinstance(raw, (list, tuple)):
        raise ValueError("operator method args must be a list")
    return tuple(raw)


def _kwargs_mapping(raw: Any) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError("operator method kwargs must be an object")
    return dict(raw)


def _validate_operator_method_call(
    method_name: str, args: tuple[Any, ...], kwargs: Mapping[str, Any]
) -> None:
    if method_name == "locate_nearest_apriltag":
        _require_arg_count(method_name, args, 0)
        _require_kwargs(method_name, kwargs, set())
        return
    if method_name == "orient_to_tag":
        _require_arg_count(method_name, args, 1)
        _require_tag_index(args[0])
        _require_kwargs(method_name, kwargs, set())
        return
    if method_name == "move_to_tag":
        _require_arg_count(method_name, args, 1)
        _require_tag_index(args[0])
        _require_kwargs(method_name, kwargs, {"target_distance_m"})
        if "target_distance_m" in kwargs:
            _require_nonnegative_number(
                method_name, "target_distance_m", kwargs["target_distance_m"]
            )
        return
    if method_name in {"pickup_ball", "grab", "lift", "release"}:
        _require_arg_count(method_name, args, 0)
        _require_kwargs(method_name, kwargs, {"duration_ms"})
        if "duration_ms" in kwargs:
            duration_ms = kwargs["duration_ms"]
            if not isinstance(duration_ms, int) or duration_ms <= 0:
                raise ValueError(f"{method_name}.duration_ms must be a positive integer")
        return
    raise ValueError(f"unsupported operator method: {method_name}")


def _require_arg_count(method_name: str, args: tuple[Any, ...], count: int) -> None:
    if len(args) != count:
        raise ValueError(f"{method_name} requires {count} args")


def _require_kwargs(method_name: str, kwargs: Mapping[str, Any], allowed: set[str]) -> None:
    extra = sorted(set(kwargs) - allowed)
    if extra:
        raise ValueError(f"{method_name} got unsupported kwargs: {extra}")


def _require_tag_index(value: Any) -> None:
    if not isinstance(value, int):
        raise ValueError("tag_index must be an integer")
    if not MIN_TAG_ID <= value <= MAX_TAG_ID:
        raise ValueError(f"tag_index must be in {MIN_TAG_ID}..{MAX_TAG_ID}: {value}")


def _require_nonnegative_number(method_name: str, field_name: str, value: Any) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{method_name}.{field_name} must be a nonnegative number")
