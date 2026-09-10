import unittest

from core.quality.generation_qc import review_generated_lesson


class GenerationQCTests(unittest.TestCase):
    def _lesson(self):
        return {
            "level": "A2",
            "objective": "Discuss past experiences and ask follow-up questions.",
            "duration_minutes": 90,
            "activities": [{"name": "discussion"}],
        }

    def test_valid_lesson_matches_official_qc_contract(self):
        result = review_generated_lesson(
            self._lesson(),
            level="A2",
            objective="Discuss past experiences and ask follow-up questions.",
            duration_minutes=90,
        )

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["blocking_errors"], [])
        self.assertEqual(result["score"], 100.0)
        self.assertFalse(result["critical_failure"])
        self.assertFalse(result["revision_required"])
        self.assertEqual(result["checks"]["level_alignment"], True)
        self.assertEqual(result["checks"]["objective_alignment"], True)
        self.assertEqual(result["checks"]["communicative_value"], True)
        self.assertEqual(result["checks"]["time_realism"], True)
        self.assertEqual(result["checks"]["linguistic_accuracy"], True)
        self.assertEqual(result["checks"]["assessment_alignment"], True)

    def test_qc_rejects_misaligned_lesson(self):
        lesson = self._lesson()
        lesson["level"] = "B1"
        lesson["duration_minutes"] = 120

        result = review_generated_lesson(
            lesson,
            level="A2",
            objective="Discuss past experiences and ask follow-up questions.",
            duration_minutes=90,
        )

        self.assertEqual(result["status"], "REJECT_AND_REDESIGN")
        self.assertEqual(result["score"], 40.0)
        self.assertTrue(result["critical_failure"])
        self.assertTrue(result["revision_required"])
        self.assertFalse(result["checks"]["level_alignment"])
        self.assertFalse(result["checks"]["time_realism"])
        self.assertIn("LEVEL_MISMATCH", result["blocking_errors"])
        self.assertIn("DURATION_EXCEEDED", result["blocking_errors"])


if __name__ == "__main__":
    unittest.main()
