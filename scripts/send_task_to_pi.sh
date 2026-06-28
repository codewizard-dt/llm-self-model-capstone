#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  source "$REPO_ROOT/.env"
  set +a
fi

if [[ "$#" -ne 1 ]]; then
  echo "usage: $0 path/to/task.json" >&2
  exit 2
fi

task_file="$1"
if [[ ! -f "$task_file" ]]; then
  echo "task file does not exist: $task_file" >&2
  exit 2
fi
if [[ "$task_file" != *.json ]]; then
  echo "task file must be JSON (*.json): $task_file" >&2
  exit 2
fi

PYTHONPATH="$REPO_ROOT/contracts/src${PYTHONPATH:+:$PYTHONPATH}" uv run --project "$REPO_ROOT/contracts" python - "$task_file" <<'PY'
import json
import sys
from pathlib import Path

from contracts.task_envelope import TaskEnvelope

path = Path(sys.argv[1])
try:
    TaskEnvelope.model_validate(json.loads(path.read_text()))
except Exception as exc:
    print(f"task file does not match TaskEnvelope JSON: {exc}", file=sys.stderr)
    raise SystemExit(2) from exc
PY

if [[ -z "${VEXY_HOST:-}" ]]; then
  echo "VEXY_HOST is required, for example: VEXY_HOST=vexy.local" >&2
  exit 2
fi

vexy_user="${VEXY_SSH_USER:-}"
vexy_task_inbox="${VEXY_TASK_INBOX:-/vexy/tasks/inbox}"
remote="$VEXY_HOST"
if [[ -n "$vexy_user" ]]; then
  remote="${vexy_user}@${VEXY_HOST}"
fi

if [[ -n "${VEXY_SSH_PW:-}" ]]; then
  export SSHPASS="$VEXY_SSH_PW"
  sshpass -e ssh "$remote" "mkdir -p \"$vexy_task_inbox\""
  sshpass -e scp "$task_file" "$remote:$vexy_task_inbox/$(basename "$task_file")"
  telemetry_dir="$(sshpass -e ssh "$remote" "ls -td /home/vexy/telemetry/run-* 2>/dev/null | head -n 1" || true)"
else
  ssh "$remote" "mkdir -p \"$vexy_task_inbox\""
  scp "$task_file" "$remote:$vexy_task_inbox/$(basename "$task_file")"
  telemetry_dir="$(ssh "$remote" "ls -td /home/vexy/telemetry/run-* 2>/dev/null | head -n 1" || true)"
fi

echo "sent task: $(basename "$task_file")"
if [[ -n "$telemetry_dir" ]]; then
  echo "telemetry output: $telemetry_dir"
else
  echo "telemetry output: no /home/vexy/telemetry/run-* directory found yet"
fi
