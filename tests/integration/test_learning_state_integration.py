import unittest

from core.adaptation.adaptation_engine import AdaptationDecision
from core.evidence.learning_evidence import EvidenceRecord, InMemoryLearningEvidenceStore
from core.memory.course_memory import InMemoryCourseMemoryStore
from core.workflow.learning_state import LessonOutcome, record_lesson_outcome


class LearningStateIntegrationTests(unittest.TestCase):
    def _evidence(self, evidence_id="e1", score=72):
        return EvidenceRecord(
            evidence_id=evidence_id,
            course_id="course-1",
            lesson_id="lesson-1",
            activity_id="activity-1",
            level="A1",
            objective="Describe daily routines.",
            evidence_type="PERFORMANCE",
            observation="Student completed the target task.",
            score=score,
            success=True,
        )

    def test_completed_lesson_updates_memory_and_generates_adaptation(self):
        memory_store = InMemoryCourseMemoryStore()
        evidence_store = InMemoryLearningEvidenceStore()
        outcome = record_lesson_outcome(
            memory_store=memory_store,
            evidence_store=evidence_store,
            course_id="course-1",
            lesson_id="lesson-1",
            topic="Daily routines",
            level="A1",
            objective="Describe daily routines.",
            duration_minutes=60,
            evidence=(self._evidence(),),
        )
        self.assertIsInstance(outcome, LessonOutcome)
        self.assertEqual(outcome.memory.session_count, 1)
        self.assertEqual(outcome.evidence, (self._evidence(),))
        self.assertIsInstance(outcome.adaptation, AdaptationDecision)
        self.assertEqual(outcome.adaptation.action, "GUIDED_PRACTICE")

    def test_generation_does_not_imply_completion(self):
        memory_store = InMemoryCourseMemoryStore()
        self.assertEqual(memory_store.get("course-1").session_count, 0)

    def test_mismatched_evidence_is_rejected_before_memory_update(self):
        memory_store = InMemoryCourseMemoryStore()
        evidence_store = InMemoryLearningEvidenceStore()
        bad = EvidenceRecord(
            evidence_id="e1", course_id="other", lesson_id="lesson-1",
            activity_id="a", level="A1", objective="x",
            evidence_type="PERFORMANCE", observation="observed"
        )
        with self.assertRaises(ValueError):
            record_lesson_outcome(
                memory_store=memory_store, evidence_store=evidence_store,
                course_id="course-1", lesson_id="lesson-1", topic="x",
                level="A1", objective="x", duration_minutes=60, evidence=(bad,)
            )
        self.assertEqual(memory_store.get("course-1").session_count, 0)
        self.assertEqual(evidence_store.list_for_lesson("course-1", "lesson-1"), ())

    def test_duplicate_lesson_outcome_is_idempotent_for_memory(self):
        memory_store = InMemoryCourseMemoryStore()
        evidence_store = InMemoryLearningEvidenceStore()
        evidence = self._evidence()
        first = record_lesson_outcome(
            memory_store=memory_store, evidence_store=evidence_store,
            course_id="course-1", lesson_id="lesson-1", topic="Daily routines",
            level="A1", objective="Describe daily routines.", duration_minutes=60,
            evidence=(evidence,)
        )
        second = record_lesson_outcome(
            memory_store=memory_store, evidence_store=evidence_store,
            course_id="course-1", lesson_id="lesson-1", topic="Daily routines",
            level="A1", objective="Describe daily routines.", duration_minutes=60,
            evidence=(evidence,)
        )
        self.assertEqual(first.memory, second.memory)
        self.assertEqual(second.memory.session_count, 1)


if __name__ == "__main__":
    unittest.main()
