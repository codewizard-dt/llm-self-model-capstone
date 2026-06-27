from __future__ import annotations

import signal
import subprocess
from pathlib import Path

STRING_TELEMETRY_TOPICS = (
    "/operator/run_start",
    "/operator/events",
    "/operator/command_log",
    "/operator/results",
    "/operator/status",
    "/vex/telemetry",
    "/vision/scene_map",
    "/vision/object_detections",
)

BAG_TOPICS = (
    *STRING_TELEMETRY_TOPICS,
    "/apriltag/detections",
    "/tf",
)


def start_operator_run_capture(
    out_dir: Path,
    *,
    run_id: str | None = None,
    label: str | None = None,
) -> list[subprocess.Popen]:
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
        ),
        subprocess.Popen(
            [
                "ros2",
                "bag",
                "record",
                "-s",
                "mcap",
                "-o",
                str(out_dir / "bag"),
                *BAG_TOPICS,
            ],
            stdout=(out_dir / "bag-record.log").open("w"),
            stderr=subprocess.STDOUT,
        ),
    ]


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=8)
        return
    except subprocess.TimeoutExpired:
        pass
    process.terminate()
    try:
        process.wait(timeout=3)
        return
    except subprocess.TimeoutExpired:
        pass
    process.kill()
    process.wait(timeout=3)


def stop_operator_run_capture(processes: list[subprocess.Popen]) -> None:
    for process in reversed(processes):
        stop_process(process)
