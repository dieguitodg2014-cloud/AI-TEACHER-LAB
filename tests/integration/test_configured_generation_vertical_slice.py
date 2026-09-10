import json
import tempfile
import unittest
from pathlib import Path

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import run_lesson_planning


class ConfiguredGenerationVerticalSliceTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Discuss past experiences and ask follow-up questions.",
            "group_size": 12,
            "topic": "life experiences",
        }

    def test_real_tool_registry_config_controls_generation(self):
        config = {
            "tools": [
                {
                    "tool_id": "configured-generator",
                    "capabilities": ["lesson_generation"],
                    "quality": 9,
                    "reliability": 9,
                    "accessibility": 9,
                    "speed": 9,
                    "cost": 0,
                }
            ],
            "policy": {"free_first": True},
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tools.json"
            path.write_text(json.dumps(config), encoding="utf-8")

            def generator(request, errors):
                return {
                    "level": request["level"],
                    "objective": request["objective"],
                    "duration_minutes": request["duration_minutes"],
                    "activities": [{"name": "communicative task"}],
                }

            result = run_lesson_planning(
                self.request,
                generators={"configured-generator": generator},
                tool_config_path=path,
            )

        self.assertEqual(result.status, "READY")
        self.assertEqual(result.generation["tool_id"], "configured-generator")
        self.assertEqual(result.generation["result"]["status"], "READY")

    def test_configured_registry_without_generator_handoffs(self):
        config = {
            "tools": [
                {
                    "tool_id": "configured-generator",
                    "capabilities": ["lesson_generation"],
                    "quality": 9,
                    "reliability": 9,
                    "accessibility": 9,
                    "speed": 9,
                    "cost": 0,
                }
            ],
            "policy": {"free_first": True},
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tools.json"
            path.write_text(json.dumps(config), encoding="utf-8")

            result = run_lesson_planning(
                self.request,
                generators={},
                tool_config_path=path,
            )

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertEqual(result.generation["errors"], ["GENERATOR_UNAVAILABLE"])


if __name__ == "__main__":
    unittest.main()
