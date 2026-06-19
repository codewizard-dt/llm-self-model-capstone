---
name: wiki-lint
description: Health-check the wiki — find contradictions, stale claims, orphan pages, missing concept pages, missing cross-references, and never-ingested raw sources; fix only with approval
category: researching
model: claude-sonnet-4-6
disable-model-invocation: false
user-invocable: true
---

# Wiki Lint

Audit the wiki for structural and semantic problems. Report findings ranked by severity. **Never fix anything without explicit user approval.**

---

## Step 1: Inventory the wiki tree

Use `Bash` with `find` to build a complete file list:
- `find wiki/ -maxdepth 1 -name "*.md"` (top-level markdown only)
- `find wiki/knowledge/ -type f -name "*.md"` (recursive)
- `find wiki/work/ -type f -name "*.md"` (recursive)
- `find raw/ -type f -not -name ".gitkeep"` (to find never-ingested sources)

## Step 2: Run all checks

### 2.0 Stranded terminal files (HIGH)

For each work family, after reading `lifecycle.md` to identify terminal statuses, find stranded files with a single grep rather than reading every file individually:

```
find wiki/work/<family>/ -maxdepth 1 -name "*.md" \
  -not -name "lifecycle.md" -not -name "index.md" -not -name ".gitkeep" \
  | xargs grep -l "^status: <terminal-status>" 2>/dev/null
```

Run once per terminal status value (or combine values with `grep -lE "^status: (done|trashed)"`). Files not returned by any terminal-status grep are active — do not read them. If the status is in the terminal set for that family (read `lifecycle.md` — do NOT hardcode), report it as a stranded file.

Report format:
```
[HIGH] stranded terminal file — wiki/work/tasks/TASK-014-some-slug.md has status: done but is not in archive/
```

Proposed fix for each: `git mv wiki/work/<family>/<file>.md wiki/work/<family>/archive/<file>.md`

These should have been auto-archived by the skill that set the terminal status.

### 2.1 Family-index drift (HIGH)

For each work family (`requirements`, `decisions`, `roadmaps`, `tasks`, `uat`, `bugs`):
1. Read the family's `index.md`.
2. For each row in the index: verify the linked file exists; use `grep -m1 "^status:" <file>` to read just the status line (not the full file) and confirm it is an active status per that family's `lifecycle.md`.
3. To find active files missing from the index, use:
   ```
   find wiki/work/<family>/ -maxdepth 1 -name "*.md" \
     -not -name "lifecycle.md" -not -name "index.md" -not -name ".gitkeep" \
     | xargs grep -lE "^status: <active-status>" 2>/dev/null
   ```
   Cross-reference results against the index rows to detect omissions — avoid reading full file content.

Report:
- Active item missing from index
- Non-active item still listed in index
- Index row pointing at a missing file

### 2.2 Two-domain violations (HIGH)

- Any file under `wiki/knowledge/` that has a `status:` frontmatter key (stateful artifacts don't belong in knowledge)
- Any file under `wiki/work/` that lacks a `status:` frontmatter key (work artifacts must be status-driven)
- Any file under `wiki/knowledge/` whose name matches a work-family ID pattern (REQ-NNN, TASK-NNN, BUG-NNNN, etc.)

### 2.3 ID / filename mismatch (MEDIUM)

For each file in `wiki/work/`: verify that the `id:` frontmatter value matches the filename prefix (e.g. `id: TASK-014` → filename must start with `TASK-014`). Report mismatches.

### 2.4 UAT ↔ Task cross-link integrity (MEDIUM)

For each UAT file in `wiki/work/uat/`:
- The `task:` frontmatter must point to an existing task file in `wiki/work/tasks/`.
- The referenced task file must have a `uat:` frontmatter link back to this UAT.

Report broken or asymmetric links.

### 2.5 Typed-link vocabulary (LOW)

Extract only the unique relation keywords (not full lines) with:
```
grep -roh '[a-zA-Z_]*::\[\[' wiki/ --include="*.md" | sed 's/::.*//' | sort -u
```
Verify each keyword against the vocabulary in `wiki/conventions.md`. Report unknown keywords.

### 2.6 Orphan pages (LOW)

Pages that appear in the file tree but are not linked from any other wiki page (including `wiki/index.md`). Collect all link targets in a single pass, then diff against the file list:
```
grep -roh '](\.\.\/[^)#"]*\.md\|[^/)#"]*\.md)' wiki/ --include="*.md" \
  | grep -o '[^/(]*\.md' | sort -u
```
Compare the resulting set against the file inventory from Step 1 to find pages with no incoming links.

### 2.7 Never-ingested raw sources (LOW)

List files in `raw/` (excluding `.gitkeep`) that have no matching summary page in `wiki/knowledge/sources/`.

### 2.8 Contradictions (MEDIUM)

Use `Bash` with `grep -rn "Contradiction:" wiki/ --include="*.md"` to find contradiction callouts with file and line number; list them so the user can resolve or confirm they are intentional.

### 2.9 Stale frontmatter (LOW)

Pages where `updated:` is more than 90 days old — these may contain outdated claims.

## Step 3: Report findings

Group by severity (HIGH / MEDIUM / LOW). For each finding:
```
[HIGH] family-index drift — tasks/index.md row for TASK-014 but file status is: done
```

Summarize total counts per severity.

## Step 4: Propose fixes

For each HIGH finding, propose the exact `Edit` operation that would fix it. Do not apply without approval.

Ask: **"Which findings should I fix?"** — wait for the user's reply before making any edits.

## Step 5: Apply approved fixes only

For each approved fix, apply it with a single `Edit` call. After all fixes, append one log entry to `wiki/log.md`:
```
## [YYYY-MM-DD] lint | <N> issues found, <M> fixed
Summary of findings and fixes applied.
```
