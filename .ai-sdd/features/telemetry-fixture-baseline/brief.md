# Telemetry Fixture Baseline

## Goal

Create a driveable feature that unblocks downstream self-modeling work by providing a deterministic,
contract-valid telemetry fixture path that mirrors the real-run semantic handoff, while clearly
separating that MVP fixture path from later full hardware MCAP capture.

The downstream MVP features - F10 gap analyzer, F8 generator, F9 critic panel, F11 markdown
presenter, and F12 demo replay / `make demo` - should consume stable JSON fixtures shaped as
`contracts.ContractLine` evidence. A real robot run is not required for this feature. Hardware MCAP
capture remains a later integration requirement and must not be faked or implied by fixture output.

## In Scope

- Add a stable telemetry fixture location, expected to be `telemetry-fixtures/`, containing a small
  representative run with JSONL artifacts.
- Ensure the canonical downstream fixture includes contract-valid `contract.jsonl`.
- Add manifest metadata that labels the run as fixture-backed, not real hardware.
- Add validation or tests proving the fixture can be consumed by downstream code without ROS, MCAP,
  or hardware.
- Update requirements/docs so F8/F9/F10/F11/F12 are explicitly unblocked by contract JSONL fixtures.
- Clarify that MCAP is required for later hardware audit/replay, not for fixture-backed MVP demo
  development, and that PR #43 is a JSONL baseline with partial MCAP capture only.

## Out of Scope

- No real robot run is required.
- No generated or fake MCAP should be committed.
- Do not implement F8, F9, F10, F11, or F12 in this feature.
- Do not change frozen `contracts.ContractLine` schema fields unless validation proves a bug in the
  existing schema.
- Do not make downstream services consume ROS or MCAP directly.

## Acceptance

- A checked-in fixture run exists under `telemetry-fixtures/` with a manifest and at least one
  contract-valid `contract.jsonl` line.
- The fixture is labeled as fixture/synthetic/replay-backed so demo output cannot be mistaken for a
  real hardware capture.
- `make validate` or an equivalent repo test validates the fixture against `contracts.ContractLine`.
- At least one targeted test proves downstream fixture loading works without ROS or MCAP installed.
- Documentation states that downstream self-modeling components consume contract JSONL, while MCAP
  remains the raw hardware replay/audit source for later real runs.
- Existing PR #43 telemetry behavior is documented as a JSONL baseline plus partial MCAP recording,
  not as completion of full hardware-capture or replay/audit requirements.

## Constraints

- Follow `MASTER_REQUIREMENTS.md` when it conflicts with older docs.
- Use `uv` for Python execution/dependencies and `ruff` for lint/format.
- Keep schemas owned by `contracts/`; other verticals import them.
- Keep fixture data deterministic, small, and committed.
- Preserve the distinction between MVP demo fixtures and later real robot captures.
- No network, secrets, or live hardware dependencies in tests for this feature.

## Open Questions

- Should the fixture directory be named `telemetry-fixtures/` at repo root, or live under
  `contracts/fixtures/`?
- Should the manifest use a new schema, a plain documented JSON shape, or just a README?
- Should `make validate` include `telemetry-fixtures/**/*.jsonl`, or should validation be a separate
  targeted test?
