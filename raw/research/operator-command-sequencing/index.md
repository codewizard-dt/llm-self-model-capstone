---
topic: "$research how to make sure that the operator executes all commands in sequence, waiting for each one to finish before the next"
slug: operator-command-sequencing
researched: 2026-06-26
sources: [./sources.md]
---

# Research: Operator Command Sequencing

> The operator should treat an outline as a single active run with one current step, not as a loop over method calls. The current timer-driven wrapper is the right base for ROS 2 because it keeps subscriptions, timers, telemetry, vision, and acks moving while a step is in progress. It is not yet sufficient for every outline command: `move_to_tag` and `pickup_ball` are stateful and completion-aware, but `grab`, `lift`, and `release` still return success immediately after command send. The recommended fix is to make every outline step completion-aware through explicit per-method step policies and either telemetry/ack predicates or method-level state machines.

## Research Questions
- What does the current operator runner do to preserve ordered task execution?
- Which operator methods already expose true completion versus merely "command sent"?
- What ROS 2/rclpy constraints shape the design?
- Which sequencing approach best fits this codebase without blocking ROS callbacks?
- What tests should prove the operator waits before advancing?

## Current State (Codebase)

`OperatorNode.__init__` creates normal ROS subscriptions for TF, vision, ack, telemetry, bridge status, and ad-hoc commands, plus timers for controller ticks, task-outline ticks, status publication, and inbox polling [S1]. This means the task runner must avoid long blocking loops; the ROS executor needs callbacks to return so fresh sensor state can arrive.

`OperatorNode._run_task_outline` now starts a `TaskOutlineRun` instead of executing all outline methods synchronously. It records the source, method plan, current step index, and step start time [S2].

`OperatorNode._tick_task_outline` drives the current step on a timer. It calls only the current method, advances on `OperatorResult.success`, stays on the same step if `result.reason in IN_PROGRESS_REASONS`, and fails the run on timeout or terminal failure [S3].

`Operator.pickup_ball` is already a method-level state machine. It progresses through idle/opening/approaching/closing/done phases and returns in-progress reasons such as `opening_claw`, `moving_to_ball`, `closing_claw`, and `grab_not_confirmed`; it returns success only with `ball_grabbed` [S4].

`Operator.move_to_tag` is completion-aware. It repeatedly emits drive/turn/arm commands while returning `moving_to_tag`, `tag_not_visible`, or `raising_arm_for_tag`, and returns success only once AprilTag distance, yaw, and lateral tolerances are satisfied [S5].

The gap is `Operator._timed_claw`: `grab`, `lift`, and `release` call `_timed_claw`, which sends a primitive command and immediately returns `OperatorResult(True, "<cmd>_sent")` [S6]. That preserves ordering only at "sent to bridge" granularity, not "claw/arm operation completed" granularity.

`RosCommandSink.send_command` increments and publishes command packets with a sequence number, and `_on_ack` records the latest ack sequence from `/vex/ack` [S7][S8]. The code has enough raw material to distinguish "sent" from "acknowledged", but it does not yet attach a specific outline step to an ack or wait on a command-completion predicate.

The current regression tests prove the new wrapper does not advance from `pickup_ball` to the later bin `move_to_tag`, `lift`, or `release` while pickup returns in-progress reasons, and that timeout stops the run before those later steps [S9][S10]. Those tests cover the previously reported failure class, but not primitive `grab`/`lift`/`release` completion.

## Key Findings

1. The correct architecture is a non-blocking task-runner state machine, not `async def` or a blocking loop. ROS 2 docs define executors as responsible for callback execution, and callback groups as the mechanism for concurrency rules [S11]. The current timer-based runner matches that model.

2. Blocking inside a callback is a known ROS 2 failure mode when the blocked operation needs another callback to complete. ROS docs describe deadlock when a timer callback waits for a service response whose done callback cannot run in the same mutually exclusive group [S12]. By analogy, a task-outline callback must not sleep-wait for telemetry, vision, or acks; it should return and let later timer ticks re-evaluate state.

3. Reason-string-based in-progress detection works as a tactical patch but is brittle. Today, the wrapper has to know every retryable `OperatorResult.reason`. A safer boundary is for `OperatorResult` or a step-policy layer to expose structured status, for example `RUNNING`, `SUCCEEDED`, `FAILED`, plus `retryable` and `deadline_s` metadata. This is an inference from the current `OperatorResult` shape, which contains only `success` and `reason` for status [S13].

4. "Command sent" is not equivalent to "operation complete." `_timed_claw` immediately returns success after publishing the command [S6]. Therefore an outline containing `release` followed by `move_to_tag` can still advance before the release duration has elapsed, even with the new outline wrapper.

5. The sequencing guarantee should be stated as: exactly one outline step is active; a later step may not be invoked until the current step reaches a terminal success state; terminal failure or timeout aborts the run; in-progress steps return control to ROS between attempts.

## Constraints

- The node already relies on ROS timers/subscriptions for TF, vision, object detections, VEX acks, telemetry, bridge state, status, and inbox polling [S1].
- Live state changes needed by operator methods arrive through callbacks, so the outline runner must keep callbacks short [S11][S12].
- Method plans are contract-validated operator method tuples, not arbitrary primitive commands.
- Existing operator methods already encode some domain state internally (`pickup_ball`, `move_to_tag`), so a solution should not throw that away.
- The V5 bridge currently exposes ack sequence and telemetry, but the operator does not yet record per-step pending sequence/completion state [S7][S8].
- `raw/` files become immutable project sources after this report is written; follow-up wiki synthesis should ingest rather than edit this file [S14].

## Solution Comparison

| Criteria | Option A: Current Reason-Set Wrapper | Option B: Step Policy Layer | Option C: ROS Action Server |
|----------|--------------------------------------|-----------------------------|-----------------------------|
| Approach | Keep `_tick_task_outline`; maintain `IN_PROGRESS_REASONS`; advance on success. | Keep `_tick_task_outline`, but add explicit per-method policies with `start`, `poll`, `completion_predicate`, `timeout`, and terminal classification. | Model each high-level operator method or whole outline as ROS actions with feedback/result semantics. |
| Pros | Already mostly implemented; minimal code. | Best fit for current code; handles one-shot primitive commands; avoids blocking; testable without new ROS graph surface. | Native long-running-operation abstraction; explicit feedback/result/cancel. |
| Cons | Brittle reason strings; does not solve `_timed_claw` completion; hidden per-method semantics. | Some new orchestration code; needs careful tests for each method class. | More invasive; more moving parts; likely overkill before the operator protocol is stable. |
| Complexity | Low | Medium | High |
| Dependencies | None | None | ROS action interfaces/client-server plumbing |
| Codebase fit | Partial | Strong | Medium later, weak now |
| Maintenance | Easy until reason names drift | Clearer long-term | Higher operational and test cost |

## Recommendation

Use Option B: keep the timer-driven `TaskOutlineRun`, but replace reason-only sequencing with explicit step policies.

Implementation outline:

1. Add a structured step status boundary:
   - `StepStatus.RUNNING`
   - `StepStatus.SUCCEEDED`
   - `StepStatus.FAILED`
   - `StepStatus.TIMED_OUT`

2. Keep one active `TaskOutlineRun` and one active step:
   - `source_name`
   - `method_plan`
   - `step_index`
   - `step_started_s`
   - `attempt_count`
   - `pending_command_seq`
   - `last_result`
   - optional `phase` or `wait_until_s`

3. Make stateful operator methods continue to own domain logic:
   - `move_to_tag` remains polled until `arrived`.
   - `pickup_ball` remains polled until `ball_grabbed` or `grab_failed`.

4. Add step policies for one-shot timed commands:
   - On first tick for `grab`, `lift`, or `release`, send the command once and record `pending_command_seq`, `duration_ms`, and `wait_until_s`.
   - On later ticks, do not resend the command. Poll ack/telemetry/time.
   - Treat success as either: ack observed and duration plus settle elapsed, or telemetry predicate satisfied.
   - Treat failure as bridge fault, timeout, or impossible telemetry.

5. Separate three concepts in events/results:
   - `command_sent`
   - `step_in_progress`
   - `step_succeeded` / `step_failed`

6. Replace `IN_PROGRESS_REASONS` with one of:
   - a structured `OperatorResult.status`, or
   - a central `classify_operator_result(method_name, result)` table that returns `RUNNING/SUCCEEDED/FAILED`.

7. Extend tests:
   - `release` does not advance to the next outline step until `duration_ms + settle` or completion predicate.
   - `lift` does not advance until arm telemetry or timeout.
   - `grab` does not advance until close duration/settle and optional object telemetry.
   - `pickup_ball` success and timeout tests stay.
   - bridge fault/estop aborts the active outline.
   - a second inbox file is not consumed while `_task_file_active` and `_task_outline_run` are active.

Risks and mitigations:

- Risk: repeated timer ticks resend one-shot commands. Mitigation: step policy must distinguish `start` from `poll` and record `pending_command_seq`.
- Risk: duration-only waits are not real completion. Mitigation: prefer telemetry predicates where available; use duration as fallback.
- Risk: reason strings drift. Mitigation: structured status or a classification table with tests for every operator method.
- Risk: a method never reaches success. Mitigation: per-method timeout plus failure event and run abort.
- Risk: blocking callback regression. Mitigation: no sleeps or synchronous waits inside `_tick_task_outline`; every in-progress path returns immediately.

## Next Steps

- Create an implementation task: `/task-add Add explicit task-outline step policies so grab/lift/release wait for command completion before advancing`.
- If the team wants a durable architectural record, create a decision: `/decision-create Choose task-outline sequencing model: step policy state machine vs ROS action server`.
- Use the `wiki-ingest` skill on `raw/research/operator-command-sequencing/index.md` to synthesize this research into the knowledge base.
