import json
import tempfile
import unittest
from pathlib import Path

from core.evidence.learning_evidence import (
    EvidenceRecord,
    InMemoryLearningEvidenceStore,
    JsonLearningEvidenceStore,
)


class LearningEvidenceTests(unittest.TestCase):
    def _record(self, evidence_id="evidence-1"):
        return EvidenceRecord(
            evidence_id=evidence_id,
            course_id="course-1",
            lesson_id="lesson-1",
            activity_id="activity-3",
            level="A1",
            objective="Describe daily routines.",
            evidence_type="SPEAKING_PERFORMANCE",
            observation="Student described five routine actions with understandable time expressions.",
            success=True,
            score=80,
            criteria_met=("uses simple present", "communicates routine actions"),
        )

    def test_evidence_record_is_immutable_and_normalized(self):
        record = self._record()
        self.assertEqual(record.criteria_met, ("uses simple present", "communicates routine actions"))
        with self.assertRaises(Exception):
            record.score = 90

    def test_evidence_requires_observable_fields(self):
        with self.assertRaises(ValueError):
            self._record().from_dict({
                "evidence_id": "e", "course_id": "c", "lesson_id": "l",
                "activity_id": "a", "level": "A1", "objective": "x",
                "evidence_type": "observation", "observation": ""
            })

    def test_in_memory_store_is_idempotent_but_conflict_safe(self):
        store = InMemoryLearningEvidenceStore()
        record = self._record()
        self.assertEqual(store.save(record), record)
        self.assertEqual(store.save(record), record)
        conflicting = self._record()
        object.__setattr__(conflicting, "score", 81)
        with self.assertRaises(ValueError):
            store.save(conflicting)
        self.assertEqual(store.list_for_lesson("course-1", "lesson-1"), (record,))

    def test_json_store_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "learning-evidence.json"
            store = JsonLearningEvidenceStore(path)
            record = self._record()
            store.save(record)
            restored = JsonLearningEvidenceStore(path).list_for_lesson("course-1", "lesson-1")
            self.assertEqual(restored, (record,))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["evidence-1"]["score"], 80)

    def test_score_range_is_validated(self):
        with self.assertRaises(ValueError):
            EvidenceRecord(**{**self._record().to_dict(), "score": 101})


if __name__ == "__main__":
    unittest.main()
