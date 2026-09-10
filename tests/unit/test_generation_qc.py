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

    def test_valid_lesson_passes_qc(self):
        result = review_generated_lesson(
            self._lesson(),
            level="A2",
            objective="Discuss past experiences and ask follow-up questions.",
            duration_minutes=90,
        )

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["blocking_errors"], [])
        self.assertIn("level_alignment", result["checked"])
        self.assertIn("objective_alignment", result["checked"])
        self.assertIn("duration", result["checked"])
        self.assertIn("activity_presence", result["checked"])

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

        self.assertEqual(result["status"], "REJECT")
        self.assertIn("LEVEL_MISMATCH", result["blocking_errors"])
        self.assertIn("DURATION_EXCEEDED", result["blocking_errors"])


if __name__ == "__main__":
    unittest.main()
