# Telemetry Capture Pattern

Every run (launch stack + proof_runner) produces TWO simultaneous outputs:
- **JSONL** via `vexy_telemetry_writer_node` (live, appended per message)
- **MCAP** via `ros2 bag record` (recorded to `<run_dir>/bag/`)

Both write the same five topics: `/operator/run_start`, `/operator/events`, `/operator/results`, `/operator/status`, `/vex/telemetry`.

## run_id injection
`TelemetryWriterNode` injects `run_id` into every JSONL line via `payload.setdefault("run_id", self._run_id)`. Defaults to `out_dir.name` if `--run-id` CLI arg is not passed. This allows correlation of `vex_telemetry.jsonl` lines to the run directory.

## Launch args (vexy.launch.py)
- `telemetry_writer_enabled` (default `true`) — toggle JSONL writer
- `bag_record_enabled` (default `true`) — toggle MCAP recorder
Both are respected inside `_launch_nodes` via `LaunchConfiguration(...).perform(context)`.

## proof_runner flags
- `--no-telemetry` — skip JSONL writer
- `--no-bag-record` — skip MCAP recorder
Both processes are stopped in the `finally` block via `_stop_process()`. Settle sleep fires if either process was started.

## Extracting JSONL from MCAP after the fact
Use `vexy_ros.telemetry_extract`: `python -m vexy_ros.telemetry_extract <bag_dir> --out-dir <out_dir>`. Writes one JSONL file per `std_msgs/String` topic, injecting `_bag_timestamp_ns`.
