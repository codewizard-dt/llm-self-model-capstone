---
topic: would it be possible to create a submodule within my git repo, and then on the RPi, have it only sync to that one submodule?  Like how does that work?
slug: git-submodule-rpi-sync
researched: 2026-06-26
sources: [./sources.md]
---

# Research: Git Submodule for RPi-Only Sync

> **Yes, this is exactly what submodules are for** — and the RPi workflow is even simpler than the parent-repo workflow. A git submodule is a fully independent repository embedded inside another. On the RPi, you skip the parent repo entirely and clone the submodule's URL directly. Updates are just `git pull` inside that clone. The recommended approach for this project is to extract `robot/pi-runtime/` into its own GitHub repo, register it as a submodule in the main capstone repo, and have the RPi clone only that repo.

---

## Research Questions

1. What exactly is a git submodule — is it truly an independent repo?
2. Can the RPi clone and sync only the submodule without pulling the parent repo?
3. How do you create the submodule in the first place (from an existing directory)?
4. What are the day-to-day workflows on both the dev machine and the RPi?
5. What are the alternatives (sparse-checkout, separate repo with no link) and when does each win?

---

## Current State (Codebase)

The capstone repo has no `.gitmodules` file — no submodules exist yet [S1]. The RPi-specific code lives at `robot/pi-runtime/` with subdirectories `src/`, `scripts/`, `services/`, `config/`, `tests/`, and `docs/`, plus a `requirements.txt`. The parent repo also contains `robot/v5-brain/`, `robot/ros2-runtime/`, and the entire `operator/`, `self_model_generator/`, `wiki/`, etc. tree — none of which the RPi needs.

---

## Key Findings

### A submodule is a standalone repository [S2, S3]

A git submodule is a normal git repository that is embedded as a subdirectory of another ("superproject") repository. The submodule has:

- Its own remote URL (e.g., a separate GitHub repo)
- Its own branches, commits, and history
- Its own `.git/` directory (stored under the parent's `.git/modules/`)

The parent repo tracks only a **pointer** (a specific commit SHA) to the submodule — not the files themselves.

**Critical implication**: Because the submodule is a real repo with its own URL, you can `git clone <submodule-url>` on the RPi without ever touching the parent repo. [S2]

### The RPi workflow is simple [S3, S4]

On the RPi, you never interact with the parent repo at all:

```bash
# One-time setup on RPi
git clone https://github.com/your-org/vex-pi-runtime.git

# Every time you want to pull changes
cd vex-pi-runtime
git pull origin main
```

That's it. The RPi tracks the submodule's branch directly (e.g., `main`), completely ignoring the commit-pin that the parent repo maintains.

### Creating the submodule from an existing directory [S3, S5]

Since `robot/pi-runtime/` already exists in the repo (as regular tracked files), the setup process is:

1. **Create a new empty GitHub repo** (e.g., `vex-pi-runtime`)
2. **Extract the directory's history into the new repo** using `git subtree split` or by copying + `git init` + initial commit
3. **Register the new repo as a submodule**:

```bash
# Remove the existing tracked directory from the parent index
git rm -r --cached robot/pi-runtime

# Add it back as a submodule pointing to the new repo
git submodule add https://github.com/your-org/vex-pi-runtime.git robot/pi-runtime

# Commit the .gitmodules file and the submodule pointer
git add .gitmodules robot/pi-runtime
git commit -m "Convert robot/pi-runtime to submodule"
git push
```

Alternatively (simpler, loses old history):
```bash
# Move the files out temporarily
cp -r robot/pi-runtime /tmp/pi-runtime-backup

# Remove from parent repo
git rm -r robot/pi-runtime
git commit -m "Remove pi-runtime before converting to submodule"

# Push the files to the new repo manually, then:
git submodule add https://github.com/your-org/vex-pi-runtime.git robot/pi-runtime
git commit -m "Add pi-runtime as submodule"
```

### Dev machine workflow after setup [S3, S4]

From the dev machine, `robot/pi-runtime/` behaves as a normal directory to edit, but git treats it as a separate repo context:

```bash
# Edit files in robot/pi-runtime/ normally

# Commit + push the submodule changes (goes to vex-pi-runtime repo)
cd robot/pi-runtime
git add .
git commit -m "Update telemetry handler"
git push origin main

# Back in parent repo, update the commit pointer
cd ../..
git add robot/pi-runtime        # stages the new commit SHA
git commit -m "Bump pi-runtime submodule"
git push
```

The parent and submodule are **two separate push operations** — this is the main friction point of submodules.

### Sparse-checkout as an alternative [S6, S7]

Instead of a submodule, you could clone the parent repo on the RPi with git's sparse-checkout feature to only materialize `robot/pi-runtime/`:

```bash
git clone --no-checkout --filter=blob:none https://github.com/your-org/capstone.git
cd capstone
git sparse-checkout set --cone robot/pi-runtime
git checkout main
```

`git pull` would then only sync the files in `robot/pi-runtime/` (plus minimal root files). This avoids creating a second GitHub repo but still fetches the parent's commit graph and `.git/` metadata for the whole repo.

---

## Constraints

- The capstone repo currently has `robot/pi-runtime/` as normal tracked files — migration to a submodule requires a one-time restructuring commit.
- GitHub SSH keys (or deploy keys) must be set up on the RPi to pull from whatever repo it clones.
- The RPi's git version should be ≥ 2.25 for sparse-checkout if you choose that route; submodules work with any modern git.
- Do not store secrets in either repo — the `.env` restriction in `CLAUDE.md` applies.

---

## Solution Comparison

| Criteria | Submodule (Recommended) | Sparse-Checkout | Separate repo (no link) |
|----------|------------------------|-----------------|------------------------|
| **Approach** | `robot/pi-runtime/` becomes its own GitHub repo, embedded in parent | Clone parent on RPi, only checkout `robot/pi-runtime/` | Manually maintain a second copy, no git link |
| **RPi sync command** | `git pull` in the submodule clone | `git pull` in the sparse parent clone | `git pull` in the separate clone |
| **# of GitHub repos** | 2 (parent + submodule) | 1 | 2 (unlinked) |
| **Dev friction** | Two-step push (submodule then parent pointer) | Single push | Manual sync / copy |
| **RPi disk/bandwidth** | Only submodule history | Full commit graph, only some blobs | Only submodule history |
| **Semantic clarity** | Explicit: RPi code is a distinct deployable unit | Implicit: RPi just ignores most of the repo | Clear, but no formal link |
| **Complexity** | Medium (submodule concepts) | Low once set up | Low, but diverges over time |
| **History preservation** | Can preserve `robot/pi-runtime/` git history | Preserved (it's the same repo) | Lost on creation |

---

## Recommendation

**Use git submodules.** Extract `robot/pi-runtime/` to a new GitHub repo (e.g., `vex-pi-runtime` or `capstone-pi-runtime`), register it as a submodule in the parent at `robot/pi-runtime/`, and on the RPi just clone the submodule repo directly.

**Why submodules over sparse-checkout here:**
- The RPi doesn't need *any* of the parent's history or structure — not even root files. With sparse-checkout, the parent's `.git/` metadata still lives on the RPi.
- Submodules make the deployment boundary explicit and permanent. Sparse-checkout is a local configuration that has to be set up per-clone.
- The `robot/pi-runtime/` directory is a self-contained deployable unit — it deserves its own identity.

**Why submodules over a disconnected second repo:**
- The parent repo's `.gitmodules` documents the relationship forever.
- The parent's commit pointer lets you reproduce any historical state (which firmware commit corresponded to which pi-runtime commit).

**Implementation outline:**
1. Create a new GitHub repo: `vex-pi-runtime` (or similar name)
2. Push the contents of `robot/pi-runtime/` to it (either with history via `git subtree split`, or fresh)
3. In the capstone repo: `git rm -r --cached robot/pi-runtime` → `git submodule add <url> robot/pi-runtime` → commit + push
4. On the RPi: `git clone <submodule-url>` (one time), then `git pull` to update

**Risks and mitigations:**
- *Forgetting to push the submodule before the parent pointer*: use `git push --recurse-submodules=on-demand` on the dev machine to push both in one command.
- *RPi tracking the wrong commit*: since the RPi clones the submodule directly and follows the branch (not the parent's pinned SHA), it will always be on the latest `main` — which is what you want for a deployment target.
- *SSH keys*: if the new repo is private, add a deploy key to the RPi for the submodule repo specifically.

**Alternative if constraints change:** If you never want two GitHub repos, use sparse-checkout. It's a good middle ground that costs minimal disk on the RPi and requires no repo restructuring.

---

## Next Steps

- To create the task: `/task-add Extract robot/pi-runtime into git submodule for RPi deployment`
- Push the `robot/pi-runtime/` contents to a new GitHub repo first, then do the `git submodule add` migration in the parent
- Consider `git push --recurse-submodules=on-demand` as your default push command on the dev machine going forward
