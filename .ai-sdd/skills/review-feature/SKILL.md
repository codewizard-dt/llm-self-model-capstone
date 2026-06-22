---
name: review-feature
description: Review an ai-sdd changeset against the feature plan and this repo's conventions, and emit a blocking verdict artifact.
---

# Review a feature (VEX self-model factory)

Read `.ai-sdd/artifacts/feature-plan.v1.yaml`, `.ai-sdd/artifacts/changeset.v1.yaml`, and
`.ai-sdd/conventions/<stack>.md` (this slice's vertical). Inspect the diff and the relevant
source/tests.

Write `.ai-sdd/artifacts/review.v1.yaml` with:

- `items`: one entry for **every** plan acceptance id, each `{ id, verdict, notes }` where `verdict`
  is `pass` or `fail`. (The `review.coverage` gate enforces that every acceptance id appears here.)
- `verdict`: `approve` **only** when every item passes AND the conventions/boundary rules are
  satisfied; otherwise `reject`.
- `rework`: required on `reject`, each entry naming the indicted input schema:
  - `target: changeset.v1` for an implementation defect (routes to the implementer).
  - `target: feature-plan.v1` for a plan/acceptance-contract defect (routes to the planner).

You **must reject** if any acceptance item is unmet or any boundary rule is violated — in particular:

- a schema defined outside `contracts`;
- the loop depending on a concrete provider rather than the `TelemetrySource`/`VisionSource`
  interfaces;
- the Generator reading the oracle's hidden parameters (information-separation breach);
- a wrong toolchain (pip/poetry/black/isort/flake8 instead of uv/ruff);
- a frozen contract changed in a way that breaks `.ai-sdd/schemas/examples/*.json`.

Do not approve when an acceptance item is unjudged. `review.structure` is the blocking verdict gate:
all items `pass` + overall `approve`, or the engine routes rework to the producer you indict.
