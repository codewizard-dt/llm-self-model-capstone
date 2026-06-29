# Vexy Mission Team Edit Guide

This guide explains how teammates update their own section of the Vexy
presentation and get a Vercel preview without Grace rebuilding the deck.

## Where The Presentation Lives

All presentation files live here:

```text
presentation/vexy-mission
```

The Vercel project should use this folder as the project root. When a teammate
pushes a branch or opens a pull request, Vercel can create a preview for that
branch from the same static package.

## How teammates update their own section

1. Start from latest `main`.
2. Create a branch named for your edit, for example
   `speaker/jake-evidence-notes`.
3. Edit only your speaker section unless the team agrees otherwise.
4. Run the presentation validator.
5. Push the branch.
6. Open a pull request.
7. Use the Vercel preview URL to check your slide and video flow.

Validation command:

```bash
make presentation-validate
```

Local preview command:

```bash
python3 -m http.server 8766 -b 127.0.0.1 -d presentation/vexy-mission
```

Then open:

```text
http://127.0.0.1:8766/
```

## Direct Review Links

Use these on a local preview or Vercel preview:

- Grace: `?edit=1&owner=grace`
- David Taylor: `?edit=1&owner=david`
- Erick: `?edit=1&owner=erick`
- Jake: `?edit=1&owner=jake`

These links open the browser review tools for each speaker. The browser review
tools are useful for pinning comments and drafting speaker notes, but those
browser edits are not automatically committed to Git. Commit real final changes
to files in this folder.

## Which Files To Edit

Most copy and speaker notes are in:

```text
presentation/vexy-mission/index.html
presentation/vexy-mission/presentation-plan.json
presentation/vexy-mission/data/speaker-assets.json
presentation/vexy-mission/speaker-assets.html
```

If you only need to change what appears on screen, start with `index.html`.

If you need to change the run-of-show or speaker timing, update
`presentation-plan.json` and `run-of-show.html`.

If you need to change private speaker notes, note cards, or copy suggestions,
update `data/speaker-assets.json` and `speaker-assets.html`.

## Speaker Ownership

Grace owns:

- opening premise
- what VEX V5 is
- why a real robot body matters
- Raspberry Pi, camera, AprilTag, yellow ball setup
- language self-model premise

David Taylor owns:

- plan, execute, analyze telemetry, start over
- the larger Generational Loop
- research synthesis and future morphology-redesign framing
- honest status of what the system could do next

Erick owns:

- the hard technical problem
- trusted motion
- bounded command vocabulary
- ack/fault states
- watchdogs and safe execution boundaries

Jake owns:

- perception-to-proof framing
- AprilTag localization and yellow-ball/object observations
- robot-relative and map-relative scene coordinates
- MCAP/raw ROS evidence exported into contract-valid JSONL
- why the gap only matters when perception is structured

## Vercel Preview Expectations

Every branch preview should show:

- the full audience deck at `/`
- speaker review mode at `/?edit=1`
- each owner lane at `/?edit=1&owner=...`
- team handoff at `/team-handoff`
- phase dashboard at `/phase-execution`
- rehearsal console at `/rehearsal-console`
- shareback proof at `/shareback-proof`

If a preview is missing videos or images, confirm the media files under
`presentation/vexy-mission/media/` are still committed.

## Truth Boundary

The presentation proves the demo artifact and the repository-backed story. It
does not prove a live robot success claim unless the team also shows real run
evidence, telemetry, or operator proof from the robot.
