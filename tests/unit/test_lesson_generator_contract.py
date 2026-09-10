import unittest

from core.generation.lesson_generator import LessonGenerator


class LessonGeneratorContractTests(unittest.TestCase):
    def test_callable_satisfies_runtime_contract(self):
        calls = []

        def generator(generation_request, previous_errors):
            calls.append((generation_request, previous_errors))
            return {
                "level": generation_request["level"],
                "objective": generation_request["objective"],
                "duration_minutes": generation_request["duration_minutes"],
                "activities": [{"name": "Contract test"}],
            }

        typed_generator: LessonGenerator = generator
        result = typed_generator(
            {
                "level": "A2",
                "objective": "Test objective",
                "duration_minutes": 90,
            },
            ["LEVEL_MISMATCH"],
        )

        self.assertEqual(result["level"], "A2")
        self.assertEqual(calls[0][1], ["LEVEL_MISMATCH"])


if __name__ == "__main__":
    unittest.main()
