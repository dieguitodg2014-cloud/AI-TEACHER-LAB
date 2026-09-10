import unittest
from dataclasses import replace

from core.context.engine import build_context
from core.pedagogy.decision_engine import decide_learning_plan
from core.progression.level_control import decide_level


class PedagogicalDecisionEngineTests(unittest.TestCase):
    def _context(self):
        result = build_context(
            {
                "context_id": "ctx-golden-001",
                "level": "A2",
                "audience": "adult learners",
                "duration_minutes": 90,
                "objective": "Discuss past experiences and ask follow-up questions.",
                "constraints": [],
            }
        )
        self.assertFalse(result.errors)
        self.assertIsNotNone(result.context)
        return result.context

    def test_plan_uses_level_and_preserves_class_time(self):
        context = self._context()
        level = decide_level(context)
        plan = decide_learning_plan(context, level)

        self.assertEqual(
            [activity.purpose for activity in plan.sequence],
            [
                "presentation",
                "modeling",
                "guided_practice",
                "communicative_practice",
                "production",
                "assessment",
            ],
        )
        self.assertEqual(sum(activity.minutes for activity in plan.sequence), 90)
        self.assertEqual(plan.total_minutes, 90)
        self.assertEqual(plan.objective, context.objective)
        self.assertTrue(plan.evidence_of_learning)
        self.assertEqual(plan.resource_need, "NO_RESOURCE_DECIDED_YET")

    def test_mismatched_level_is_rejected(self):
        context = self._context()
        level = replace(decide_level(context), level="B1")

        with self.assertRaises(ValueError):
            decide_learning_plan(context, level)


if __name__ == "__main__":
    unittest.main()
