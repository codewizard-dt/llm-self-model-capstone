from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def default_proof_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(f"/home/vexy/telemetry/run-{stamp}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run calibrated tag-action proof with JSON telemetry and ContractLine export."
    )
    parser.add_argument("--proof-dir", type=Path, default=None)
    parser.add_argument("--mode", default="visual-one-foot-scan")
    parser.add_argument("--no-telemetry", action="store_true",
                        help="Skip live JSON telemetry writer")
    parser.add_argument("--no-bag-record", action="store_true",
                        help="Skip MCAP bag recording")
    parser.add_argument("--no-export", action="store_true")
    parser.add_argument("--settle-before-s", type=float, default=2.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    proof_dir = args.proof_dir or default_proof_dir()
    proof_dir.mkdir(parents=True, exist_ok=True)
    (proof_dir / "proof-dir.txt").write_text(str(proof_dir) + "\n")

    writer = None
    bag_recorder = None
    try:
        if not args.no_telemetry:
            writer = subprocess.Popen(
                [
                    "ros2", "run", "vexy_ros", "vexy_telemetry_writer_node",
                    "--out-dir", str(proof_dir),
                ],
                stdout=(proof_dir / "telemetry-writer.log").open("w"),
                stderr=subprocess.STDOUT,
            )
        if not args.no_bag_record:
            bag_recorder = subprocess.Popen(
                [
                    "ros2", "bag", "record",
                    "-o", str(proof_dir / "bag"),
                    "/operator/run_start",
                    "/operator/events",
                    "/operator/results",
                    "/operator/status",
                    "/vex/telemetry",
                ],
                stdout=(proof_dir / "bag-record.log").open("w"),
                stderr=subprocess.STDOUT,
            )
        if writer is not None or bag_recorder is not None:
            time.sleep(max(0.0, args.settle_before_s))

        proof_cmd = [
            "ros2",
            "run",
            "vexy_ros",
            "vexy_tag_action_proof",
            "--mode",
            args.mode,
            "--summary-out",
            str(proof_dir / "summary.json"),
        ]
        with (proof_dir / "tag-action.log").open("w") as log:
            result = subprocess.run(proof_cmd, stdout=log, stderr=subprocess.STDOUT)
        (proof_dir / "proof-rc.txt").write_text(f"proof_rc={result.returncode}\n")
        return_code = result.returncode
    finally:
        if writer is not None:
            _stop_process(writer)
        if bag_recorder is not None:
            _stop_process(bag_recorder)

    if not args.no_export:
        with (proof_dir / "export.log").open("w") as log:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "vexy_ros.evidence_export",
                    "--proof-dir",
                    str(proof_dir),
                    "--out",
                    str(proof_dir / "contract.jsonl"),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
            )

    print(proof_dir)
    return return_code


def _stop_process(process: subprocess.Popen) -> None:
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


if __name__ == "__main__":
    raise SystemExit(main())
