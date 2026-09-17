import unittest

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import run_lesson_planning


class AcceptanceGateTests(unittest.TestCase):
    def test_end_to_end_generation_cannot_bypass_independent_validator(self):
        tool = ToolCandidate(
            "test-generator",
            frozenset({"lesson_generation"}),
            quality=9,
            reliability=9,
            accessibility=9,
            speed=9,
            cost=0,
        )

        def generator(request, errors):
            return {
                "level": request["level"],
                "objective": request["objective"],
                "duration_minutes": request["duration_minutes"],
                "activities": [{
                    "name": "discussion",
                    "student_production": "Students discuss a past experience.",
                    "assessment_link": "Teacher observes target language use.",
                }],
            }

        result = run_lesson_planning(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 30,
                "objective": "Discuss past experiences.",
                "group_size": 10,
            },
            tools=[tool],
            generators={"test-generator": generator},
            independent_validator=None,
        )

        self.assertEqual(result.status, "FAILED")
        self.assertIn("INDEPENDENT_VALIDATOR_REQUIRED", result.errors)
        self.assertIsNone(result.generation)


if __name__ == "__main__":
    unittest.main()
