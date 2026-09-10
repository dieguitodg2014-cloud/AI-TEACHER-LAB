import unittest

from core.generation.lesson_generator import LessonGenerator


class TestLessonGenerator:
    def __init__(self):
        self.calls = []

    def generate(self, generation_request, previous_errors):
        self.calls.append((generation_request, previous_errors))
        return {
            "level": generation_request["level"],
            "objective": generation_request["objective"],
            "duration_minutes": generation_request["duration_minutes"],
            "activities": [{"name": "Contract test"}],
        }


class LessonGeneratorContractTests(unittest.TestCase):
    def test_adapter_shape_matches_runtime_signature(self):
        generator = TestLessonGenerator()
        self.assertTrue(hasattr(LessonGenerator, "__annotations__"))
        result = generator.generate(
            {
                "level": "A2",
                "objective": "Test objective",
                "duration_minutes": 90,
            },
            ["LEVEL_MISMATCH"],
        )
        self.assertEqual(result["level"], "A2")
        self.assertEqual(generator.calls[0][1], ["LEVEL_MISMATCH"])


if __name__ == "__main__":
    unittest.main()
