#!/usr/bin/env bash
set -euo pipefail

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
  echo "task file must be a .json file: $task_file" >&2
  exit 2
fi

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
  sshpass -p "$VEXY_SSH_PW" ssh "$remote" "mkdir -p \"$vexy_task_inbox\""
  sshpass -p "$VEXY_SSH_PW" scp "$task_file" "$remote:$vexy_task_inbox/$(basename "$task_file")"
else
  ssh "$remote" "mkdir -p \"$vexy_task_inbox\""
  scp "$task_file" "$remote:$vexy_task_inbox/$(basename "$task_file")"
fi
