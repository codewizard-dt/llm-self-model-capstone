# PM3 Live Observation Feature Requirements

Status: approved
Source brief: `PILOT_MASTER_REQUIREMENTS.md` (`pm3` live-observation milestone)
Program: `pilot-online-task-loop`
Feature slug: `pm3-live-observation`
Owner: 215eight
Verticals: `pilot`, `coprocessor`

## Goal

Prove the pilot can build contract-valid live observation snapshots from the ROS runtime without
commanding robot motion. The feature connects the existing ROS-free `pilot.observation` builder to
live, read-only ROS evidence from the Pi stack, normalizes that evidence into `ObservationCache`,
emits `contracts.PilotObservation` snapshots, and provides a manual observe-only proof path suitable
for a live robot connection.

## In Scope

- Add a live observation adapter in the `pilot` vertical that can consume ROS JSON evidence and build
  `contracts.PilotObservation` snapshots through the existing `ObservationCache` and
  `build_observation_snapshot` APIs.
- Consume `/vision/agent_scene` as the preferred compact source because it already combines scene map,
  object tracks, telemetry, bridge status, task plan, and operator status for agent use.
- Support fallback parsing from the underlying read-only JSON topics used by `agent_scene_node`:
  `/vision/scene_map`, `/vision/object_tracks`, `/vex/telemetry`, `/vex/bridge_status`,
  `/task_plan/current`, and `/operator/status`.
- Map live evidence into contract-owned fields for objective, task phase, robot pose, localization,
  visible objects, visible tags, manipulator state, bridge health, last command/result when available,
  recent failures, and current assertions.
- Add a no-motion CLI entrypoint such as `pilot observe --duration-s 30` that subscribes, builds
  snapshots, prints or writes JSONL observations, and exits cleanly on timeout or interrupt.
- Add deterministic unit tests using JSON fixtures or in-memory payloads, with ROS imports optional or
  isolated so off-robot tests can run without `rclpy`.
- Add manual proof documentation or command output expectations for running the observe-only path on
  the Pi with a live robot connection.
- Preserve the existing `pilot.observation` contract behavior and deterministic sorting/truncation.

## Out Of Scope

- Publishing to `/operator/command`, `/task_plan/request`, `/vex/cmd`, or any other motion-producing
  command topic.
- Executing a skill, waiting for terminal skill feedback, validating LLM decisions, or running the
  full observe-decide-act loop.
- Adding or changing contract schemas in `contracts/`.
- Reworking `robot/ros2-runtime` perception, mapping, bridge, or operator nodes except for minimal
  read-only compatibility fixes required to expose already-existing JSON evidence.
- Hardware motion, skill calibration, delivery recipe behavior, LLM invocation, run logging beyond the
  observe-only snapshot output, or replay-loop orchestration.

## Acceptance

- A `pilot` live-observation API converts representative `/vision/agent_scene` payloads into
  `ObservationCache` and then into contract-valid `PilotObservation` snapshots.
- The adapter also handles missing or stale live inputs by surfacing explicit unknown/stale contract
  values rather than fabricating pose, manipulator, or bridge state.
- Unit tests cover agent-scene mapping for robot pose, localization confidence/age, visible objects,
  visible tags, bridge health, motion/estop state, held-object/manipulator hints, and objective/phase
  defaults.
- Unit tests cover fallback topic mapping for at least scene map, object tracks, telemetry, bridge
  status, and operator status payloads.
- Tests prove the live adapter can be imported and exercised on a development machine without `rclpy`.
- The observe-only CLI can run for a bounded duration, emits one or more `PilotObservation` JSON
  records when live data is present, and exits nonzero with a clear reason when required ROS runtime
  dependencies or topics are unavailable.
- The observe-only path never creates publishers for motion command topics and never sends command
  payloads.
- Manual verification instructions identify the live robot command, expected topics, expected output
  file or stdout shape, and the evidence that no motion was commanded.
- Existing repo gates remain green for affected verticals: `make test`, `make validate`, and
  `make lint`, or their focused `uv run pytest`/`ruff` equivalents where full gates are too broad for
  the slice.

## Constraints

- `contracts/` remains the only vertical that defines schemas; `pilot/` imports `PilotObservation` and
  related component models.
- Live observation code must stay read-only with respect to robot motion and task dispatch.
- The CLI must be bounded by duration or snapshot count and must handle `KeyboardInterrupt` cleanly.
- ROS dependencies must be optional at import time so normal pilot unit tests work off the Pi.
- Snapshot compaction must remain deterministic and compact for repeatable prompts and replay.
- Hardware safety fields must preserve stale bridge ack, stale telemetry, estop, motion-enabled state,
  command rejection/fault state, and missing-data indicators where source payloads provide them.
- Tooling remains `uv` and `ruff`; do not introduce pip/poetry/black/isort/flake8.

## Proposed Decisions

| ID | Status | Decision | Rationale | Rejected / Deferred |
|---|---|---|---|---|
| PM3-001 | closed | Use `/vision/agent_scene` as the primary live input and underlying JSON topics as fallback sources. | `agent_scene_node` already performs the ROS-side compaction needed by an agent-facing observer, while fallbacks keep the adapter useful if that node is not running. | Subscribing directly to raw camera, AprilTag, or serial message types in `pilot`. |
| PM3-002 | closed | Keep ROS integration in an optional live module/CLI path while keeping payload-to-observation mapping testable without `rclpy`. | The Pi needs ROS subscriptions, but development and CI-style unit tests must run on machines without ROS 2 Jazzy installed. | Making all `pilot` imports require ROS packages. |
| PM3-003 | closed | The PM3 proof is observe-only: no command publishers and no task-plan requests. | The milestone explicitly proves live snapshots without commanding motion. | Reusing `observation_proof.py` behavior that publishes `/task_plan/request` during this milestone. |
| PM3-004 | closed | Emit observations as contract JSON or JSONL, not ad hoc proof bundles. | Downstream replay, prompts, assertions, and run logging consume `PilotObservation`, and PM3 should validate that exact boundary. | Writing only a ROS-topic bundle summary that requires later conversion. |
| PM3-005 | closed | Require `--objective` for every live observe run because `build_observation_snapshot` requires an objective. | Live ROS scene evidence does not necessarily carry the task objective, and the operator should make the live proof objective explicit. | Relaxing the observation contract, allowing blank objectives, or hiding the objective behind a default. |
| PM3-006 | closed | Map source field mismatches conservatively and surface unknowns when no reliable source exists. | ROS payloads use names such as `yaw_rad`, `pose_confidence`, and `bridge_status`; contract fields require `heading_rad`, confidence, ages, and structured health. | Inferring precise state from ambiguous or absent source fields. |

## Resolved Questions

- **PM3-O1** The live observe CLI must require `--objective` for every run. There is no implicit
  delivery-task objective default.
- **PM3-O2** Observe output defaults to stdout JSONL unless `--out` is provided.
- **PM3-O3** The manual proof pass threshold is strict: `/vision/agent_scene`, bridge telemetry, and
  object tracks must all be available.

## Approval Gate

Approved by the human in-session. `.ai-sdd/features/pm3-live-observation/pipeline.yaml` and
`slices/*.md` files may be emitted.
