import json
import unittest
from pathlib import Path

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import run_lesson_planning


GOLDEN_CASE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "regression"
    / "golden_case_a2_present_perfect.json"
)


class GoldenCaseA2PresentPerfectGenerationTests(unittest.TestCase):
    def test_golden_case_generation_passes_tool_selection_and_qc(self):
        case = json.loads(GOLDEN_CASE.read_text(encoding="utf-8"))
        request = case["request"]

        tool_id = "golden-test-generator"
        tool = ToolCandidate(
            tool_id=tool_id,
            capabilities=frozenset({"lesson_generation"}),
            quality=1.0,
            reliability=1.0,
            accessibility=1.0,
            speed=1.0,
            cost=0.0,
        )

        calls = []

        def generator(generation_request, previous_errors):
            calls.append(list(previous_errors))
            return {
                "level": generation_request["level"],
                "objective": generation_request["objective"],
                "duration_minutes": generation_request["duration_minutes"],
                "topic": generation_request["topic"],
                "activities": [
                    {"name": "Golden Case activity"}
                ],
            }

        result = run_lesson_planning(
            request,
            tools=[tool],
            generators={tool_id: generator},
        )

        self.assertEqual(result.status, "READY")
        self.assertIsNotNone(result.generation)
        self.assertEqual(result.generation["tool_id"], tool_id)

        generation_result = result.generation["result"]
        self.assertEqual(generation_result["status"], "READY")
        self.assertEqual(generation_result["errors"], [])
        self.assertEqual(generation_result["attempts"], 1)
        self.assertEqual(generation_result["qc"]["status"], "READY")
        self.assertFalse(generation_result["qc"]["critical_failure"])
        self.assertEqual(generation_result["qc"]["score"], 100.0)
        self.assertEqual(calls, [[]])


if __name__ == "__main__":
    unittest.main()
