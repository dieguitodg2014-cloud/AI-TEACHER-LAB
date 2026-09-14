import unittest

from core.foundation.models import AssessmentDecision


class AssessmentDecisionImmutabilityTests(unittest.TestCase):
    def _assessment(self, success_criteria):
        return AssessmentDecision(
            assessment_id="assessment-1",
            type="PERFORMANCE",
            target="past experiences",
            evidence="student oral response",
            success_criteria=success_criteria,
        )

    def test_success_criteria_is_normalized_to_tuple(self):
        assessment = self._assessment(["uses past tense", "asks a follow-up question"])

        self.assertEqual(
            assessment.success_criteria,
            ("uses past tense", "asks a follow-up question"),
        )
        self.assertIsInstance(assessment.success_criteria, tuple)

    def test_success_criteria_cannot_be_mutated(self):
        assessment = self._assessment(["uses past tense"])

        with self.assertRaises(AttributeError):
            assessment.success_criteria.append("asks a follow-up question")


if __name__ == "__main__":
    unittest.main()
