import json
import unittest
from pathlib import Path

from core.workflow.vertical_slice import run_lesson_planning


GOLDEN_CASE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "regression"
    / "golden_case_a2_present_perfect.json"
)


class GoldenCaseA2PresentPerfectTests(unittest.TestCase):
    def test_golden_case_preserves_core_pedagogical_invariants(self):
        case = json.loads(GOLDEN_CASE.read_text(encoding="utf-8"))
        result = run_lesson_planning(case["request"])
        invariants = case["expected_invariants"]

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNotNone(result.context)
        self.assertIsNotNone(result.level_decision)
        self.assertIsNotNone(result.learning_plan)

        self.assertEqual(result.context.level, invariants["level"])
        self.assertEqual(result.context.duration_minutes, invariants["duration_minutes"])
        self.assertEqual(result.context.objective, invariants["objective"])
        self.assertEqual(
            [activity.purpose for activity in result.learning_plan.sequence],
            [
                "presentation",
                "modeling",
                "guided_practice",
                "communicative_practice",
                "production",
                "assessment",
            ],
        )
        self.assertEqual(
            result.learning_plan.total_minutes,
            invariants["duration_minutes"],
        )
        self.assertTrue(result.learning_plan.evidence_of_learning)
        if invariants["resource_decision_must_be_explicit"]:
            self.assertIn(
                result.learning_plan.resource_need,
                {"CREATE", "REUSE", "ADAPT", "OMIT", "NO_RESOURCE_REQUIRED"},
            )


if __name__ == "__main__":
    unittest.main()
