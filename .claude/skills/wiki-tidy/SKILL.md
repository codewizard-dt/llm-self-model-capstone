---
name: wiki-tidy
description: One-shot wiki cleanup — runs lint, archives terminal items across all families, and rotates the log if overgrown, in sequence with user confirmation at each phase
category: wiki
model: claude-sonnet-4-6
user-invocable: true
---

# Wiki Tidy

Three-phase cleanup for a neglected wiki. Runs in order: **lint → archive → rotate-log**. Each phase summarises its findings and asks for confirmation before making changes. You can stop after any phase.

---

## Phase 1: Lint

Run the full wiki-lint audit by following every step in `/wiki-lint` exactly as written:

1. Inventory the wiki tree using `Bash` with `find`.
2. Run all 10 checks (stranded terminal files, family-index drift, two-domain violations, ID/filename mismatch, UAT↔task cross-links, typed-link vocabulary, orphan pages, never-ingested raw sources, contradictions, stale frontmatter).
3. Report findings grouped by severity (HIGH / MEDIUM / LOW).
4. For each HIGH finding, propose the exact fix.
5. Ask: **"Which findings should I fix? Reply with 'all', specific IDs, or 'none' to skip. Type 'stop' to end wiki-tidy here."**
6. Apply approved fixes. Append one `lint` entry to `wiki/log.md`.

If the user types `stop`, end the skill here. Otherwise continue to Phase 2.

---

## Phase 2: Archive

Run `/wiki-archive` as a cleanup sweep — it scans for any work items with terminal status that were not automatically moved to `archive/` by their originating skill (`uat-auto`, `bug-close`, `task-trash`, etc.). In a healthy wiki this phase finds nothing; it exists as a safety net.

Scan all 6 families in sequence: `tasks`, `uat`, `bugs`, `requirements`, `decisions`, `roadmaps`.

For each family:
1. Read its `lifecycle.md` to confirm the terminal statuses (do NOT hardcode).
2. Find terminal files with a single grep — avoid reading every file:
   ```
   find wiki/work/<family>/ -maxdepth 1 -name "*.md" \
     -not -name "lifecycle.md" -not -name "index.md" -not -name ".gitkeep" \
     | xargs grep -lE "^status: (<terminal1>|<terminal2>)" 2>/dev/null
   ```
   Substitute actual terminal status values from `lifecycle.md`. Files not returned are active — skip without reading.

After scanning all 6 families, show a combined summary:

```
Archive candidates:
  tasks       — N items  (TASK-012 done, TASK-019 trashed, …)
  uat         — N items  (UAT-012 passed, …)
  bugs        — N items
  requirements— N items
  decisions   — N items
  roadmaps    — N items

Total: N items across N families.
```

Ask: **"Archive all, specific families (e.g. 'tasks uat'), or 'none' to skip? Type 'stop' to end wiki-tidy here."**

For each confirmed family:
1. Move each terminal file: `mv wiki/work/<family>/<file> wiki/work/<family>/archive/<file>`
2. Read the file's `id`, `title`, `status`, and `updated` frontmatter.
3. Append a row to `wiki/work/<family>/archive/index.md`:
   ```
   | [[ID]] | Title | final-status | YYYY-MM-DD |
   ```
4. Remove the item's row from the family's active `index.md` if it is still listed there.

After all moves, append one `archive` entry to `wiki/log.md`:
```
## [YYYY-MM-DD] archive | wiki-tidy — N items archived across K families
Moved N terminal items: <comma-separated IDs>.
```

If the user types `stop`, end the skill here. Otherwise continue to Phase 3.

---

## Phase 3: Rotate log

Run `/wiki-rotate-log`:

1. Read `wiki/log.md` and count the total number of lines.
2. If under 500: report the count and ask **"Log has N lines (threshold: 500). Rotate anyway? (yes / no / stop)"**. If `no`, skip this phase; if `stop`, end the skill.
3. If 500 or more: proceed directly.
4. Determine the archive filename: generate a timestamp with `date +%Y_%m_%d_%H%M%S` and use `log-<timestamp>.md` (unique to the second — no collision handling needed).
5. Show the rotation plan and ask **"Proceed with rotation? (yes / no)"**.
6. On confirmation: rename `wiki/log.md` → `wiki/log-<timestamp>.md`, create a fresh `wiki/log.md` with an archive-pointer header and a `rotate` entry as its first log line.

---

## Final report

After all three phases, print a one-paragraph summary:

```
Wiki tidy complete.
  Lint:    N issues found, M fixed.
  Archive sweep: N stranded items moved (0 is healthy).
  Log:     rotated / not rotated (N entries).
```

---

## CRITICAL rules

- Follow each sub-skill's CRITICAL rules exactly — they take precedence over brevity.
- Never move an active item. Never edit archived file content. Never delete anything.
- Always confirm with the user before applying changes in each phase.
- `stop` at any phase prompt ends the skill immediately without proceeding further.
