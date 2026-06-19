---
name: research
description: Deep research on a topic using codebase analysis, library docs, and web search — writes the report plus its primary sources to raw/research/<slug>/
category: researching
model: claude-sonnet-4-6
effort: high
argument-hint: <topic or question to research>
disable-model-invocation: false
user-invocable: true
---

# Research

Perform comprehensive research on a topic by combining codebase analysis, library documentation, and web research. Produce actionable findings with implementation suggestions, and **persist the report together with its primary sources** as ground-truth files under `raw/research/<slug>/` so they can later be `/wiki-ingest`ed into the knowledge base.

---

**Research Topic**: $ARGUMENTS

---

## Phase 1: Understand the Research Question

1. **Parse the topic**: Extract the core question, scope, and any constraints from `$ARGUMENTS`
2. **Identify research dimensions**:
   - What needs to be understood about the **current codebase**? (existing patterns, dependencies, relevant code)
   - What **external knowledge** is needed? (libraries, best practices, architectural patterns)
   - Are there **multiple possible approaches** to compare?
3. **Formulate specific research questions** — break the topic into 3-5 concrete questions to answer
4. **Derive a slug & output directory** — lowercase the topic, spaces → hyphens, strip special characters, and trim to a short stable identifier (e.g. "Choosing a job queue for the API" → `job-queue`). The output directory is `raw/research/<slug>/`. **A prior run's files are immutable ground truth — never overwrite or edit them.** Writing new files into `raw/research/` is allowed; if a target file (`index.md` / `sources.md`) already exists, write the next free numeric sibling instead — `index-2.md`, then `index-3.md`, and so on. **The new `-N` file must not repeat data already present in the prior file(s)** — read the existing report first and capture only what is new, changed, or contradicts it, cross-referencing the prior file for everything unchanged. Treat existing research as read-only context you may cite, not as a file to update in place.

> **Collect primary sources as you go.** Throughout Phases 2–3, keep a running register of every primary source you actually rely on — its type (codebase / web), its locator (file path + symbol, or URL), the date accessed, and the specific excerpt(s) or facts it contributed. You will write this register out in Phase 5. A "primary source" is the document you drew the claim from, not your paraphrase of it.

---

## Phase 2: Internal Research (Codebase Analysis)

Use standard file tools to understand the current state of the codebase as it relates to the topic.

### 2a. Project Context

- Read `CLAUDE.md` and any project documentation files for constraints, conventions, and architectural decisions
- Review `wiki/work/tasks/` for any related active or completed tasks
- Check `wiki/index.md` to understand what the wiki already covers on this topic

### 2b. Code Exploration

- **Structure**: Use `Bash` with `find <dir> -type f -name "*.py"` (or appropriate extension) to survey; use `Read` on key files only
- **Dependencies**: Use `grep -rl --include="*.py" "<import-pattern>" .` to get file lists, then `Read` only the relevant files — never grep without `--include` to avoid scanning binaries
- **Patterns**: Use `grep -rn --include=<ext> "<symbol>"` to locate functions/classes with line numbers, then `Read` the specific offset rather than the whole file
- **Configuration**: `Read` specific config files directly (`package.json`, `pyproject.toml`, etc.) rather than grepping for them

### 2c. Identify Constraints

Document what already exists that any solution must work with:
- Existing dependencies and their versions
- Established patterns and conventions
- Integration points and data flow
- Testing approach and quality gates

---

## Phase 3: External Research (Web)

### 3a. Library Documentation

For each relevant library or framework identified, use `WebSearch` to find official documentation, then `WebFetch` to read specific doc pages:

1. **Search for docs**: `WebSearch("<library> official documentation <version>")`
2. **Fetch specific pages**: `WebFetch(<doc URL>)` for API references, configuration guides, migration notes
3. **Repeat** with refined queries if initial results are insufficient

Focus on:
- API syntax and usage patterns
- Configuration options
- Migration guides and version-specific features
- Known limitations and edge cases

### 3b. Web Research

Use `WebSearch` for:
- Best practices and recommended approaches (e.g., `"<topic> best practices 2025"`)
- Common pitfalls and failure modes (e.g., `"<topic> common mistakes"`)
- Comparison of alternative solutions (e.g., `"<library A> vs <library B>"`)
- Community recommendations and real-world experience (e.g., `"<topic> production experience"`)
- Performance benchmarks and scalability considerations

**Sequential searches**: run one at a time; fetch promising results with `WebFetch` before moving to the next search.

### 3c. Package Discovery

When the research involves choosing packages or tools:

1. **Search for candidates**: Use `WebSearch` to find popular options (e.g., `"best <category> library for <framework> 2025"`)
2. **Evaluate each candidate** against these criteria:
   - Maintenance status (last release, open issues, bus factor)
   - Community adoption (downloads, GitHub stars, Stack Overflow presence)
   - Bundle size and performance impact
   - TypeScript support and type quality
   - Compatibility with existing stack
3. **Verify documentation**: Use `WebFetch` to read docs pages for top candidates

---

## Phase 4: Synthesis & Recommendations

### 4a. Summarize Findings

Present a clear, structured summary:

1. **Current State**: What exists in the codebase today relevant to this topic
2. **Key Findings**: Most important discoveries from research (with sources)
3. **Constraints**: What any solution must account for

### 4b. Solution Comparison (if multiple approaches exist)

For each viable approach, present:

| Criteria | Option A | Option B | Option C |
|----------|----------|----------|----------|
| **Approach** | Brief description | Brief description | Brief description |
| **Pros** | Key advantages | Key advantages | Key advantages |
| **Cons** | Key drawbacks | Key drawbacks | Key drawbacks |
| **Complexity** | Low/Medium/High | Low/Medium/High | Low/Medium/High |
| **Dependencies** | New deps needed | New deps needed | New deps needed |
| **Codebase fit** | How well it fits | How well it fits | How well it fits |
| **Maintenance** | Ongoing cost | Ongoing cost | Ongoing cost |

### 4c. Recommendation

- **Recommended approach**: State which option you recommend and why
- **Implementation outline**: High-level steps to implement the recommended approach
- **Risks and mitigations**: What could go wrong and how to handle it
- **Alternative if constraints change**: Note when a different option would become preferable

### 4d. Next Steps

Suggest concrete next steps:
- If the user wants to proceed: `To create a task: /task-add <description based on findings>`
- If more research is needed: Identify specific areas that need deeper investigation
- If a decision is needed: Frame the decision clearly with the trade-offs

---

## Phase 5: Write Output Files

The synthesis from Phase 4 is the **report**; the register from the Phase 1 callout is the **primary sources**. Persist both under `raw/research/<slug>/` using the **Write tool** (do not rely only on the chat transcript). Create the directory if it does not exist. Write two files — and honor the Phase 1 no-overwrite rule: if `index.md` or `sources.md` already exists, write `index-2.md` / `sources-2.md` (then `-3`, …) carrying only non-redundant new/changed content with a cross-reference back to the prior file.

### `index.md` — the research report

```
---
topic: <the research question, verbatim>
slug: <slug>
researched: <YYYY-MM-DD>
sources: [./sources.md]
---

# Research: <Topic>

> One-paragraph executive summary — the answer and the recommendation in brief.

## Research Questions
- <the 3–5 concrete questions from Phase 1>

## Current State (Codebase)
<what exists today relevant to the topic — cite file paths + symbols>

## Key Findings
<most important discoveries, each with an inline citation to a source id in sources.md, e.g. [S3]>

## Constraints
<what any solution must account for>

## Solution Comparison
<the Phase 4b table, if multiple approaches exist — omit if not applicable>

## Recommendation
<recommended approach and why; implementation outline; risks & mitigations>

## Next Steps
<the Phase 4d suggestions>
```

### `sources.md` — the primary-source register

Every source you actually relied on, one row per source, with a stable id (`S1`, `S2`, …) that the report cites. Keep the excerpt to the specific fact you used — enough to verify the claim without re-fetching.

```
---
topic: <the research question, verbatim>
slug: <slug>
researched: <YYYY-MM-DD>
---

# Primary Sources — <Topic>

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `path/to/file.ts` | <YYYY-MM-DD> | <fact drawn from it> |
| S2 | web | <full URL> | <YYYY-MM-DD> | <fact, with a short quoted excerpt> |

## Excerpts

### S2 — <source title>
<URL>
> <verbatim quoted excerpt that supports the cited claim>
```

Rules for this phase:
- **One source per row** — never collapse multiple URLs into one row.
- **Only sources you actually used** — do not pad the register with searches that produced nothing.
- **Quote, don't paraphrase, in the Excerpts section** — the excerpt is the ground-truth evidence.
- **Never fabricate a source or excerpt.** If a claim has no real source, mark it *(inference — no primary source)* in the report instead of inventing one.

---

## Phase 6: Confirm & Suggest Next Steps

After writing the files, tell the user:
- The paths written (`raw/research/<slug>/index.md` and `raw/research/<slug>/sources.md`)
- A 2–4 bullet summary of the recommendation
- That the report is now a `raw/` ground-truth source: **"Run `/wiki-ingest raw/research/<slug>/index.md` to synthesize this research into the knowledge base."**
- Any follow-on `/task-add` or `/decision-create` suggested by the findings

---

## Research Quality Standards

- **Cite sources**: Note whether information came from codebase analysis or web search
- **Distinguish fact from opinion**: Clearly separate what the code shows from what best practices suggest
- **Stay current**: Prefer recent sources (2024-2025) over older ones
- **Be specific**: Include version numbers, specific API calls, and concrete examples
- **Acknowledge gaps**: If something couldn't be determined, say so rather than guessing

---

## CRITICAL Rules

1) **Run searches sequentially** — do not fire parallel web searches; fetch one result, evaluate, then proceed
2) **Use WebFetch for library docs**: fetch official documentation pages directly rather than relying on search snippets alone
3) **Use Bash/Read/Grep for code**: navigate the codebase with `grep -rn --include=<ext>`, `find`, and `Read` — always scope `grep -r` with `--include` to avoid scanning binaries; use `-l` for file lists and `-n` to get line numbers for targeted `Read` calls
4) **Always write the output files** to `raw/research/<slug>/` (`index.md` + `sources.md`) with the **Write tool** — the report is not done until it is persisted as a ground-truth source
5) **Never overwrite `raw/` files**: if a target already exists, write `<name>-2.md` / `-3.md` instead, carrying only non-redundant new/changed data with a cross-reference to the prior file
6) **No fabricated sources**: every row in `sources.md` is a source you actually consulted; mark unsupported claims as inferences rather than inventing citations
7) **`raw/research/` is the only `raw/` path this skill may write to** — never modify or delete anything elsewhere under `raw/`
