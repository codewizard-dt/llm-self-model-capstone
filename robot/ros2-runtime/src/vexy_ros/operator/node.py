from __future__ import annotations

import json
import math
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from tf2_msgs.msg import TFMessage
from contracts.task_envelope import TaskEnvelope
from pydantic import ValidationError

from ..align_to_tag import (
    AlignToTagController,
    AlignToTagGoal,
    BridgeHealth,
    TagObservation as AlignTagObservation,
    VexCommand,
)
from ..bridge_protocol import PROTOCOL_VERSION, normalize_outbound, now_ms
from ..survey_scan import SurveyScanController, SurveyScanGoal, SurveyTelemetry
from ..vision_map import (
    DEFAULT_CAMERA_IN_ROBOT,
    Pose2D,
    camera_from_apriltag_translation,
    parse_tag_anchors,
    pose_from_mapping,
    robot_from_camera_pose,
    tag_id_from_frame_id,
)
from ._core import (
    MAX_TAG_ID,
    MIN_TAG_ID,
    TIMED_PRIMITIVE_METHOD_NAMES,
    CommandSink,
    ObjectObservation,
    Operator,
    OperatorEvent,
    OperatorResult,
    OperatorTaskContract,
    PrimitiveCommand,
    TagObservation,
    TelemetrySnapshot,
    VisionSnapshot,
    packet_from_primitive,
    telemetry_snapshot_from_mapping,
    timed_primitive_default_duration_ms,
)


IN_PROGRESS_REASONS = {
    "no_fresh_apriltag",
    "tag_not_visible",
    "turning_to_tag",
    "turning_to_map_tag",
    "moving_to_tag",
    "raising_arm_for_tag",
    "opening_claw",
    "moving_to_ball",
    "closing_claw",
    "grab_not_confirmed",
}


@dataclass
class TimedPrimitiveStep:
    method_name: str
    duration_ms: int
    started_s: float
    deadline_s: float
    seq: int | None
    result: OperatorResult
    ack_state: str | None = None


@dataclass
class TaskOutlineRun:
    source_name: str
    method_plan: tuple[Any, ...]
    step_index: int
    step_started_s: float
    pending_timed_primitive: TimedPrimitiveStep | None = None


class RosCommandSink(CommandSink):
    def __init__(self, node: Node) -> None:
        self.node = node
        self.pub = node.create_publisher(String, "/vex/cmd", 10)
        self.seq = 32000

    def send_command(self, command: PrimitiveCommand) -> int:
        self.seq += 1
        packet = packet_from_primitive(command, seq=self.seq)
        self.pub.publish(String(data=json.dumps(packet, separators=(",", ":"))))
        return self.seq

    def send_packet(self, packet: Mapping[str, Any]) -> int:
        self.seq += 1
        outbound = dict(packet)
        outbound["seq"] = self.seq
        outbound["sent_ms"] = now_ms()
        normalized = normalize_outbound(outbound)
        self.pub.publish(String(data=json.dumps(normalized, separators=(",", ":"))))
        return self.seq


class OperatorNode(Node):
    def __init__(self) -> None:
        super().__init__("vexy_operator")
        self.declare_parameter("camera_in_robot_json", DEFAULT_CAMERA_IN_ROBOT)
        self.declare_parameter("workspace_map_path", "")
        self.declare_parameter("tag_anchors_json", "")
        self.declare_parameter("task_contract_json", "")
        self.declare_parameter("task_outline_json", "")
        self.declare_parameter("task_inbox_dir", "/vexy/tasks/inbox")
        self.declare_parameter("task_archive_dir", "")
        self.declare_parameter("task_rejected_dir", "")
        self.declare_parameter("task_poll_period_s", 1.0)
        self.declare_parameter("task_step_timeout_s", 30.0)
        self.declare_parameter("task_timed_primitive_settle_s", 0.05)
        self.declare_parameter("command_topic", "/operator/command")
        self.declare_parameter("event_topic", "/operator/events")
        self.declare_parameter("result_topic", "/operator/results")
        self.declare_parameter("status_topic", "/operator/status")
        self.declare_parameter("run_start_topic", "/operator/run_start")
        self.declare_parameter("raw_session_path", "")

        camera_raw = (
            self.get_parameter("camera_in_robot_json")
            .get_parameter_value()
            .string_value
        )
        self.camera_in_robot = pose_from_mapping(json.loads(camera_raw))
        april_tag_map = self._load_april_tag_map()
        task_contract = self._load_task_contract()
        task_outline = self._load_task_outline()
        self._tags: dict[int, TagObservation] = {}
        self._latest_align_tag: AlignTagObservation | None = None
        self._objects: tuple[ObjectObservation, ...] = ()
        self._last_scene_map: Mapping[str, Any] | None = None
        self._last_telemetry: TelemetrySnapshot | None = None
        self._bridge = BridgeHealth(stamp_s=None)
        self._survey_telemetry = SurveyTelemetry(stamp_s=None)
        self._observed_tag_ids: list[int] = []
        self._align_controller = AlignToTagController()
        self._survey_controller = SurveyScanController()
        self._align_cancel_requested = False
        self._survey_cancel_requested = False
        self._run_id = datetime.now().strftime("run-%Y%m%d-%H%M%S")
        raw_session_path = (
            self.get_parameter("raw_session_path").get_parameter_value().string_value
        )
        self._task_inbox_dir = self._parameter_path("task_inbox_dir")
        archive_dir = self._parameter_path("task_archive_dir")
        rejected_dir = self._parameter_path("task_rejected_dir")
        self._task_archive_dir = archive_dir or self._task_inbox_dir.parent / "archive"
        self._task_rejected_dir = (
            rejected_dir or self._task_inbox_dir.parent / "rejected"
        )
        self._task_file_active = False
        self._task_outline_run: TaskOutlineRun | None = None
        self._task_step_timeout_s = max(
            0.1, self._parameter_float("task_step_timeout_s")
        )
        self._task_timed_primitive_settle_s = max(
            0.0, self._parameter_float("task_timed_primitive_settle_s")
        )
        self._ack_states: dict[int, str] = {}
        self._event_pub = self.create_publisher(
            String,
            self.get_parameter("event_topic").get_parameter_value().string_value,
            10,
        )
        self._status_pub = self.create_publisher(
            String,
            self.get_parameter("status_topic").get_parameter_value().string_value,
            10,
        )
        self._result_pub = self.create_publisher(
            String,
            self.get_parameter("result_topic").get_parameter_value().string_value,
            10,
        )
        self._align_feedback_pub = self.create_publisher(
            String, "/align_to_tag/feedback", 10
        )
        self._align_result_pub = self.create_publisher(
            String, "/align_to_tag/result", 10
        )
        self._survey_feedback_pub = self.create_publisher(
            String, "/survey/feedback", 10
        )
        self._survey_result_pub = self.create_publisher(String, "/survey/result", 10)
        self._run_start_pub = self.create_publisher(
            String,
            self.get_parameter("run_start_topic").get_parameter_value().string_value,
            10,
        )
        self._sink = RosCommandSink(self)
        self.operator = Operator(
            self._sink,
            april_tag_map=april_tag_map,
            camera_in_robot=self.camera_in_robot,
            task_contract=task_contract,
            task_outline=task_outline,
            event_sink=self._publish_event,
            raw_session_path=raw_session_path or f"/operator/results/{self._run_id}",
        )

        self.create_subscription(TFMessage, "/tf", self._on_tf, 10)
        self.create_subscription(String, "/vision/scene_map", self._on_scene_map, 10)
        self.create_subscription(
            String, "/vision/object_detections", self._on_object_detections, 10
        )
        self.create_subscription(
            String, "/vision/object_indications", self._on_object_indications, 10
        )
        self.create_subscription(String, "/vex/ack", self._on_ack, 10)
        self.create_subscription(String, "/vex/telemetry", self._on_telemetry, 10)
        self.create_subscription(
            String, "/vex/bridge_status", self._on_bridge_status, 10
        )
        self.create_subscription(
            String,
            self.get_parameter("command_topic").get_parameter_value().string_value,
            self._on_command,
            10,
        )
        self.create_timer(0.1, self._tick_controllers)
        self.create_timer(0.1, self._tick_task_outline)
        self.create_timer(0.25, self._publish_status)
        self.create_timer(
            max(0.1, self._parameter_float("task_poll_period_s")),
            self._poll_task_inbox,
        )

    def _load_april_tag_map(self) -> Mapping[int, Any]:
        workspace_map_path = (
            self.get_parameter("workspace_map_path").get_parameter_value().string_value
        )
        if workspace_map_path:
            return parse_tag_anchors(Path(workspace_map_path).read_text())

        tag_anchors_json = (
            self.get_parameter("tag_anchors_json").get_parameter_value().string_value
        )
        if tag_anchors_json:
            return parse_tag_anchors(tag_anchors_json)
        raise ValueError(
            "vexy_operator requires workspace_map_path or tag_anchors_json"
        )

    def _load_task_contract(self) -> Mapping[str, Any]:
        task_contract_json = (
            self.get_parameter("task_contract_json").get_parameter_value().string_value
        )
        if not task_contract_json:
            return _idle_task_contract()
        payload = json.loads(task_contract_json)
        if not isinstance(payload, Mapping):
            raise ValueError("task_contract_json must decode to a JSON object")
        return payload

    def _load_task_outline(self) -> Any:
        task_outline_json = (
            self.get_parameter("task_outline_json").get_parameter_value().string_value
        )
        if not task_outline_json:
            return _idle_task_outline()
        return json.loads(task_outline_json)

    def _parameter_path(self, name: str) -> Path | None:
        raw = self.get_parameter(name).get_parameter_value().string_value
        if not raw:
            return None
        return Path(raw).expanduser()

    def _parameter_float(self, name: str) -> float:
        value = self.get_parameter(name).get_parameter_value()
        if hasattr(value, "double_value"):
            return float(value.double_value)
        return float(value.string_value)

    def _poll_task_inbox(self) -> None:
        if self._task_file_active:
            return
        try:
            self._task_inbox_dir.mkdir(parents=True, exist_ok=True)
            self._task_archive_dir.mkdir(parents=True, exist_ok=True)
            self._task_rejected_dir.mkdir(parents=True, exist_ok=True)
            task_files = sorted(
                path for path in self._task_inbox_dir.glob("*.json") if path.is_file()
            )
        except OSError as exc:
            self._publish_event(
                OperatorEvent(
                    name="task_inbox_error",
                    stamp_s=time.monotonic(),
                    detail={"error": str(exc), "path": str(self._task_inbox_dir)},
                )
            )
            return
        if task_files:
            self._consume_task_file(task_files[0])

    def _consume_task_file(self, path: Path) -> None:
        self._task_file_active = True
        try:
            envelope = TaskEnvelope.model_validate(json.loads(path.read_text()))
            operator_task = OperatorTaskContract.from_inputs(
                contract_line=envelope.contract.model_dump(mode="json"),
                task_outline=envelope.outline.root,
            )
            archived_path = self._move_task_file(path, self._task_archive_dir)
        except (
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
            ValidationError,
        ) as exc:
            self._reject_task_file(path, exc)
            self._task_file_active = False
            return

        try:
            self.operator.set_task_contract(operator_task)
            self._publish_event(
                OperatorEvent(
                    name="task_file_accepted",
                    stamp_s=time.monotonic(),
                    detail={
                        "source": str(path),
                        "archive": str(archived_path),
                        "session_id": operator_task.contract_line.get("session_id"),
                        "task": operator_task.contract_line.get("task"),
                    },
                )
            )
            self._run_task_outline(path.name)
        except (TypeError, ValueError) as exc:
            self._publish_event(
                OperatorEvent(
                    name="task_file_execution_failed",
                    stamp_s=time.monotonic(),
                    detail={
                        "source": str(path),
                        "archive": str(archived_path),
                        "error": str(exc),
                    },
                )
            )
            self._task_file_active = False

    def _move_task_file(self, path: Path, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        target = target_dir / f"{path.stem}.{stamp}{path.suffix}"
        return Path(shutil.move(str(path), str(target)))

    def _reject_task_file(self, path: Path, exc: Exception) -> None:
        try:
            rejected_path = self._move_task_file(path, self._task_rejected_dir)
            error_path = rejected_path.with_suffix(rejected_path.suffix + ".error.json")
            error_path.write_text(
                json.dumps(
                    {
                        "source": str(path),
                        "rejected": str(rejected_path),
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            detail = {
                "source": str(path),
                "rejected": str(rejected_path),
                "error": str(exc),
            }
        except OSError as move_exc:
            detail = {
                "source": str(path),
                "error": str(exc),
                "move_error": str(move_exc),
            }
        self._publish_event(
            OperatorEvent(
                name="task_file_rejected",
                stamp_s=time.monotonic(),
                detail=detail,
            )
        )

    def _run_task_outline(self, source_name: str) -> None:
        if self._task_outline_run is not None:
            raise ValueError("task outline already running")
        self._run_start_pub.publish(
            String(
                data=json.dumps(
                    {
                        "type": "run_start",
                        "run_id": self._run_id,
                        "run_start_wall_s": time.time(),
                        "run_index": self.operator.run_index,
                        "action": "task_file",
                        "source": source_name,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
        )
        self._task_outline_run = TaskOutlineRun(
            source_name=source_name,
            method_plan=tuple(self.operator.task_contract.method_plan),
            step_index=0,
            step_started_s=time.monotonic(),
        )

    def _tick_task_outline(self) -> None:
        run = self._task_outline_run
        if run is None:
            return
        if run.step_index >= len(run.method_plan):
            self._finish_task_outline_run("task_file_completed", {})
            return

        method_name, args, kwargs = run.method_plan[run.step_index]
        elapsed_s = time.monotonic() - run.step_started_s
        if elapsed_s > self._task_step_timeout_s:
            self._finish_task_outline_run(
                "task_file_execution_failed",
                {
                    "source": run.source_name,
                    "method": method_name,
                    "step_index": run.step_index,
                    "reason": "step_timeout",
                    "timeout_s": self._task_step_timeout_s,
                },
            )
            return

        if method_name in TIMED_PRIMITIVE_METHOD_NAMES:
            self._tick_timed_primitive_step(run, method_name, args, kwargs)
            return

        try:
            self.operator.require_allowed_method(method_name)
            method = getattr(self.operator, method_name)
            result = method(*args, **dict(kwargs))
        except (TypeError, ValueError) as exc:
            self._finish_task_outline_run(
                "task_file_execution_failed",
                {
                    "source": run.source_name,
                    "method": method_name,
                    "step_index": run.step_index,
                    "error": str(exc),
                },
            )
            return

        if not isinstance(result, OperatorResult):
            self._advance_task_outline_step(run)
            return

        if result.success:
            self._publish_contract_result(method_name, result)
            self._advance_task_outline_step(run)
            return

        if result.reason in IN_PROGRESS_REASONS:
            return

        self._publish_contract_result(method_name, result)
        self._finish_task_outline_run(
            "task_file_execution_failed",
            {
                "source": run.source_name,
                "method": method_name,
                "step_index": run.step_index,
                "reason": result.reason,
            },
        )

    def _tick_timed_primitive_step(
        self,
        run: TaskOutlineRun,
        method_name: str,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> None:
        pending = run.pending_timed_primitive
        if pending is None:
            try:
                self.operator.require_allowed_method(method_name)
                method = getattr(self.operator, method_name)
                result = method(*args, **dict(kwargs))
            except (TypeError, ValueError) as exc:
                self._finish_task_outline_run(
                    "task_file_execution_failed",
                    {
                        "source": run.source_name,
                        "method": method_name,
                        "step_index": run.step_index,
                        "error": str(exc),
                    },
                )
                return

            if not isinstance(result, OperatorResult):
                self._advance_task_outline_step(run)
                return
            if not result.success:
                if result.reason in IN_PROGRESS_REASONS:
                    return
                self._publish_contract_result(method_name, result)
                self._finish_task_outline_run(
                    "task_file_execution_failed",
                    {
                        "source": run.source_name,
                        "method": method_name,
                        "step_index": run.step_index,
                        "reason": result.reason,
                    },
                )
                return

            now_s = time.monotonic()
            duration_ms = _timed_primitive_duration_ms(method_name, kwargs, result)
            run.pending_timed_primitive = TimedPrimitiveStep(
                method_name=method_name,
                duration_ms=duration_ms,
                started_s=now_s,
                deadline_s=now_s
                + (duration_ms / 1000.0)
                + self._task_timed_primitive_settle_s,
                seq=self._sink.seq if result.command is not None else None,
                result=result,
            )
            return

        if pending.method_name != method_name:
            self._finish_task_outline_run(
                "task_file_execution_failed",
                {
                    "source": run.source_name,
                    "method": method_name,
                    "step_index": run.step_index,
                    "reason": "pending_timed_primitive_mismatch",
                    "pending_method": pending.method_name,
                },
            )
            return

        if pending.seq is not None and pending.seq in self._ack_states:
            pending.ack_state = self._ack_states[pending.seq]
            if pending.ack_state in {"rejected", "fault"}:
                self._publish_contract_result(method_name, pending.result)
                self._finish_task_outline_run(
                    "task_file_execution_failed",
                    {
                        "source": run.source_name,
                        "method": method_name,
                        "step_index": run.step_index,
                        "reason": f"command_{pending.ack_state}",
                        "seq": pending.seq,
                    },
                )
                return

        if self._bridge.fault:
            self._publish_contract_result(method_name, pending.result)
            self._finish_task_outline_run(
                "task_file_execution_failed",
                {
                    "source": run.source_name,
                    "method": method_name,
                    "step_index": run.step_index,
                    "reason": "bridge_fault",
                    "fault": self._bridge.fault,
                },
            )
            return

        if time.monotonic() < pending.deadline_s:
            return

        run.pending_timed_primitive = None
        self._publish_contract_result(method_name, pending.result)
        self._advance_task_outline_step(run)

    def _advance_task_outline_step(self, run: TaskOutlineRun) -> None:
        run.pending_timed_primitive = None
        run.step_index += 1
        run.step_started_s = time.monotonic()
        if run.step_index >= len(run.method_plan):
            self._finish_task_outline_run(
                "task_file_completed", {"source": run.source_name}
            )

    def _finish_task_outline_run(
        self, event_name: str, detail: Mapping[str, Any]
    ) -> None:
        self._publish_event(
            OperatorEvent(
                name=event_name,
                stamp_s=time.monotonic(),
                detail=detail,
            )
        )
        self._task_outline_run = None
        self._task_file_active = False

    def _on_tf(self, msg: TFMessage) -> None:
        stamp_s = time.monotonic()
        for stamped in msg.transforms:
            tag_id = tag_id_from_frame_id(stamped.child_frame_id)
            if tag_id is None or not MIN_TAG_ID <= tag_id <= MAX_TAG_ID:
                continue
            translation = stamped.transform.translation
            camera_from_tag = camera_from_apriltag_translation(
                optical_x_m=float(translation.x),
                optical_z_m=float(translation.z),
            )
            robot_from_tag = robot_from_camera_pose(
                camera_from_tag, self.camera_in_robot
            )
            if robot_from_tag.x_m <= 0.05:
                continue
            self._tags[tag_id] = TagObservation(
                tag_id=tag_id,
                stamp_s=stamp_s,
                forward_m=robot_from_tag.x_m,
                left_m=robot_from_tag.y_m,
                distance_m=math.hypot(robot_from_tag.x_m, robot_from_tag.y_m),
                yaw_rad=math.atan2(robot_from_tag.y_m, robot_from_tag.x_m),
            )
            self._latest_align_tag = AlignTagObservation(
                tag_id=tag_id,
                stamp_s=stamp_s,
                yaw_error_rad=math.atan2(robot_from_tag.y_m, robot_from_tag.x_m),
                lateral_error_m=robot_from_tag.y_m,
                distance_m=math.hypot(robot_from_tag.x_m, robot_from_tag.y_m),
                confidence=None,
            )
        self._refresh_vision(stamp_s=stamp_s)

    def _on_scene_map(self, msg: String) -> None:
        try:
            self._last_scene_map = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"ignored bad scene map: {exc}")
            return
        self._observed_tag_ids = sorted(
            int(tag_id) for tag_id in self._last_scene_map.get("observed_tag_ids", [])
        )
        self._refresh_vision(stamp_s=time.monotonic())

    def _on_object_detections(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"ignored bad object detections: {exc}")
            return
        stamp_s = float(payload.get("stamp_s", time.monotonic()))
        objects: list[ObjectObservation] = list(self._objects)
        for item in payload.get("detections", []):
            if not isinstance(item, Mapping):
                continue
            objects.append(
                ObjectObservation(
                    name=str(item.get("label", item.get("name", "object"))),
                    category=str(item.get("label", item.get("name", "object"))),
                    stamp_s=float(item.get("stamp_s", stamp_s)),
                    confidence=(
                        float(item["confidence"])
                        if item.get("confidence") is not None
                        else None
                    ),
                    source=str(payload.get("source", "object_detections")),
                )
            )
        self._objects = tuple(objects[-50:])
        self._refresh_vision(stamp_s=time.monotonic())

    def _on_object_indications(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"ignored bad object indications: {exc}")
            return
        if isinstance(payload, Mapping):
            payload = [payload]
        objects: list[ObjectObservation] = []
        now_s = time.monotonic()
        for item in payload:
            if not isinstance(item, Mapping):
                continue
            name = str(item.get("name", "object"))
            forward_m = _optional_float(item.get("forward_m"))
            left_m = _optional_float(item.get("left_m"))
            if forward_m is not None and left_m is not None:
                robot_from_object = robot_from_camera_pose(
                    Pose2D(forward_m, left_m, float(item.get("yaw_rad", 0.0))),
                    self.camera_in_robot,
                )
                forward_m = robot_from_object.x_m
                left_m = robot_from_object.y_m
            objects.append(
                ObjectObservation(
                    name=name,
                    category=name,
                    stamp_s=float(item.get("stamp_s", now_s)),
                    forward_m=forward_m,
                    left_m=left_m,
                    confidence=(
                        float(item["confidence"])
                        if item.get("confidence") is not None
                        else None
                    ),
                    source=str(item.get("source", "object_indications")),
                )
            )
        self._objects = tuple(objects)
        self._refresh_vision(stamp_s=now_s)

    def _on_ack(self, msg: String) -> None:
        try:
            ack = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        ack_seq = ack.get("ack")
        if isinstance(ack_seq, int):
            self._ack_states[ack_seq] = str(ack.get("state", "ack"))
        self._bridge = BridgeHealth(
            stamp_s=time.monotonic(),
            last_ack_seq=ack_seq if isinstance(ack_seq, int) else None,
            fault=ack.get("fault") if isinstance(ack.get("fault"), str) else None,
            status=str(ack.get("state", "ack")),
        )

    def _on_telemetry(self, msg: String) -> None:
        try:
            raw = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"ignored bad telemetry: {exc}")
            return
        self._last_telemetry = telemetry_snapshot_from_mapping(raw)
        self._survey_telemetry = SurveyTelemetry(
            stamp_s=self._last_telemetry.stamp_s,
            motion_enabled=self._last_telemetry.motion_enabled,
            estop=self._last_telemetry.estop,
            drive_ports_ok=self._last_telemetry.drive_ports_ok,
            left_pos_deg=self._last_telemetry.left_pos_deg,
            right_pos_deg=self._last_telemetry.right_pos_deg,
            left_vel_rpm=self._last_telemetry.left_vel_rpm,
            right_vel_rpm=self._last_telemetry.right_vel_rpm,
        )
        self.operator.update_telemetry(self._last_telemetry)

    def _on_bridge_status(self, msg: String) -> None:
        try:
            status = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        state = str(status.get("state", "unknown"))
        fault = str(status.get("reason", "bridge_fault")) if state == "fault" else None
        self._bridge = BridgeHealth(
            stamp_s=time.monotonic() if fault else self._bridge.stamp_s,
            last_ack_seq=self._bridge.last_ack_seq,
            fault=fault,
            status=state,
        )

    def _on_command(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
            action = str(payload.get("action", ""))
            self._run_start_pub.publish(
                String(
                    data=json.dumps(
                        {
                            "type": "run_start",
                            "run_id": self._run_id,
                            "run_start_wall_s": time.time(),
                            "run_index": self.operator.run_index,
                            "action": action,
                        },
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                )
            )
            result = self._dispatch_command(payload)
            if isinstance(result, OperatorResult):
                self._publish_contract_result(action, result)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._publish_event(
                OperatorEvent(
                    name="command_rejected",
                    stamp_s=time.monotonic(),
                    detail={"error": str(exc), "raw": msg.data},
                )
            )
            return
        self._status_pub.publish(
            String(
                data=json.dumps(
                    {
                        "type": "operator_result",
                        "action": payload.get("action"),
                        "success": bool(getattr(result, "success", False)),
                        "reason": str(getattr(result, "reason", "accepted")),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
        )

    def _dispatch_command(self, payload: Mapping[str, Any]) -> Any:
        action = str(payload.get("action", ""))
        tag_index = _tag_index_from_payload(payload)
        if action == "locate_nearest_apriltag":
            self.operator.require_allowed_method(action)
            return self.operator.locate_nearest_apriltag()
        if action == "orient_to_tag":
            self.operator.require_allowed_method(action)
            if tag_index is None:
                raise ValueError("orient_to_tag requires tag_index")
            return self.operator.orient_to_tag(tag_index)
        if action == "move_to_tag":
            self.operator.require_allowed_method(action)
            if tag_index is None:
                raise ValueError("move_to_tag requires tag_index")
            target = payload.get("target_distance_m")
            return self.operator.move_to_tag(
                tag_index,
                target_distance_m=None if target is None else float(target),
            )
        if action == "pickup_ball":
            self.operator.require_allowed_method(action)
            duration = payload.get("duration_ms")
            return (
                self.operator.pickup_ball()
                if duration is None
                else self.operator.pickup_ball(duration_ms=int(duration))
            )
        if action in {"grab", "lift", "release"}:
            self.operator.require_allowed_method(action)
            duration = payload.get("duration_ms")
            method = getattr(self.operator, action)
            return method() if duration is None else method(duration_ms=int(duration))
        if action == "align_to_tag":
            return self._start_align_to_tag(payload)
        if action == "cancel_align_to_tag":
            self._align_cancel_requested = True
            return OperatorResult(False, "align_cancel_requested")
        if action == "survey_scan":
            return self._start_survey_scan(payload)
        if action == "cancel_survey_scan":
            self._survey_cancel_requested = True
            return OperatorResult(False, "survey_cancel_requested")
        if action == "run_routine":
            return self._run_routine(payload)
        raise ValueError(f"unsupported operator action: {action}")

    def _start_align_to_tag(self, payload: Mapping[str, Any]) -> Any:
        goal = AlignToTagGoal(
            tag_id=int(payload.get("tag_id", payload.get("tag_index", 0))),
            target_distance_m=float(payload.get("target_distance_m", 0.45)),
            yaw_tolerance_rad=float(payload.get("yaw_tolerance_rad", 0.05)),
            lateral_tolerance_m=float(payload.get("lateral_tolerance_m", 0.03)),
            distance_tolerance_m=float(payload.get("distance_tolerance_m", 0.05)),
            timeout_s=float(payload.get("timeout_s", 8.0)),
            max_step_ms=int(payload.get("max_step_ms", payload.get("ttl_ms", 150))),
            max_vx=float(payload.get("max_vx", 0.12)),
            max_vy=float(payload.get("max_vy", 0.08)),
            max_omega=float(payload.get("max_omega", 0.25)),
            min_vx=float(payload.get("min_vx", 0.06)),
            min_turn_omega=float(payload.get("min_turn_omega", 0.35)),
            tag_stale_s=float(payload.get("tag_stale_s", 0.5)),
            ack_stale_s=float(payload.get("ack_stale_s", 0.8)),
        )
        decision = self._align_controller.start(
            goal,
            now_s=time.monotonic(),
            tag=self._latest_align_tag,
            bridge=self._bridge,
        )
        self._handle_align_decision(decision)
        return decision.result or OperatorResult(True, "align_started")

    def _start_survey_scan(self, payload: Mapping[str, Any]) -> Any:
        goal = SurveyScanGoal(
            duration_s=float(payload.get("duration_s", 14.5)),
            omega_rad_s=float(payload.get("omega_rad_s", payload.get("omega", 0.45))),
            max_step_ms=int(payload.get("max_step_ms", payload.get("ttl_ms", 180))),
            ack_stale_s=float(payload.get("ack_stale_s", 0.8)),
            telemetry_stale_s=float(payload.get("telemetry_stale_s", 1.0)),
        )
        decision = self._survey_controller.start(
            goal,
            now_s=time.monotonic(),
            bridge=self._bridge,
            telemetry=self._survey_telemetry,
            observed_tag_ids=self._observed_tag_ids,
        )
        self._handle_survey_decision(decision)
        return decision.result or OperatorResult(True, "survey_started")

    def _run_routine(self, payload: Mapping[str, Any]) -> OperatorResult:
        slot = int(payload.get("slot", 0))
        packet = {
            "v": PROTOCOL_VERSION,
            "type": "cmd",
            "cmd": "routine",
            "slot": slot,
            "ttl_ms": int(payload.get("ttl_ms", 5000)),
            "omega": float(payload.get("omega", 0.0)),
        }
        if payload.get("reason") is not None:
            packet["reason"] = str(payload["reason"])
        self._sink.send_packet(packet)
        return OperatorResult(True, "routine_sent")

    def _tick_controllers(self) -> None:
        align_decision = self._align_controller.step(
            now_s=time.monotonic(),
            tag=self._latest_align_tag,
            bridge=self._bridge,
            cancel=self._align_cancel_requested,
        )
        self._align_cancel_requested = False
        self._handle_align_decision(align_decision)

        survey_decision = self._survey_controller.step(
            now_s=time.monotonic(),
            bridge=self._bridge,
            telemetry=self._survey_telemetry,
            observed_tag_ids=self._observed_tag_ids,
            cancel=self._survey_cancel_requested,
        )
        self._survey_cancel_requested = False
        self._handle_survey_decision(survey_decision)

    def _handle_align_decision(self, decision: Any) -> None:
        self._align_feedback_pub.publish(
            String(data=json.dumps(asdict(decision.feedback), sort_keys=True))
        )
        if decision.command is not None:
            self._send_vex_command(decision.command)
        if decision.result is not None:
            self._align_result_pub.publish(
                String(data=json.dumps(asdict(decision.result), sort_keys=True))
            )

    def _handle_survey_decision(self, decision: Any) -> None:
        self._survey_feedback_pub.publish(
            String(data=json.dumps(asdict(decision.feedback), sort_keys=True))
        )
        if decision.command is not None:
            self._send_vex_command(decision.command)
        if decision.result is not None:
            self._survey_result_pub.publish(
                String(data=json.dumps(asdict(decision.result), sort_keys=True))
            )

    def _send_vex_command(self, command: VexCommand) -> None:
        self._sink.send_packet(_packet_from_vex_command(command))

    def _refresh_vision(self, *, stamp_s: float) -> None:
        self.operator.update_vision(
            VisionSnapshot(
                stamp_s=stamp_s,
                tags=dict(self._tags),
                objects=self._objects,
                raw_scene_map=self._last_scene_map,
            )
        )

    def _publish_event(self, event: OperatorEvent) -> None:
        payload = {
            "type": "operator_event",
            "run_id": self._run_id,
            "name": event.name,
            "stamp_s": event.stamp_s,
            "detail": dict(event.detail),
        }
        self._event_pub.publish(
            String(data=json.dumps(payload, separators=(",", ":"), sort_keys=True))
        )

    def _publish_contract_result(self, action: str, result: Any) -> None:
        payload = self.operator.contract_result(method_name=action, result=result)
        payload["run_id"] = self._run_id
        self._result_pub.publish(
            String(data=json.dumps(payload, separators=(",", ":"), sort_keys=True))
        )

    def _publish_status(self) -> None:
        telemetry = self._last_telemetry
        pose = self.operator.current_pose()
        payload = {
            "type": "operator_status",
            "run_id": self._run_id,
            "stamp_s": time.monotonic(),
            "protocol_version": PROTOCOL_VERSION,
            "last_sent_ms": now_ms(),
            "available_tag_ids": list(self.operator.available_april_tag_ids),
            "camera_in_robot": self.operator.camera_in_robot.to_json(),
            "known_tags": sorted(self._tags),
            "object_categories": sorted({obj.category for obj in self._objects}),
            "telemetry_seen": telemetry is not None,
            "localization_source": self.operator.localization_source,
            "map_pose": None if pose is None else pose.to_json(),
            "has_object": self.operator.has_object(),
        }
        self._status_pub.publish(
            String(data=json.dumps(payload, separators=(",", ":"), sort_keys=True))
        )


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _timed_primitive_duration_ms(
    method_name: str, kwargs: Mapping[str, Any], result: OperatorResult
) -> int:
    if "duration_ms" in kwargs:
        return int(kwargs["duration_ms"])
    if result.command is not None and result.command.duration_ms is not None:
        return int(result.command.duration_ms)
    return timed_primitive_default_duration_ms(method_name)


def _idle_task_contract() -> Mapping[str, Any]:
    return {
        "schema_version": "1.0",
        "session_id": "operator-idle",
        "generation": 0,
        "round": 0,
        "task": "idle",
        "motor_samples": [{"device": "left_drive"}],
        "predicted": {"success": True},
        "gap": {"distance_error_m": 0.0},
    }


def _idle_task_outline() -> list[list[Any]]:
    return [["locate_nearest_apriltag", []]]


def _tag_index_from_payload(payload: Mapping[str, Any]) -> int | None:
    if "tag_index" in payload:
        return int(payload["tag_index"])
    if "tag_id" in payload:
        return int(payload["tag_id"])
    return None


def _packet_from_vex_command(command: VexCommand) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "v": PROTOCOL_VERSION,
        "type": "cmd",
        "cmd": command.cmd,
        "ttl_ms": command.ttl_ms,
    }
    if command.cmd == "drive":
        packet.update({"vx": command.vx, "vy": command.vy, "omega": command.omega})
    if command.cmd == "turn":
        packet["omega"] = command.omega
    if command.reason:
        packet["reason"] = command.reason
    return packet


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = OperatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
