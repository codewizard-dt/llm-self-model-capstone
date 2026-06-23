---
topic: "What kind of object would be best in terms of graspability, scoopability, and launchability — various ball types and alternatives that would not be damaging or damaged when launched"
slug: game-object-selection
researched: 2026-06-22
sources: [./sources.md]
---

# Research: Game Object Selection — Graspability, Scoopability, Launchability

> **Recommendation: racquetball (57 mm, hollow rubber, ~40 g).** It is the only common off-the-shelf ball that fits cleanly inside the passive serving-spoon scoop, closes to a secure grip position on the Clawbot claw, compresses correctly against a 3" flex-wheel flywheel, and absorbs enough impact energy to be safe at robot-scale launch velocities. A small foam ball (55–70 mm, Nerf-style) is the runner-up and is preferred if the flywheel is the *only* launch mechanism; it is marginally worse for reliable claw grip because it deforms under pressure.

---

## Research Questions

1. What are the physical size and weight constraints imposed by the Clawbot claw, the passive serving-spoon scoop, and the 3" flex-wheel flywheel?
2. Which ball types satisfy all three constraints simultaneously?
3. How do material properties (compression, surface texture, weight) affect flywheel energy transfer and flight consistency?
4. Are non-ball objects (wiffle balls, rings, discs) competitive with balls on any criteria?
5. What are the safety and durability considerations for launches at robot-scale velocities (~0.45–22 m/s)?

---

## Current State (Codebase)

The capstone robot has **three morphologies relevant to object handling**, each with its own constraint on object geometry [S1]:

### Claw (Gen 1 Clawbot default)
- Port 3 motor, 12T gear; maximum grip force ~42 N stall / ~14.7 N continuous
- Claw spans approximately 100–125 mm fully open; closes to stall on the object
- Object width proxy logged as `open_degrees − claw_motor.position()` [S2]
- Objects **2–5 inches (50–125 mm)** in diameter are workable; ideal sweet spot is 55–75 mm where the motor still has travel to close on grip

### Passive Scoop (serving-spoon swap)
- Mounts in the 1" (25.4 mm) bracket gap left by the removed claw [S3]
- A standard plastic serving-spoon bowl is ~70–80 mm wide and 45–55 mm deep
- Scoop action is "slide under + arm lift": the object must rest on a flat surface, be light enough to slide up onto the bowl, and fit within the bowl width
- Objects **≤ 65 mm** diameter scoop cleanly; 70–75 mm is marginal (ball must drop into bowl); > 80 mm does not fit

### Flywheel launcher (exclusive arm-motor swap)
- 3" (76 mm) OD flex wheels, 60A durometer [S4]
- Motor at 600 RPM × 7:1 gear ratio → ~4 200 RPM at wheel rim → ~22 m/s rim speed
- Compression gap tuned to object: **~1–2 mm compression** is optimal — too little = ball slips past without enough friction; too much = energy is wasted deforming object rather than accelerating it [S5]
- Works best with **spherical or disc-shaped objects** 50–75 mm in diameter
- Objects must have enough surface grip to accept energy from the wheel (smooth rubber > felt > bare plastic > rigid metal)

### Slow catapult (base kit, no flywheel swap)
- Arm motor at 200 RPM + rubber-band assist → ~0.45 m/s release at 150 mm arm
- Suitable for objects up to **~50 g** over 0.25–0.5 m range [S2]

---

## Key Findings

### VEX-validated game objects [S5] [S6]
VEX Nothing But Net (2015–16) used **4" (100 mm) polyurethane foam balls** with single-flywheel launchers — the gold-standard VRC flywheel proof-of-concept. These balls weigh ~50–80 g, compress well against flex wheels, and were used at thousands of RPM at competition. The core insight from that game: **foam balls and hollow-rubber balls of the right compression ratio are the most flywheel-compatible game objects.** Turning Point (2018–19) used similar competition balls (~100 mm) for flag-toggling via launcher. In both seasons, the 4" ball was proven at thousands of competition launches with minimal damage to balls or targets.

Key finding from the VEX forum: balls that are "hard as baseballs" (solid rubber, no give) *hurt flywheel consistency* because they don't compress at all — the wheel slips over them [S5]. Compression/deformability matters more than surface texture for flywheel energy transfer.

### Flywheel compression physics [S5] [S10]
- Single flywheel + backplate is the most accurate and common design
- Compression = `object_diameter − (wheel_rim_to_backplate_gap)`; VEX Nothing But Net teams used **0.35–0.5" (9–13 mm) compression** on 4" foam balls [S10] — approximately 9–12% of object diameter
- General rule: target **~10% of object diameter** in compression
- For a 57 mm racquetball: target gap = 57 − (57 × 0.10) ≈ 51 mm between wheel rim and backplate
- Hollow rubber balls (racquetballs) — compressible but consistent; ideal for shot-to-shot repeatability
- Foam balls — compress more readily (easier to tune) but compression is more variable run-to-run, causing greater velocity spread
- Felt-covered balls (tennis) — felt grabs the wheel unevenly; shots are inconsistent; not recommended for flywheel use

### Claw compatibility
- Objects ≤ 50 mm are hard to grip: the claw closes past center and loses mechanical advantage
- Objects ≥ 100 mm barely close enough to generate grip force
- **Sweet spot: 55–75 mm** — the claw has 25–50 mm of travel remaining after initial contact, giving stable grip across motor position variation

### Scoop compatibility
- Serving-spoon bowl limits usable diameter to **≤ 65–70 mm**
- Lighter objects (≤ 40 g) scoop more reliably; heavy objects require more arm torque to lift
- Round, smooth-bottomed objects (spheres) roll up into the spoon more reliably than faceted or holed ones

---

## Constraints

1. The scoop (≤ 65–70 mm) and the flywheel (55–75 mm optimal) are **compatible ranges** — objects of 55–65 mm satisfy both
2. The claw also handles this range well — 57 mm is comfortably in the 50–100 mm grip zone
3. Object weight ≤ ~50 g for the slow-catapult arm; no weight limit for flywheel morphology
4. No sharp edges or hard protrusions — must not damage the 3" flex wheel (60A durometer silicone)
5. Must be findable in the room / on a flat surface by the vision system (colored, non-transparent)

---

## Solution Comparison

| Object | Diameter | Weight | Graspability | Scoopability | Flywheel launch | Arm catapult | Safety | Durability | Cost |
|--------|----------|--------|-------------|-------------|----------------|-------------|--------|------------|------|
| **Racquetball** | 57 mm | ~40 g | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★ | ★★★★★ | $1–3 |
| Small foam ball (Nerf-type, 55–70 mm) | 55–70 mm | 20–35 g | ★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★ | $1–5 |
| Wiffle ball | 73 mm | ~20 g | ★★★★★ | ★★★★ | ★★★ | ★★★★ | ★★★★★ | ★★★★ | $1–2 |
| Tennis ball | 67 mm | ~57 g | ★★★★★ | ★★★★ | ★★★ | ★★★ | ★★★★★ | ★★★ | $1–3 |
| VEX 4" foam ball | 100 mm | ~60 g | ★★★★ | ★★ | ★★★★★ | ★★★ | ★★★★★ | ★★★★ | $3–5 |
| Ping pong ball | 40 mm | 2.7 g | ★★ | ★★★★ | ★★★ | ★★★ | ★★★★★ | ★★ | < $1 |
| Lacrosse ball | 64 mm | ~145 g | ★★★★ | ★★★ | ★★★ | ★ | ★★★ | ★★★★★ | $3–8 |

**Notes on each:**
- **Racquetball**: hollow rubber at 57 mm hits all three mechanism sweet spots. Smooth surface launches consistently from flywheel. Hollow construction means it deforms enough on impact to be safe. Extremely durable — designed for repeated high-speed wall impacts.
- **Small foam ball**: marginally better for flywheel (more compression) and maximally safe, but the claw must be torque-limited or it will deform the ball shape. Shot-to-shot consistency is slightly lower because foam compression is more variable.
- **Wiffle ball**: holes are a graspability advantage (claw fingers catch in holes → repeatable grip position), but holes also create asymmetric aerodynamic drag → unpredictable flight arc. Good choice if launch trajectory doesn't matter (e.g., tossing into a bin directly below). Not recommended for aimed flywheel shots.
- **Tennis ball**: felt is the problem — it grabs the flywheel wheel unevenly and causes wobble. Fine for slow-arm catapult. Too heavy for slow catapult at full range.
- **VEX 4" foam ball**: proven flywheel object, but 100 mm does not fit in serving-spoon scoop. If the robot never uses the scoop morphology alongside the launcher morphology, this is viable.
- **Ping pong**: grip is the fatal flaw — claw force (14–42 N) will crush the 2.7 g shell. Also, at 2.7 g, any claw overshoot is immediately destructive.
- **Lacrosse ball**: too heavy for the arm catapult at any useful range; safety concern at speed (solid rubber, 145 g at 0.45 m/s = meaningful impact force).

---

## Recommendation

**Use a standard racquetball** (any brand; US spec: 57.15 ± 0.5 mm diameter, ~40 g, hollow rubber).

**Why it wins across all three morphologies:**
1. **Scoop**: 57 mm diameter vs ~70 mm bowl width — drops cleanly into the spoon bowl; rolls forward onto the bowl during approach; ~40 g is light enough for the arm to lift
2. **Claw**: 57 mm puts the claw ~30–40 mm from fully closed at first contact — maximum mechanical advantage zone; rubber surface provides enough friction against the claw plates that the ball doesn't slip even at minimum torque settings
3. **Flywheel**: hollow rubber compresses ~2–3 mm against the 60A flex wheel — right in the ideal compression range for the 3" wheels; smooth surface ensures consistent energy transfer without the uneven grab of felt; ~40 g is light enough to reach 5–8 m range at 22 m/s rim speed
4. **Safety**: hollow construction collapses on impact — essentially harmless at robot launch velocities (0.45–22 m/s); no bruising risk in indoor lab use
5. **Durability**: racquetballs withstand thousands of wall impacts at much higher velocity than a robot flywheel; will last indefinitely in this application

**Implementation outline:**
1. Acquire 3–6 racquetballs (any brand, ~$5–10 total); mark them with colored tape or paint for vision-sensor detection (racquetballs are typically blue or green — confirm contrast against your arena floor)
2. For claw morphology: tune `max_torque` to ~50% stall (enough to hold, not enough to deform); log `claw_motor.position()` at grip → ball width proxy
3. For scoop morphology: angle the spoon bowl 10–15° upward from horizontal; approach slowly so the ball rolls onto the bowl rather than being pushed off the side
4. For flywheel morphology: set backplate gap = ~51 mm from wheel rim (10% compression on 57 mm ball); tune motor velocity to 560–600 RPM; expect consistent launch with ±5% velocity variation — adjust gap in 1 mm steps if ball skips (too little compression) or motor stalls (too much)

**Risks and mitigations:**
- *Ball rolls away during scoop approach*: slow approach speed (< 50% drive power) and use a low-profile approach angle; spoon tip should touch floor ~20 cm before contact
- *Racquetball too smooth for vision system*: apply 2–3 strips of colored electrical tape; alternatively use a colored racquetball (most are brightly colored already)
- *Flywheel compression too high causes motor stall*: widen the backplate gap by 1 mm increments; log motor current — should stay < 1.5 A at steady state spin-up

**Alternative if constraints change:** If the robot *never* uses the scoop morphology (pure claw + flywheel), upgrade to a **4" (100 mm) foam ball** — it's the VEX-proven flywheel object and the larger size gives more consistent shots. If the flywheel is never used and only arm-catapult + scoop are needed, a **small wiffle ball (73 mm)** has the best grip consistency (holes catch claw reliably).

---

## Next Steps

- To add this to the typed assembly grammar: extend the `game_object` node type with `{diameter_mm, weight_g, material, compressibility}` — the racquetball values become GEN-0 defaults
- To create a task: `/task-add procure-game-objects — buy 5 racquetballs and mark for vision detection`
- To validate: place one racquetball in the arena, run all three morphology task primitives, log telemetry — gap residuals on flywheel launch range vs predicted will be the first real data for the self-model
