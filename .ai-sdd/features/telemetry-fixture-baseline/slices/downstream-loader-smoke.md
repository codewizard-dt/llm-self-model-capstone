# Slice: downstream-loader-smoke

| Field | Value |
|---|---|
| Feature | telemetry-fixture-baseline |
| Stack | self_model_generator |
| Depends on | fixture-and-validation |

## What this slice delivers

Add a small downstream-facing fixture loading path or smoke test proving that F8 generator, F9 critic
panel, F10 gap analyzer, F11 markdown presenter, and F12 demo replay can treat the fixture as ordinary
`contracts.ContractLine` evidence without importing ROS or MCAP-specific modules.

## Scope

- Add a focused helper or test that loads the telemetry fixture's `contract.jsonl`.
- Validate the loaded records as `contracts.ContractLine`.
- Assert the loaded evidence exposes the fields downstream work will need: `task`, `predicted`,
  `gap`, `outcome`, `motor_samples`, and optional `vision`.
- Ensure the smoke path has no import-time dependency on `rclpy`, `rosbag2_py`, MCAP packages, camera
  packages, or robot hardware code.
- Reuse existing fixture readers if the repo already has a suitable path; avoid duplicate abstractions.

## Acceptance

1. A targeted test demonstrates no-ROS/no-MCAP fixture loading.
2. The loaded fixture exposes at least one finite numeric gap residual.
3. The fixture loading path can be reused by upcoming F8/F9/F10/F11/F12 work.
4. No schema is defined outside `contracts/`.

## Out of Scope

- Do not implement the downstream features themselves.
- Do not add LLM calls or prompt generation beyond a smoke-level evidence reader.
- Do not consume raw ROS topic JSONL directly as the canonical downstream artifact.
