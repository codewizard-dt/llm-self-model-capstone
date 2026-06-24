# Slice: mcap-contract-export

| Field | Value |
|---|---|
| Feature | ros2-align-to-tag |
| Stack | coprocessor |
| Depends on | align-to-tag-action |

## What this slice delivers

Add the evidence bridge from ROS proof to the existing self-model loop: record the closed-loop `AlignToTag` run as ROS bag/MCAP raw evidence, then export the relevant episode window into contract-valid JSONL.

## Scope

- Add a repeatable recording command/profile for the `AlignToTag` proof topics.
- Record at minimum camera, camera info, rectified image, tag pose/detections or TF, VEX command, VEX ack, VEX telemetry, bridge status, and action feedback/result topics.
- Add an exporter that converts a recorded or sampled ROS episode into one or more `ContractLine`-valid JSONL records.
- Use the existing `contracts` package as the validation authority; do not define a second telemetry schema in `robot/ros2-runtime`.
- Represent the task as a free-string task name such as `align_to_tag`.
- Preserve raw bag paths in `source.raw_session_path` or equivalent existing provenance fields when possible.
- Add deterministic fixture/sample tests for the exporter without requiring live hardware.
- Document the evidence directory layout and artifact naming convention.

## Acceptance

1. A documented command records the required topics into an MCAP bag.
2. A sample/fake episode exports to newline-delimited JSON without trailing commas or invalid blank records.
3. The exported JSONL validates with the existing contract validation path.
4. Exported records include enough predicted/outcome/gap content for operator gap analysis to identify tag alignment residuals.
5. Exported records include vision/AprilTag pose data when available.
6. The exporter records provenance for the raw bag or source episode.
7. Tests cover at least one success episode and one explicit failure/fault episode.

## Out of scope

- Contract schema redesign.
- Full offline operator gap-analyzer implementation.
- Cloud upload or external API submission.
