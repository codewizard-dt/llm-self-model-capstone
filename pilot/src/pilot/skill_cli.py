"""CLI dispatcher for observe-only snapshots and supervised PM4 hardware skills."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, TextIO

from pydantic import TypeAdapter, ValidationError

from contracts import (
    CommandStatus,
    PilotSkillCommand,
    PilotSkillName,
    PilotSkillResult,
)
from pilot.execution import ExecutionStatus, execute_one_skill, normalize_skill_result
from pilot.safety import ValidationMode
from pilot.trace import PilotTraceWriter

APPROVED_PM4_SKILLS: tuple[PilotSkillName, ...] = (
    PilotSkillName.SURVEY_SCENE,
    PilotSkillName.CLAW_OPEN,
    PilotSkillName.CLAW_CLOSE,
    PilotSkillName.VERIFY_GRASP,
    PilotSkillName.VERIFY_DROP,
)
APPROVED_PM4_SKILL_VALUES = tuple(skill.value for skill in APPROVED_PM4_SKILLS)

DEFAULT_OBJECTIVE = "pm4 supervised hardware proof"
DEFAULT_DURATION_S = 3.0
DEFAULT_READINESS_TIMEOUT_S = 5.0

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_REJECTED = 20
EXIT_TIMED_OUT = 21
EXIT_INTERRUPTED = 22
EXIT_ROS_DEPENDENCY = 23
EXIT_RUNTIME = 24
EXIT_OUTPUT = 25

_SKILL_COMMAND_ADAPTER = TypeAdapter(PilotSkillCommand)


class HardwareSkillTransport(Protocol):
    def read_observation(self, *, objective: str, readiness_timeout_s: float) -> object: ...

    def bind_observation(self, observation: object) -> None: ...

    def preflight_terminal_outcome(self, command: object, observation: object) -> object | None: ...

    def dispatch(self, command: object) -> None: ...

    def wait_for_terminal_result(self, command: object, *, timeout_ms: int) -> object: ...

    def cancel(self, command: object, *, reason: str) -> None: ...

    def close(self) -> None: ...


class SkillCliError(Exception):
    """Expected skill CLI failure with a stable process exit code."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pilot")
    subparsers = parser.add_subparsers(dest="command", required=True)
    skill = subparsers.add_parser("skill", help="run one supervised PM4 hardware skill")
    skill.add_argument("--hardware", action="store_true", help="enable live hardware transport")
    skill.add_argument(
        "--human-supervised",
        action="store_true",
        help="confirm a human operator is supervising the hardware run",
    )
    skill.add_argument("--skill", help="approved PM4 skill name")
    skill.add_argument(
        "--command-json",
        type=Path,
        help="path to a contract PilotSkillCommand JSON object",
    )
    skill.add_argument("--command-id", help="optional command id for CLI-built commands")
    skill.add_argument("--objective", default=DEFAULT_OBJECTIVE)
    skill.add_argument(
        "--duration-s",
        type=_positive_float,
        default=DEFAULT_DURATION_S,
        help="duration bound for survey_scene and executor timeout",
    )
    skill.add_argument("--yaw-span-deg", type=_bounded_float(0.0, 360.0), default=180.0)
    skill.add_argument("--object-id")
    skill.add_argument("--destination-id")
    skill.add_argument("--min-confidence", type=_bounded_float(0.0, 1.0), default=0.65)
    skill.add_argument("--opening-pct", type=_bounded_float(0.0, 100.0))
    skill.add_argument("--grip-force-n", type=_bounded_float(0.0, 100.0))
    skill.add_argument("--timeout-ms", type=_positive_int)
    skill.add_argument(
        "--readiness-timeout-s",
        type=_positive_float,
        default=DEFAULT_READINESS_TIMEOUT_S,
    )
    skill.add_argument("--out", type=Path, help="required PilotTraceRecord JSONL output path")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    transport_factory: Callable[[], HardwareSkillTransport] | None = None,
    clock_ms: Callable[[], int] = lambda: time.monotonic_ns() // 1_000_000,
    observe_ros_loader: Callable[[], object] | None = None,
) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list[:1] == ["observe"]:
        from pilot import observe

        try:
            return observe.main(args_list, ros_loader=observe_ros_loader)
        except Exception as exc:
            if _is_observe_cli_error(exc):
                print(f"pilot observe: {exc}", file=sys.stderr)
                return int(exc.exit_code)
            raise

    parser = build_parser()
    args = parser.parse_args(args_list)
    try:
        if args.command == "skill":
            return run_skill(args, transport_factory=transport_factory, clock_ms=clock_ms)
    except SkillCliError as exc:
        print(f"pilot skill: {exc}", file=sys.stderr)
        return exc.exit_code
    parser.error("unknown command")
    return EXIT_RUNTIME


def run_skill(
    args: argparse.Namespace,
    *,
    transport_factory: Callable[[], HardwareSkillTransport] | None,
    clock_ms: Callable[[], int],
) -> int:
    _validate_hardware_gates(args)
    issued_ms = _issued_ms(clock_ms)
    command = build_skill_command(args, issued_ms=issued_ms)
    timeout_ms = args.timeout_ms or _command_timeout_ms(command, fallback_s=args.duration_s)
    session_id = command.command_id

    output, should_close = _open_output(args.out)
    transport: HardwareSkillTransport | None = None
    try:
        writer = PilotTraceWriter(output, session_id=session_id)
        transport = _build_transport(transport_factory)
        observation = transport.read_observation(
            objective=args.objective,
            readiness_timeout_s=args.readiness_timeout_s,
        )
        transport.bind_observation(observation)
        preflight = transport.preflight_terminal_outcome(command, observation)
        if preflight is not None:
            return _write_preflight_result(writer, command=command, terminal=preflight)

        outcome = execute_one_skill(
            command,
            observation,
            mode=ValidationMode.HARDWARE,
            human_supervised=True,
            timeout_ms=timeout_ms,
            session_id=session_id,
            trace_sink=writer,
            transport=transport,
        )
        return _exit_code_for_status(outcome.status)
    except OSError as exc:
        raise SkillCliError(f"could not write trace output: {exc}", EXIT_OUTPUT) from exc
    except KeyboardInterrupt as exc:
        raise SkillCliError("execution interrupted by operator", EXIT_INTERRUPTED) from exc
    except Exception as exc:
        _raise_transport_error(exc)
        raise SkillCliError(f"runtime error: {exc}", EXIT_RUNTIME) from exc
    finally:
        if transport is not None:
            transport.close()
        if should_close:
            output.close()


def build_skill_command(args: argparse.Namespace, *, issued_ms: int) -> PilotSkillCommand:
    if args.command_json is not None:
        command = _command_from_json(args.command_json)
        if args.skill is not None and str(command.skill) != args.skill:
            raise SkillCliError("--skill does not match --command-json skill", EXIT_USAGE)
        _require_approved_skill(str(command.skill))
        return command

    if args.skill is None:
        raise SkillCliError("--skill is required unless --command-json is provided", EXIT_USAGE)
    skill = _require_approved_skill(args.skill)
    payload: dict[str, Any] = {
        "v": 1,
        "command_id": args.command_id or f"pm4-{skill.value}-{issued_ms}",
        "issued_ms": issued_ms,
        "skill": skill.value,
        "params": _params_for_skill(skill, args),
    }
    try:
        return _SKILL_COMMAND_ADAPTER.validate_python(payload)
    except ValidationError as exc:
        raise SkillCliError(
            f"command is not contract-valid: {exc.errors()[0]['msg']}", EXIT_USAGE
        ) from exc


def _validate_hardware_gates(args: argparse.Namespace) -> None:
    if not args.hardware:
        raise SkillCliError("--hardware is required for pilot skill", EXIT_USAGE)
    if not args.human_supervised:
        raise SkillCliError("--human-supervised is required for pilot skill", EXIT_USAGE)
    if args.out is None:
        raise SkillCliError("--out is required for pilot skill trace JSONL", EXIT_USAGE)


def _require_approved_skill(raw: str) -> PilotSkillName:
    try:
        skill = PilotSkillName(raw)
    except ValueError as exc:
        raise SkillCliError(f"unknown pilot skill: {raw}", EXIT_USAGE) from exc
    if skill not in APPROVED_PM4_SKILLS:
        raise SkillCliError(
            "unsupported PM4 hardware skill "
            f"{skill.value!r}; approved skills: {', '.join(APPROVED_PM4_SKILL_VALUES)}",
            EXIT_USAGE,
        )
    return skill


def _params_for_skill(skill: PilotSkillName, args: argparse.Namespace) -> dict[str, Any]:
    if skill is PilotSkillName.SURVEY_SCENE:
        return {
            "yaw_span_deg": args.yaw_span_deg,
            "timeout_ms": int(round(args.duration_s * 1000)),
        }
    if skill is PilotSkillName.CLAW_OPEN:
        return {"opening_pct": args.opening_pct}
    if skill is PilotSkillName.CLAW_CLOSE:
        return {"grip_force_n": args.grip_force_n}
    if skill is PilotSkillName.VERIFY_GRASP:
        return {"object_id": args.object_id, "min_confidence": args.min_confidence}
    if skill is PilotSkillName.VERIFY_DROP:
        return {"destination_id": args.destination_id, "min_confidence": args.min_confidence}
    raise AssertionError(f"unhandled approved skill: {skill}")


def _command_from_json(path: Path) -> PilotSkillCommand:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SkillCliError(f"could not read --command-json: {exc}", EXIT_USAGE) from exc
    except json.JSONDecodeError as exc:
        raise SkillCliError(f"--command-json is not valid JSON: {exc.msg}", EXIT_USAGE) from exc
    try:
        return _SKILL_COMMAND_ADAPTER.validate_python(payload)
    except ValidationError as exc:
        raise SkillCliError(
            "--command-json is not a contract PilotSkillCommand", EXIT_USAGE
        ) from exc


def _build_transport(
    transport_factory: Callable[[], HardwareSkillTransport] | None,
) -> HardwareSkillTransport:
    if transport_factory is not None:
        return transport_factory()
    from pilot.ros_execution import PM4HardwareTransport, load_ros_runtime

    return PM4HardwareTransport(load_ros_runtime())


def _write_preflight_result(
    writer: PilotTraceWriter,
    *,
    command: PilotSkillCommand,
    terminal: object,
) -> int:
    result: PilotSkillResult = normalize_skill_result(terminal, command=command)
    writer.write_result(result)
    writer.write_stop(reason="failure", message=result.message or "preflight rejected")
    if result.status is CommandStatus.STALE:
        return EXIT_REJECTED
    return EXIT_REJECTED if result.status is CommandStatus.REJECTED else EXIT_RUNTIME


def _open_output(path: Path | None) -> tuple[TextIO, bool]:
    if path is None:
        raise SkillCliError("--out is required for pilot skill trace JSONL", EXIT_USAGE)
    try:
        return path.open("w", encoding="utf-8"), True
    except OSError as exc:
        raise SkillCliError(f"could not open --out: {exc}", EXIT_OUTPUT) from exc


def _command_timeout_ms(command: PilotSkillCommand, *, fallback_s: float) -> int:
    timeout_ms = getattr(command.params, "timeout_ms", None)
    if timeout_ms is not None:
        return int(timeout_ms)
    return int(round(fallback_s * 1000))


def _exit_code_for_status(status: ExecutionStatus) -> int:
    match status:
        case ExecutionStatus.SUCCEEDED:
            return EXIT_OK
        case ExecutionStatus.TIMED_OUT:
            return EXIT_TIMED_OUT
        case ExecutionStatus.INTERRUPTED:
            return EXIT_INTERRUPTED
        case ExecutionStatus.REJECTED | ExecutionStatus.STALE:
            return EXIT_REJECTED
        case _:
            return EXIT_RUNTIME


def _raise_transport_error(exc: Exception) -> None:
    from pilot.ros_execution import RosDependencyError, RosExecutionError

    if isinstance(exc, RosDependencyError):
        raise SkillCliError(str(exc), EXIT_ROS_DEPENDENCY) from exc
    if isinstance(exc, RosExecutionError):
        raise SkillCliError(str(exc), EXIT_RUNTIME) from exc


def _is_observe_cli_error(exc: Exception) -> bool:
    return exc.__class__.__name__ == "ObserveCliError" and isinstance(
        getattr(exc, "exit_code", None), int
    )


def _issued_ms(clock_ms: Callable[[], int]) -> int:
    value = int(clock_ms())
    if value < 0:
        raise SkillCliError("clock returned a negative issued_ms", EXIT_RUNTIME)
    return value


def _positive_float(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return value


def _positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return value


def _bounded_float(minimum: float, maximum: float) -> Callable[[str], float]:
    def parse(raw: str) -> float:
        try:
            value = float(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be a number") from exc
        if not minimum <= value <= maximum:
            raise argparse.ArgumentTypeError(f"must be between {minimum:g} and {maximum:g}")
        return value

    return parse


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "APPROVED_PM4_SKILLS",
    "APPROVED_PM4_SKILL_VALUES",
    "DEFAULT_DURATION_S",
    "DEFAULT_OBJECTIVE",
    "EXIT_INTERRUPTED",
    "EXIT_OK",
    "EXIT_OUTPUT",
    "EXIT_REJECTED",
    "EXIT_ROS_DEPENDENCY",
    "EXIT_RUNTIME",
    "EXIT_TIMED_OUT",
    "EXIT_USAGE",
    "SkillCliError",
    "build_parser",
    "build_skill_command",
    "main",
    "run_skill",
]
