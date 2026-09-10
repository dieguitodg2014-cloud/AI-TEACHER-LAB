import unittest

from core.context.engine import build_context
from core.progression.level_control import decide_level


class LevelControlEngineTests(unittest.TestCase):
    def test_context_level_is_translated_into_level_decision(self):
        result = build_context(
            {
                "context_id": "ctx-001",
                "level": "B1",
                "audience": "adults",
                "duration_minutes": 90,
                "objective": "Discuss everyday experiences and give reasons.",
                "constraints": [],
            }
        )

        self.assertFalse(result.errors)
        self.assertFalse(result.missing)

        decision = decide_level(result.context)

        self.assertEqual(decision.level, "B1")
        self.assertIn("Connected", decision.linguistic_complexity)
        self.assertTrue(decision.interaction_expectation)
        self.assertTrue(decision.assessment_expectation)

    def test_all_supported_levels_have_profiles(self):
        for level in ("A0", "A1", "A2", "B1", "B2"):
            result = build_context(
                {
                    "context_id": f"ctx-{level}",
                    "level": level,
                    "audience": "adult learners",
                    "duration_minutes": 90,
                    "objective": "Complete a meaningful communication task.",
                    "constraints": [],
                }
            )
            self.assertFalse(result.errors)
            decision = decide_level(result.context)
            self.assertEqual(decision.level, level)


if __name__ == "__main__":
    unittest.main()
