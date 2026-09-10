import unittest

from core.generation.revision import generate_with_revision


class GenerationRevisionTests(unittest.TestCase):
    def _request(self):
        return {
            "level": "A2",
            "objective": "Discuss past experiences and ask follow-up questions.",
            "duration_minutes": 90,
        }

    def test_valid_generation_is_accepted_without_revision(self):
        calls = []

        def generator(request, errors):
            calls.append(errors)
            return {
                "level": "A2",
                "objective": request["objective"],
                "duration_minutes": 90,
                "activities": [{"name": "discussion"}],
            }

        result = generate_with_revision(generator, self._request())

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["qc"]["status"], "READY")
        self.assertEqual(result["qc"]["blocking_errors"], [])

    def test_invalid_generation_can_be_revised(self):
        outputs = [
            {
                "level": "B1",
                "objective": "wrong",
                "duration_minutes": 120,
                "activities": [{"name": "discussion"}],
            },
            {
                "level": "A2",
                "objective": "Discuss past experiences and ask follow-up questions.",
                "duration_minutes": 90,
                "activities": [{"name": "discussion"}],
            },
        ]

        def generator(request, errors):
            return outputs.pop(0)

        result = generate_with_revision(generator, self._request())

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["qc"]["status"], "READY")
        self.assertEqual(result["qc"]["blocking_errors"], [])

    def test_repeated_failure_is_rejected(self):
        def generator(request, errors):
            return {
                "level": "B1",
                "objective": request["objective"],
                "duration_minutes": 90,
                "activities": [{"name": "discussion"}],
            }

        result = generate_with_revision(generator, self._request(), max_revisions=2)

        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["attempts"], 3)
        self.assertIn("LEVEL_MISMATCH", result["errors"])
        self.assertEqual(result["qc"]["status"], "REJECT")
        self.assertIn("LEVEL_MISMATCH", result["qc"]["blocking_errors"])


if __name__ == "__main__":
    unittest.main()
