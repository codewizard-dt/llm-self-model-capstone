# Vexy Mission Presentation Design System

This file is the source of truth for the presentation's visual system. The goal is not to copy Apple, Lovable, or Framer directly; it is to adapt their interaction principles to a red/black Vexy moon-mission story.

## Research Basis

- Apple HIG Materials / Liquid Glass: use translucent materials to separate controls from cinematic content without hiding the media underneath.
- Apple HIG Layout: keep navigation and controls visually distinct from content, especially when layered over rich imagery or video.
- Apple HIG Motion: motion should orient the presenter and audience, not distract from the story.
- Motion.dev scroll animations: use scroll-triggered reveals for section entrances, scroll-linked progress for position awareness, and parallax for depth.
- Animos reference: use kinetic text, reveal choreography, object permanence, and premium interaction pacing as the animation bar.
- Lovable Vexy reference: use the dark red/black mission-control vibe, strong contrast, cinematic sections, and confident technical hierarchy.

Sources:
- https://developer.apple.com/design/human-interface-guidelines/materials
- https://developer.apple.com/design/human-interface-guidelines/layout
- https://developer.apple.com/design/human-interface-guidelines/motion
- https://motion.dev/docs/react-scroll-animations
- https://animos.app/
- https://vexycapstone.lovable.app/

## Visual Rules

1. Red/black mission base: black lunar surfaces, red command accents, small cyan/yellow telemetry highlights.
2. Liquid Glass surfaces: use `backdrop-filter`, translucent borders, inner highlights, and a faint red/cyan reflection.
3. No generic SaaS cards: cards only exist as repeated diagrams, speaker notes, or control surfaces.
4. Full-screen film moments: every speaker film should feel like a cinematic chapter break.
5. Proof labels stay visible: Flow asset, Repo proof, Run evidence, and Blocked until proven must stay honest.
6. Review mode is part of the product: pins, comment drawer, speaker-owner filtering, and export/import must feel designed, not bolted on.

## Motion Rules

1. Scroll-triggered: `.scroll-reveal` enters with blur, rise, and scale.
2. Scroll-linked: the top progress bar tracks the whole vertical route.
3. Parallax: `.parallax-drift` creates slow depth on mission diagrams.
4. Framer-like transitions: `.framer-transition` uses a fast-out/smooth-settle cubic-bezier.
5. Video lock: after the Start Presentation gesture, a fullscreen film plays with sound and the page releases scroll after the clip ends.
6. Animos-style primitives: `.animos-rise`, `.mission-scan`, `.kinetic-word`, `.stagger-reveal`, and `.diagram-choice-card` create the premium motion language.

## Diagram Rules

1. Grace default: VEX body to language model, connecting VEX V5 Brain, Smart Ports, Smart Motors, red claw, Raspberry Pi, camera, AprilTag, yellow ball, telemetry, contracts, and LLM self-model.
2. David default: Generational Loop, connecting plan, execute, analyze telemetry, and future body redesign.
3. Erick default: trusted motion gates, connecting intent, bounded vocabulary, limits, watchdog, ack/fault, and evidence.
4. Jake default: evidence packet, connecting command, vision, telemetry, predicted, observed, gap, and update.
5. Each speaker must have five diagram choices so teammates can swap the visual without rewriting the whole slide.

## Speaker Flow

1. Grace: Self-Modeling Machines, in Language; what Vexy is physically; why VEX V5 matters; Raspberry Pi/AprilTags/yellow ball; Loop 1, Loop 2, grab, pull, and throw.
2. David Taylor: the small learning loop and the larger Generational Loop.
3. Erick: trusted motion, bounded commands, and why safe physical action is hard.
4. Jake: evidence packet, prediction versus observation, and the gap as the learning signal.

## Reject Gates

- Reject if the order drifts away from Grace -> David Taylor -> Erick -> Jake.
- Reject if video clips loop forever during the locked presentation path.
- Reject if Flow assets are presented as proof of physical robot performance.
- Reject if David is only a final wrap-up instead of the immediate post-Grace learning-loop speaker.
- Reject if the page lacks Liquid Glass, scroll-triggered reveal, scroll-linked progress, parallax, and diagram-heavy technical explanation.
- Reject if the page lacks pin/comment review mode or if teammate edits cannot be exported.
- Reject if Grace's slide does not explicitly say Self-Modeling Machines, in Language and show the VEX/Raspberry Pi/AprilTag/yellow-ball body stack.
- Reject if the final four-person moon image is dark enough that David's face is hard to see.
