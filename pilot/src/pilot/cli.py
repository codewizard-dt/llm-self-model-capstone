"""ROS-free command-line hooks for supervised pilot skill execution."""

from __future__ import annotations

import argparse
from contextlib import redirect_stderr
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from time import monotonic_ns
from typing import TextIO

from pydantic import ValidationError

from contracts import (
    BridgeHealth,
    CommandStatus,
    LocalizationState,
    ManipulatorState,
    PilotObservation,
    PilotSkillName,
    PilotTaskPhase,
    SurveySceneParams,
    SurveySceneSkillCommand,
)
from pilot.executor import ExecutionResult, TransportBoundary, execute_validated_command
from pilot.observe import (
    DEFAULT_DURATION_S,
    DEFAULT_READINESS_TIMEOUT_S,
    DEFAULT_SNAPSHOT_INTERVAL_S,
    ObserveConfig,
    ObserveCliError,
    run_observe,
)
from pilot.safety import ValidationMode, ValidationResult, validate_skill_command

ClockMs = Callable[[], int]
Validator = Callable[..., ValidationResult]
Executor = Callable[[ValidationResult], ExecutionResult]
ObservationFactory = Callable[[int], PilotObservation]


@dataclass(frozen=True, slots=True)
class CliDependencies:
    """Injectable CLI seams for ROS-free tests and future hardware adapters."""

    clock_ms: ClockMs = lambda: monotonic_ns() // 1_000_000
    validator: Validator = validate_skill_command
    executor: Executor | None = None
    observation_factory: ObservationFactory = lambda observed_ms: _default_observation(observed_ms)
    transport: TransportBoundary | None = None


class _UnavailableTransport:
    def send(self, request: object) -> None:
        raise RuntimeError("hardware transport is not configured for the pilot CLI")


def main(argv: Sequence[str] | None = None) -> int:
    """Console script entry point."""

    return run(argv)


def run(
    argv: Sequence[str] | None = None,
    *,
    deps: CliDependencies | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Parse CLI arguments and execute the requested pilot command."""

    out = stdout or sys.stdout
    err = stderr or sys.stderr
    parser = _build_parser()
    try:
        with redirect_stderr(err):
            args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2

    if args.command == "skill":
        return _run_skill(args, deps=deps or CliDependencies(), stdout=out, stderr=err)
    if args.command == "observe":
        try:
            return run_observe(
                ObserveConfig(
                    objective=args.objective,
                    duration_s=args.duration_s,
                    count=args.count,
                    out=args.out,
                    readiness_timeout_s=args.readiness_timeout_s,
                    snapshot_interval_s=args.snapshot_interval_s,
                )
            )
        except ObserveCliError as exc:
            print(f"pilot observe: {exc}", file=err)
            return exc.exit_code
    parser.print_help(err)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pilot")
    subcommands = parser.add_subparsers(dest="command", required=True)

    skill = subcommands.add_parser("skill", help="execute one supervised pilot skill")
    skill.add_argument("--hardware", action="store_true", help="validate using hardware policy")
    skill.add_argument(
        "--skill",
        required=True,
        choices=(PilotSkillName.SURVEY_SCENE.value,),
        help="pilot skill to execute",
    )
    skill.add_argument(
        "--duration-s",
        required=True,
        type=_positive_duration_s,
        help="survey duration in seconds",
    )
    skill.add_argument(
        "--no-supervision",
        action="store_true",
        help="withhold the hardware supervision signal before validation",
    )

    observe = subcommands.add_parser(
        "observe",
        help="emit observe-only PilotObservation JSONL from read-only ROS evidence topics",
    )
    observe.add_argument("--objective", required=True, help="live task objective for snapshots")
    observe.add_argument(
        "--duration-s",
        type=_positive_duration_s,
        default=DEFAULT_DURATION_S,
        help=f"wall-clock observe bound in seconds (default: {DEFAULT_DURATION_S:g})",
    )
    observe.add_argument(
        "--count",
        type=_positive_int,
        default=None,
        help="optional maximum number of snapshots to emit",
    )
    observe.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write JSONL to this file instead of stdout",
    )
    observe.add_argument(
        "--readiness-timeout-s",
        type=_positive_duration_s,
        default=DEFAULT_READINESS_TIMEOUT_S,
        help=(
            "seconds to wait for /vision/agent_scene, /vision/object_tracks, "
            "/vex/telemetry, and /vex/bridge_status"
        ),
    )
    observe.add_argument(
        "--snapshot-interval-s",
        type=_positive_duration_s,
        default=DEFAULT_SNAPSHOT_INTERVAL_S,
        help=f"minimum seconds between snapshots (default: {DEFAULT_SNAPSHOT_INTERVAL_S:g})",
    )
    return parser


def _run_skill(
    args: argparse.Namespace,
    *,
    deps: CliDependencies,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    issued_ms = deps.clock_ms()
    try:
        command = _build_skill_command(args, issued_ms=issued_ms)
    except ValueError as exc:
        _emit(
            stderr,
            {
                "command_id": None,
                "skill": getattr(args, "skill", None),
                "status": "invalid_arguments",
                "reason_code": "invalid_arguments",
                "message": str(exc),
            },
        )
        return 2

    observation = deps.observation_factory(issued_ms)
    mode = ValidationMode.HARDWARE if args.hardware else ValidationMode.REPLAY
    human_supervised = bool(args.hardware and not args.no_supervision)
    validation = deps.validator(
        command,
        observation,
        mode=mode,
        human_supervised=human_supervised,
    )
    if not validation.accepted:
        _emit(stdout, _validation_output(validation))
        return 1

    result = (
        deps.executor(validation)
        if deps.executor is not None
        else execute_validated_command(
            validation,
            deps.transport or _UnavailableTransport(),
            clock_ms=deps.clock_ms,
        )
    )
    _emit(stdout, _execution_output(result))
    return 0 if result.status is CommandStatus.OK else 1


def _build_skill_command(args: argparse.Namespace, *, issued_ms: int) -> SurveySceneSkillCommand:
    if args.skill != PilotSkillName.SURVEY_SCENE.value:
        raise ValueError(f"unsupported skill for pilot CLI: {args.skill}")

    timeout_ms = int(round(args.duration_s * 1000))
    command_id = f"pilot-{PilotSkillName.SURVEY_SCENE.value}-{issued_ms}"
    try:
        return SurveySceneSkillCommand(
            command_id=command_id,
            issued_ms=issued_ms,
            params=SurveySceneParams(timeout_ms=timeout_ms),
        )
    except ValidationError as exc:
        raise ValueError("survey_scene arguments are not contract-valid") from exc


def _default_observation(observed_ms: int) -> PilotObservation:
    return PilotObservation(
        observed_ms=observed_ms,
        task_phase=PilotTaskPhase.SURVEY,
        objective="manual survey_scene proof",
        localization=LocalizationState(pose=None, confidence=0.0, age_ms=0),
        manipulator=ManipulatorState(arm_deg=None, claw_state="unknown"),
        bridge=BridgeHealth(
            state="ok",
            last_heartbeat_age_ms=0,
            estop=False,
            battery_pct=None,
        ),
        visible_objects=[],
        visible_tags=[],
        recent_failures=[],
        current_assertions=[],
    )


def _positive_duration_s(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--duration-s must be a positive number") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("--duration-s must be greater than zero")
    return parsed


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def _validation_output(validation: ValidationResult) -> dict[str, object]:
    command = validation.command
    skill = validation.skill.value if validation.skill is not None else None
    return {
        "command_id": command.command_id if command is not None else None,
        "skill": skill,
        "status": validation.status.value,
        "reason_code": validation.reason_code.value,
        "message": validation.message,
    }


def _execution_output(result: ExecutionResult) -> dict[str, object]:
    return {
        "command_id": result.command_id,
        "skill": result.skill.value if result.skill is not None else None,
        "status": result.status.value,
        "reason_code": result.reason_code,
        "message": result.message,
    }


def _emit(stream: TextIO, payload: dict[str, object]) -> None:
    print(json.dumps(payload, sort_keys=True), file=stream)


__all__ = ["CliDependencies", "main", "run"]
