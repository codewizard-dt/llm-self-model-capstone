---
topic: "VEX V5 Classroom Starter Kit — configuration spec audit: remove all booster-kit-only vocabulary entries"
slug: vex-v5-starter-kit-configurations
researched: 2026-06-17
---

# Primary Sources — VEX V5 Starter Kit Config Spec Audit

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://www.vexrobotics.com/276-4840.html | 2026-06-17 | V5 Smart Motor product page: "Ships with a standard [200 RPM, 18:1] gear cartridge." Confirms 18:1 is the only cartridge shipped with each motor |
| S2 | web | https://nooby.tech/en/shop/1138-vex-v5-smart-motor-6-1-cartridge-600-rpm.html | 2026-06-17 | Third-party reseller confirming: "Cartridges for 36:1 (100 RPM) & 6:1 (600 RPM) are available separately" — both are sold apart from the motor, not bundled |
| S3 | codebase | `raw/research/vex-v5-classroom-starter-kit/index.md` | 2026-06-17 | Full Starter Kit BOM: "(2) 4" Omni Wheels", "(2) 4" Wheels", "(4) V5 Smart Motors" — no separate cartridge packs listed; 2+2 wheel split confirmed |
| S4 | codebase | `raw/research/vex-v5-booster-kit/index.md` | 2026-06-17 | Booster Kit full contents: Intake Roller (276-1499) and Motor Clutch (276-1098) are listed as booster-kit-only parts; confirms "roller" end-effector requires booster kit |

---

## Excerpts

### S1 — VEX V5 Smart Motor & Gear Cartridges product page
https://www.vexrobotics.com/276-4840.html
> "Ships with a standard [200 RPM, 18:1] gear cartridge."
> "18:1 (200 RPM) - Standard gear ratio for drive train applications"

### S2 — VEX V5 Smart Motor 6:1 Cartridge (third-party reseller)
https://nooby.tech/en/shop/1138-vex-v5-smart-motor-6-1-cartridge-600-rpm.html
> "Ships with the standard gear cartridge of 18:1 (200 RPM) Cartridges for 36:1 (100 RPM) & 6:1 (600 RPM) are available separately"

### S3 — Starter Kit BOM (wheels and motors)
`raw/research/vex-v5-classroom-starter-kit/index.md`
> "(2) 4" Omni Wheels"
> "(2) 4" Wheels"
> "(4) V5 Smart Motors"

### S4 — Booster Kit contents (roller + clutch)
`raw/research/vex-v5-booster-kit/index.md`
> "| **Intake Roller** | 276-1499 | 4 | Enables **intake/conveyor** grab mechanisms |"
> "| **Motor Clutch** | 276-1098 | 3 | Slip/torque-limit element → overload protection + catapult-style release |"
