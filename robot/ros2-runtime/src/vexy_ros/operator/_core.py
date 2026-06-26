from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Literal, Mapping, Protocol, TypeAlias

from ..bridge_protocol import (
    DEFAULT_GRAB_MS,
    DEFAULT_LIFT_MS,
    DEFAULT_RELEASE_MS,
    PROTOCOL_VERSION,
    clamp,
    now_ms,
    normalize_outbound,
)
from ..vision_map import Pose2D, TagAnchor, average_poses, normalize_angle

MIN_TAG_ID = 0
MAX_TAG_ID = 14
WHEEL_CIRCUMFERENCE_M = 0.319
TRACK_WIDTH_M = 0.28
OperatorMethodName: TypeAlias = Literal[
    "locate_nearest_apriltag",
    "orient_to_tag",
    "move_to_tag",
    "pickup_ball",
    "grab",
    "lift",
    "release",
]
OperatorMethodCall: TypeAlias = tuple[
    OperatorMethodName, tuple[Any, ...], Mapping[str, Any]
]
OPERATOR_METHOD_NAMES = {
    "locate_nearest_apriltag",
    "orient_to_tag",
    "move_to_tag",
    "pickup_ball",
    "grab",
    "lift",
    "release",
}
TIMED_PRIMITIVE_METHOD_NAMES = {"grab", "lift", "release"}
MOTOR_CONTRACT_FIELDS = (
    "position_deg",
    "velocity_rpm",
    "current_amp",
    "power_w",
    "torque_nm",
    "efficiency_pct",
    "temperature_c",
)


def timed_primitive_default_duration_ms(method_name: str) -> int:
    if method_name == "grab":
        return DEFAULT_GRAB_MS
    if method_name == "lift":
        return DEFAULT_LIFT_MS
    if method_name == "release":
        return DEFAULT_RELEASE_MS
    raise ValueError(f"unsupported timed primitive method: {method_name}")


MOTOR_CONTRACT_METHODS = {
    "position_deg": "position",
    "velocity_rpm": "velocity",
    "current_amp": "current",
    "power_w": "power",
    "torque_nm": "torque",
    "efficiency_pct": "efficiency",
    "temperature_c": "temperature",
}


@dataclass(frozen=True)
class PrimitiveCommand:
    cmd: Literal["stop", "drive", "turn", "grab", "lift", "release", "arm"]
    ttl_ms: int = 180
    vx: float = 0.0
    vy: float = 0.0
    omega: float = 0.0
    duration_ms: int | None = None
    target_deg: float | None = None
    reason: str | None = None


class CommandSink(Protocol):
    def send_command(self, command: PrimitiveCommand) -> int:
        """Send one primitive command to the V5 Brain and return its sequence id."""


@dataclass(frozen=True)
class TagObservation:
    tag_id: int
    stamp_s: float
    forward_m: float
    left_m: float
    distance_m: float | None = None
    yaw_rad: float | None = None
    confidence: float | None = None

    def normalized(self) -> TagObservation:
        distance_m = (
            math.hypot(self.forward_m, self.left_m)
            if self.distance_m is None
            else float(self.distance_m)
        )
        yaw_rad = (
            math.atan2(self.left_m, self.forward_m)
            if self.yaw_rad is None
            else float(self.yaw_rad)
        )
        return TagObservation(
            tag_id=self.tag_id,
            stamp_s=self.stamp_s,
            forward_m=self.forward_m,
            left_m=self.left_m,
            distance_m=distance_m,
            yaw_rad=yaw_rad,
            confidence=self.confidence,
        )


@dataclass(frozen=True)
class ObjectObservation:
    name: str
    category: str
    stamp_s: float
    forward_m: float | None = None
    left_m: float | None = None
    confidence: float | None = None
    source: str = "unknown"


@dataclass(frozen=True)
class VisionSnapshot:
    stamp_s: float
    tags: Mapping[int, TagObservation] = field(default_factory=dict)
    objects: tuple[ObjectObservation, ...] = ()
    raw_scene_map: Mapping[str, Any] | None = None

    def fresh_tags(self, *, now_s: float, max_age_s: float) -> list[TagObservation]:
        return [
            tag.normalized()
            for tag in self.tags.values()
            if now_s - tag.stamp_s <= max_age_s
        ]

    def fresh_tag(
        self, tag_id: int, *, now_s: float, max_age_s: float
    ) -> TagObservation | None:
        tag = self.tags.get(tag_id)
        if tag is None or now_s - tag.stamp_s > max_age_s:
            return None
        return tag.normalized()


@dataclass(frozen=True)
class MotorSample:
    device: str
    subsystem: str
    sample_ms: int | None
    position_deg: float | None = None
    velocity_rpm: float | None = None
    current_amp: float | None = None
    power_w: float | None = None
    torque_nm: float | None = None
    temperature_c: float | None = None


@dataclass(frozen=True)
class TelemetrySnapshot:
    stamp_s: float
    left_vel_rpm: float | None = None
    right_vel_rpm: float | None = None
    left_pos_deg: float | None = None
    right_pos_deg: float | None = None
    motion_enabled: bool = False
    estop: bool = False
    drive_ports_ok: bool = False
    motor_samples: tuple[MotorSample, ...] = ()
    raw: Mapping[str, Any] | None = None

    def sample_for(self, device: str) -> MotorSample | None:
        return next(
            (sample for sample in self.motor_samples if sample.device == device),
            None,
        )

    def contract_motor_samples(self) -> list[dict[str, Any]]:
        return [contract_motor_sample(sample) for sample in self.motor_samples]

    @property
    def raw_t_ms(self) -> int | None:
        if self.raw is None:
            return None
        value = self.raw.get("t_ms")
        return None if value is None else int(value)

    @property
    def manipulator_sample(self) -> MotorSample | None:
        return next(
            (
                sample
                for sample in self.motor_samples
                if sample.subsystem == "manipulator"
                or sample.device in {"claw", "release", "release_motor", "manipulator"}
            ),
            None,
        )


@dataclass(frozen=True)
class DriveHealth:
    state: Literal["ok", "disabled", "unknown"]
    reason: str
    wheel_velocity_rpm: float | None = None


@dataclass(frozen=True)
class OperatorResult:
    success: bool
    reason: str
    command: PrimitiveCommand | None = None
    tag: TagObservation | None = None
    target_distance_m: float | None = None
    target_pose: Pose2D | None = None
    map_pose: Pose2D | None = None
    localization_source: Literal["apriltag", "dead_reckoning", "unknown"] = "unknown"
    drive_health: DriveHealth | None = None
    has_object: bool | None = None


@dataclass(frozen=True)
class OperatorEvent:
    name: str
    stamp_s: float
    detail: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OperatorTaskContract:
    contract_line: Mapping[str, Any]
    method_plan: tuple[OperatorMethodCall, ...]

    @classmethod
    def from_inputs(
        cls,
        *,
        contract_line: Mapping[str, Any],
        task_outline: Any,
    ) -> OperatorTaskContract:
        validate_contract_line_shape(contract_line)
        method_plan = parse_operator_method_plan(task_outline)
        if not method_plan:
            raise ValueError("task outline requires at least one operator method")
        return cls(
            contract_line=MappingProxyType(dict(contract_line)),
            method_plan=method_plan,
        )


@dataclass(frozen=True)
class OperatorConfig:
    tag_stale_s: float = 0.5
    object_stale_s: float = 0.75
    yaw_tolerance_rad: float = 0.06
    lateral_tolerance_m: float = 0.04
    distance_tolerance_m: float = 0.05
    target_distance_m: float = 0.45
    bin_standoff_m: float = 0.2
    ball_staging_standoff_m: float = 0.05
    home_standoff_m: float = 0.45
    arm_raise_trigger_distance_m: float = 0.8128
    arm_raise_target_deg: float = 20.0
    max_vx: float = 0.14
    search_omega: float = 0.35
    max_omega: float = 0.45
    turn_kp: float = 0.9
    drive_ttl_ms: int = 180
    stop_ttl_ms: int = 200
    pickup_open_ms: int = 600
    pickup_open_settle_s: float = 0.2
    pickup_grab_settle_s: float = 0.35
    ball_capture_forward_m: float = 0.14
    ball_capture_lateral_m: float = 0.08
    ball_approach_target_forward_m: float = 0.07
    ball_approach_max_vx: float = 0.09
    ball_blind_approach_s: float = 1.35
    ball_blind_approach_vx: float = 0.07
    end_effector_current_object_amp: float = 0.25
    end_effector_low_velocity_rpm: float = 8.0
    end_effector_object_max_closed_deg: float = 430.0
    end_effector_open_max_deg: float = 80.0
    pickup_max_attempts: int = 2


class PacketCommandSink:
    """Small command sink useful for tests and non-ROS callers."""

    def __init__(self, *, seq_start: int = 30000) -> None:
        self.seq = seq_start
        self.packets: list[dict[str, Any]] = []

    def send_command(self, command: PrimitiveCommand) -> int:
        self.seq += 1
        packet = packet_from_primitive(command, seq=self.seq)
        self.packets.append(packet)
        return self.seq


class Operator:
    """One-level-above-primitive robot operator.

    Methods in this class combine the latest vision/telemetry snapshot with a
    single primitive command decision. Multi-step tasks should call these
    methods in sequence instead of adding more Brain programs.
    """

    def __init__(
        self,
        command_sink: CommandSink,
        *,
        april_tag_map: Mapping[int, TagAnchor],
        camera_in_robot: Pose2D,
        task_contract: OperatorTaskContract | Mapping[str, Any],
        task_outline: Any | None = None,
        config: OperatorConfig | None = None,
        clock: Any = time.monotonic,
        event_sink: Callable[[OperatorEvent], None] | None = None,
    ) -> None:
        self.april_tag_map = validate_april_tag_map(april_tag_map)
        self.camera_in_robot = camera_in_robot
        self.task_contract = (
            task_contract
            if isinstance(task_contract, OperatorTaskContract)
            else OperatorTaskContract.from_inputs(
                contract_line=task_contract,
                task_outline=task_outline,
            )
        )
        self.allowed_operator_methods = tuple(
            dict.fromkeys(call[0] for call in self.task_contract.method_plan)
        )
        self.command_sink = command_sink
        self.config = config or OperatorConfig()
        self.clock = clock
        self.event_sink = event_sink
        self.available_april_tag_ids = tuple(sorted(self.april_tag_map))
        self.vision = VisionSnapshot(stamp_s=0.0)
        self.telemetry: TelemetrySnapshot | None = None
        self.map_pose: Pose2D | None = None
        self.localization_source: Literal["apriltag", "dead_reckoning", "unknown"] = (
            "unknown"
        )
        self.last_pose_update_s: float | None = None
        self.last_command: PrimitiveCommand | None = None
        self.pickup_phase: Literal[
            "idle", "opening", "approaching", "closing", "done"
        ] = "idle"
        self.pickup_phase_start_s: float | None = None
        self.pickup_visual_capture_confirmed = False
        self.pickup_attempts = 0
        self.run_index = 0
        self.arm_raise_sent_for_tags: set[int] = set()
        self._emit(
            "apriltag_map_loaded",
            {
                "available_tag_ids": list(self.available_april_tag_ids),
                "tag_count": len(self.available_april_tag_ids),
                "camera_in_robot": self.camera_in_robot.to_json(),
            },
        )

    def set_task_contract(self, task_contract: OperatorTaskContract) -> None:
        self.task_contract = task_contract
        self.allowed_operator_methods = tuple(
            dict.fromkeys(call[0] for call in self.task_contract.method_plan)
        )
        self._emit(
            "task_contract_loaded",
            {
                "session_id": self.task_contract.contract_line.get("session_id"),
                "task": self.task_contract.contract_line.get("task"),
                "operator_methods": list(self.allowed_operator_methods),
            },
        )

    def update_vision(self, snapshot: VisionSnapshot) -> None:
        self.vision = snapshot
        self._update_pose_from_vision()

    def update_telemetry(self, snapshot: TelemetrySnapshot) -> None:
        self.telemetry = snapshot

    def current_pose(self) -> Pose2D | None:
        self._advance_dead_reckoning(self.clock())
        return self.map_pose

    def require_allowed_method(self, method_name: str) -> None:
        if method_name not in self.allowed_operator_methods:
            raise ValueError(
                f"operator method {method_name!r} is not in the task outline; "
                f"allowed methods: {list(self.allowed_operator_methods)}"
            )

    def contract_result(
        self,
        *,
        method_name: str,
        result: OperatorResult,
    ) -> dict[str, Any]:
        telemetry = self.telemetry
        motor_samples = [] if telemetry is None else telemetry.contract_motor_samples()
        if not motor_samples:
            motor_samples = [zero_motor_sample()]
        self.run_index += 1
        contract_line = dict(self.task_contract.contract_line)
        pose = result.map_pose or self.map_pose
        payload: dict[str, Any] = {
            "schema_version": "1.0",
            "session_id": contract_line["session_id"],
            "generation": int(contract_line["generation"]),
            "round": int(contract_line["round"]) + self.run_index,
            "task": str(contract_line["task"]),
            "motor_samples": motor_samples,
            "predicted": dict(contract_line["predicted"]),
            "gap": self._contract_gap(result),
            "outcome": self._contract_outcome(method_name, result),
            "vision": self._contract_vision(pose),
            "source": {
                "raw_session_path": None,
                "brain_start_ms": None,
                "brain_end_ms": None if telemetry is None else telemetry.raw_t_ms,
                "pi_received_ms": None if telemetry is None else telemetry.raw_t_ms,
                "telemetry_sample_count": 0 if telemetry is None else 1,
            },
        }
        return _strip_none(payload)

    def _contract_gap(self, result: OperatorResult) -> dict[str, float]:
        gap = dict(self.task_contract.contract_line.get("gap", {}))
        if result.tag is not None:
            gap["yaw_error_rad"] = float(result.tag.yaw_rad or 0.0)
            gap["lateral_error_m"] = float(result.tag.left_m)
            if result.command is not None and result.command.cmd == "drive":
                gap["distance_error_m"] = float(result.tag.distance_m or 0.0) - float(
                    result.target_distance_m or self.config.target_distance_m
                )
        return gap or {"result_error": 0.0}

    def _contract_outcome(
        self, method_name: str, result: OperatorResult
    ) -> dict[str, Any]:
        return _strip_none(
            {
                "method": method_name,
                "success": result.success,
                "reason": result.reason,
                "command": None if result.command is None else result.command.cmd,
                "tag_index": None if result.tag is None else result.tag.tag_id,
                "target_distance_m": result.target_distance_m,
                "target_pose": None
                if result.target_pose is None
                else result.target_pose.to_json(),
                "camera_in_robot": self.camera_in_robot.to_json(),
                "localization_source": result.localization_source,
                "has_object": result.has_object,
                "drive_health": None
                if result.drive_health is None
                else result.drive_health.state,
            }
        )

    def _contract_vision(self, pose: Pose2D | None) -> dict[str, Any]:
        return _strip_none(
            {
                "object_detected": bool(self.vision.tags or self.vision.objects),
                "apriltag_pose": None
                if pose is None
                else {
                    "x": float(pose.x_m),
                    "y": float(pose.y_m),
                    "heading": float(pose.yaw_rad),
                },
            }
        )

    def locate_nearest_apriltag(self) -> OperatorResult:
        now_s = self.clock()
        fresh = self.vision.fresh_tags(now_s=now_s, max_age_s=self.config.tag_stale_s)
        valid = [tag for tag in fresh if tag.tag_id in self.april_tag_map]
        if not valid:
            command = PrimitiveCommand(
                "turn",
                omega=self.config.search_omega,
                ttl_ms=self.config.drive_ttl_ms,
                reason="operator_locate_nearest_apriltag",
            )
            self._send(command)
            self._emit("apriltag_searching", {"reason": "no_fresh_apriltag"})
            return OperatorResult(False, "no_fresh_apriltag", command=command)
        tag = min(valid, key=lambda item: float(item.distance_m or 0.0))
        self._emit(
            "apriltag_located", {"tag_id": tag.tag_id, "distance_m": tag.distance_m}
        )
        return OperatorResult(
            True,
            "nearest_apriltag_located",
            tag=tag,
            map_pose=self.map_pose,
            localization_source=self.localization_source,
        )

    def orient_to_tag(self, tag_index: int) -> OperatorResult:
        self._validate_tag_index(tag_index)
        tag = self.vision.fresh_tag(
            tag_index, now_s=self.clock(), max_age_s=self.config.tag_stale_s
        )

        if tag is None:
            # Tag not directly visible — use map localization to turn toward its known position.
            # As the robot rotates, the tag will come into view and direct visual tracking takes over.
            if self.map_pose is not None:
                anchor = self.april_tag_map[tag_index]
                tag_map = anchor.map_from_tag
                dx = tag_map.x_m - self.map_pose.x_m
                dy = tag_map.y_m - self.map_pose.y_m
                bearing = math.atan2(dy, dx)
                yaw_error = normalize_angle(bearing - self.map_pose.yaw_rad)
                if abs(yaw_error) <= self.config.yaw_tolerance_rad:
                    command = PrimitiveCommand(
                        "stop",
                        ttl_ms=self.config.stop_ttl_ms,
                        reason=f"oriented_to_tag_{tag_index}_via_map",
                    )
                    self._send(command)
                    self._emit(
                        "oriented",
                        {"tag_index": tag_index, "yaw_rad": yaw_error, "source": "map"},
                    )
                    return OperatorResult(
                        True,
                        "oriented",
                        command=command,
                        map_pose=self.map_pose,
                        localization_source=self.localization_source,
                    )
                command = PrimitiveCommand(
                    "turn",
                    omega=clamp(
                        self.config.turn_kp * yaw_error,
                        -self.config.max_omega,
                        self.config.max_omega,
                    ),
                    ttl_ms=self.config.drive_ttl_ms,
                    reason=f"orient_to_tag_{tag_index}_via_map",
                )
                self._send(command)
                self._emit(
                    "apriltag_map_orient",
                    {"tag_index": tag_index, "yaw_error_rad": yaw_error},
                )
                return OperatorResult(
                    False,
                    "turning_to_map_tag",
                    command=command,
                    map_pose=self.map_pose,
                    localization_source=self.localization_source,
                )
            # No map pose — blind search spin
            command = PrimitiveCommand(
                "turn",
                omega=self.config.search_omega,
                ttl_ms=self.config.drive_ttl_ms,
                reason=f"search_for_tag_{tag_index}",
            )
            self._send(command)
            self._emit("apriltag_searching", {"tag_index": tag_index})
            return OperatorResult(
                False,
                "tag_not_visible",
                command=command,
                map_pose=self.map_pose,
                localization_source=self.localization_source,
            )

        yaw_rad = float(tag.yaw_rad or 0.0)
        if abs(yaw_rad) <= self.config.yaw_tolerance_rad:
            command = PrimitiveCommand(
                "stop",
                ttl_ms=self.config.stop_ttl_ms,
                reason=f"oriented_to_tag_{tag_index}",
            )
            self._send(command)
            self._emit("oriented", {"tag_index": tag_index, "yaw_rad": yaw_rad})
            return OperatorResult(
                True,
                "oriented",
                command=command,
                tag=tag,
                map_pose=self.map_pose,
                localization_source=self.localization_source,
            )

        command = PrimitiveCommand(
            "turn",
            omega=clamp(
                self.config.turn_kp * yaw_rad,
                -self.config.max_omega,
                self.config.max_omega,
            ),
            ttl_ms=self.config.drive_ttl_ms,
            reason=f"orient_to_tag_{tag_index}",
        )
        self._send(command)
        return OperatorResult(
            False,
            "turning_to_tag",
            command=command,
            tag=tag,
            map_pose=self.map_pose,
            localization_source=self.localization_source,
        )

    def move_to_tag(
        self, tag_index: int, *, target_distance_m: float | None = None
    ) -> OperatorResult:
        self._validate_tag_index(tag_index)
        target_distance_m = (
            target_distance_m
            if target_distance_m is not None
            else self.target_distance_for_tag(tag_index)
        )
        target_pose = self.target_pose_for_tag(tag_index, target_distance_m)
        tag = self._fresh_tag_or_search(tag_index)
        if isinstance(tag, OperatorResult):
            return tag

        previous_command_is_approach = (
            self.last_command is not None
            and self.last_command.reason == f"move_to_tag_{tag_index}"
        )
        drive_health = (
            self.detect_drive_health(tag_index=tag_index)
            if previous_command_is_approach
            else DriveHealth("ok", "approach_not_started")
        )
        if drive_health.state == "disabled":
            command = PrimitiveCommand(
                "stop",
                ttl_ms=self.config.stop_ttl_ms,
                reason=f"operator_{drive_health.state}",
            )
            self._send(command)
            self._emit(
                drive_health.state,
                {
                    "tag_index": tag_index,
                    "reason": drive_health.reason,
                    "wheel_velocity_rpm": drive_health.wheel_velocity_rpm,
                },
            )
            return OperatorResult(
                False,
                drive_health.state,
                command=command,
                tag=tag,
                target_distance_m=target_distance_m,
                target_pose=target_pose,
                map_pose=self.map_pose,
                localization_source=self.localization_source,
                drive_health=drive_health,
            )

        distance_m = float(tag.distance_m or 0.0)
        yaw_rad = float(tag.yaw_rad or 0.0)
        lateral_m = float(tag.left_m)
        distance_error_m = distance_m - target_distance_m
        if (
            abs(distance_error_m) <= self.config.distance_tolerance_m
            and abs(yaw_rad) <= self.config.yaw_tolerance_rad
            and abs(lateral_m) <= self.config.lateral_tolerance_m
        ):
            command = PrimitiveCommand(
                "stop",
                ttl_ms=self.config.stop_ttl_ms,
                reason=f"arrived_at_tag_{tag_index}",
            )
            self._send(command)
            self._emit("arrived", {"tag_index": tag_index, "distance_m": distance_m})
            return OperatorResult(
                True,
                "arrived",
                command=command,
                tag=tag,
                target_distance_m=target_distance_m,
                target_pose=target_pose,
                map_pose=self.map_pose,
                localization_source=self.localization_source,
            )

        if (
            distance_m <= self.config.arm_raise_trigger_distance_m
            and tag_index not in self.arm_raise_sent_for_tags
        ):
            self.arm_raise_sent_for_tags.add(tag_index)
            command = PrimitiveCommand(
                "arm",
                ttl_ms=self.config.stop_ttl_ms,
                target_deg=self.config.arm_raise_target_deg,
                reason=f"raise_arm_for_tag_{tag_index}",
            )
            self._send(command)
            self._emit(
                "arm_raise_requested",
                {
                    "tag_index": tag_index,
                    "distance_m": distance_m,
                    "target_deg": self.config.arm_raise_target_deg,
                },
            )
            return OperatorResult(
                False,
                "raising_arm_for_tag",
                command=command,
                tag=tag,
                target_distance_m=target_distance_m,
                target_pose=target_pose,
                map_pose=self.map_pose,
                localization_source=self.localization_source,
                drive_health=drive_health,
            )

        vx = clamp(0.45 * distance_error_m, -self.config.max_vx, self.config.max_vx)
        if abs(yaw_rad) > 0.45:
            vx = clamp(vx, -0.04, 0.04)
        if abs(yaw_rad) > 0.9:
            vx = 0.0
        command = PrimitiveCommand(
            "drive",
            vx=vx,
            vy=0.0,
            omega=clamp(
                self.config.turn_kp * yaw_rad,
                -self.config.max_omega,
                self.config.max_omega,
            ),
            ttl_ms=self.config.drive_ttl_ms,
            reason=f"move_to_tag_{tag_index}",
        )
        self._send(command)
        return OperatorResult(
            False,
            "moving_to_tag",
            command=command,
            tag=tag,
            target_distance_m=target_distance_m,
            target_pose=target_pose,
            map_pose=self.map_pose,
            localization_source=self.localization_source,
            drive_health=drive_health,
        )

    def grab(self, *, duration_ms: int = DEFAULT_GRAB_MS) -> OperatorResult:
        return self._timed_claw("grab", duration_ms, reason="operator_grab")

    def pickup_ball(self, *, duration_ms: int = DEFAULT_GRAB_MS) -> OperatorResult:
        now_s = self.clock()
        if self.pickup_phase == "idle":
            if self.pickup_attempts >= self.config.pickup_max_attempts:
                return OperatorResult(
                    False,
                    "grab_failed",
                    map_pose=self.map_pose,
                    localization_source=self.localization_source,
                    has_object=self.has_object(),
                )
            self.pickup_attempts += 1
            command = PrimitiveCommand(
                "release",
                ttl_ms=max(self.config.stop_ttl_ms, self.config.pickup_open_ms),
                duration_ms=self.config.pickup_open_ms,
                reason="open_claw_for_ball_pickup",
            )
            self._send(command)
            self.pickup_phase = "opening"
            self.pickup_phase_start_s = now_s
            self.pickup_visual_capture_confirmed = False
            self._emit(
                "claw_opening_for_pickup", {"duration_ms": self.config.pickup_open_ms}
            )
            return OperatorResult(
                False,
                "opening_claw",
                command=command,
                map_pose=self.map_pose,
                localization_source=self.localization_source,
            )

        if self.pickup_phase == "opening":
            opened_for_s = now_s - float(self.pickup_phase_start_s or now_s)
            required_s = (
                self.config.pickup_open_ms / 1000.0 + self.config.pickup_open_settle_s
            )
            if opened_for_s < required_s:
                return OperatorResult(
                    False,
                    "opening_claw",
                    map_pose=self.map_pose,
                    localization_source=self.localization_source,
                )
            self.pickup_phase = "approaching"
            self.pickup_phase_start_s = now_s

        if self.pickup_phase == "approaching":
            ball = self.fresh_ball()
            if ball is None or ball.forward_m is None or ball.left_m is None:
                approach_elapsed_s = now_s - float(self.pickup_phase_start_s or now_s)
                if approach_elapsed_s >= self.config.ball_blind_approach_s:
                    command = PrimitiveCommand(
                        "grab",
                        ttl_ms=max(self.config.stop_ttl_ms, duration_ms),
                        duration_ms=duration_ms,
                        reason="close_claw_after_ball_intake",
                    )
                    self._send(command)
                    self.pickup_phase = "closing"
                    self.pickup_phase_start_s = now_s
                    self._emit(
                        "ball_intake_elapsed",
                        {
                            "approach_elapsed_s": approach_elapsed_s,
                            "duration_ms": duration_ms,
                        },
                    )
                    return OperatorResult(
                        False,
                        "closing_claw",
                        command=command,
                        map_pose=self.map_pose,
                        localization_source=self.localization_source,
                    )
                command = PrimitiveCommand(
                    "drive",
                    vx=self.config.ball_blind_approach_vx,
                    vy=0.0,
                    omega=0.0,
                    ttl_ms=self.config.drive_ttl_ms,
                    reason="intake_ball_without_visual_lock",
                )
                self._send(command)
                self._emit(
                    "ball_blind_approach",
                    {
                        "reason": "no_fresh_ball",
                        "approach_elapsed_s": approach_elapsed_s,
                    },
                )
                return OperatorResult(
                    False,
                    "moving_to_ball",
                    command=command,
                    map_pose=self.map_pose,
                    localization_source=self.localization_source,
                )

            forward_m = float(ball.forward_m)
            left_m = float(ball.left_m)
            if (
                forward_m <= self.config.ball_capture_forward_m
                and abs(left_m) <= self.config.ball_capture_lateral_m
            ):
                command = PrimitiveCommand(
                    "grab",
                    ttl_ms=max(self.config.stop_ttl_ms, duration_ms),
                    duration_ms=duration_ms,
                    reason="close_claw_on_visual_ball",
                )
                self._send(command)
                self.pickup_phase = "closing"
                self.pickup_phase_start_s = now_s
                self.pickup_visual_capture_confirmed = True
                self._emit(
                    "ball_in_claw_zone",
                    {
                        "forward_m": forward_m,
                        "left_m": left_m,
                        "duration_ms": duration_ms,
                    },
                )
                return OperatorResult(
                    False,
                    "closing_claw",
                    command=command,
                    map_pose=self.map_pose,
                    localization_source=self.localization_source,
                )

            yaw_rad = math.atan2(left_m, max(forward_m, 0.05))
            distance_error_m = forward_m - self.config.ball_approach_target_forward_m
            vx = clamp(
                0.45 * distance_error_m,
                0.0,
                self.config.ball_approach_max_vx,
            )
            if abs(yaw_rad) > 0.45:
                vx = min(vx, 0.04)
            if abs(yaw_rad) > 0.9:
                vx = 0.0
            command = PrimitiveCommand(
                "drive",
                vx=vx,
                vy=0.0,
                omega=clamp(
                    self.config.turn_kp * yaw_rad,
                    -self.config.max_omega,
                    self.config.max_omega,
                ),
                ttl_ms=self.config.drive_ttl_ms,
                reason="move_ball_into_claw",
            )
            self._send(command)
            self._emit(
                "ball_approach",
                {"forward_m": forward_m, "left_m": left_m, "yaw_rad": yaw_rad},
            )
            return OperatorResult(
                False,
                "moving_to_ball",
                command=command,
                map_pose=self.map_pose,
                localization_source=self.localization_source,
            )

        if self.pickup_phase == "closing":
            closed_for_s = now_s - float(self.pickup_phase_start_s or now_s)
            required_s = duration_ms / 1000.0 + self.config.pickup_grab_settle_s
            if closed_for_s < required_s:
                return OperatorResult(
                    False,
                    "closing_claw",
                    map_pose=self.map_pose,
                    localization_source=self.localization_source,
                )
            has_object = self.has_object()
            ball_after_close = self.fresh_ball()
            ball_still_outside_claw = (
                ball_after_close is not None
                and ball_after_close.forward_m is not None
                and float(ball_after_close.forward_m)
                > self.config.ball_capture_forward_m
            )
            if has_object is not True or ball_still_outside_claw:
                self.pickup_phase = "idle"
                self.pickup_phase_start_s = now_s
                self.pickup_visual_capture_confirmed = False
                self._emit(
                    "grab_retry",
                    {
                        "has_object": has_object,
                        "attempts": self.pickup_attempts,
                        "ball_still_outside_claw": ball_still_outside_claw,
                    },
                )
                return OperatorResult(
                    False,
                    "grab_not_confirmed",
                    map_pose=self.map_pose,
                    localization_source=self.localization_source,
                    has_object=has_object,
                )
            self.pickup_phase = "done"
            self.pickup_attempts = 0
            self._emit(
                "grabbed",
                {
                    "duration_ms": duration_ms,
                    "has_object": has_object,
                    "visual_capture_confirmed": self.pickup_visual_capture_confirmed,
                },
            )
            return OperatorResult(
                True,
                "ball_grabbed",
                map_pose=self.map_pose,
                localization_source=self.localization_source,
                has_object=has_object,
            )

        return OperatorResult(
            True,
            "ball_grabbed",
            map_pose=self.map_pose,
            localization_source=self.localization_source,
            has_object=self.has_object(),
        )

    def lift(self, *, duration_ms: int = DEFAULT_LIFT_MS) -> OperatorResult:
        return self._timed_claw("lift", duration_ms, reason="operator_lift")

    def release(self, *, duration_ms: int = DEFAULT_RELEASE_MS) -> OperatorResult:
        return self._timed_claw("release", duration_ms, reason="operator_release")

    def target_distance_for_tag(self, tag_index: int) -> float:
        anchor = self.april_tag_map[tag_index]
        label = (anchor.label or "").strip().lower()
        if label == "bin":
            return self.config.bin_standoff_m
        if label in {"ball_staging", "ball_loading", "ball"}:
            return self.config.ball_staging_standoff_m
        if label == "home":
            return self.config.home_standoff_m
        return self.config.target_distance_m

    def target_pose_for_tag(
        self, tag_index: int, target_distance_m: float | None = None
    ) -> Pose2D:
        anchor = self.april_tag_map[tag_index]
        standoff_m = (
            target_distance_m
            if target_distance_m is not None
            else self.target_distance_for_tag(tag_index)
        )
        return anchor.map_from_tag.compose(Pose2D(standoff_m, 0.0, 0.0))

    def detect_drive_health(self, *, tag_index: int | None = None) -> DriveHealth:
        telemetry = self.telemetry
        if telemetry is None:
            return DriveHealth("unknown", "no_telemetry")
        if (
            telemetry.estop
            or not telemetry.motion_enabled
            or not telemetry.drive_ports_ok
        ):
            return DriveHealth("disabled", "motion_disabled")
        if self.last_command is None or self.last_command.cmd not in {"drive", "turn"}:
            return DriveHealth("ok", "no_active_drive_command")

        left = abs(float(telemetry.left_vel_rpm or 0.0))
        right = abs(float(telemetry.right_vel_rpm or 0.0))
        mean_rpm = (left + right) / 2.0
        return DriveHealth("ok", "drive_telemetry_nominal", mean_rpm)

    def fresh_ball(self) -> ObjectObservation | None:
        now_s = self.clock()
        candidates = [
            obj
            for obj in self.vision.objects
            if now_s - obj.stamp_s <= self.config.object_stale_s
            and obj.forward_m is not None
            and obj.left_m is not None
            and obj.category.strip().lower().replace(" ", "_")
            in {"yellow_ball", "ball", "sports_ball"}
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda obj: math.hypot(
                float(obj.forward_m or 0.0), float(obj.left_m or 0.0)
            ),
        )

    def has_object(self) -> bool | None:
        telemetry = self.telemetry
        if telemetry is None:
            return None
        sample = telemetry.manipulator_sample
        if sample is None:
            return None
        current_amp = abs(float(sample.current_amp or 0.0))
        velocity_rpm = abs(float(sample.velocity_rpm or 0.0))
        if sample.position_deg is not None:
            position_deg = abs(float(sample.position_deg))
            if position_deg <= self.config.end_effector_open_max_deg:
                return False
            if (
                position_deg <= self.config.end_effector_object_max_closed_deg
                and velocity_rpm <= self.config.end_effector_low_velocity_rpm
            ):
                return True
            return False
        return (
            current_amp >= self.config.end_effector_current_object_amp
            and velocity_rpm <= self.config.end_effector_low_velocity_rpm
        )

    def _timed_claw(
        self,
        cmd: Literal["grab", "lift", "release"],
        duration_ms: int,
        *,
        reason: str,
    ) -> OperatorResult:
        command = PrimitiveCommand(
            cmd,
            ttl_ms=max(self.config.stop_ttl_ms, duration_ms),
            duration_ms=duration_ms,
            reason=reason,
        )
        self._send(command)
        has_object = self.has_object()
        if cmd == "grab" and has_object:
            self._emit("grabbed", {"duration_ms": duration_ms})
        return OperatorResult(
            True,
            f"{cmd}_sent",
            command=command,
            map_pose=self.map_pose,
            localization_source=self.localization_source,
            has_object=has_object,
        )

    def _fresh_tag_or_search(self, tag_index: int) -> TagObservation | OperatorResult:
        tag = self.vision.fresh_tag(
            tag_index, now_s=self.clock(), max_age_s=self.config.tag_stale_s
        )
        if tag is not None:
            return tag
        command = PrimitiveCommand(
            "turn",
            omega=self.config.search_omega,
            ttl_ms=self.config.drive_ttl_ms,
            reason=f"search_for_tag_{tag_index}",
        )
        self._send(command)
        self._emit("apriltag_searching", {"tag_index": tag_index})
        return OperatorResult(
            False,
            "tag_not_visible",
            command=command,
            map_pose=self.map_pose,
            localization_source=self.localization_source,
        )

    def _send(self, command: PrimitiveCommand) -> int:
        self._advance_dead_reckoning(self.clock())
        self.last_command = command
        return self.command_sink.send_command(command)

    def _update_pose_from_vision(self) -> None:
        now_s = self.clock()
        fresh_tags = self.vision.fresh_tags(
            now_s=now_s, max_age_s=self.config.tag_stale_s
        )
        estimates: list[Pose2D] = []
        for tag in fresh_tags:
            anchor = self.april_tag_map.get(tag.tag_id)
            if anchor is None:
                continue
            robot_from_tag = Pose2D(
                x_m=tag.forward_m,
                y_m=tag.left_m,
                yaw_rad=float(tag.yaw_rad or 0.0),
            )
            estimates.append(anchor.map_from_tag.compose(robot_from_tag.inverse()))
        if estimates:
            self.map_pose = average_poses(estimates)
            self.localization_source = "apriltag"
            self.last_pose_update_s = now_s
            self._emit(
                "pose_estimated",
                {"source": "apriltag", "pose": self.map_pose.to_json()},
            )
            return
        self._advance_dead_reckoning(now_s)

    def _advance_dead_reckoning(self, now_s: float) -> None:
        if self.map_pose is None:
            return
        if self.last_pose_update_s is None:
            self.last_pose_update_s = now_s
            return
        command = self.last_command
        if command is None or command.cmd not in {"drive", "turn"}:
            self.last_pose_update_s = now_s
            return
        dt_s = max(0.0, now_s - self.last_pose_update_s)
        if dt_s <= 0.0:
            return
        dt_s = min(dt_s, command.ttl_ms / 1000.0)
        if dt_s <= 0.0:
            return
        yaw = self.map_pose.yaw_rad
        dx = math.cos(yaw) * command.vx * dt_s
        dy = math.sin(yaw) * command.vx * dt_s
        self.map_pose = Pose2D(
            x_m=self.map_pose.x_m + dx,
            y_m=self.map_pose.y_m + dy,
            yaw_rad=normalize_angle(self.map_pose.yaw_rad + command.omega * dt_s),
        )
        self.localization_source = "dead_reckoning"
        self.last_pose_update_s = now_s

    def _emit(self, name: str, detail: Mapping[str, Any]) -> None:
        if self.event_sink is None:
            return
        self.event_sink(OperatorEvent(name=name, stamp_s=self.clock(), detail=detail))

    def _validate_tag_index(self, tag_index: int) -> None:
        if not MIN_TAG_ID <= int(tag_index) <= MAX_TAG_ID:
            raise ValueError(
                f"AprilTag index must be in {MIN_TAG_ID}..{MAX_TAG_ID}: {tag_index}"
            )
        if int(tag_index) not in self.april_tag_map:
            raise ValueError(
                f"AprilTag index {tag_index} is not available in loaded map; "
                f"available ids: {list(self.available_april_tag_ids)}"
            )


def expected_wheel_rpm(*, vx_mps: float, omega_rad_s: float) -> float:
    rpm_per_mps = 60.0 / WHEEL_CIRCUMFERENCE_M
    turn_mps = abs(omega_rad_s) * (TRACK_WIDTH_M / 2.0)
    return max(abs(vx_mps) * rpm_per_mps, turn_mps * rpm_per_mps)


def validate_contract_line_shape(raw: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "session_id",
        "generation",
        "round",
        "task",
        "motor_samples",
        "predicted",
        "gap",
    }
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(f"contract line missing required fields: {missing}")
    if raw["schema_version"] != "1.0":
        raise ValueError("contract line schema_version must be '1.0'")
    if not isinstance(raw["session_id"], str) or not raw["session_id"].strip():
        raise ValueError("contract line session_id must be a non-empty string")
    if not isinstance(raw["generation"], int):
        raise ValueError("contract line generation must be an integer")
    if not isinstance(raw["round"], int):
        raise ValueError("contract line round must be an integer")
    if not isinstance(raw["task"], str) or not raw["task"].strip():
        raise ValueError("contract line task must be a non-empty string")
    if not isinstance(raw["motor_samples"], list) or not raw["motor_samples"]:
        raise ValueError("contract line motor_samples must be a non-empty list")
    if not isinstance(raw["predicted"], Mapping):
        raise ValueError("contract line predicted must be an object")
    if not isinstance(raw["gap"], Mapping):
        raise ValueError("contract line gap must be an object")
    if (
        "outcome" in raw
        and raw["outcome"] is not None
        and not isinstance(raw["outcome"], Mapping)
    ):
        raise ValueError("contract line outcome must be an object or null")


def contract_motor_sample(sample: MotorSample) -> dict[str, Any]:
    device = sample.device
    subsystem = contract_subsystem(sample)
    values = {
        "position_deg": float(sample.position_deg or 0.0),
        "velocity_rpm": float(sample.velocity_rpm or 0.0),
        "current_amp": float(sample.current_amp or 0.0),
        "power_w": float(sample.power_w or 0.0),
        "torque_nm": float(sample.torque_nm or 0.0),
        "efficiency_pct": 0.0,
        "temperature_c": float(sample.temperature_c or 0.0),
    }
    return {
        "device": device,
        "subsystem": subsystem,
        "api_binding": "vexcode_python",
        "sample_ms": int(sample.sample_ms or 0),
        "values": values,
        "source_api": motor_source_api(device),
    }


def contract_subsystem(sample: MotorSample) -> Literal["claw", "arm", "drivetrain"]:
    if sample.subsystem in {"drivetrain", "arm", "claw"}:
        return sample.subsystem  # type: ignore[return-value]
    if sample.subsystem == "manipulator" or sample.device in {
        "release_motor",
        "claw",
        "claw_motor",
        "manipulator",
    }:
        return "claw"
    return "drivetrain"


def zero_motor_sample() -> dict[str, Any]:
    return contract_motor_sample(
        MotorSample(
            device="operator_unknown_motor",
            subsystem="drivetrain",
            sample_ms=0,
            position_deg=0.0,
            velocity_rpm=0.0,
            current_amp=0.0,
            power_w=0.0,
            torque_nm=0.0,
            temperature_c=0.0,
        )
    )


def motor_source_api(device: str) -> dict[str, str]:
    return {
        field: f"{device}.{method}(DEGREES)"
        if field == "position_deg"
        else f"{device}.{method}(RPM)"
        if field == "velocity_rpm"
        else f"{device}.{method}(AMP)"
        if field == "current_amp"
        else f"{device}.{method}(WATT)"
        if field == "power_w"
        else f"{device}.{method}(NM)"
        if field == "torque_nm"
        else f"{device}.{method}(PERCENT)"
        if field == "efficiency_pct"
        else f"{device}.{method}(CELSIUS)"
        for field, method in MOTOR_CONTRACT_METHODS.items()
    }


def _strip_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_none(item) for key, item in value.items() if item is not None
        }
    if isinstance(value, list):
        return [_strip_none(item) for item in value]
    return value


def parse_operator_method_plan(raw: Any) -> tuple[OperatorMethodCall, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, (list, tuple)):
        raise ValueError("operator_methods must be a tuple/list of method-call tuples")
    return tuple(_parse_operator_method_call(item) for item in raw)


def _parse_operator_method_call(raw: Any) -> OperatorMethodCall:
    if not isinstance(raw, (list, tuple)):
        raise ValueError("operator method call must be a tuple/list")
    if len(raw) not in {2, 3}:
        raise ValueError(
            "operator method call must be (method_name, args) or "
            "(method_name, args, kwargs)"
        )
    method_name = str(raw[0])
    if method_name not in OPERATOR_METHOD_NAMES:
        raise ValueError(f"unsupported operator method: {method_name}")
    args = _args_tuple(raw[1])
    kwargs = _kwargs_mapping({} if len(raw) == 2 else raw[2])
    _validate_operator_method_call(method_name, args, kwargs)
    return method_name, args, MappingProxyType(dict(kwargs))  # type: ignore[return-value]


def _args_tuple(raw: Any) -> tuple[Any, ...]:
    if not isinstance(raw, (list, tuple)):
        raise ValueError("operator method args must be a tuple/list")
    return tuple(raw)


def _kwargs_mapping(raw: Any) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError("operator method kwargs must be a JSON object/mapping")
    return {str(key): value for key, value in raw.items()}


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
    if method_name == "pickup_ball":
        _require_arg_count(method_name, args, 0)
        _require_kwargs(method_name, kwargs, {"duration_ms"})
        if "duration_ms" in kwargs:
            duration_ms = kwargs["duration_ms"]
            if not isinstance(duration_ms, int) or duration_ms <= 0:
                raise ValueError(
                    f"{method_name}.duration_ms must be a positive integer"
                )
        return
    if method_name in {"grab", "lift", "release"}:
        _require_arg_count(method_name, args, 0)
        _require_kwargs(method_name, kwargs, {"duration_ms"})
        if "duration_ms" in kwargs:
            duration_ms = kwargs["duration_ms"]
            if not isinstance(duration_ms, int) or duration_ms <= 0:
                raise ValueError(
                    f"{method_name}.duration_ms must be a positive integer"
                )
        return
    raise ValueError(f"unsupported operator method: {method_name}")


def _require_arg_count(method_name: str, args: tuple[Any, ...], expected: int) -> None:
    if len(args) != expected:
        raise ValueError(
            f"{method_name} requires {expected} positional args, got {len(args)}"
        )


def _require_kwargs(
    method_name: str, kwargs: Mapping[str, Any], allowed: set[str]
) -> None:
    extra = set(kwargs) - allowed
    if extra:
        raise ValueError(f"{method_name} does not allow kwargs: {sorted(extra)}")


def _require_tag_index(value: Any) -> None:
    if not isinstance(value, int):
        raise ValueError("tag_index must be an integer")
    if not MIN_TAG_ID <= value <= MAX_TAG_ID:
        raise ValueError(f"tag_index must be in {MIN_TAG_ID}..{MAX_TAG_ID}: {value}")


def _require_nonnegative_number(method_name: str, key: str, value: Any) -> None:
    if not isinstance(value, int | float) or value < 0:
        raise ValueError(f"{method_name}.{key} must be a non-negative number")


def validate_april_tag_map(
    april_tag_map: Mapping[int, TagAnchor],
) -> dict[int, TagAnchor]:
    if not april_tag_map:
        raise ValueError("operator requires a non-empty AprilTag map")
    validated: dict[int, TagAnchor] = {}
    for raw_tag_id, anchor in april_tag_map.items():
        tag_id = int(raw_tag_id)
        if not MIN_TAG_ID <= tag_id <= MAX_TAG_ID:
            raise ValueError(
                f"AprilTag id must be in {MIN_TAG_ID}..{MAX_TAG_ID}: {tag_id}"
            )
        if anchor.tag_id != tag_id:
            raise ValueError(
                f"AprilTag map key {tag_id} does not match anchor tag_id {anchor.tag_id}"
            )
        validated[tag_id] = anchor
    return validated


def packet_from_primitive(command: PrimitiveCommand, *, seq: int) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "v": PROTOCOL_VERSION,
        "seq": seq,
        "type": "cmd",
        "cmd": command.cmd,
        "sent_ms": now_ms(),
        "ttl_ms": command.ttl_ms,
    }
    if command.cmd == "drive":
        packet.update({"vx": command.vx, "vy": command.vy, "omega": command.omega})
    elif command.cmd == "turn":
        packet["omega"] = command.omega
    elif command.cmd == "arm" and command.target_deg is not None:
        packet["target_deg"] = command.target_deg
    elif command.cmd in {"grab", "lift", "release"} and command.duration_ms is not None:
        packet["duration_ms"] = command.duration_ms
    if command.reason:
        packet["reason"] = command.reason
    return normalize_outbound(packet)


def telemetry_snapshot_from_mapping(
    raw: Mapping[str, Any], *, stamp_s: float | None = None
) -> TelemetrySnapshot:
    return TelemetrySnapshot(
        stamp_s=time.monotonic() if stamp_s is None else stamp_s,
        left_vel_rpm=_optional_float(raw.get("left_vel_rpm")),
        right_vel_rpm=_optional_float(raw.get("right_vel_rpm")),
        left_pos_deg=_optional_float(raw.get("left_pos_deg")),
        right_pos_deg=_optional_float(raw.get("right_pos_deg")),
        motion_enabled=bool(raw.get("motion_enabled", False)),
        estop=bool(raw.get("estop", False)),
        drive_ports_ok=bool(raw.get("drive_ports_ok", False)),
        motor_samples=tuple(
            motor_sample_from_mapping(sample)
            for sample in raw.get("motor_samples", [])
            if isinstance(sample, Mapping)
        ),
        raw=raw,
    )


def motor_sample_from_mapping(raw: Mapping[str, Any]) -> MotorSample:
    values = raw.get("values", {})
    values = values if isinstance(values, Mapping) else {}
    return MotorSample(
        device=str(raw.get("device", "unknown")),
        subsystem=str(raw.get("subsystem", "unknown")),
        sample_ms=_optional_int(raw.get("sample_ms")),
        position_deg=_optional_float(values.get("position_deg")),
        velocity_rpm=_optional_float(values.get("velocity_rpm")),
        current_amp=_optional_float(values.get("current_amp")),
        power_w=_optional_float(values.get("power_w")),
        torque_nm=_optional_float(values.get("torque_nm")),
        temperature_c=_optional_float(values.get("temperature_c")),
    )


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)
