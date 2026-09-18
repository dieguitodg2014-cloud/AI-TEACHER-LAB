import unittest

from core.adaptation.adaptation_engine import AdaptationDecision, decide_adaptation
from core.evidence.learning_evidence import EvidenceRecord


class AdaptationEngineTests(unittest.TestCase):
    def _evidence(self, evidence_id="e1", success=None, score=None):
        return EvidenceRecord(
            evidence_id=evidence_id,
            course_id="course-1",
            lesson_id="lesson-1",
            activity_id="activity-1",
            level="A1",
            objective="Describe daily routines.",
            evidence_type="PERFORMANCE",
            observation="Observable classroom performance.",
            success=success,
            score=score,
        )

    def test_no_evidence_maintains_current_approach(self):
        decision = decide_adaptation(())
        self.assertEqual(decision.action, "MAINTAIN")
        self.assertEqual(decision.basis_evidence_ids, ())
        self.assertTrue(decision.preserve_level)

    def test_explicit_failure_reinforces(self):
        decision = decide_adaptation((self._evidence(success=False, score=90),))
        self.assertEqual(decision.action, "REINFORCE")
        self.assertEqual(decision.recommended_scaffolding_delta, 1)

    def test_scores_produce_deterministic_guidance(self):
        decision = decide_adaptation((self._evidence("e1", score=70), self._evidence("e2", score=80)))
        self.assertEqual(decision.action, "GUIDED_PRACTICE")
        self.assertEqual(decision.recommended_scaffolding_delta, 0)
        self.assertEqual(decision.basis_evidence_ids, ("e1", "e2"))

    def test_high_evidence_extends_with_less_scaffolding(self):
        decision = decide_adaptation((self._evidence(score=90),))
        self.assertEqual(decision.action, "EXTEND")
        self.assertEqual(decision.recommended_scaffolding_delta, -1)

    def test_cross_lesson_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            decide_adaptation((self._evidence("e1"), self._evidence("e2").__class__(
                evidence_id="e2", course_id="course-1", lesson_id="lesson-2",
                activity_id="activity-1", level="A1", objective="x",
                evidence_type="PERFORMANCE", observation="x"
            )))

    def test_decision_is_immutable_and_cannot_change_level(self):
        decision = decide_adaptation((self._evidence(score=75),))
        self.assertIsInstance(decision, AdaptationDecision)
        with self.assertRaises(Exception):
            decision.action = "CHANGE_LEVEL"
        with self.assertRaises(ValueError):
            AdaptationDecision("a", "c", "l", "x", "r", (), 0, False)


if __name__ == "__main__":
    unittest.main()
