# Vexy Mission Presentation Adversarial Review

Purpose: ensure the sendable presentation follows the agreed plan, speaking notes, video/photo order, and Lovable-style transitions rather than reverting into a planning document.

## Round 1 - Product Shape

Question: does this feel like the actual presentation, or a plan about a presentation?

Findings:
- Reject if the visible page says prompts still need to be made.
- Reject if the contact sheet appears before the actual talk.
- Reject if the deck keeps a separate after-talk extra section after Grace explicitly asked for it to be removed.
- Reject if Jake or David are labeled as unfinished in the visible presentation.

Resolution:
- The visible flow now opens with the Vexy film, moves through the mission premise, then uses each speaker film and talk section in order.
- The contact sheet is kept as edit-only review support inside the finale, not as a public extra section.
- Placeholder language is removed from visible presentation copy.

## Round 2 - Lovable transitions

Question: does the page have enough premium motion and continuity to feel like a Lovable-style presentation, not a static document?

Findings:
- Reject if every section just appears as static text.
- Reject if there is no scroll progress, no active-slide state, and no card reveal rhythm.
- Reject if video moments do not feel like cinematic section breaks.

Resolution:
- Added vertical scroll snapping, progress bar, slide counter, arrow-key navigation, scroll-reveal primitives, transition-card hover states, and parallax-drift motion on the self-model loop.
- Video slides act as full-screen cinematic chapter breaks.

## Round 3 - Video playback, speaker order, and proof

Question: does the presentation follow the exact video/photo/speaking order and does video playback work?

Findings:
- Reject if the opening video is only a static background.
- Reject if speaker clips are out of order.
- Reject if David Taylor appears only as a final wrap-up instead of immediately after Grace.
- Reject if locked videos loop forever and never release the presenter to scroll.
- Reject if the yellow ball / AprilTag image is not placed before Jake's evidence explanation.

Resolution:
- Opening and speaker videos use autoplay, muted startup, controls, active-section playback logic, and sound unlock after the Play with sound click.
- JavaScript plays the active slide video, pauses inactive videos, locks scroll while a full-screen clip plays, and releases scroll on the `ended` event.
- Eval enforces the order: intro video, premise, Grace video, Grace section, David video, David learning-loop section, mechanism video, Erick video, Erick section, yellow ball / AprilTag, Jake video, Jake evidence, finale.
- Required speaker order is Grace -> David Taylor -> Erick -> Jake.

## Round 4 - Liquid Glass and technical diagrams

Question: does the page connect premium design to a clear technical explanation?

Findings:
- Reject if the style is only dark cards with no material system.
- Reject if there are fewer than ten diagram or transition elements.
- Reject if the small learning loop and Generational Loop are described only in prose.

Resolution:
- Added Liquid Glass surfaces, scroll-triggered reveals, scroll-linked progress, parallax drift, and Framer-like cubic-bezier transitions.
- Added a Generational Loop diagram and research-lattice cards explaining numerical self-modeling, LLM morphology generation, LLM self-improvement, and Vexy's synthesis.

## Round 5 - Review mode and teammate editability

Question: can Grace and teammates point to a specific broken area and send Codex an actionable packet?

Findings:
- Reject if edit mode only changes text but cannot pin a location.
- Reject if comments cannot be exported with slide id, coordinates, author, and status.
- Reject if speaker-owner filtering is not visible.
- Reject if Vercel edit mode is presented as shared collaboration without a backend.

Resolution:
- Added `Pin a spot`, review drawer, speaker selector, speaker guidance, review JSON export/import, and Codex-readable markdown export.
- Added `?edit=1` Vercel edit mode language and an honest note that shared persistence requires a Vercel Function plus storage.
- Review links open in a discreet review lane first; they do not automatically put the whole deck into edit mode until the teammate clicks `Review / Edit`.
- `Play with sound` must clear editing, pinning, and drawer state so no review UI leaks into the audience presentation.

## Round 6 - Grace premise and final image

Question: does Grace's slide now explain the actual X35 premise instead of generic VEX hardware?

Findings:
- Reject if Grace does not say `Self-Modeling Machines, in Language`.
- Reject if the slide omits Loop 1 calibration, Loop 2 morphology, grab/pull/throw, Raspberry Pi, AprilTag, or yellow ball.
- Reject if David repeats the hardware intro instead of covering the learning loop and research synthesis.
- Reject if the four-person moon image appears only early and not as the final thank-you frame.

Resolution:
- Grace now owns the physical premise, the VEX/Raspberry Pi/AprilTag/yellow-ball body stack, and the grab/pull/throw primitive arc.
- David remains responsible for the small learning loop, Generational Loop, prior research lanes, telemetry, and future redesign path.
- The final frame uses the brightened four-person moon image as the thank-you / mission-complete moment.

## Hard Reject Gates

- No blue or redesigned Vexy.
- No raw footage as the public visual layer.
- No planning prompts in the visible presentation.
- No unfinished placeholder language in visible slides.
- No public extra section after the finale.
- No horizontal slide deck behavior.
- No speaker order drift.
- No video-only background that cannot play.
- No David-at-the-end wrap-up drift.
- No missing pin/comment export workflow.
- No missing five-diagram-choice control per speaker.
- No Grace slide without Self-Modeling Machines, in Language.
- No review URL that automatically starts full edit mode.
- No stale audience helper pills or generic `speaker film` labels.
