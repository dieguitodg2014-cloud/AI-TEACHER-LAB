import unittest

from core.orchestration.generation_orchestrator import GenerationOrchestrator
from core.orchestration.tool_selector import ToolCandidate


class GenerationOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.tools = [
            ToolCandidate(
                "free-generator",
                frozenset({"lesson_generation"}),
                quality=9,
                reliability=9,
                accessibility=9,
                speed=8,
                cost=0,
            ),
            ToolCandidate(
                "premium-generator",
                frozenset({"lesson_generation"}),
                quality=10,
                reliability=10,
                accessibility=10,
                speed=10,
                cost=5,
            ),
        ]
        self.request = {
            "level": "A2",
            "objective": "Discuss past experiences.",
            "duration_minutes": 90,
        }

    def test_selected_tool_executes_generation(self):
        def generator(request, errors):
            return {
                "level": request["level"],
                "objective": request["objective"],
                "duration_minutes": request["duration_minutes"],
                "activities": [{"name": "discussion"}],
            }

        orchestrator = GenerationOrchestrator(
            self.tools,
            {"free-generator": generator},
        )
        result = orchestrator.run(self.request)

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["tool_id"], "free-generator")

    def test_missing_generator_causes_handoff(self):
        orchestrator = GenerationOrchestrator(self.tools, {})
        result = orchestrator.run(self.request)

        self.assertEqual(result["status"], "HUMAN_HANDOFF")
        self.assertEqual(result["errors"], ["GENERATOR_UNAVAILABLE"])

    def test_no_capable_tool_causes_handoff(self):
        orchestrator = GenerationOrchestrator(self.tools, {})
        result = orchestrator.run(
            self.request,
            required_capabilities={"source_based_multimedia"},
        )

        self.assertEqual(result["status"], "HUMAN_HANDOFF")
        self.assertEqual(result["errors"], ["NO_SUITABLE_TOOL"])


if __name__ == "__main__":
    unittest.main()
