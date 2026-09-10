import unittest

from core.workflow.vertical_slice import run_lesson_planning


class VerticalSliceIntegrationTests(unittest.TestCase):
    def test_complete_request_reaches_planned_state(self):
        result = run_lesson_planning(
            {
                "context_id": "golden-a2-001",
                "level": "A2",
                "audience": "adult learners",
                "duration_minutes": 90,
                "objective": "Discuss past experiences and ask follow-up questions.",
                "constraints": ["communicative approach"],
            }
        )

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNotNone(result.context)
        self.assertIsNotNone(result.level_decision)
        self.assertIsNotNone(result.learning_plan)
        self.assertEqual(result.learning_plan.total_minutes, 90)
        self.assertEqual(result.level_decision.level, "A2")
        self.assertFalse(result.errors)

    def test_incomplete_request_stops_before_pedagogical_decision(self):
        result = run_lesson_planning(
            {
                "context_id": "incomplete-001",
                "level": "A2",
                "duration_minutes": 90,
            }
        )

        self.assertEqual(result.status, "MISSING_CONTEXT")
        self.assertIsNone(result.level_decision)
        self.assertIsNone(result.learning_plan)
        self.assertTrue(result.missing)


if __name__ == "__main__":
    unittest.main()
