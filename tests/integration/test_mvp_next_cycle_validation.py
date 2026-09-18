import unittest

from core.adaptation.adaptation_engine import decide_adaptation
from core.evidence.learning_evidence import EvidenceRecord, InMemoryLearningEvidenceStore
from core.memory.course_memory import InMemoryCourseMemoryStore
from core.workflow.learning_state import record_lesson_outcome
from core.workflow.vertical_slice import run_lesson_planning


class MVPNextCycleValidationTests(unittest.TestCase):
    """Executable certification of the post-MVP learner-state cycle."""

    def test_planning_to_explicit_completion_to_adaptation(self):
        request = {
            "context_id": "mvp-next-a1-cycle",
            "level": "A1",
            "audience": "adult beginner ESL learners",
            "duration_minutes": 60,
            "objective": "Describe your daily routine using simple present.",
            "topic": "Daily Routines",
            "constraints": ["Use high-frequency everyday vocabulary."],
        }
        planned = run_lesson_planning(request)
        self.assertEqual(planned.status, "PLANNED")
        self.assertEqual(planned.context.level, "A1")
        self.assertEqual(planned.learning_plan.total_minutes, 60)

        memory_store = InMemoryCourseMemoryStore()
        evidence_store = InMemoryLearningEvidenceStore()
        evidence = EvidenceRecord(
            evidence_id="mvp-e1",
            course_id="mvp-course",
            lesson_id="mvp-lesson-1",
            activity_id=planned.learning_plan.sequence[3].activity_id,
            level=planned.context.level,
            objective=planned.context.objective,
            evidence_type="PERFORMANCE",
            observation="Student described routine actions in a pair task.",
            success=True,
            score=74,
        )
        outcome = record_lesson_outcome(
            memory_store=memory_store,
            evidence_store=evidence_store,
            course_id="mvp-course",
            lesson_id="mvp-lesson-1",
            topic=planned.context.topic,
            level=planned.context.level,
            objective=planned.context.objective,
            duration_minutes=planned.context.duration_minutes,
            evidence=(evidence,),
        )

        self.assertEqual(outcome.memory.session_count, 1)
        self.assertEqual(outcome.memory.last_lesson_id, "mvp-lesson-1")
        self.assertEqual(outcome.evidence[0].evidence_id, "mvp-e1")
        self.assertEqual(outcome.adaptation.action, "GUIDED_PRACTICE")
        self.assertTrue(outcome.adaptation.preserve_level)
        self.assertEqual(outcome.adaptation.basis_evidence_ids, ("mvp-e1",))

    def test_no_evidence_means_no_adaptation_side_effect(self):
        memory_store = InMemoryCourseMemoryStore()
        evidence_store = InMemoryLearningEvidenceStore()
        self.assertEqual(memory_store.get("course").session_count, 0)
        self.assertEqual(evidence_store.list_for_lesson("course", "lesson"), ())
        decision = decide_adaptation(())
        self.assertEqual(decision.action, "MAINTAIN")


if __name__ == "__main__":
    unittest.main()
