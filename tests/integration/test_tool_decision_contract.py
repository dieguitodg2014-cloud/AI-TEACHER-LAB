import unittest

from core.orchestration.generation_orchestrator import GenerationOrchestrator
from core.orchestration.tool_selector import ToolCandidate


class ToolDecisionContractTests(unittest.TestCase):
    def test_capability_selection_and_human_handoff_are_explicit(self):
        capable = ToolCandidate(
            tool_id="capable-tool",
            capabilities=frozenset({"lesson_generation"}),
            quality=1.0,
            reliability=1.0,
            accessibility=1.0,
            speed=1.0,
            cost=0.0,
        )
        blocked = ToolCandidate(
            tool_id="blocked-tool",
            capabilities=frozenset({"lesson_generation"}),
            quality=1.0,
            reliability=1.0,
            accessibility=1.0,
            speed=1.0,
            cost=0.0,
        )

        generator = lambda request, errors: {
            "level": request["level"],
            "objective": request["objective"],
            "duration_minutes": request["duration_minutes"],
            "activities": [{"name": "Contract test"}],
        }

        orchestrator = GenerationOrchestrator(
            [blocked, capable],
            {"capable-tool": generator},
        )
        result = orchestrator.run(
            {
                "level": "A2",
                "objective": "Practice communication.",
                "duration_minutes": 60,
            },
            blocked_tools={"blocked-tool"},
        )

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["tool_id"], "capable-tool")

        no_match = GenerationOrchestrator([capable], {}).run(
            {
                "level": "A2",
                "objective": "Practice communication.",
                "duration_minutes": 60,
            },
            required_capabilities={"unsupported_capability"},
        )
        self.assertEqual(no_match["status"], "HUMAN_HANDOFF")
        self.assertEqual(no_match["errors"], ["NO_SUITABLE_TOOL"])


if __name__ == "__main__":
    unittest.main()
