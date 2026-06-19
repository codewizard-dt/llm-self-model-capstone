---
name: wiki-rotate-log
description: Rotate wiki/log.md into a timestamped archive file when it grows past ~500 lines; create a fresh log.md with an archive-pointer header
category: wiki
model: claude-sonnet-4-6
---

# Wiki Rotate Log

Rotate `wiki/log.md` into a timestamped archive file (`log-YYYY_MM_DD_HHMMSS.md`) when it exceeds ~500 lines. Create a fresh `wiki/log.md` with an archive-pointer header. **Never truncate** — all content moves to the timestamped file.

The timestamp (to the second) makes every archive filename unique by construction, so repeated rotations never collide — no half-year or sequence-suffix logic needed.

---

## Step 1: Check current log size

Read `wiki/log.md`. Count the total number of lines.

- If line count is **under 500**: report the count and warn the user: "The log has N lines — rotation is recommended at ~500. Proceed anyway? (yes / no)"
- If line count is **500 or more**: proceed directly.

## Step 2: Determine the archive filename

Generate a timestamp to the second using Bash: `date +%Y_%m_%d_%H%M%S`.

The archive filename is `log-<timestamp>.md` — e.g. `log-2026_06_14_153012.md`. Because the timestamp is unique to the second, no collision check or suffix logic is needed.

## Step 3: Confirm with the user

Show the plan:
```
Log rotation plan:
  Current: wiki/log.md (N lines)
  Archive: wiki/log-2026_06_14_153012.md
  New log: wiki/log.md (empty, with archive pointer)

The existing log.md will be renamed — no content is deleted.
Proceed? (yes / no)
```

Wait for confirmation.

## Step 4: Rotate

1. **Rename** `wiki/log.md` → `wiki/log-<timestamp>.md` using Bash `mv`.
2. **Check** for any existing archive pointers in the old log (lines starting with `> Archives:`). If present, carry them forward into the new log.
3. **Create** a new `wiki/log.md` with:

```markdown
# Wiki Log

Append-only record of wiki operations — ingests, queries filed back, lint passes, scaffolding. **Never edit existing entries**; only append new ones at the bottom.

Entry format (consistent prefix keeps the log greppable — `grep "^## \[" log.md | tail -5`):

```
## [YYYY-MM-DD] <op> | <subject>
1–3 sentences on what happened.
```

Operations: `scaffold`, `ingest`, `query`, `lint`, `decision`, `task`, `bug`, `requirement`, `roadmap`, `archive`, `rotate`.

> Archives: [2026_06_14_153012](log-2026_06_14_153012.md)

---

## [YYYY-MM-DD] rotate | log.md rotated — N lines archived to log-<timestamp>.md
Previous log archived to log-<timestamp>.md. Fresh log started.
```

Replace `<timestamp>` with the actual timestamp and `N` with the entry count. The `[YYYY-MM-DD]` date prefix on the rotation entry stays date-only (matching all other log entries) — only the archive filename carries the full timestamp. If there were prior archive pointers, add them to the `> Archives:` line separated by ` · `.

## Step 5: Report

Confirm rotation is complete:
```
Done. wiki/log.md rotated:
  - N lines moved to wiki/log-2026_06_14_153012.md
  - New wiki/log.md created with archive pointer
```

---

## CRITICAL rules

- **Never delete** any log content — rotation is renaming + creating a new file.
- **Never edit** the archived file after renaming.
- The `> Archives:` header line in the new `log.md` must link to ALL prior archive files, not just the most recent one.
- The first entry in the new `log.md` must be the rotation event itself.
