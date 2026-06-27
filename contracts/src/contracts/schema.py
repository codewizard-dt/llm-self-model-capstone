"""Generate the committed JSON Schemas from the pydantic models.

`make schema` invokes this as the single generator: it writes
`schemas/contract_line.json` (byte-stable vs the F1-committed file),
`schemas/self_model.json`, and `schemas/score_contract.json` (the typed `score`
task line), using identical `json.dumps` formatting.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from contracts.contract_line import ContractLine, ScoreContractLine
from contracts.control_command import AckLine, ControlLine
from contracts.pilot import (
    PilotAssertion,
    PilotDecision,
    PilotObservation,
    PilotSkillCommand,
    PilotTraceRecord,
)
from contracts.self_model import SelfModel
from contracts.task_envelope import TaskEnvelope, TaskOutline

SCHEMAS = {
    "contract_line.json": ContractLine,
    "self_model.json": SelfModel,
    "score_contract.json": ScoreContractLine,
    "control_command.json": ControlLine,
    "ack_line.json": AckLine,
    "task_outline.json": TaskOutline,
    "task_envelope.json": TaskEnvelope,
    "pilot_skill_command.json": PilotSkillCommand,
    "pilot_observation.json": PilotObservation,
    "pilot_assertion.json": PilotAssertion,
    "pilot_decision.json": PilotDecision,
    "pilot_trace_record.json": PilotTraceRecord,
}


def _render(model: type) -> str:
    if hasattr(model, "model_json_schema"):
        schema = model.model_json_schema()
    else:
        schema = TypeAdapter(model).json_schema()
    return json.dumps(schema, indent=2, sort_keys=True)


def main() -> None:
    schemas_dir = Path(__file__).resolve().parents[2] / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    for filename, model in SCHEMAS.items():
        (schemas_dir / filename).write_text(_render(model) + "\n")


if __name__ == "__main__":
    main()
