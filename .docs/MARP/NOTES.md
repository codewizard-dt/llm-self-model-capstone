**Grace Huang** - 2 Minutes

This is Vexy: a physical VEX V5 robot that uses an AI self-model to understand its own body. Vexy is built from metal rails, wheels, and a red claw grasper which can be interchangeable and composable in nature. It is powered by a V5 Brain and Smart Motors plugged into Smart Ports, but it also carries a Raspberry Pi and a camera. This ‘vision stack’ allows Vexy to find AprilTags for its location and track this yellow ball to finish its tasks based on the goal our team sets.

Engineers usually train robots in perfect computer simulations. When those models are deployed to a physical robot, they often fail because the real world has friction, stripped gears, and uneven weight distribution. Even the floor from carpet to tile makes a big difference. Small details like mechanical alignment or camera limits can change how the robot actually moves. By modeling the specific, flawed physical machine rather than a perfect abstraction, Vexy addresses the reality gap directly.

The heart of our project is Vexy’s self-modeling that is observable to us due to the telemetry tracking that David will go into.


Core Premise: Vexy is a physical VEX V5 robot that uses an AI self-model to understand its own body.
Hardware Build: Constructed from interchangeable, composable metal rails, wheels, and a red claw grasper, powered by a V5 Brain and Smart Motors.
Vision Stack: Carries a Raspberry Pi and camera to locate AprilTags for positioning and track a yellow ball to complete assigned tasks.
The Reality Gap: Robots trained in perfect computer simulations often fail when facing real-world physics like friction, stripped gears, uneven weight, or varying floor surfaces.
The Solution: Vexy addresses this gap directly by modeling its specific, flawed physical mechanics and limits instead of relying on a perfect abstraction.
Observable Data: The foundation of the project is this self-modeling system, which is made visible through telemetry tracking (to be detailed by David).

**David Taylor** — 2 Minutes
Key Points:

The small learning loop is not “LLM says robot improved.” It is generates a plan, executes it, analyzes its own telemetry, revises it hardware control decisions, and starts over.  The larger loop is the Generational Loop, where the LLM can redesign its own body and adapt to conditions in the real world.

- It comes from work based on numerical self-modeling, which stays in a sub-symbolic tensor that is not human readable. 
- It also inspired by LLM morphology generation, which uses LLMs to generate robot designs, though only in simulation.  
- A final piece is LLM self-improvement, which optimizes control parameters on real hardware, but there is no self-model component.

The novel thing about this experiment is combining all of these and adding morphology that the LLM itself can redesign. 

What if an LLM could redesign its own body and adapt to conditions in the real world? The telemetry, including motor samples, vision state, and operator results creates a feedback loop that gives the LLM enough information to reason about what went wrong and suggest improvements. 

The most novel thing about Vexy is that it treats every run as evidence, and uses that evidence in a continuous improvement loop to better itself.  

The challenges we encountered, which I'll let the others get into detail about, restricted us to very simple tasks.  

Vexy was just beginning to conquer the basic task of putting the ball in the bin.  If it had been successful at learning that, our next steps would have been to allow Vexy to redesign its component parts to evolve into a new form, one that could perform ever increasingly complex tasks. 

**Erick**

-- no notes, all Brain

**Jake**

here is my section change diff:  diff --git a/presentation/vexy-mission/index.html b/presentation/vexy-mission/index.html
--- a/presentation/vexy-mission/index.html
+++ b/presentation/vexy-mission/index.html
@@ -589,32 +589,32 @@
-          <p class="eyebrow" data-edit-key="jake_film_eyebrow">Jake · evidence packet</p>
-          <h2 data-edit-key="jake_film_title">Prediction. Observation. Gap.</h2>
+          <p class="eyebrow" data-edit-key="jake_film_eyebrow">Jake · perception to proof</p>
+          <h2 data-edit-key="jake_film_title">Vision becomes evidence.</h2>
@@
-          <span>Evidence packet and measurement</span>
+          <span>Perception, localization, and evidence</span>
@@
-            <h2 data-edit-key="jake_title" data-owner="jake">A run matters only if it leaves behind evidence.</h2>
+            <h2 data-edit-key="jake_title" data-owner="jake">Perception turns motion into evidence.</h2>
             <p class="big-copy" data-edit-key="jake_copy">
-              Vexy needs a packet that says what was predicted, what was observed, what telemetry
-              came back, and where reality disagreed. That gap is the learning signal.
+              Vexy does not just need camera frames. It needs AprilTag localization, object positions,
+              scene state, and contract-valid evidence so the control loop and self-model can trust what the robot saw.
             </p>
@@
-              <li>The gap is the learning signal.</li>
-              <li>Sense means AprilTags, yellow ball detection, and object confidence.</li>
-              <li>Measure means predicted state versus observed outcome.</li>
-              <li>Structure keeps the LLM from inventing explanations.</li>
-              <li>The evidence packet turns a run into something the model can safely learn from.</li>
+              <li>AprilTags localize the robot in the workspace.</li>
+              <li>Yellow-ball and object detections become robot-relative and map-relative positions.</li>
+              <li>Scene summaries give the agent a compact view of the world.</li>
+              <li>MCAP/raw ROS observations export into contract-valid JSONL.</li>
+              <li>The gap is only useful when perception is localized and structured.</li>
@@
-          <p>Jake closes the loop: prediction, observation, gap, and update keep learning honest when reality pushes back.</p>
+          <p>Jake closes the loop: camera observations become localized scene evidence, then prediction, observation, gap, and update keep learning honest when reality pushes back.</p>
@@
-          <article class="transition-card framer-transition scroll-reveal" data-transition data-diagram data-reveal><span>Expected</span><strong>What Vexy thought would happen</strong></article>
-          <article class="transition-card framer-transition scroll-reveal" data-transition data-diagram data-reveal><span>Observed</span><strong>What sensors and telemetry saw</strong></article>
-          <article class="transition-card framer-transition scroll-reveal" data-transition data-diagram data-reveal><span>Gap</span><strong>What reality proved different</strong></article>
+          <article class="transition-card framer-transition scroll-reveal" data-transition data-diagram data-reveal><span>Raw vision</span><strong>Camera frames, AprilTags, and object detections</strong></article>
+          <article class="transition-card framer-transition scroll-reveal" data-transition data-diagram data-reveal><span>Scene state</span><strong>Robot pose, object positions, and confidence</strong></article>
+          <article class="transition-card framer-transition scroll-reveal" data-transition data-diagram data-reveal><span>Evidence</span><strong>Telemetry, vision state, operator result, and gap</strong></article>
@@
-          <article class="active-diagram-panel is-selected" data-diagram-panel="jake-evidence-packet" data-diagram data-transition>
+          <article class="active-diagram-panel" data-diagram-panel="jake-evidence-packet" data-diagram data-transition hidden>
@@
-          <article class="active-diagram-panel" data-diagram-panel="jake-vision-funnel" data-diagram data-transition hidden>
+          <article class="active-diagram-panel is-selected" data-diagram-panel="jake-vision-funnel" data-diagram data-transition>
             <span>Selected diagram</span>
-            <strong>Vision Funnel</strong>
-            <p>AprilTags, yellow ball detection, object confidence, camera pose, and scene observations become the perception layer that grounds the evidence packet.</p>
+            <strong>Perception to Proof</strong>
+            <p>AprilTags, yellow ball detection, object confidence, camera pose, and scene coordinates become the structured evidence that grounds the operator and self-model loop.</p>

diff --git a/presentation/vexy-mission/data/diagram-options.json b/presentation/vexy-mission/data/diagram-options.json
--- a/presentation/vexy-mission/data/diagram-options.json
+++ b/presentation/vexy-mission/data/diagram-options.json
@@ -3,7 +3,7 @@
-    "Jake": "jake-evidence-packet"
+    "Jake": "jake-vision-funnel"
@@
-        "rationale": "Best for Jake because it turns a run into command, vision, telemetry, predicted, observed, gap, and update.",
-        "selected": true
+        "rationale": "Shows how a complete run record carries command, vision, telemetry, predicted, observed, gap, and update."
@@
-        "title": "Vision Funnel",
-        "rationale": "Explains AprilTags, yellow ball detection, object confidence, and scene observations."
+        "title": "Perception to Proof",
+        "rationale": "Best for Jake because it explains AprilTags, yellow ball detection, object confidence, scene coordinates, and contract-valid evidence.",
+        "selected": true