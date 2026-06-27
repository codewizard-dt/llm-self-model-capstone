# Robot Runtime

This directory holds the code that actually runs near the physical robot.

```text
ros2-runtime/ Raspberry Pi ROS 2 coprocessor runtime.
v5-brain/     VEX V5 Brain starter code and notes.
```

The research wiki and planning docs describe the capstone loop. This directory is the deployable implementation surface.

## Evidence Scope

The self-modeling handoff is `contracts.ContractLine` JSONL. Fixture-backed
runs under `../telemetry-fixtures/` can unblock F8, F9, F10, F11, F12, and
`make demo` without a robot, ROS, or MCAP. Later real-hardware runs still record
MCAP for replay/audit and export the same contract-valid JSONL shape.

See [../DEVOPS.md](../DEVOPS.md) for the branch, deploy, and device-config workflow.
