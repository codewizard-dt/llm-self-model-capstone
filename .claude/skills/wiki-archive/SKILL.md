---
name: wiki-archive
description: Cleanup tool — sweep for work items with terminal status that were not auto-archived by their originating skill, and move them to archive/
category: wiki
model: claude-sonnet-4-6
---

# Wiki Archive

> **Recovery sweep.** Skills that set terminal statuses (`uat-auto`, `uat-skip`, `bug-close`, etc.) now automatically move files to `archive/` at the time of completion. This skill finds any items that were missed — for example, items from before the auto-archive update, or edge cases where the originating skill didn't complete the move. In a healthy wiki, this skill finds nothing to do.

Move terminal work items from a family directory into `archive/` to reduce directory clutter. **Terminal items only** — items with active statuses are never moved. Safe because links use stable IDs, not paths.

---

## Usage

```
/wiki-archive [family]
```

`family` — one of `tasks`, `uat`, `bugs`, `requirements`, `decisions`, `roadmaps`. Omit to show a count summary across all families without moving anything.

---

## Step 1: Determine scope

If a family was specified, process only that family. Otherwise, scan all 6 families and report terminal item counts, then ask the user which families to archive.

For each family to process, read its `lifecycle.md` to confirm the **terminal statuses** for that family:
- **tasks**: `done`, `trashed`
- **uat**: `passed`, `skipped`, `trashed`
- **bugs**: `closed`, `wontfix`, `duplicate`, `cannot-reproduce`
- **requirements**: `retired`
- **decisions**: all decisions in the group are `accepted` or `superseded`
- **roadmaps**: `done`

Do NOT hardcode these — read `lifecycle.md` to confirm them before moving anything.

## Step 2: Identify terminal items

After reading `lifecycle.md` to determine terminal statuses, find terminal files with a single grep rather than reading every file:
```
find wiki/work/<family>/ -maxdepth 1 -name "*.md" \
  -not -name "lifecycle.md" -not -name "index.md" -not -name ".gitkeep" \
  | xargs grep -lE "^status: (done|trashed)" 2>/dev/null
```
Substitute the actual terminal status values from `lifecycle.md` into the pattern. For decisions, use per-block status patterns. Files not returned are active — skip them without reading.

If the move list is empty, report "No terminal items found in `<family>/`" and stop.

## Step 3: Confirm with the user

Show the move list:
```
Ready to archive N items from wiki/work/<family>/:
  - TASK-023-some-slug.md   (status: done)
  - TASK-031-other.md       (status: trashed)

This moves them to wiki/work/<family>/archive/. Links using [[TASK-023]] remain valid.
Proceed? (yes / skip)
```

Wait for confirmation before moving.

## Step 4: Move files and update archive/index.md

For each confirmed file:
1. Use `Bash` with `mv` to move the file: `mv wiki/work/<family>/<file> wiki/work/<family>/archive/<file>`
2. Read the file's `id`, `title`, `status`, and `updated` frontmatter fields.
3. Append a row to `wiki/work/<family>/archive/index.md`:
   ```
   | [[ID]] | Title | final-status | YYYY-MM-DD |
   ```
   where the date is today's date.

Do NOT edit the moved file itself — its frontmatter and content are preserved exactly.

## Step 5: Update wiki/log.md

Append one entry:
```
## [YYYY-MM-DD] archive | <family> — N items archived
Moved N terminal items from wiki/work/<family>/ to wiki/work/<family>/archive/. IDs: TASK-023, TASK-031, …
```

## Step 6: Report

Print a summary of what was moved. If any files were skipped (e.g., active status found unexpectedly), list them explicitly.

---

## CRITICAL rules

- **Never move an active item.** If a file's status is not in the terminal set for its family, skip it and warn.
- **Never edit content** of moved files — only the location changes.
- **Never delete** — archiving is moving, not deleting.
- **`archive/index.md` is append-only** — only add rows, never remove or edit existing rows.
- The `archive/` directory already exists in every family — do not create it.
