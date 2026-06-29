---
marp: true
theme: default
paginate: true
size: 16:9
header: 'Vexy presentation notes'
footer: 'Grace Huang, David Taylor, Erick, Jake · 2026-06-29'
style: |
  section {
    font-size: 28px;
    background: #0d1117;
    color: #c9d1d9;
  }
  section.lead h1 { font-size: 64px; }
  section.lead { text-align: center; }
  h1, h2 { color: #58a6ff; }
  h3, h4 { color: #79c0ff; }
  strong { color: #f0f6fc; }
  a { color: #58a6ff; }
  code {
    font-size: 0.9em;
    background: #161b22;
    color: #f0f6fc;
  }
  pre {
    background: #161b22;
    border: 1px solid #30363d;
  }
  table {
    background: #0d1117;
    border-color: #30363d;
  }
  th {
    background: #161b22;
    color: #f0f6fc;
  }
  td, th {
    border-color: #30363d;
  }
  blockquote {
    color: #8b949e;
    border-left-color: #30363d;
  }
  header, footer {
    color: #8b949e;
  }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# Vexy Presentation Notes

---

<!-- _class: lead -->

# Grace Huang

---

- 2 Minutes
- This is Vexy: a physical VEX V5 robot that uses an AI self-model to understand its own body.
- Vexy is built from metal rails, wheels, and a red claw grasper which can be interchangeable and composable in nature.
- It is powered by a V5 Brain and Smart Motors plugged into Smart Ports, but it also carries a Raspberry Pi and a camera.
- This ‘vision stack’ allows Vexy to find AprilTags for its location and track this yellow ball to finish its tasks based on the goal our team sets.

---

- Engineers usually train robots in perfect computer simulations.
- When those models are deployed to a physical robot, they often fail because the real world has friction, stripped gears, and uneven weight distribution.
- Even the floor from carpet to tile makes a big difference.
- Small details like mechanical alignment or camera limits can change how the robot actually moves.
- By modeling the specific, flawed physical machine rather than a perfect abstraction, Vexy addresses the reality gap directly.

---

- The heart of our project is Vexy’s self-modeling that is observable to us due to the telemetry tracking that David will go into.
- Core Premise: Vexy is a physical VEX V5 robot that uses an AI self-model to understand its own body.
- Hardware Build: Constructed from interchangeable, composable metal rails, wheels, and a red claw grasper, powered by a V5 Brain and Smart Motors.
- Vision Stack: Carries a Raspberry Pi and camera to locate AprilTags for positioning and track a yellow ball to complete assigned tasks.

---

- The Reality Gap: Robots trained in perfect computer simulations often fail when facing real-world physics like friction, stripped gears, uneven weight, or varying floor surfaces.
- The Solution: Vexy addresses this gap directly by modeling its specific, flawed physical mechanics and limits instead of relying on a perfect abstraction.
- Observable Data: The foundation of the project is this self-modeling system, which is made visible through telemetry tracking (to be detailed by David).

---

<!-- _class: lead -->

# David Taylor

---

- 2 Minutes
- Key Points:
- The small learning loop is not “LLM says robot improved.”
- It is generates a plan, executes it, analyzes its own telemetry, revises it hardware control decisions, and starts over.
- The larger loop is the Generational Loop, where the LLM can redesign its own body and adapt to conditions in the real world.

---

- It comes from work based on numerical self-modeling, which stays in a sub-symbolic tensor that is not human readable.
- It also inspired by LLM morphology generation, which uses LLMs to generate robot designs, though only in simulation.
- A final piece is LLM self-improvement, which optimizes control parameters on real hardware, but there is no self-model component.
- The novel thing about this experiment is combining all of these and adding morphology that the LLM itself can redesign.

---

- What if an LLM could redesign its own body and adapt to conditions in the real world?
- The telemetry, including motor samples, vision state, and operator results creates a feedback loop that gives the LLM enough information to reason about what went wrong and suggest improvements.
- The most novel thing about Vexy is that it treats every run as evidence, and uses that evidence in a continuous improvement loop to better itself.

---

- The challenges we encountered, which I'll let the others get into detail about, restricted us to very simple tasks.
- Vexy was just beginning to conquer the basic task of putting the ball in the bin.
- If it had been successful at learning that, our next steps would have been to allow Vexy to redesign its component parts to evolve into a new form, one that could perform ever increasingly complex tasks.

---

<!-- _class: lead -->

# Erick

---

- -- no notes, all Brain

---

<!-- _class: lead -->

# Jake

---

- Jake · perception to proof
- Vision becomes evidence.
- Perception, localization, and evidence
- Perception turns motion into evidence.

---

- Vexy does not just need camera frames.
- It needs AprilTag localization, object positions, scene state, and contract-valid evidence so the control loop and self-model can trust what the robot saw.
- AprilTags localize the robot in the workspace.
- Yellow-ball and object detections become robot-relative and map-relative positions.

---

- Scene summaries give the agent a compact view of the world.
- MCAP/raw ROS observations export into contract-valid JSONL.
- The gap is only useful when perception is localized and structured.
- Jake closes the loop: camera observations become localized scene evidence, then prediction, observation, gap, and update keep learning honest when reality pushes back.

---

- Raw vision: Camera frames, AprilTags, and object detections
- Scene state: Robot pose, object positions, and confidence
- Evidence: Telemetry, vision state, operator result, and gap
- Selected diagram: Perception to Proof
- AprilTags, yellow ball detection, object confidence, camera pose, and scene coordinates become the structured evidence that grounds the operator and self-model loop.

---

- Jake: jake-vision-funnel
- Shows how a complete run record carries command, vision, telemetry, predicted, observed, gap, and update.
- Perception to Proof
- Best for Jake because it explains AprilTags, yellow ball detection, object confidence, scene coordinates, and contract-valid evidence.

