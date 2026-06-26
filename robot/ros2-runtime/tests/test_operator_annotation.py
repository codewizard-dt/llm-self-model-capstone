from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vexy_ros.operator_annotation import (  # noqa: E402
    AnnotationCommand,
    annotation_json,
    build_annotation,
    build_parser,
    label_help,
    parse_annotation_command,
)


class OperatorAnnotationTests(unittest.TestCase):
    def test_default_hotkeys_map_to_calibration_labels(self) -> None:
        self.assertEqual(parse_annotation_command("1"), AnnotationCommand("normal_drive"))
        self.assertEqual(parse_annotation_command("4"), AnnotationCommand("stuck_or_slipping"))
        self.assertEqual(parse_annotation_command("space"), AnnotationCommand("clear_label"))

    def test_custom_label_can_include_note(self) -> None:
        command = parse_annotation_command("contact left wall")

        self.assertEqual(command, AnnotationCommand("contact", "left wall"))

    def test_invalid_label_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_annotation_command("BadLabel")

    def test_annotation_json_is_compact_and_timestamped(self) -> None:
        payload = annotation_json("3 gentle bump", source="test", wall_ms=123)

        self.assertEqual(
            json.loads(payload or ""),
            {
                "type": "annotation",
                "label": "contact",
                "wall_ms": 123,
                "source": "test",
                "note": "gentle bump",
            },
        )

    def test_build_annotation_uses_command_fields(self) -> None:
        payload = build_annotation(
            AnnotationCommand("turning", "left arc"), source="agent", wall_ms=5
        )

        self.assertEqual(payload["label"], "turning")
        self.assertEqual(payload["note"], "left arc")
        self.assertEqual(payload["source"], "agent")
        self.assertEqual(payload["wall_ms"], 5)

    def test_parser_defaults_match_runtime_topic(self) -> None:
        args = build_parser().parse_args([])

        self.assertEqual(args.topic, "/operator/annotation")
        self.assertEqual(args.source, "agent_hotkey")

    def test_label_help_lists_operator_keys(self) -> None:
        text = label_help()

        self.assertIn("1 normal_drive", text)
        self.assertIn("6 scored_or_delivered", text)

    def test_setup_declares_annotation_entrypoint(self) -> None:
        setup_text = (ROOT / "setup.py").read_text()

        ast.parse(setup_text)
        self.assertIn(
            "vexy_operator_annotation = vexy_ros.operator_annotation:main",
            setup_text,
        )


if __name__ == "__main__":
    unittest.main()
