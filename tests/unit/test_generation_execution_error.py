import unittest

from core.generation.revision import generate_with_revision


class GenerationExecutionErrorTests(unittest.TestCase):
    def test_generator_exception_becomes_controlled_execution_error(self):
        def generator(request, errors):
            raise RuntimeError("simulated provider failure")

        result = generate_with_revision(
            generator,
            {
                "level": "A2",
                "objective": "Discuss past experiences.",
                "duration_minutes": 90,
            },
        )

        self.assertEqual(result["status"], "FAILED")
        self.assertIsNone(result["lesson"])
        self.assertEqual(result["errors"][0], "EXECUTION_ERROR")
        self.assertEqual(result["attempts"], 1)
        self.assertIsNone(result["qc"])

    def test_negative_revision_limit_is_rejected(self):
        def generator(request, errors):
            return {}

        result = generate_with_revision(
            generator,
            {
                "level": "A2",
                "objective": "Discuss past experiences.",
                "duration_minutes": 90,
            },
            max_revisions=-1,
        )

        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["errors"], ["INVALID_GENERATION_REQUEST"])


if __name__ == "__main__":
    unittest.main()
