---
topic: Deep dive into Prof. Justin Hart's robot self-modeling papers, citations, and LLM-in-robotics work as a direct predecessor to the capstone's primary concept
slug: justin-hart-self-modeling
researched: 2026-06-16
---

# Primary Sources — Justin Hart Self-Modeling Research

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://justinhart.net/publications/ | 2026-06-16 | Complete publication list: 40+ papers spanning 2006–2025; confirmed PhD thesis title/date; complete arc of self-modeling work (2010–2017); Dobby publication details |
| S2 | web | https://scazlab.yale.edu/sites/default/files/files/Hart_Dissertation_Robotselfmodeling.pdf | 2026-06-16 | PhD thesis abstract snippet: robot Nico (infant humanoid) creates "highly-accurate self-representation" via visual self-observation; geometric/kinematic self-model built bottom-up |
| S3 | web | https://www.cs.utexas.edu/people/faculty-researchers/justin-hart | 2026-06-16 | Current research scope: "use of large language models and other foundation models in robotics"; Living with Robots Laboratory description |
| S4 | web | https://arxiv.org/html/2310.06303 | 2026-06-16 | Dobby full paper content: GPT-4 function calling architecture, semantic embedding action matcher, history buffer memory, Segway RMP hardware, full experimental results (22 participants, 14.3 vs 5.8 min) |
| S5 | web | https://arxiv.org/abs/2503.05398 | 2026-06-16 | 2025 self-modeling paper: "Learning High-Fidelity Robot Self-Model with Articulated 3D Gaussian Splatting" — confirms field still pursuing numerical self-models |
| S6 | web | https://arxiv.org/abs/2209.02010 | 2026-06-16 | "On the Origins of Self-Modeling": self-modeling value scales with robot complexity (R²=0.90); confirms self-modeling as active research area |
| S7 | web | https://arxiv.org/abs/2111.06389 | 2026-06-16 | "Full-Body Visual Self-Modeling of Robot Morphologies" — visual neural field self-modeling; confirms numerical track is active, language track is unoccupied |

## Excerpts

### S1 — Hart Publications Page (complete list)
https://justinhart.net/publications/
> PhD thesis entry: **"Robot Self-Modeling"**, Justin Hart, Yale University, December 2014.
> 2017 journal entry: **"Robot Self-Modeling"**, J. W. Hart & B. Scassellati, International Journal of Humanoid Robotics.
> 2024 Dobby: **"Dobby: A Conversational Service Robot Driven by GPT-4"**, Stark, Chun, Charleston, Ravi, Pabon, Sunkari, Mohan, Stone, Hart. RO-MAN 2024. DOI: https://doi.org/10.1109/RO-MAN60168.2024.10731375

### S2 — PhD Thesis Abstract Snippet (Yale scazlab)
https://scazlab.yale.edu/sites/default/files/files/Hart_Dissertation_Robotselfmodeling.pdf
> "Abstract Robot Self-Modeling Justin Wildrick Hart 2014 ... an upper torso humanoid robot, Nico, creates a highly-accurate self-representation"
> "search presented in this thesis attempts to enable robots to learn unified models of [their own body]"

### S3 — UT Austin CS Faculty Profile
https://www.cs.utexas.edu/people/faculty-researchers/justin-hart
> "his work spans social and autonomous human-robot interaction and the technologies to support wide-spread service robots, such as semantic mapping and the use of large language models and other foundation models in robotics."

### S4 — Dobby Paper (arXiv HTML)
https://arxiv.org/html/2310.06303
> "Dobby uses an LLM acting as an agent for both top-[level task planning and conversation]"
> "[The system] embeds a conversational AI agent in an embodied system for natural language understanding and intelligent decision-making for service tasks; integrating task planning and human-like conversation."
> Results: "Interaction Time: 14.3 minutes (conversational) vs. 5.8 minutes (non-conversational); Destinations Visited: 5.27 vs. 3.00; Personality Rating: 5.88 vs. 2.09 (7-point scale)"
> Architecture: "GPT-4 functions as the system's 'artificially intelligent agent with vast general knowledge, basic reasoning skills, and advanced communication abilities.' The implementation uses OpenAI's chat completion API with the gpt-4-0613 model, which features function calling to generate structured JSON objects triggering robot commands."
> Memory: "System messages accumulate in a history buffer sent with each API query, enabling context-aware dialogue and behavior generation."
> Action matching: "the system uses semantic matching via embeddings. The process compares cosine similarity between LLM-generated action strings and predefined action titles, selecting the highest-matching option."

### S6 — On the Origins of Self-Modeling
https://arxiv.org/abs/2209.02010
> "Self-Modeling is the process by which an agent, such as an animal or machine, learns to create a predictive model of its own dynamics. Once captured, this self-model can then allow the agent to plan and evaluate various potential behaviors internally using the self-model, rather than using costly physical experimentation."
> "strong statistical relationship (R²=0.90) between robot complexity and the value of self-modeling"
