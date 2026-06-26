# Operator Task Outline Sequencing Plan

Research and planning on 2026-06-26 found that `OperatorNode._tick_task_outline()` is the right non-blocking ROS timer-driven shape, but standalone timed primitives (`grab`, `lift`, `release`) still advance too early because `Operator._timed_claw()` returns `OperatorResult(True, "<cmd>_sent")` immediately after publishing the command.

Recommended implementation pattern:
- Keep completion waiting in `node.py` runner-owned state, not in blocking sleeps and not by changing ad-hoc `/operator/command` semantics.
- Add a `TimedPrimitiveStep` dataclass and extend `TaskOutlineRun` with `pending_timed_primitive`.
- Special-case `grab`/`lift`/`release` in `_tick_task_outline()` before generic method invocation.
- On first tick: call the operator method once, record command seq/duration/start/deadline/result, and do not advance.
- On later ticks: do not resend; poll deadline, bridge fault/ack if available, and telemetry predicate if implemented.
- Advance only after duration+settle/ack predicate succeeds; fail early on bridge fault/rejection or global per-step timeout.
- Leave `_timed_claw()` immediate-success for direct/non-outline callers unless product requirements change.

Test plan: add focused tests in `robot/ros2-runtime/tests/test_operator.py` for in-order deliver-ball execution, timed kwargs preservation, timed primitive wait/no-resend, failure stop, exception details, timeout details, and timeout reset per step. Update fixture tests if `task_deliver_ball.json` is restored/changed.