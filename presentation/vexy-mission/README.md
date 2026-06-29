# Vexy Mission Presentation

Status: ready for teammate review, Vercel deployment, and live rehearsal.

This folder contains the 10-minute vertical Vexy mission presentation as a
static HTML/CSS/JS site. It includes the Flow videos, four-person moon hero
image, diagrams, speaker notes, browser edit tools, pinned review comments,
review packet export/import, rehearsal console, shareback proof page, and the
Phase 5/6 execution dashboard.

## Vercel Setup

Vercel Project Root Directory: `presentation/vexy-mission`

Current live URL: `https://vexy-mission.vercel.app`

Current Vercel project: `gracexiyuan-2067s-projects/vexy-mission`

Verified on 2026-06-29:

- audience deck returns HTTP 200;
- `media/grace_mission_control.mp4` returns HTTP 200;
- `media/team-final-hero.jpeg` returns HTTP 200;
- `team-handoff` returns HTTP 200;
- `phase-execution` returns HTTP 200;
- Vercel project root directory is set to `presentation/vexy-mission`.

Recommended Vercel settings:

- Framework Preset: `Other`
- Build Command: leave empty
- Output Directory: `.`
- Install Command: leave empty
- Git Repository: `codewizard-dt/llm-self-model-capstone`
- Production Branch: whichever branch the team merges for the final deck

Once Vercel is connected to this folder, teammates can update their own slides
in this repo, push a branch, and use the Vercel preview for that branch without
Grace manually rebuilding or uploading the presentation.

## GitHub integration gate

The live Vercel project exists and serves the deck, but automatic branch previews
still require Vercel's GitHub integration to access the private repository
`codewizard-dt/llm-self-model-capstone`.

Attempted command:

```bash
vercel git connect https://github.com/codewizard-dt/llm-self-model-capstone --scope gracexiyuan-2067s-projects --yes
```

Current blocker:

```text
Failed to connect codewizard-dt/llm-self-model-capstone to project.
Make sure there aren't any typos and that you have access to the repository if it's private.
```

To finish automatic teammate previews, authorize or install the Vercel GitHub
app for this private repo, then connect the project to the repo with root
directory `presentation/vexy-mission`.

## How To View Locally

From the repo root:

```bash
python3 -m http.server 8766 -b 127.0.0.1 -d presentation/vexy-mission
```

Then open:

```text
http://127.0.0.1:8766/
```

The page is intentionally vertical. Scroll down through the mission like a
webpage, or use the arrow keys during rehearsal.

Click **Play with sound** before presenting. It unlocks video audio, starts the
fullscreen video sequence, and clears any open review/edit UI so the audience
view is clean.

Click **Review / Edit** in the lower-left corner to reveal or hide the reviewer
console.

## Direct teammate edit links

Use these paths after local launch or after Vercel deployment:

- Grace: `/?edit=1&owner=grace`
- David Taylor: `/?edit=1&owner=david`
- Erick: `/?edit=1&owner=erick`
- Jake: `/?edit=1&owner=jake`

Each owner lane opens the private key points, note suggestions, diagram choices,
speaker notes, and ready confirmation for that person. Speaker-note saves run a
lightweight overlap check so one person does not accidentally take over another
person's assigned explanation.

## Review Workflow

For teammate-owned file edits and Vercel previews, read
[`TEAM_EDIT_GUIDE.md`](TEAM_EDIT_GUIDE.md).

1. Open the direct teammate edit link for your name.
2. Click **Review / Edit** if the review console is not already visible.
3. Review the key points and speaker notes for your section.
4. Use **Suggestions** to compare alternate copy options.
5. Use **Pin a spot** to click the exact slide area that needs a change.
6. Edit speaker notes directly in the browser.
7. Click **Mark my section ready** when your section is ready for rehearsal.
8. Use **Copy review link**, **Export review packet**, or **Copy review MD** to
   hand back your edits.

The browser review mode is database-free. It stores edits in localStorage and
shareable review packets. True multi-user sync would require a Vercel Function
plus KV, Supabase, Neon, or another database. For this capstone handoff, the
intended workflow is: teammate edits locally or on a Vercel preview, exports the
packet or commits file changes, and pushes a branch.

## Presentation Pages

- `index.html` - audience presentation.
- `team-handoff.html` - sendable teammate review packet.
- `phase-execution.html` - Phase 5/6 dashboard for rehearsal, review links, and
  final proof checklist.
- `rehearsal-console.html` - live 10-minute rehearsal timer and checklist.
- `shareback-proof.html` - paste returned review links and final proof state.
- `speaker-assets.html` - speaker notes, copy options, and note cards.
- `run-of-show.html` - the full speaking order.
- `demo-readiness.html` - readiness checklist before presenting.

## What Is Included

- Fullscreen Vexy opener.
- Grace premise slide: Self-Modeling Machines, in Language; VEX V5 Brain; Smart
  Ports; Smart Motors; Raspberry Pi; AprilTags; yellow ball; grab, pull, and
  throw.
- David Taylor learning-loop and Generational Loop section.
- Erick hard technical problem section with trusted-motion framing.
- Jake evidence-packet section.
- In-presentation architecture, contract, evidence, critic, hardware-stack, and
  diagram-choice visuals.
- Speaker notes, key points, diagram-picker controls, and note suggestions that
  are private to the selected speaker in edit mode.
- Final brightened four-person moon hero of Vexy with Grace, David Taylor,
  Erick, and Jake behind it, with truth labels that distinguish Flow visuals
  from repo-backed proof and required run evidence.

## Current Timing

The target duration is exactly 10 minutes across 10 parts.

## Validation

From the repo root:

```bash
make presentation-validate
```

This checks that the presentation package is committed in the team repo, all
required media and handoff pages are present, the four speaker lanes exist, the
Vercel root-directory instructions are present, and the finale avoids awkward
sales copy like telling the audience that the project is impressive.
