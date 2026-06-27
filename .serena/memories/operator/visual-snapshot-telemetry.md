# Operator Visual Snapshot Telemetry

Task-outline visual snapshots are emitted by `vexy_ros.operator.node.OperatorNode` as `operator_event` JSON on `/operator/events`, not by changing `TelemetryWriterNode` or subscribing the telemetry writer to raw image topics. Because `scripts/sync_telemetry.sh`/`make sync-telemetry` rsyncs the full `/home/vexy/telemetry/` directory, these snapshot events are pulled inside the existing `operator_events.jsonl` telemetry file.

Snapshot behavior:
- `visual_snapshot` event with `detail.trigger == "periodic"` is emitted at most once per `visual_snapshot_period_s` while a task outline is running.
- `visual_snapshot` event with `detail.trigger == "step_completed"` is emitted immediately before advancing each completed outline step.
- The node subscribes to `visual_snapshot_image_topic` (default `/camera/image_rect`) when `visual_snapshot_enabled` is true.
- Image payload is compact base64, preferring JPEG when OpenCV is available and falling back to PPM for dependency-light environments/tests.
- Missing or unsupported image data records unavailable/error metadata and must not fail task execution.
