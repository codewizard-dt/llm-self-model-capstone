from __future__ import annotations

import os
import shutil
import signal
import subprocess
from pathlib import Path

STRING_TELEMETRY_TOPICS = (
    "/operator/run_start",
    "/operator/events",
    "/operator/command_log",
    "/operator/results",
    "/operator/status",
    "/align_to_tag/feedback",
    "/align_to_tag/result",
    "/survey/feedback",
    "/survey/result",
    "/vex/telemetry",
    "/vision/scene_map",
    "/vision/object_detections",
)

BAG_TOPICS = (
    *STRING_TELEMETRY_TOPICS,
    "/camera/image_rect",
    "/apriltag/detections",
    "/tf",
)
MAX_LOCAL_RUNS = 10


def telemetry_bag_record_cmd(out_dir: Path | str) -> list[str]:
    return [
        "ros2",
        "bag",
        "record",
        "-s",
        "mcap",
        "-o",
        str(out_dir),
        *BAG_TOPICS,
    ]


def prune_local_runs(parent_dir: Path, *, keep: int = MAX_LOCAL_RUNS) -> None:
    parent_dir.mkdir(parents=True, exist_ok=True)
    run_dirs = [
        path
        for path in parent_dir.iterdir()
        if path.is_dir() and not path.name.startswith(".pruning-")
    ]
    run_dirs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    for old_run in run_dirs[keep:]:
        prune_target = parent_dir / f".pruning-{old_run.name}"
        try:
            old_run.rename(prune_target)
        except OSError:
            prune_target = old_run
        shutil.rmtree(prune_target, ignore_errors=True)


def start_operator_run_capture(
    out_dir: Path,
    *,
    run_id: str | None = None,
    label: str | None = None,
) -> list[subprocess.Popen]:
    if out_dir.parent.name == "telemetry":
        prune_local_runs(out_dir.parent, keep=MAX_LOCAL_RUNS - 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    if label is not None:
        (out_dir / "test.txt").write_text(label + "\n")
    run_id = run_id if run_id is not None else out_dir.name
    return [
        subprocess.Popen(
            [
                "ros2",
                "run",
                "vexy_ros",
                "vexy_telemetry_writer_node",
                "--out-dir",
                str(out_dir),
                "--run-id",
                run_id,
            ],
            stdout=(out_dir / "telemetry-writer.log").open("w"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        ),
        subprocess.Popen(
            [
                "ros2",
                "run",
                "vexy_ros",
                "vexy_image_writer_node",
                "--out-dir",
                str(out_dir),
                "--fps",
                "2",
            ],
            stdout=(out_dir / "image-writer.log").open("w"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        ),
        subprocess.Popen(
            telemetry_bag_record_cmd(out_dir / "bag"),
            stdout=(out_dir / "bag-record.log").open("w"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        ),
    ]


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGINT)
    except (ProcessLookupError, PermissionError):
        process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=8)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        process.terminate()
    try:
        process.wait(timeout=3)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        process.kill()
    process.wait(timeout=3)


def stop_operator_run_capture(processes: list[subprocess.Popen]) -> None:
    for process in reversed(processes):
        stop_process(process)
