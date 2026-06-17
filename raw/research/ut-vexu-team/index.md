---
topic: All people involved in UT Austin's VEX U Robotics Team that Won 1st Place, and the specific UT lab or professor involved
slug: ut-vexu-team
researched: 2026-06-16
sources: [./sources.md]
---

# Research: UT Austin VEX U Championship Team — People, Lab & Collaboration Angles

> The winning team is **GHOST** (team 1565X), the VEX U committee of UT Austin's **IEEE Robotics and Automation Society (RAS)**. Nine people are named in coverage; two are PhD students in ASE (the highest-value outreach targets). The team has no named faculty advisor in public sources — it is a student-run org. However, the single most relevant UT professor for the capstone is **Prof. Justin Hart** (CS, hart@cs.utexas.edu), whose listed expertise includes **robot self-modeling** and LLMs-in-robotics — directly matching the capstone's primary concept. Hart's lab is a separate path from the VEX team but far more valuable for intellectual collaboration.

---

## Research Questions

1. Who are the named members of the championship VEX U team?
2. What are their degrees, departments, and likely research areas?
3. Is there a faculty advisor for UT IEEE RAS / the GHOST VEX team?
4. Which UT lab or professor is most relevant to the capstone's robot self-model concept?
5. What are the best contact paths for collaboration or hardware access?

---

## Current State (Codebase / Wiki Context)

- `wiki/knowledge/concepts/llm-authored-self-model.md` — THE PRIMARY IDEA: LLM authors a structured self-description from finite parts; multi-LLM critics attack it
- Previous research (`raw/research/robot-rental-austin/index.md`) recommended UT Austin Texas Robotics as an outreach target for supervised VEX V5 hardware access

---

## Key Findings

### Team Members [S1][S2]

All nine members from the championship roster:

| Name | Program | Role / Notes |
|------|---------|--------------|
| **Karmanyaah Malhotra** | CS '27 | Lead programmer; motion planning, IPC, Linux integration; has personal website + GitHub (`karmanyaahm`) |
| **Michael Portillo** | Unknown | Quoted in press coverage; competition strategy focus |
| **Johnny Shen** | ECE '28 | Team member |
| **Richard Aguilar** | ASE '28 | Team member |
| **Jake Wendling** | COE '25 | Graduated May 2025 |
| **Joseph Weiss** | ME @ Austin Community College '27 | Team member |
| **Joseph Romero** | ME '26 | Team member |
| **Melissa Cruz** | ASE PhD | Graduate student — **highest-value outreach target** |
| **Maxx Wilson** | ASE PhD | Graduate student — **highest-value outreach target** |

### Team Identity [S1][S2][S3]

- **Team name**: GHOST (VEX team ID: 1565X)
- **Parent org**: UT Austin IEEE Robotics and Automation Society (RAS), founded 1997
- **Tech stack**: VEX V5 Brain + Nvidia Jetson; LIDAR; Intel Realsense camera; ROS; C++ autonomous framework
- **GitHub**: github.com/VEXU-GHOST (20 repos, private members) and github.com/ut-ras
- **Website**: ras.ece.utexas.edu
- **Contact email**: ut.ieee.ras+web@gmail.com

### Faculty Advisor — Not Publicly Named [S4]

IEEE RAS is a student-run org. IEEE RAS student branch chapters are formally required to have a faculty advisor, but no advisor is named on the ras.ece.utexas.edu website, on the ECE department's student orgs page, or in any news coverage. The best path to finding the advisor is to email ut.ieee.ras+web@gmail.com or attend an open Robotathon event.

### ⭐ Prof. Justin Hart — Most Relevant UT Faculty for the Capstone [S5][S6]

**Justin Hart**, Assistant Professor of Practice, UT Austin Department of Computer Science  
**Email**: hart@cs.utexas.edu | **Phone**: (512) 998-1757  
**Lab**: Living with Robots Laboratory (lwrl.cs.utexas.edu implied)

Published expertise that directly overlaps the capstone's primary concept:
- **"Robot Self-Modeling"** (2017 paper with B. Scassellati)
- **"A Robotic Model of the Ecological Self"** (2011, IEEE-RAS Humanoid Robots)
- Use of **large language models and foundation models in robotics**
- Semantic mapping, autonomous human-robot interaction, service robots

Hart co-directs the **"Living and Working with Robots" project** under UT Good Systems and collaborates on the **RoboCup@Home team** (service robots in home environments — closest analog to the capstone scenario).

This is the single most valuable contact in all of UT Austin for this capstone: he has literally published on robot self-modeling and is now applying LLMs to service robots.

### Other Relevant UT Faculty [S7]

| Professor | Dept | Email | Relevance |
|-----------|------|-------|-----------|
| Joydeepb Biswas | CS | joydeepb@cs.utexas.edu | Long-term robot autonomy, service mobile robots |
| Luis Sentis | ASE | lsentis@austin.utexas.edu | Humanoid robots, human-centered robotics |
| Yuke Zhu | CS | yukez@cs.utexas.edu | Robot learning, interactive perception |
| Peter Stone | CS | pstone@cs.utexas.edu | Multi-agent systems, RoboCup |

---

## Constraints

- UT IEEE RAS is a student org — collaboration requires either student relationship or faculty advisor approval
- PhD students Melissa Cruz and Maxx Wilson are in ASE (aerospace/controls) — their research may not directly overlap the LLM+robot angle, but they have hands-on VEX V5 hardware experience
- Prof. Hart's lab uses service robots (not VEX V5) — he's the intellectual collaboration target, not the hardware access target

---

## Recommendation

**Two parallel outreach paths — pursue both:**

### Path A: Hardware Access (VEX V5 hardware for the experiment)
**Contact**: Melissa Cruz and/or Maxx Wilson (ASE PhD) via Texas Robotics  
**How**: Email robotics@utexas.edu or find their profiles on robotics.utexas.edu → ask for a supervised lab session with their VEX V5 hardware in exchange for capstone demo credit  
**Fallback**: Email ut.ieee.ras+web@gmail.com to reach the GHOST team directly

### Path B: Intellectual Collaboration (robot self-model concept validation)
**Contact**: Prof. Justin Hart — hart@cs.utexas.edu — (512) 998-1757  
**Pitch**: "We're building an LLM-authored robot self-model loop on VEX V5 hardware — your 2017 Robot Self-Modeling paper is a direct predecessor. Would you have 30 minutes to discuss, or could a grad student observe our demo?"  
**Value**: A UT professor with exact expertise lending credibility to the capstone concept is worth more than any hardware shortcut

---

## Next Steps

- Email Prof. Justin Hart (hart@cs.utexas.edu) with a 3-sentence capstone pitch referencing his Robot Self-Modeling paper — this week
- Email Texas Robotics general contact (robotics@utexas.edu) asking for VEX U team contact for a collaboration request
- Look up Melissa Cruz and Maxx Wilson on robotics.utexas.edu/people to find their advisor lab and direct email
- Run `/wiki-ingest raw/research/ut-vexu-team/index.md` to add this to the knowledge base
- Consider `/task-add Draft outreach emails to Prof. Justin Hart and UT Texas Robotics VEX U PhD students`
