import unittest

from core.pedagogy.activity_contract import ActivityGenerationContract
from core.pedagogy.activity_validator import activity_is_valid, validate_activity


class ActivityValidatorTests(unittest.TestCase):
    def setUp(self):
        self.contract = ActivityGenerationContract(
            activity_id="a1",
            level="A1",
            objective="Describe a daily routine.",
            skill="SPEAKING",
            interaction="pairs",
            cognitive_demand="APPLY",
            scaffolding=2,
            duration_minutes=10,
            language_target="I get up at ...",
            must_include=("daily routine",),
            must_not_include=("used to",),
            evidence="Learner describes three routine actions.",
        )

    def test_valid_activity(self):
        activity = {
            "activity_id": "a1",
            "level": "A1",
            "objective": "Describe a daily routine.",
            "skill": "SPEAKING",
            "interaction": "pairs",
            "cognitive_demand": "APPLY",
            "scaffolding": 2,
            "duration_minutes": 10,
            "language_target": "I get up at ...",
            "evidence": "Learner describes three routine actions.",
            "instructions": "Discuss your daily routine with a partner.",
        }
        self.assertTrue(activity_is_valid(activity, self.contract))

    def test_bionic_constraints_are_blocking(self):
        activity = {
            "activity_id": "a1",
            "level": "A1",
            "objective": "Describe a daily routine.",
            "skill": "WRITING",
            "interaction": "individual",
            "cognitive_demand": "CREATE",
            "scaffolding": 0,
            "duration_minutes": 20,
            "evidence": "",
            "instructions": "Write about your daily routine using used to.",
        }
        errors = validate_activity(activity, self.contract)
        self.assertIn("SKILL_MISMATCH", errors)
        self.assertIn("INTERACTION_MISMATCH", errors)
        self.assertIn("COGNITIVE_DEMAND_MISMATCH", errors)
        self.assertIn("DURATION_MISMATCH", errors)
        self.assertIn("EVIDENCE_MISSING", errors)
        self.assertIn("MUST_NOT_INCLUDE_VIOLATION", errors)
        self.assertFalse(activity_is_valid(activity, self.contract))

    def test_speaking_requires_language_target(self):
        with self.assertRaises(ValueError):
            ActivityGenerationContract(
                activity_id="a1",
                level="A1",
                objective="Speak about routines.",
                skill="SPEAKING",
                interaction="pairs",
                cognitive_demand="APPLY",
                scaffolding=2,
                duration_minutes=10,
                evidence="Observed response.",
            )


if __name__ == "__main__":
    unittest.main()
