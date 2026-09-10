import unittest

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import run_lesson_planning


class GenerationVerticalSliceTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Discuss past experiences and ask follow-up questions.",
            "group_size": 12,
            "topic": "life experiences",
        }
        self.tools = [
            ToolCandidate(
                "test-generator",
                frozenset({"lesson_generation"}),
                quality=9,
                reliability=9,
                accessibility=9,
                speed=9,
                cost=0,
            )
        ]

    def test_full_slice_reaches_ready(self):
        def generator(request, errors):
            return {
                "level": request["level"],
                "objective": request["objective"],
                "duration_minutes": request["duration_minutes"],
                "topic": request["topic"],
                "activities": [{"name": "communicative task"}],
            }

        result = run_lesson_planning(
            self.request,
            tools=self.tools,
            generators={"test-generator": generator},
        )

        self.assertEqual(result.status, "READY")
        self.assertEqual(result.generation["tool_id"], "test-generator")
        self.assertEqual(result.generation["result"]["status"], "READY")

    def test_full_slice_can_handoff(self):
        result = run_lesson_planning(
            self.request,
            tools=[],
            generators={},
        )

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertIn("NO_SUITABLE_TOOL", result.errors)

    def test_without_execution_dependencies_it_remains_planned(self):
        result = run_lesson_planning(self.request)

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNone(result.generation)


if __name__ == "__main__":
    unittest.main()
