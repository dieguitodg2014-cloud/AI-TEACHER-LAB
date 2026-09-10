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


class GoldenCaseRevisionLoopTests(unittest.TestCase):
    def test_failed_generation_is_revised_and_then_approved(self):
        case = json.loads(GOLDEN_CASE.read_text(encoding="utf-8"))
        request = case["request"]
        tool_id = "golden-revision-generator"
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
            if len(calls) == 1:
                return {
                    "level": "B1",
                    "objective": generation_request["objective"],
                    "duration_minutes": 120,
                    "topic": generation_request["topic"],
                    "activities": [{"name": "Incorrect first attempt"}],
                }
            return {
                "level": generation_request["level"],
                "objective": generation_request["objective"],
                "duration_minutes": generation_request["duration_minutes"],
                "topic": generation_request["topic"],
                "activities": [{"name": "Corrected attempt"}],
            }

        result = run_lesson_planning(
            request,
            tools=[tool],
            generators={tool_id: generator},
        )

        self.assertEqual(result.status, "READY")
        generation_result = result.generation["result"]
        self.assertEqual(generation_result["status"], "READY")
        self.assertEqual(generation_result["attempts"], 2)
        self.assertEqual(generation_result["qc"]["status"], "READY")
        self.assertFalse(generation_result["qc"]["critical_failure"])
        self.assertEqual(calls[0], [])
        self.assertIn("LEVEL_MISMATCH", calls[1])
        self.assertIn("DURATION_EXCEEDED", calls[1])

    def test_persistent_failure_is_bounded_and_rejected(self):
        case = json.loads(GOLDEN_CASE.read_text(encoding="utf-8"))
        request = case["request"]
        tool_id = "golden-persistent-failure-generator"
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
                "level": "B1",
                "objective": generation_request["objective"],
                "duration_minutes": 120,
                "topic": generation_request["topic"],
                "activities": [{"name": "Still incorrect"}],
            }

        result = run_lesson_planning(
            request,
            tools=[tool],
            generators={tool_id: generator},
        )

        self.assertEqual(result.status, "REJECT")
        generation_result = result.generation["result"]
        self.assertEqual(generation_result["status"], "REJECT")
        self.assertEqual(generation_result["attempts"], 3)
        self.assertEqual(len(calls), 3)
        self.assertEqual(generation_result["qc"]["status"], "REJECT_AND_REDESIGN")
        self.assertTrue(generation_result["qc"]["critical_failure"])


if __name__ == "__main__":
    unittest.main()
