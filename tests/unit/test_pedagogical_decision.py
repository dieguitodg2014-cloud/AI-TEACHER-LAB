import unittest
from dataclasses import replace

from core.context.engine import build_context
from core.pedagogy.decision_engine import build_lesson_trajectory, decide_learning_plan
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

    def test_plan_uses_trajectory_and_preserves_class_time(self):
        context = self._context()
        level = decide_level(context)
        plan = decide_learning_plan(context, level)
        trajectory = build_lesson_trajectory(context, level)

        self.assertEqual(len(plan.sequence), 8)
        self.assertEqual(
            [activity.interaction for activity in plan.sequence],
            [
                "teacher_to_class",
                "teacher_to_class",
                "teacher_to_class",
                "pairs",
                "pairs_or_small_groups",
                "pairs_or_small_groups",
                "individual_or_pairs",
                "individual",
            ],
        )
        self.assertTrue(all(activity.purpose for activity in plan.sequence))
        self.assertEqual(sum(activity.minutes for activity in plan.sequence), 90)
        self.assertEqual(plan.total_minutes, 90)
        self.assertEqual(plan.objective, context.objective)
        self.assertEqual(plan.evidence_of_learning, trajectory.final_evidence)
        self.assertEqual(plan.resource_need, "NO_RESOURCE_REQUIRED")

    def test_trajectory_moves_from_access_to_transfer(self):
        context = self._context()
        level = decide_level(context)
        trajectory = build_lesson_trajectory(context, level)

        self.assertEqual(trajectory.starting_point, "P0")
        self.assertEqual(trajectory.target_point, "P3")
        self.assertEqual(trajectory.phases[0].phase, "EXPERIENCE")
        self.assertEqual(trajectory.phases[-1].phase, "TRANSFER")
        self.assertEqual(trajectory.phases[-1].scaffolding, 0)

    def test_mismatched_level_is_rejected(self):
        context = self._context()
        level = replace(decide_level(context), level="B1")

        with self.assertRaises(ValueError):
            decide_learning_plan(context, level)

        with self.assertRaises(ValueError):
            build_lesson_trajectory(context, level)


if __name__ == "__main__":
    unittest.main()
