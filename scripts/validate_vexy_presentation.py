#!/usr/bin/env python3
"""Validate the committed Vexy mission presentation package."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "presentation" / "vexy-mission"

ROOT_REQUIRED_FILES = [
    ".github/workflows/presentation-validate.yml",
]

REQUIRED_FILES = [
    "README.md",
    "TEAM_EDIT_GUIDE.md",
    "index.html",
    "styles.css",
    "presentation.js",
    "presentation-plan.json",
    "vercel.json",
    "team-handoff.html",
    "phase-execution.html",
    "run-of-show.html",
    "rehearsal-console.html",
    "shareback-proof.html",
    "speaker-assets.html",
    "demo-readiness.html",
    "data/diagram-options.json",
    "data/phase-audit.json",
    "data/review-config.json",
    "data/speaker-assets.json",
    "media/vexy_identity_lock_trailer.mp4",
    "media/grace_mission_control.mp4",
    "media/david_mission_commander.mp4",
    "media/erick_mission_commands.mp4",
    "media/jake_holographic_screen.mp4",
    "media/red_mechanism_macro_slide.mp4",
    "media/team-final-hero.jpeg",
    "media/yellow_ball_apriltag.jpeg",
]

REQUIRED_TEXT = {
    "index.html": [
        "Vexy connects a real VEX V5 robot to a language-based self-model.",
        "telemetry, vision state, operator result, and gap",
        "The next model only earns trust after that evidence moves through the analyzer and critic gate.",
        "Grace",
        "David Taylor",
        "Erick",
        "Jake",
    ],
    "README.md": [
        "Vercel Project Root Directory: `presentation/vexy-mission`",
        "Direct teammate edit links",
        "Grace",
        "David Taylor",
        "Erick",
        "Jake",
    ],
    "TEAM_EDIT_GUIDE.md": [
        "How teammates update their own section",
        "presentation/vexy-mission",
        "make presentation-validate",
        "Vercel preview",
        "Grace",
        "David Taylor",
        "Erick",
        "Jake",
    ],
    "phase-execution.html": [
        "Phase 5/6 Execution Dashboard",
        "Copy teammate launch message",
        "Copy final proof checklist",
        "No live robot success claim without run evidence",
    ],
    "team-handoff.html": [
        "phase-execution.html",
        "?edit=1&owner=grace",
        "?edit=1&owner=david",
        "?edit=1&owner=erick",
        "?edit=1&owner=jake",
    ],
}

REJECTED_TEXT = [
    "The capstone is impressive because",
    "Mission difficult became mission possible",
    "RepoRipper/output",
    "output/vexy-mission-presentation-plan-2026-06-29",
    "https://vexy-mission-presentation-plan-2026.vercel.app",
]

ROOT_REQUIRED_TEXT = {
    ".github/workflows/presentation-validate.yml": [
        "name: Presentation validation",
        "make presentation-validate",
        "presentation/vexy-mission/**",
        "scripts/validate_vexy_presentation.py",
    ],
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    failures: list[str] = []

    for relative_path in ROOT_REQUIRED_FILES:
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing required file: {relative_path}")

    for relative_path, snippets in ROOT_REQUIRED_TEXT.items():
        path = ROOT / relative_path
        if path.is_file():
            text = read_text(path)
            for snippet in snippets:
                if snippet not in text:
                    failures.append(f"{relative_path} missing text: {snippet}")

    if not SITE.is_dir():
        failures.append(f"missing presentation directory: {SITE.relative_to(ROOT)}")
    else:
        for relative_path in REQUIRED_FILES:
            path = SITE / relative_path
            if not path.is_file():
                failures.append(f"missing required file: {path.relative_to(ROOT)}")

        for relative_path, snippets in REQUIRED_TEXT.items():
            path = SITE / relative_path
            if path.is_file():
                text = read_text(path)
                for snippet in snippets:
                    if snippet not in text:
                        failures.append(f"{relative_path} missing text: {snippet}")

        all_text = "\n".join(
            read_text(path)
            for path in SITE.rglob("*")
            if path.is_file() and path.suffix.lower() in {".html", ".md", ".json", ".js", ".css"}
        )
        for rejected in REJECTED_TEXT:
            if rejected in all_text:
                failures.append(f"presentation contains rejected text: {rejected}")

        plan_path = SITE / "presentation-plan.json"
        if plan_path.is_file():
            plan = json.loads(read_text(plan_path))
            scenes = plan.get("scenes", [])
            speakers = {scene.get("speaker") for scene in scenes if scene.get("speaker")}
            for speaker in {"Grace", "David Taylor", "Erick", "Jake"}:
                if speaker not in speakers:
                    failures.append(f"presentation plan missing speaker: {speaker}")
            if len(scenes) < 10:
                failures.append("presentation plan must contain at least 10 scenes")

        vercel_path = SITE / "vercel.json"
        if vercel_path.is_file():
            vercel = json.loads(read_text(vercel_path))
            if vercel.get("cleanUrls") is not True:
                failures.append("vercel.json must enable cleanUrls")

    result = {
        "site": str(SITE.relative_to(ROOT)),
        "score": 0 if failures else 100,
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
