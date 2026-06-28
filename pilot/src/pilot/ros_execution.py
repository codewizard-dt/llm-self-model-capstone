"""Optional ROS transport for supervised PM4 pilot skill execution."""

from __future__ import annotations

import json
import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from contracts import CommandStatus, PilotObservation, PilotSkillName
from pilot.execution import TransportTerminalOutcome
from pilot.live_observation import build_live_observation

READ_ONLY_TOPIC_FIELDS: dict[str, str] = {
    "/vision/agent_scene": "agent_scene",
    "/vision/scene_map": "scene_map",
    "/vision/object_tracks": "object_tracks",
    "/vex/telemetry": "telemetry",
    "/vex/bridge_status": "bridge_status",
    "/task_plan/current": "task_plan",
    "/operator/status": "operator_status",
}
REQUIRED_OBSERVATION_TOPICS: tuple[str, ...] = (
    "/vision/agent_scene",
    "/vision/object_tracks",
    "/vex/telemetry",
    "/vex/bridge_status",
)

SURVEY_GOAL_TOPIC = "/survey/goal"
SURVEY_RESULT_TOPIC = "/survey/result"
SURVEY_CANCEL_TOPIC = "/survey/cancel"
OPERATOR_COMMAND_TOPIC = "/operator/command"
OPERATOR_RESULT_TOPIC = "/operator/results"

DEFAULT_SPIN_INTERVAL_S = 0.05
DEFAULT_CLAW_DURATION_MS = 450
_STALE_REASONS = {"stale", "stale_ack", "stale_telemetry", "timeout", "timed_out", "expired"}
_REJECTED_REASONS = {"bad_goal", "motion_disabled", "drive_fault", "not_ready", "unsupported"}
_CLAW_ACTION_BY_SKILL: dict[PilotSkillName, str] = {
    PilotSkillName.CLAW_OPEN: "release",
    PilotSkillName.CLAW_CLOSE: "grab",
}


@dataclass(frozen=True, slots=True)
class RosRuntime:
    """Runtime boundary for ROS packages, injectable in tests."""

    rclpy: Any
    string_msg_type: Any


class RosExecutionError(Exception):
    """Expected ROS transport failure with a concise CLI-facing message."""


class RosDependencyError(RosExecutionError):
    """ROS dependencies are missing from the current Python environment."""


class TopicJsonCache:
    """Latest JSON object payloads from read-only observation topics."""

    def __init__(self) -> None:
        self._payloads: dict[str, Mapping[str, Any]] = {}
        self._malformed_required: dict[str, str] = {}

    def update(self, topic: str, raw_data: str) -> None:
        try:
            decoded = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            self._record_malformed(topic, f"invalid JSON at byte {exc.pos}: {exc.msg}")
            return
        if not isinstance(decoded, Mapping):
            self._record_malformed(topic, "payload must be a JSON object")
            return
        self._payloads[READ_ONLY_TOPIC_FIELDS[topic]] = decoded

    @property
    def ready(self) -> bool:
        return not self._malformed_required and not self.missing_required_topics()

    @property
    def malformed_required(self) -> Mapping[str, str]:
        return self._malformed_required

    def missing_required_topics(self) -> list[str]:
        return [
            topic
            for topic in REQUIRED_OBSERVATION_TOPICS
            if READ_ONLY_TOPIC_FIELDS[topic] not in self._payloads
        ]

    def mapper_kwargs(self) -> dict[str, Mapping[str, Any] | None]:
        return {field: self._payloads.get(field) for field in READ_ONLY_TOPIC_FIELDS.values()}

    def _record_malformed(self, topic: str, reason: str) -> None:
        if topic in REQUIRED_OBSERVATION_TOPICS:
            self._malformed_required[topic] = reason


class PM4HardwareTransport:
    """ROS std_msgs/String transport for one approved supervised PM4 skill."""

    def __init__(
        self,
        runtime: RosRuntime,
        *,
        clock: Callable[[], float] = time.monotonic,
        operator_surface_available: bool = True,
    ) -> None:
        self._runtime = runtime
        self._clock = clock
        self._operator_surface_available = operator_surface_available
        self._cache = TopicJsonCache()
        self._terminal_payloads: dict[str, deque[Mapping[str, Any]]] = {
            SURVEY_RESULT_TOPIC: deque(),
            OPERATOR_RESULT_TOPIC: deque(),
        }
        self._observation: PilotObservation | None = None
        self._initialized = False
        self._closed = False

        self._runtime.rclpy.init(args=None)
        self._initialized = True
        self.node = self._runtime.rclpy.create_node("pilot_pm4_skill")
        self._survey_goal_pub = self.node.create_publisher(
            self._runtime.string_msg_type, SURVEY_GOAL_TOPIC, 10
        )
        self._survey_cancel_pub = self.node.create_publisher(
            self._runtime.string_msg_type, SURVEY_CANCEL_TOPIC, 10
        )
        self._operator_command_pub = self.node.create_publisher(
            self._runtime.string_msg_type, OPERATOR_COMMAND_TOPIC, 10
        )
        for topic in READ_ONLY_TOPIC_FIELDS:
            self.node.create_subscription(
                self._runtime.string_msg_type,
                topic,
                self._observation_callback(topic),
                10,
            )
        for topic in self._terminal_payloads:
            self.node.create_subscription(
                self._runtime.string_msg_type,
                topic,
                self._terminal_callback(topic),
                10,
            )

    def read_observation(
        self,
        *,
        objective: str,
        readiness_timeout_s: float,
    ) -> PilotObservation:
        """Spin read-only topics until a contract-valid live observation is available."""

        if readiness_timeout_s <= 0:
            raise ValueError("readiness_timeout_s must be positive")
        deadline_s = self._clock() + readiness_timeout_s
        while self._clock() <= deadline_s:
            if self._cache.malformed_required:
                topic, reason = next(iter(self._cache.malformed_required.items()))
                raise RosExecutionError(f"required topic {topic} is malformed: {reason}")
            if self._cache.ready:
                observation = build_live_observation(
                    objective=objective,
                    observed_ms=_observed_ms(self._clock()),
                    **self._cache.mapper_kwargs(),
                )
                self._observation = observation
                return observation
            self._runtime.rclpy.spin_once(self.node, timeout_sec=DEFAULT_SPIN_INTERVAL_S)

        missing = ", ".join(self._cache.missing_required_topics())
        raise RosExecutionError(
            f"strict readiness not reached; missing required topic(s): {missing}"
        )

    def bind_observation(self, observation: PilotObservation) -> None:
        """Bind the validator-approved observation for read-only verification results."""

        self._observation = PilotObservation.model_validate(observation)

    def preflight_terminal_outcome(
        self,
        command: object,
        observation: PilotObservation,
    ) -> TransportTerminalOutcome | None:
        """Reject unavailable live surfaces before publishing any motion-producing message."""

        skill = PilotSkillName(str(getattr(command, "skill")))
        self.bind_observation(observation)
        if skill in _CLAW_ACTION_BY_SKILL and not self._operator_surface_available:
            return TransportTerminalOutcome(
                status=CommandStatus.REJECTED,
                message=(
                    f"{skill.value} requires /operator/command and /operator/results; "
                    "operator claw surface is unavailable"
                ),
                fault="operator_surface_unavailable",
            )
        return None

    def dispatch(self, command: object) -> None:
        skill = PilotSkillName(str(getattr(command, "skill")))
        if skill is PilotSkillName.SURVEY_SCENE:
            self._publish(self._survey_goal_pub, _survey_goal_payload(command))
            return
        if skill in _CLAW_ACTION_BY_SKILL:
            if not self._operator_surface_available:
                raise RosExecutionError("operator claw surface is unavailable")
            self._publish(self._operator_command_pub, _operator_command_payload(command))
            return
        if skill in {PilotSkillName.VERIFY_GRASP, PilotSkillName.VERIFY_DROP}:
            return
        raise RosExecutionError(f"unsupported PM4 hardware skill: {skill.value}")

    def wait_for_terminal_result(
        self, command: object, *, timeout_ms: int
    ) -> TransportTerminalOutcome:
        skill = PilotSkillName(str(getattr(command, "skill")))
        if skill in {PilotSkillName.VERIFY_GRASP, PilotSkillName.VERIFY_DROP}:
            return TransportTerminalOutcome(
                status=CommandStatus.OK,
                message=f"{skill.value} verified from live observation evidence",
            )

        topic = (
            SURVEY_RESULT_TOPIC if skill is PilotSkillName.SURVEY_SCENE else OPERATOR_RESULT_TOPIC
        )
        deadline_s = self._clock() + timeout_ms / 1000
        while self._clock() <= deadline_s:
            terminal = self._pop_matching_terminal(topic, command)
            if terminal is not None:
                return terminal
            self._runtime.rclpy.spin_once(self.node, timeout_sec=DEFAULT_SPIN_INTERVAL_S)
        raise TimeoutError

    def cancel(self, command: object, *, reason: str) -> None:
        skill = PilotSkillName(str(getattr(command, "skill")))
        payload = {"command_id": getattr(command, "command_id"), "reason": reason}
        if skill is PilotSkillName.SURVEY_SCENE:
            self._publish(self._survey_cancel_pub, payload)
            return
        if skill in _CLAW_ACTION_BY_SKILL and self._operator_surface_available:
            self._publish(
                self._operator_command_pub,
                {
                    "action": "reset_operator",
                    "command_id": getattr(command, "command_id"),
                    "reason": reason,
                },
            )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        destroy_node = getattr(self.node, "destroy_node", None)
        if destroy_node is not None:
            destroy_node()
        if self._initialized:
            self._runtime.rclpy.shutdown()
            self._initialized = False

    def _observation_callback(self, topic: str) -> Callable[[Any], None]:
        def on_message(message: Any) -> None:
            self._cache.update(topic, str(getattr(message, "data", "")))

        return on_message

    def _terminal_callback(self, topic: str) -> Callable[[Any], None]:
        def on_message(message: Any) -> None:
            try:
                decoded = json.loads(str(getattr(message, "data", "")))
            except json.JSONDecodeError:
                return
            if isinstance(decoded, Mapping):
                self._terminal_payloads[topic].append(decoded)

        return on_message

    def _pop_matching_terminal(
        self,
        topic: str,
        command: object,
    ) -> TransportTerminalOutcome | None:
        retained: deque[Mapping[str, Any]] = deque()
        matched: TransportTerminalOutcome | None = None
        queue = self._terminal_payloads[topic]
        while queue:
            payload = queue.popleft()
            if matched is None and _payload_matches_command(payload, command):
                matched = _terminal_from_payload(payload, command)
            else:
                retained.append(payload)
        self._terminal_payloads[topic] = retained
        return matched

    def _publish(self, publisher: Any, payload: Mapping[str, Any]) -> None:
        publisher.publish(
            self._runtime.string_msg_type(
                data=json.dumps(payload, separators=(",", ":"), sort_keys=True)
            )
        )


def load_ros_runtime() -> RosRuntime:
    """Load ROS packages lazily so parser/core imports work without ROS installed."""

    try:
        import rclpy
        from std_msgs.msg import String
    except ImportError as exc:
        raise RosDependencyError(
            "ROS dependencies are required for pilot skill hardware transport; source a ROS 2 "
            "environment with rclpy and std_msgs available"
        ) from exc
    return RosRuntime(rclpy=rclpy, string_msg_type=String)


def _survey_goal_payload(command: object) -> dict[str, Any]:
    params = getattr(command, "params")
    timeout_ms = int(getattr(params, "timeout_ms", 5000))
    return {
        "command_id": getattr(command, "command_id"),
        "duration_s": timeout_ms / 1000,
        "yaw_span_deg": float(getattr(params, "yaw_span_deg", 180.0)),
        "ttl_ms": min(max(timeout_ms, 1), 250),
    }


def _operator_command_payload(command: object) -> dict[str, Any]:
    skill = PilotSkillName(str(getattr(command, "skill")))
    return {
        "action": _CLAW_ACTION_BY_SKILL[skill],
        "command_id": getattr(command, "command_id"),
        "duration_ms": DEFAULT_CLAW_DURATION_MS,
    }


def _payload_matches_command(payload: Mapping[str, Any], command: object) -> bool:
    command_id = getattr(command, "command_id")
    if payload.get("command_id") == command_id:
        return True
    skill = PilotSkillName(str(getattr(command, "skill")))
    if skill is PilotSkillName.SURVEY_SCENE:
        return _payload_action(payload) in {None, "survey_scene", "survey_scan"}
    return _payload_action(payload) == _CLAW_ACTION_BY_SKILL.get(skill)


def _payload_action(payload: Mapping[str, Any]) -> str | None:
    outcome = payload.get("outcome")
    if isinstance(outcome, Mapping):
        method = outcome.get("method")
        if method is not None:
            return str(method)
    action = payload.get("action")
    return None if action is None else str(action)


def _terminal_from_payload(payload: Mapping[str, Any], command: object) -> TransportTerminalOutcome:
    outcome = payload.get("outcome")
    details = outcome if isinstance(outcome, Mapping) else payload
    reason = _string(details.get("reason")) or _string(payload.get("reason"))
    fault = _string(details.get("fault")) or _string(payload.get("fault"))
    status = _status_from_payload(details, reason=reason)
    return TransportTerminalOutcome(
        status=status,
        command_id=_string(payload.get("command_id")),
        completed_ms=_completed_ms(payload, details),
        message=reason or f"{getattr(command, 'skill')} terminal result: {status.value}",
        fault=fault,
    )


def _status_from_payload(payload: Mapping[str, Any], *, reason: str | None) -> CommandStatus:
    raw_status = payload.get("status")
    if raw_status is not None:
        try:
            return CommandStatus(str(raw_status))
        except ValueError:
            lowered = str(raw_status).casefold()
            if lowered in {"success", "succeeded"}:
                return CommandStatus.OK
            if lowered in _STALE_REASONS:
                return CommandStatus.STALE
            if lowered in _REJECTED_REASONS:
                return CommandStatus.REJECTED
            return CommandStatus.FAILED

    if payload.get("success") is True:
        return CommandStatus.OK
    lowered_reason = "" if reason is None else reason.casefold()
    if lowered_reason in _STALE_REASONS:
        return CommandStatus.STALE
    if lowered_reason in _REJECTED_REASONS:
        return CommandStatus.REJECTED
    return CommandStatus.FAILED


def _completed_ms(*payloads: Mapping[str, Any]) -> int | None:
    for payload in payloads:
        for key in ("completed_ms", "end_ms", "brain_end_ms", "pi_received_ms"):
            value = payload.get(key)
            if isinstance(value, int) and value >= 0:
                return value
    return None


def _observed_ms(monotonic_s: float) -> int:
    return max(0, int(round(monotonic_s * 1000)))


def _string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "DEFAULT_CLAW_DURATION_MS",
    "OPERATOR_COMMAND_TOPIC",
    "OPERATOR_RESULT_TOPIC",
    "PM4HardwareTransport",
    "READ_ONLY_TOPIC_FIELDS",
    "REQUIRED_OBSERVATION_TOPICS",
    "RosDependencyError",
    "RosExecutionError",
    "RosRuntime",
    "SURVEY_CANCEL_TOPIC",
    "SURVEY_GOAL_TOPIC",
    "SURVEY_RESULT_TOPIC",
    "TopicJsonCache",
    "load_ros_runtime",
]
