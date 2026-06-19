---
name: wiki-ingest
description: Process a source from raw/ into the wiki — write a summary page, update affected entity and concept pages, and record the ingest in the index and log
category: researching
model: claude-sonnet-4-6
argument-hint: <raw-file-path>
disable-model-invocation: false
user-invocable: true
---

# Wiki Ingest

Integrate a raw source document into the persistent wiki. The source is read once, distilled, and woven into the existing page network — summary page, entity pages, concept pages, index, and log — so the wiki compounds rather than the source sitting unprocessed.

---

**Source to ingest**: $ARGUMENTS

---

## Step 1: Read the Source Fully

1. Resolve `$ARGUMENTS` to a file under `raw/`. If the path is ambiguous or missing, use `Bash` with `find raw/ -iname "*<pattern>*"` to locate candidates and confirm with the user.
2. Read the source **in full** with `Read` — never summarize from a partial read. For long files, read in sequential chunks until complete.
3. Note the source type (article, spec, notes, data) and its date if discernible — recency matters when claims conflict.

## Step 2: Discuss Key Takeaways

Before writing anything, present a brief summary to the user:

- 3–7 bullet key takeaways from the source
- Which existing wiki pages this source will touch (read `wiki/index.md` to determine this)
- Any apparent **contradictions** with existing wiki pages (see Rules below)

Keep this short — it is a checkpoint, not a report. Incorporate any emphasis or corrections the user offers.

## Step 3: Write or Update the Summary Page

1. Use `Bash` with `ls wiki/knowledge/sources/` to check whether a summary page for this source already exists.
2. Write (or update) a summary page in `wiki/knowledge/sources/` with a **kebab-case filename** derived from the source title (e.g. `raw/Some Article.md` → `wiki/knowledge/sources/some-article.md`). Create the directory if it does not exist.
3. Frontmatter:
   ```yaml
   ---
   id: some-article
   title: Some Article
   updated: YYYY-MM-DD
   sources:
     - ../../raw/some-article.md
   tags: []
   ---
   ```
4. Body: 2–4 paragraph distillation. Bold key claims. Add typed links to entities and concepts mentioned: `rel::[[Entity Name]]` (e.g. `derived_from::`, `uses::`, `relates_to::`).

## Step 4: Update or Create Entity Pages

For each person, organisation, tool, or component mentioned significantly in the source:

1. Determine the entity sub-type: `people`, `organisations`, `tools`, or `components` (components = this project's own modules/skills/scripts).
2. Use `Bash` with `ls wiki/knowledge/entities/<sub-type>/` to check for an existing page.
3. **Existing page**: add a new section or bullet noting what this source says. Never remove existing content. Use a `> **Contradiction:**` callout if the new claim conflicts.
4. **New page**: create `wiki/knowledge/entities/<sub-type>/<entity-slug>.md` with frontmatter:
   ```yaml
   ---
   id: entity-slug
   title: Entity Name
   aliases: [Alternative Name]
   updated: YYYY-MM-DD
   sources:
     - ../../../raw/some-article.md
   tags: []
   ---
   ```
   Body: 1–2 paragraphs with key facts. Add typed links.

## Step 5: Update or Create Concept Pages

For each pattern, idea, convention, or recurring theme the source illuminates:

1. Use `Bash` with `ls wiki/knowledge/concepts/` to check for an existing page.
2. **Existing**: extend or cross-link; add contradiction callout if needed.
3. **New**: create `wiki/knowledge/concepts/<concept-slug>.md` with frontmatter (`id`, `title`, `updated`, `sources`, `tags`) and a focused distillation.

## Step 6: Update the Home Index

In `wiki/index.md`:
- Under **Sources**: add `- [Source Title](knowledge/sources/source-slug.md) — one-line summary` (knowledge pages are listed in the home index; work items are not).
- Under the relevant entity sub-type: add or update the entity listing.
- Under **Concepts**: add any new concept pages.

Use a single `Edit` call per section.

## Step 7: Append to the Log

Append to `wiki/log.md`:
```
## [YYYY-MM-DD] ingest | <source title>
Ingested from raw/<filename>. Key claims: [2–3 bullet summary]. [N] entity pages touched, [M] concept pages touched.
```

---

## CRITICAL RULES

1. `raw/` is **immutable** — never create, modify, move, or delete files under `raw/`.
2. The **two-domain rule** — timeless synthesis belongs under `wiki/knowledge/`; never file a source summary or concept page under `wiki/work/`.
3. **Flag contradictions explicitly** — add a `> **Contradiction:**` callout citing both the new source and the conflicting page; never silently overwrite.
4. Use **relative links** from the file's location: a page at `wiki/knowledge/sources/` reaches `raw/` as `../../raw/`, reaches concepts as `../concepts/`, reaches entities as `../entities/`.
5. Add `id:` and `aliases:` frontmatter to every page you create or touch.
6. Use typed links (`derived_from::`, `uses::`, `relates_to::`, `contradicts::`) wherever a link has a meaning — see `wiki/conventions.md` for the full vocabulary.
7. **Work artifacts** (requirements, decisions, tasks, bugs) are never modified by this skill — only knowledge pages and the home index.
