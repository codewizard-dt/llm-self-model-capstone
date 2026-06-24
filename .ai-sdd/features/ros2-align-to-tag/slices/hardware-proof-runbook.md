# Slice: hardware-proof-runbook

| Field | Value |
|---|---|
| Feature | ros2-align-to-tag |
| Stack | coprocessor |
| Depends on | mcap-contract-export |

## What this slice delivers

Make the final proof surface unambiguous for humans and future agents: a runbook and lightweight smoke scripts that separate camera proof, tag proof, serial ack proof, bounded motion proof, closed-loop `AlignToTag` proof, bag capture, and contract JSONL export.

## Scope

- Update `robot/ros2-runtime/docs/RUNBOOK.md` and/or add a focused proof runbook for this feature.
- Include direct-IP SSH fallback because mDNS has been flaky on `vexy`.
- Define where proof artifacts are saved under the repo or Pi runtime workspace.
- Provide commands for:
  - ROS/Jazzy base check
  - camera image proof
  - nonzero camera info proof
  - rectified image proof
  - AprilTag pose proof
  - bridge ack proof
  - bounded motion-on-blocks proof
  - `AlignToTag` action proof
  - MCAP recording
  - JSONL export
  - contract validation
- Add a proof manifest template that records exact commands, timestamps, host/IP, serial device, bag path, JSONL path, and pass/fail notes.
- Keep status language honest: a camera proof is not serial proof; serial ack is not motion proof; motion on blocks is not navigation proof.

## Acceptance

1. A human can follow the runbook from a fresh shell on the Pi and know which proof gate they are running.
2. Every proof command has a named expected output or saved artifact.
3. The runbook tells the operator when to use the IP address instead of `vexy.local`.
4. The proof manifest template distinguishes pass, fail, blocked, and not-run states.
5. The final checklist cannot mark `AlignToTag` complete unless camera, tag, serial ack, motion, MCAP, and contract JSONL gates are all accounted for.
6. Static/local checks for scripts/docs pass where available.

## Out of scope

- Claiming live hardware success without a current run.
- Long-running autonomous tasks.
- Replacing the older `robot/pi-runtime` fallback docs.
