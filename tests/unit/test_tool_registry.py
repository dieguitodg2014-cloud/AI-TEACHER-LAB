import unittest

from core.orchestration.tool_selector import ToolCandidate
from tools.registry import ToolRegistry


class ToolRegistryTests(unittest.TestCase):
    def test_registry_returns_registered_tools(self):
        tool = ToolCandidate("test-tool", frozenset({"lesson_generation"}))
        registry = ToolRegistry([tool])

        self.assertEqual(registry.get("test-tool"), tool)
        self.assertEqual(registry.list_available(), [tool])

    def test_registry_rejects_duplicate_ids(self):
        tool = ToolCandidate("test-tool", frozenset({"lesson_generation"}))
        registry = ToolRegistry([tool])

        with self.assertRaises(ValueError):
            registry.register(tool)


if __name__ == "__main__":
    unittest.main()
