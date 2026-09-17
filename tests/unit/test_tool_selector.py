import unittest

from core.foundation.models import ToolDecision
from core.orchestration.tool_selector import ToolCandidate, select_tool, select_tool_decision


class ToolSelectorTests(unittest.TestCase):
    def setUp(self):
        self.tools = [
            ToolCandidate(
                "premium-tool",
                frozenset({"lesson_generation"}),
                quality=10,
                reliability=10,
                accessibility=10,
                speed=10,
                cost=5,
            ),
            ToolCandidate(
                "free-tool",
                frozenset({"lesson_generation"}),
                quality=9,
                reliability=9,
                accessibility=9,
                speed=9,
                cost=0,
            ),
        ]

    def test_selects_best_eligible_free_tool(self):
        selected = select_tool(self.tools, {"lesson_generation"})
        self.assertEqual(selected.tool_id, "free-tool")

    def test_capability_mismatch_is_not_selected(self):
        tools = [
            ToolCandidate("visual-tool", frozenset({"visual_generation"}), quality=10),
        ]
        self.assertIsNone(select_tool(tools, {"lesson_generation"}))

    def test_blocked_tool_is_not_selected(self):
        tools = [
            ToolCandidate("preferred-tool", frozenset({"lesson_generation"}), quality=10),
            ToolCandidate("fallback-tool", frozenset({"lesson_generation"}), quality=8),
        ]
        selected = select_tool(tools, {"lesson_generation"}, blocked_tools={"preferred-tool"})
        self.assertEqual(selected.tool_id, "fallback-tool")

    def test_selection_produces_authoritative_tool_decision(self):
        decision = select_tool_decision(
            self.tools,
            {"lesson_generation"},
            task_type="LESSON_GENERATION",
        )

        self.assertIsInstance(decision, ToolDecision)
        self.assertEqual(decision.selected_tool, "free-tool")
        self.assertEqual(decision.task_type, "LESSON_GENERATION")
        self.assertEqual(decision.fallback_policy, ())
        self.assertTrue(decision.human_handoff_allowed)

    def test_explicit_fallback_policy_is_preserved(self):
        decision = select_tool_decision(
            self.tools,
            {"lesson_generation"},
            fallback_policy=("premium-tool",),
            human_handoff_allowed=False,
        )

        self.assertEqual(decision.selected_tool, "free-tool")
        self.assertEqual(decision.fallback_policy, ("premium-tool",))
        self.assertFalse(decision.human_handoff_allowed)


if __name__ == "__main__":
    unittest.main()
