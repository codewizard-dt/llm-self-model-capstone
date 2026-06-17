---
topic: ENPIRE — Agentic Robot Policy Self-Improvement; hyperfamila as hobbyist reference; inspiration for independent experiment track
slug: enpire
researched: 2026-06-16
---

# Primary Sources — ENPIRE + Hyperfamila

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://research.nvidia.com/labs/gear/enpire/ | 2026-06-16 | Full ENPIRE architecture: four modules (EN/PI/R/E), task list, MRU/MTU metrics, AutoEnvBench definition, agent comparison (Codex/Claude Code/Kimi), fleet scaling findings, author list |
| S2 | web | https://digg.com/tech/e2a52ozk | 2026-06-16 | Jim Fan's summary of ENPIRE; open-source announcement; "bottleneck shifts from algorithms to feedback loops" framing |
| S3 | web | https://x.com/ludocomito/status/2066550082128814312 | 2026-06-16 | Hyperfamila hackathon summary (content provided by user in conversation — tweet not directly accessible): SO101 + ACT + Codex + Flywheel; 8-hour build; 4 prizes; "AI for Science" framing |
| S4 | web | https://github.com/giacomoran/hyperfamila-hackrome-2026 | 2026-06-16 | Repo structure: /agent and /classifier directories; key scripts: goto_waypoint.py, classify_top_camera.py, eval_flask.py, processor_act_patched.py; Python 85.5% / Shell 14.5% |
| S5 | web | https://raw.githubusercontent.com/giacomoran/hyperfamila-hackrome-2026/main/NOTES.md | 2026-06-16 | Full hardware config (leader/follower ports, camera indices), dataset layout (400 eps across 4 flask targets), training hyperparams (BS64, 10K steps, 100 epochs), syringe end effector timing, H100/L40S SSH compute |
| S6 | web | https://huggingface.co/datasets/giacomoran/hyperfamila_provette | 2026-06-16 | Dataset stats: 400 episodes, 90,620 frames, 2.15 GB; 6-DOF joint states + actions; wrist + overhead cameras; AV1 at 30fps; LeRobot codebase v3.0 |

---

## Excerpts

### S1 — NVIDIA GEAR ENPIRE Project Page
https://research.nvidia.com/labs/gear/enpire/
> "We conjecture that the missing abstraction to automate robotics research is a repeatable feedback loop for real-world policy improvement: reset the scene, execute a policy, verify the outcome, and refine the next iteration."

> "Powered by ENPIRE, frontier coding agents can autonomously develop a policy to achieve a 99% success rate on challenging, dexterous manipulation tasks in the real world, such as PushT, organizing pins into a pin box, and using a cutter to cut a zip tie."

> "We evaluate the physical autoresearch capability of three coding agents: Codex with GPT-5.5, Claude Code with Opus 4.7, and Kimi Code with Kimi K2.6. Instead of asking only whether a final policy succeeds, AutoEnvBench tracks agent-driven research progress over wall-clock time."

### S2 — Digg / Jim Fan announcement
https://digg.com/tech/e2a52ozk
> "A part of our NVIDIA GEAR lab now self-improves tirelessly over night. We just read the reports in the morning. /goal: we all take a holiday and Jensen wouldn't even notice ;) We will be open-sourcing everything, so you can host your self-running robot lab at home too!"

> "We envision the bottleneck in robotics shifting — from building smarter algorithms to building the closed physical feedback loops an agent can finally turn on its own."

### S3 — @ludocomito tweet (content via user)
https://x.com/ludocomito/status/2066550082128814312
> "We're entering the era of AI for Science. In 2026, we trust our agents to do almost anything in software, but to unlock real world experimentation and deploy in fields like bio and med, we need to close the loop with the physical world. Our prototype tries to close this."

> "We trained policies for reaching and moving between flasks using ACT. This proved to be a solid choice: the model itself around 5M params and 100 samples per policy were enough to learn proper movements."

> "Once the robot could move, we gave OpenAI Codex full control of it. In this way we simulated autonomous experimentation: the agent creates hypotheses, tests them in the real world using the arm and uses Paradigma Inc. Flywheel as a platform for managing the knowledge."

### S5 — NOTES.md (hyperfamila)
https://raw.githubusercontent.com/giacomoran/hyperfamila-hackrome-2026/main/NOTES.md
> Hardware: "Follower: hackrome_follower_0 via /dev/tty.usbmodem5A460829821 | Leader: hackrome_leader_0 via /dev/tty.usbmodem5A460824651"

> Syringe: "Suction (min→max): full range in 8 seconds | Emptying (max→min): full range in 4 seconds"

> Training: "batch size 64, 10K steps, 100 epochs" for each of four policies (red/blue/green/output flask)

### S6 — HuggingFace dataset
https://huggingface.co/datasets/giacomoran/hyperfamila_provette
> "90,620 total frames across 400 episodes" | "2.15 GB total, with 100 MB of tabular data and 200 MB of video content"
> LeRobot codebase version 3.0 | AV1 codec at 30 fps | wrist camera 640×480 + top-down 480×640
