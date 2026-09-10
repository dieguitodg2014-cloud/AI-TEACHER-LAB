import json
import tempfile
import unittest
from pathlib import Path

from tools.registry.config_loader import load_tool_registry_config


class ToolRegistryConfigTests(unittest.TestCase):
    def test_loads_tools_and_policy(self):
        data = {
            "tools": [
                {
                    "tool_id": "test-tool",
                    "capabilities": ["lesson_generation"],
                    "quality": 0.8,
                    "cost": 0.0,
                }
            ],
            "policy": {"free_first": True},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tools.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            tools, policy = load_tool_registry_config(path)

        self.assertEqual(tools[0].tool_id, "test-tool")
        self.assertIn("lesson_generation", tools[0].capabilities)
        self.assertTrue(policy["free_first"])

    def test_rejects_invalid_tool_list(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tools.json"
            path.write_text(json.dumps({"tools": {}}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_tool_registry_config(path)


if __name__ == "__main__":
    unittest.main()
