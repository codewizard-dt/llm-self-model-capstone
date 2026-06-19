---
name: wiki-query
description: Answer a question from the wiki — locate pages via the index, synthesize a cited answer, and offer to file valuable answers back as new wiki pages
category: researching
model: claude-sonnet-4-6
argument-hint: <question>
disable-model-invocation: false
user-invocable: true
---

# Wiki Query

Answer a question using the wiki as the primary source of truth. If the wiki lacks coverage, say so and suggest `/wiki-ingest` for relevant raw sources. **Never answer from general knowledge alone when a wiki page exists — cite it.**

---

**Question**: $ARGUMENTS

---

## Step 1: Orient via the Index

1. Read `wiki/index.md` in full — it is the home Map of Content.
2. Identify the most relevant sections (Sources, Concepts, Entities, and the Work family indexes if the question is about in-flight work).
3. Read the linked pages. For work items, the family `index.md` files (`wiki/work/<family>/index.md`) list only active items — read those first, then read the individual files needed.

## Step 2: Gather Evidence

Read each relevant page completely before synthesizing. Do not summarize from the first paragraph — check for contradictions, confidence caveats, and supersession markers throughout the page.

If a page cites a `sources:` raw file, read the raw source only if the page's distillation is insufficient.

## Step 3: Synthesize and Cite

Answer the question in 2–5 paragraphs. For each claim, cite the wiki page: `([page title](relative/path/to/page.md))`.

If you found contradictions between pages, surface them explicitly with a `> **Contradiction:**` callout and note which source is more recent.

If the wiki has no coverage at all: say so clearly and suggest:
```
This question isn't covered in the wiki yet.
To add coverage: /wiki-ingest raw/<relevant-source>
```

## Step 4: Offer to File the Answer Back

If the synthesized answer represents **durable, timeless knowledge** (a pattern, a design decision rationale, an entity summary) that doesn't currently exist as its own wiki page, offer:

```
Worth filing this answer as a new wiki page?
Target: wiki/knowledge/concepts/<concept-slug>.md
```

**Never file stateful work artifacts here** — requirements, decisions, tasks, bugs belong in `wiki/work/` and are created by their own skills (`/req-create`, `/decision-create`, etc.).

If the user says yes:
1. Create `wiki/knowledge/concepts/<concept-slug>.md` with proper frontmatter (`id`, `title`, `updated`, `tags`, `sources` if derived from a raw source).
2. Add a typed link `derived_from::[[source-slug]]` if the answer came from an ingested source.
3. Add the new page to the **Concepts** section of `wiki/index.md`.
4. Append to `wiki/log.md`: `## [YYYY-MM-DD] query | <question summary>\nFiled answer as wiki/knowledge/concepts/<slug>.md.`

---

## CRITICAL RULES

1. **Answer from the wiki, not general knowledge** — if the wiki lacks coverage, say so.
2. **The two-domain rule** — filed answers (durable synthesis) go to `wiki/knowledge/`; never file under `wiki/work/`.
3. All citations use relative markdown links to the wiki page, not raw file paths.
4. Do not modify any `wiki/work/` files — this skill is read-only for work artifacts.
