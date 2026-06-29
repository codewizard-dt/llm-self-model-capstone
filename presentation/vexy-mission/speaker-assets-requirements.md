# Speaker Asset Requirements

## Purpose

The speaker assets package exists so Grace, David Taylor, Erick, and Jake can review their parts without hunting through the deck. Each person needs a private, editable preparation surface that matches the Vexy Mission story, stays grounded in the repo/premise facts, and can be sent back to Grace.

## Required Assets

Each speaker must have:

- A section purpose that explains what their part contributes to the 10-minute mission story.
- Full speaker notes with at least eight concrete beats.
- Five copywriting versions for their slide or talk track.
- A simple cheat sheet note card with one one-liner, exactly three bullets, and a closing line.
- A clear handoff into the next speaker or into the finale.

## Copywriting Version Rules

Each speaker gets five copywriting versions:

- Grounded technical version: strongest for judges who care about engineering truth.
- Premium mission version: strongest for the red/black moon-mission website tone.
- Plain-English version: easiest for a nontechnical audience to understand.
- Technical jargon version: strongest for demonstrating depth and credibility.
- Presenter-friendly version: easiest for the speaker to say live in one pass.

Each version must include:

- A label.
- A headline.
- Slide copy that can replace the public deck copy.
- A talk track that gives the speaker words they can actually say.

## Edit And Save Rules

The speaker asset page must let a teammate edit directly on the page. Edits save immediately to `localStorage` under `vexy-speaker-assets-drafts-v1`, so the same browser can reload and continue editing right there.

This is intentionally simple and static-site friendly. Static Vercel cannot synchronize edits across browsers without a backend store. If the team wants shared live editing, the next implementation should add a small API plus one store such as Vercel KV, Supabase, Neon, or Firebase.

## Editable Prep Workspace

The page must include an Editable Prep Workspace for each selected speaker. This is the practical answer to "can they make changes and edit right then and there?"

The workspace must include:

- A full speaker notes editor so each person can revise the actual speaking beats, not only the tiny note card.
- A copywriting route editor with all five versions: Grounded Technical, Premium Mission, Plain English, Technical Jargon, and Presenter Friendly.
- A cheat sheet editor for the one-liner, exactly three bullets, and closing handoff line.
- Autosave to `localStorage` under `vexy-speaker-assets-live-edits-v1`.
- Reload persistence in the same browser.
- A copyable edited speaker asset packet that includes the edited notes, edited copy routes, edited cheat sheet, favorite route, and the static-site truth boundary.

Static Vercel can do direct in-browser editing and portable packet sharing. It cannot do live multiplayer editing or teammate-to-teammate sync until a backend store is added.

Each speaker must also be able to choose a favorite copy route and copy a portable speaker asset packet. The packet must include the speaker owner, display name, favorite copy route, current editable draft, and a truth boundary saying the packet shares speaker notes only.

Grace must be able to paste an imported speaker asset packet back into the speaker asset page. The imported speaker asset packet must restore the correct speaker, their current draft, and their favorite copy route in the same browser-local storage system. This keeps the workflow usable before a real shared backend exists.

## Review Handoff Rules

The main deck and team handoff page must link to the speaker assets page. The copy-ready Slack message must include:

- Audience deck.
- Four direct review lanes.
- Speaker assets page.
- Rehearsal console.
- Shareback proof board.

## Quality Bar

The package passes only if:

- All four speakers are present in the approved order: Grace, David Taylor, Erick, Jake.
- Each speaker has exactly five copywriting versions.
- Each cheat sheet has exactly three bullets.
- The page exposes direct editing and local save feedback.
- The page exposes the full speaker notes editor, copywriting route editor, and cheat sheet editor for the selected speaker.
- The page exposes a favorite copy route, a portable speaker asset packet, and an imported speaker asset packet workflow.
- The copy stays truthful: no live robot success claim without evidence, no overclaiming Slot 4, and no confusing cinematic label presented as repo proof.
