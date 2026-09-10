import unittest

from core.orchestration.tool_selector import ToolCandidate, select_tool


class ToolSelectorTests(unittest.TestCase):
    def test_selects_best_eligible_free_tool(self):
        tools = [
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

        selected = select_tool(tools, {"lesson_generation"})
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


if __name__ == "__main__":
    unittest.main()
