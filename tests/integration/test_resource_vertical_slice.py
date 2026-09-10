import unittest

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import run_lesson_planning


class ResourceVerticalSliceIntegrationTests(unittest.TestCase):
    def test_required_audio_resource_selects_capable_tool(self):
        tools = [
            ToolCandidate(
                tool_id="resource-tool",
                capabilities=frozenset({"lesson_generation", "resource_generation"}),
                quality=0.8,
                reliability=0.9,
                accessibility=1.0,
                speed=0.7,
                cost=0.0,
            )
        ]

        result = run_lesson_planning(
            {
                "context_id": "resource-001",
                "level": "A2",
                "audience": "adult learners",
                "duration_minutes": 90,
                "objective": "Practice listening to short conversations.",
                "constraints": [],
            },
            tools=tools,
        )

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNotNone(result.resource_task)
        self.assertEqual(result.resource_decision.action, "CREATE")
        self.assertEqual(result.resource_decision.resource_type, "audio")
        self.assertIsNotNone(result.resource_tool)
        self.assertEqual(result.resource_tool.tool_id, "resource-tool")

    def test_required_resource_without_capable_tool_has_no_selected_resource_tool(self):
        tools = [
            ToolCandidate(
                tool_id="lesson-only-tool",
                capabilities=frozenset({"lesson_generation"}),
            )
        ]

        result = run_lesson_planning(
            {
                "context_id": "resource-002",
                "level": "A2",
                "audience": "adult learners",
                "duration_minutes": 90,
                "objective": "Practice listening to short conversations.",
                "constraints": [],
            },
            tools=tools,
        )

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNotNone(result.resource_task)
        self.assertIsNone(result.resource_tool)

    def test_no_resource_needed_does_not_select_resource_tool(self):
        tools = [
            ToolCandidate(
                tool_id="resource-tool",
                capabilities=frozenset({"lesson_generation", "resource_generation"}),
            )
        ]

        result = run_lesson_planning(
            {
                "context_id": "resource-003",
                "level": "A2",
                "audience": "adult learners",
                "duration_minutes": 90,
                "objective": "Discuss past experiences and ask follow-up questions.",
                "constraints": [],
            },
            tools=tools,
        )

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNone(result.resource_task)
        self.assertIsNone(result.resource_tool)


if __name__ == "__main__":
    unittest.main()
