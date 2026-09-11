import unittest

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import run_lesson_planning


class ResourceDecisionVerticalSliceTests(unittest.TestCase):
    def _tools(self):
        return [
            ToolCandidate(
                "test-generator",
                frozenset({"lesson_generation"}),
                quality=9,
                reliability=9,
                accessibility=9,
                speed=9,
                cost=0,
            )
        ]

    def _generator(self):
        def generator(request, errors):
            return {
                "level": request["level"],
                "objective": request["objective"],
                "duration_minutes": request["duration_minutes"],
                "activities": [{
                    "name": "resource decision test",
                    "student_production": "Students give an observable response demonstrating the objective.",
                    "assessment_link": "Teacher observes the learner response during the activity.",
                }],
            }

        return generator

    def test_lesson_without_resource_need_does_not_create_one(self):
        result = run_lesson_planning(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 90,
                "objective": "Discuss past experiences and ask follow-up questions.",
            },
            tools=self._tools(),
            generators={"test-generator": self._generator()},
        )

        self.assertEqual(result.status, "READY")
        self.assertIsNotNone(result.resource_decision)
        self.assertEqual(result.resource_decision.action, "NO_RESOURCE_REQUIRED")
        self.assertEqual(result.learning_plan.resource_need, "NO_RESOURCE_REQUIRED")

    def test_lesson_requiring_listening_creates_audio_resource_decision(self):
        result = run_lesson_planning(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 90,
                "objective": "Understand and respond to a short listening text.",
            },
            tools=self._tools(),
            generators={"test-generator": self._generator()},
        )

        self.assertEqual(result.status, "READY")
        self.assertIsNotNone(result.resource_decision)
        self.assertEqual(result.resource_decision.action, "CREATE")
        self.assertEqual(result.resource_decision.resource_type, "audio")
        self.assertTrue(result.resource_decision.required)
        self.assertEqual(result.learning_plan.resource_need, "CREATE")


if __name__ == "__main__":
    unittest.main()
