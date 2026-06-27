# Telemetry Fixture Baseline Requirements

Status: approved - decisions closed by 215eight in-session.

## Goal

Provide a deterministic fixture-backed evidence path for downstream self-modeling work. The feature
must unblock F10 gap analyzer, F8 generator, F9 critic panel, F11 markdown presenter, and F12 demo
replay / `make demo` by giving them stable contract JSONL evidence shaped like the semantic output
of future real robot runs.

This feature does not require a real robot run. It must not fake MCAP. It must make the repo's scope
honest: fixture-backed JSONL is enough for downstream MVP development, while full MCAP-backed
hardware capture remains a later integration requirement.

## In Scope

- Create a checked-in telemetry fixture run under `telemetry-fixtures/`.
- Include a small manifest for the run that identifies provenance, task, fixture status, and the
  canonical downstream evidence file.
- Include a contract-valid `contract.jsonl` artifact for downstream self-modeling components.
- Optionally include topic-shaped JSONL files, such as `operator_run_start.jsonl`,
  `operator_results.jsonl`, and `vex_telemetry.jsonl`, only when they help fixture realism.
- Add validation coverage so fixture `contract.jsonl` lines are validated as `contracts.ContractLine`.
- Add a no-ROS/no-MCAP loader or test path that proves downstream components can consume the fixture.
- Update docs/requirements notes to state the handoff contract: downstream components consume
  `ContractLine` JSONL; real hardware runs later provide MCAP plus the same semantic JSONL shape.
- Clarify PR #43 as a useful telemetry JSONL baseline with partial MCAP capture, not completion of
  the later full hardware-capture and replay/audit requirements.

## Out of Scope

- Running robot hardware.
- Capturing real telemetry.
- Committing MCAP files.
- Generating fake MCAP files.
- Completing F8/F9/F10/F11/F12 implementations.
- Expanding PR #43's MCAP topic list as part of this feature, except for documentation that scopes
  that work as later hardware-capture follow-up.
- Changing frozen contract schemas without a separately approved schema feature.

## Acceptance

- `telemetry-fixtures/<run-id>/manifest.json` exists and marks the run as fixture-backed.
- `telemetry-fixtures/<run-id>/contract.jsonl` exists and contains at least one valid
  `contracts.ContractLine`.
- A test or validation command reads every non-empty line in fixture `contract.jsonl` and validates
  it through the runtime `contracts.ContractLine` model.
- A targeted test demonstrates that downstream fixture loading does not import ROS packages,
  `rosbag2_py`, or MCAP-specific dependencies.
- Documentation clearly states that JSONL fixtures unblock F8/F9/F10/F11/F12 and that MCAP is deferred
  to real hardware capture.
- Documentation clearly separates PR #43's JSONL baseline and partial MCAP capture from full
  hardware-capture completion.
- The feature leaves `make demo` ready to depend on fixture-backed contract JSONL without requiring
  a robot, ROS, or MCAP.

## Constraints

- `MASTER_REQUIREMENTS.md` remains authoritative.
- No schema definitions outside `contracts/`.
- No hardware, ROS daemon, camera, serial device, MCAP file, or network dependency in tests.
- Use deterministic fixture data only.
- Use `uv`; do not introduce pip/poetry/black/isort/flake8.
- Fixture data must be small enough to review in git.
- Any fixture provenance must be explicit; demo output must not imply a real hardware run.

## Decisions

- D1 - Closed: The canonical downstream artifact for this feature is `contract.jsonl`, not MCAP.
- D2 - Closed: The fixture root is repo-level `telemetry-fixtures/`, matching the user's preferred
  location and keeping generated/synced `telemetry/` ignored.
- D3 - Closed: The fixture run must include `manifest.json` to label provenance and point at
  `contract.jsonl`.
- D4 - Closed: MCAP is not required for this feature and must not be faked; full MCAP-backed
  hardware capture is deferred to the later hardware baseline milestone.
- D5 - Closed: Topic-shaped JSONL files are optional support artifacts; downstream F8/F9/F10/F11/F12
  should depend on `contracts.ContractLine` JSONL.
- D6 - Closed: Validation should be wired into repo tests or `make validate` so fixture drift is
  caught before `make demo`.
- D7 - Closed: PR #43 is scope evidence for a useful JSONL baseline plus partial MCAP capture only;
  it does not close the later real-hardware replay/audit requirement.

## Notes For Slice Planning

Expected slices after approval:

- Fixture + validation: add the fixture run, manifest, validation helper/test, and make integration.
- Docs + scope alignment: update docs/requirements notes so PR #43 telemetry, MVP fixtures, and later
  MCAP hardware capture are clearly separated.
- Downstream handoff smoke: add a small no-ROS fixture-loader test or helper that F8/F9/F10/F11/F12
  can reuse.
