import unittest

from core.context.engine import build_context
from core.pedagogy.decision_engine import decide_learning_plan
from core.progression.level_control import decide_level
from core.resources.decision_engine import apply_resource_decision, decide_resource


class ResourceDecisionTests(unittest.TestCase):
    def _plan(self, objective, constraints=None):
        result = build_context(
            {
                "context_id": "resource-test",
                "level": "A2",
                "audience": "adult learners",
                "duration_minutes": 90,
                "objective": objective,
                "constraints": constraints or [],
            }
        )
        self.assertFalse(result.errors)
        context = result.context
        level = decide_level(context)
        return context, decide_learning_plan(context, level)

    def test_no_specialized_resource_is_default(self):
        context, plan = self._plan("Discuss past experiences and ask follow-up questions.")
        decision = decide_resource(context, plan)

        self.assertEqual(decision.action, "NO_RESOURCE_REQUIRED")
        self.assertFalse(decision.required)
        self.assertEqual(apply_resource_decision(plan, decision).resource_need, "NO_RESOURCE_REQUIRED")

    def test_listening_objective_justifies_audio(self):
        context, plan = self._plan("Understand and respond to a short listening text.")
        decision = decide_resource(context, plan)

        self.assertEqual(decision.action, "CREATE")
        self.assertEqual(decision.resource_type, "audio")
        self.assertTrue(decision.required)
        self.assertEqual(apply_resource_decision(plan, decision).resource_need, "CREATE")

    def test_explicit_resource_requirement_is_preserved(self):
        context, plan = self._plan(
            "Practice speaking about daily routines.",
            ["RESOURCE_REQUIRED: role-play cards"],
        )
        decision = decide_resource(context, plan)

        self.assertEqual(decision.action, "CREATE")
        self.assertEqual(decision.resource_type, "role-play cards")
        self.assertTrue(decision.required)


if __name__ == "__main__":
    unittest.main()
