---
topic: would it be possible to create a submodule within my git repo, and then on the RPi, have it only sync to that one submodule?  Like how does that work?
slug: git-submodule-rpi-sync
researched: 2026-06-26
---

# Primary Sources — Git Submodule for RPi-Only Sync

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/pi-runtime/` (directory listing); no `.gitmodules` found | 2026-06-26 | Confirmed current state: no submodules exist, pi-runtime is tracked normally |
| S2 | web | https://git-scm.com/book/en/v2/Git-Tools-Submodules | 2026-06-26 | Submodule fundamentals: they are standalone repos; `git submodule update --remote` can target a specific submodule by name; once properly initialized they can be used as stand-alone repositories |
| S3 | web | https://www.atlassian.com/git/tutorials/git-submodule | 2026-06-26 | Confirmed submodules are independent repos with own branches/history; once initialized they work exactly like stand-alone repos; two-step push pattern |
| S4 | web | https://articles.mergify.com/git-clone-with-submodules/ | 2026-06-26 | Pulling changes in a submodule: `cd path/to/submodule && git pull origin main` — simple `git pull` in the submodule clone suffices |
| S5 | web | https://git-scm.com/docs/git-submodule | 2026-06-26 | `git submodule add <url> <path>` command; if `<path>` exists and is already a valid git repo, staged without cloning; `git submodule update --init` workflow |
| S6 | web | https://github.blog/open-source/git/bring-your-monorepo-down-to-size-with-sparse-checkout/ | 2026-06-26 | Sparse-checkout cone mode; `--filter=blob:none` to avoid downloading unnecessary blobs; cone mode command sequence |
| S7 | web | https://oneuptime.com/blog/post/2026-01-24-git-sparse-checkout/view | 2026-06-26 | Full sparse-checkout workflow: `git clone --no-checkout` → `git sparse-checkout set --cone <dir>` → `git checkout main` |

---

## Excerpts

### S2 — Git - Submodules (git-scm.com)
https://git-scm.com/book/en/v2/Git-Tools-Submodules
> "Git will by default try to update all of your submodules when you run git submodule update --remote. If you have a lot of them, you may want to pass the name of just the submodule you want to try to update."

> "Once submodules are properly initialized and updated within a parent repository they can be utilized exactly like stand-alone repositories."

### S3 — Git submodule | Atlassian
https://www.atlassian.com/git/tutorials/git-submodule
> "This enables a workflow of activating only specific submodules that are needed for work on the repository. This can be helpful if there are many submodules in a repo but they don't all need to be fetched for work you are doing. Once submodules are properly initialized and updated within a parent repository they can be utilized exactly like stand-alone repositories."

> "This means that submodules have their own branches and history. When making changes to a submodule it is important to publish submodule changes and then update the parent repositories reference to the submodule."

### S4 — Mastering Git Clone with Submodules (Mergify)
https://articles.mergify.com/git-clone-with-submodules/
> "So, you need to pull the latest changes into a submodule. A simple git pull in the main project won't cut it. Submodules are locked to a specific commit, and you have to update that reference intentionally. First, jump into the submodule's directory: cd path/to/submodule. Now, pull the latest changes like you normally would: git pull origin main."

### S5 — Git - git-submodule Documentation
https://git-scm.com/docs/git-submodule
> "If <path> exists and is already a valid Git repository, then it is staged for commit without cloning."

### S6 — Bring your monorepo down to size with sparse-checkout (GitHub Blog)
https://github.blog/open-source/git/bring-your-monorepo-down-to-size-with-sparse-checkout/
> "This combination speeds up the data transfer process since you don't need every reachable Git object, and instead, can download only those you need to populate your cone of the working directory. You can test it right now with the example repository by adding --filter=blob:none to the clone command."

### S7 — How to Configure Git Sparse Checkout (oneuptime.com)
https://oneuptime.com/blog/post/2026-01-24-git-sparse-checkout/view
> "Git 2.25 introduced cone mode, which is the recommended approach for sparse checkout. # Clone with no checkout git clone --no-checkout https://github.com/company/monorepo.git cd monorepo # Specify directories you want git sparse-checkout set --cone frontend docs # Now checkout git checkout main"
