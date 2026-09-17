import unittest

from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import select_resource_tool_decision
from core.orchestration.tool_selector import ToolCandidate


class ResourceToolDecisionAuthorityTests(unittest.TestCase):
    def test_selection_produces_resource_tool_decision(self):
        task = TaskPacket(
            task_id="resource-task",
            task_type="RESOURCE_PRODUCTION",
            objective="Practice listening.",
            level="A2",
            required_output="audio",
            constraints=(),
            quality_criteria=(),
        )
        decision = select_resource_tool_decision(
            task,
            [
                ToolCandidate(
                    "resource-tool",
                    frozenset({"resource_generation", "resource_output:audio"}),
                )
            ],
        )
        self.assertIsNotNone(decision)
        self.assertEqual(decision.selected_tool, "resource-tool")
        self.assertEqual(decision.task_type, "RESOURCE_PRODUCTION")
        self.assertEqual(decision.fallback_policy, ())
        self.assertTrue(decision.human_handoff_allowed)


if __name__ == "__main__":
    unittest.main()
