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

    def test_provider_hints_are_carried_without_changing_pedagogical_decision(self):
        context, plan = self._plan(
            "Understand and respond to a short listening text.",
            [
                "PREFERRED_RESOURCE_TOOL:notebooklm",
                "FALLBACK_RESOURCE_TOOL:audio-provider",
            ],
        )
        decision = decide_resource(context, plan)

        self.assertEqual(decision.action, "CREATE")
        self.assertEqual(decision.resource_type, "audio")
        self.assertEqual(decision.preferred_tool, "notebooklm")
        self.assertEqual(decision.fallback_tool, "audio-provider")

    def test_explicit_visual_presentation_sets_visual_requirement(self):
        context, plan = self._plan(
            "Present greetings and basic classroom language.",
            ["RESOURCE_REQUIRED: presentation"],
        )
        decision = decide_resource(context, plan)

        self.assertEqual(decision.action, "CREATE")
        self.assertEqual(decision.resource_type, "presentation")
        self.assertTrue(decision.visual)
        self.assertFalse(decision.source_based)

    def test_visual_resource_signal_sets_visual_requirement(self):
        context, plan = self._plan(
            "Practice greetings.",
            ["RESOURCE_REQUIRED: worksheet", "RESOURCE_VISUAL:true"],
        )
        decision = decide_resource(context, plan)

        self.assertTrue(decision.visual)
        self.assertFalse(decision.source_based)

    def test_source_based_resource_signal_is_preserved(self):
        context, plan = self._plan(
            "Practice using information from a source text.",
            ["RESOURCE_REQUIRED: worksheet", "RESOURCE_SOURCE_BASED:true"],
        )
        decision = decide_resource(context, plan)

        self.assertTrue(decision.source_based)
        self.assertFalse(decision.visual)

    def test_visual_objective_propagates_visual_requirement(self):
        context, plan = self._plan("Watch a visual demonstration of classroom language.")
        decision = decide_resource(context, plan)

        self.assertEqual(decision.action, "CREATE")
        self.assertEqual(decision.resource_type, "video_or_visual")
        self.assertTrue(decision.visual)

    def test_task_packet_receives_hints_but_router_can_still_ignore_unusable_hint(self):
        context, plan = self._plan(
            "Understand and respond to a short listening text.",
            ["PREFERRED_RESOURCE_TOOL:visual-only-tool"],
        )
        decision = decide_resource(context, plan)
        self.assertEqual(decision.preferred_tool, "visual-only-tool")


if __name__ == "__main__":
    unittest.main()
