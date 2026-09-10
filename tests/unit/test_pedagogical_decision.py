import unittest

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
        return result.context

    def test_plan_uses_level_and_preserves_class_time(self):
        context = self._context()
        level = decide_level(context)
        plan = decide_learning_plan(context, level)

        self.assertEqual(plan.sequence, [
            "presentation",
            "modeling",
            "guided_practice",
            "communicative_practice",
            "production",
            "assessment",
        ])
        self.assertEqual(sum(activity.minutes for activity in plan.activities), 90)
        self.assertTrue(plan.student_talk_priority)
        self.assertTrue(plan.assessment_alignment_required)
        self.assertFalse(plan.resource_generation_required)

    def test_mismatched_level_is_rejected(self):
        context = self._context()
        level = decide_level(context)
        level.level = "B1"

        with self.assertRaises(ValueError):
            decide_learning_plan(context, level)


if __name__ == "__main__":
    unittest.main()
