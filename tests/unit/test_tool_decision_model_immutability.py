import unittest

from core.foundation.models import ToolDecision


class ToolDecisionImmutabilityTests(unittest.TestCase):
    def _decision(self, fallback_policy):
        return ToolDecision(
            decision_id="tool-decision-1",
            task_type="RESOURCE_PRODUCTION",
            selected_tool="notebooklm",
            fallback_policy=fallback_policy,
            human_handoff_allowed=True,
        )

    def test_fallback_policy_is_normalized_to_tuple(self):
        decision = self._decision(["canva", "gemma_local"])
        self.assertEqual(decision.fallback_policy, ("canva", "gemma_local"))
        self.assertIsInstance(decision.fallback_policy, tuple)

    def test_fallback_policy_cannot_be_mutated(self):
        decision = self._decision(["canva"])
        with self.assertRaises(AttributeError):
            decision.fallback_policy.append("gemma_local")


if __name__ == "__main__":
    unittest.main()
