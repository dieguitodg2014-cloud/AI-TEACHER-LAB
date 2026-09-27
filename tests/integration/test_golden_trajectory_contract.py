import json
import unittest
from pathlib import Path

from core.pedagogy.decision_engine import build_lesson_trajectory
from core.workflow.vertical_slice import run_lesson_planning


REGRESSION_DIR = Path(__file__).resolve().parents[1] / "regression"


class GoldenTrajectoryContractTests(unittest.TestCase):
    def test_golden_cases_preserve_full_pedagogical_trajectory(self):
        cases = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(REGRESSION_DIR.glob("golden_case_*.json"))
        ]

        self.assertTrue(cases)

        expected_phases = [
            "EXPERIENCE",
            "NOTICE",
            "GRAMMAR_CLARIFICATION",
            "CONTROLLED_PRODUCTION",
            "GUIDED_INTERACTION",
            "EXPANDED_PRODUCTION",
            "COMMUNICATIVE_TASK",
            "TRANSFER",
        ]

        for case in cases:
            result = run_lesson_planning(case["request"])

            self.assertIn(
                result.status,
                {"PLANNED", "READY"},
                case["case_id"],
            )
            self.assertIsNotNone(result.context, case["case_id"])
            self.assertIsNotNone(result.level_decision, case["case_id"])

            trajectory = build_lesson_trajectory(
                result.context,
                result.level_decision,
            )

            self.assertEqual(
                [phase.phase for phase in trajectory.phases],
                expected_phases,
                case["case_id"],
            )
            self.assertEqual(trajectory.starting_point, "P0")
            self.assertEqual(trajectory.target_point, "P3")
            self.assertEqual(trajectory.phases[0].scaffolding, 4)
            self.assertEqual(trajectory.phases[-1].scaffolding, 0)
            self.assertEqual(
                trajectory.final_evidence,
                result.learning_plan.evidence_of_learning,
            )


if __name__ == "__main__":
    unittest.main()
