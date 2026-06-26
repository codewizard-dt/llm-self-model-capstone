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

if [[ -z "${PI_HOST:-}" ]]; then
  echo "PI_HOST is required, for example: PI_HOST=raspberrypi.local" >&2
  exit 2
fi

pi_user="${PI_USER:-}"
pi_task_inbox="${PI_TASK_INBOX:-~/vexy/tasks/inbox}"
remote="$PI_HOST"
if [[ -n "$pi_user" ]]; then
  remote="${pi_user}@${PI_HOST}"
fi

ssh "$remote" "mkdir -p \"$pi_task_inbox\""
scp "$task_file" "$remote:$pi_task_inbox/$(basename "$task_file")"
