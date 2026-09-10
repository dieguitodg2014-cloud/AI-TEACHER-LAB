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
        self.assertEqual(result["score"], 60.0)
        self.assertTrue(result["critical_failure"])
        self.assertTrue(result["revision_required"])
        self.assertFalse(result["checks"]["level_alignment"])
        self.assertFalse(result["checks"]["time_realism"])
        self.assertIn("LEVEL_MISMATCH", result["blocking_errors"])
        self.assertIn("DURATION_EXCEEDED", result["blocking_errors"])

    def test_qc_rejects_missing_target_topic(self):
        result = review_generated_lesson(
            self._lesson(),
            level="A2",
            objective="Discuss past experiences and ask follow-up questions.",
            duration_minutes=90,
            topic="Present Perfect",
        )

        self.assertEqual(result["status"], "REJECT_AND_REDESIGN")
        self.assertIn("CONTENT_TOPIC_MISSING", result["blocking_errors"])
        self.assertFalse(result["checks"]["content_alignment"])

    def test_qc_rejects_explicit_forbidden_term(self):
        lesson = self._lesson()
        lesson["activities"][0]["instructions"] = "Practice used to with a partner."

        result = review_generated_lesson(
            lesson,
            level="A2",
            objective="Discuss past experiences and ask follow-up questions.",
            duration_minutes=90,
            constraints=["FORBIDDEN_TERMS: used to"],
        )

        self.assertEqual(result["status"], "REJECT_AND_REDESIGN")
        self.assertIn("CONTENT_FORBIDDEN_TERM", result["blocking_errors"])
        self.assertFalse(result["checks"]["content_alignment"])

    def test_qc_handles_malformed_provider_output(self):
        result = review_generated_lesson(
            None,
            level="A2",
            objective="Test objective",
            duration_minutes=90,
        )

        self.assertEqual(result["status"], "REJECT_AND_REDESIGN")
        self.assertIn("INVALID_OUTPUT", result["blocking_errors"])
        self.assertTrue(result["critical_failure"])


if __name__ == "__main__":
    unittest.main()
