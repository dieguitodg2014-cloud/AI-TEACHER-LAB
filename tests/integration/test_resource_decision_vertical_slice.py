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

    def _resource_tools(self):
        capabilities = frozenset({"resource_generation", "audio_generation"})
        return [
            ToolCandidate(
                "audio-primary",
                capabilities,
                quality=9,
                reliability=9,
                accessibility=9,
                speed=9,
                cost=0,
            ),
            ToolCandidate(
                "audio-fallback",
                capabilities,
                quality=8,
                reliability=8,
                accessibility=8,
                speed=8,
                cost=0,
            ),
        ]

    def _resource_generators(self):
        def failing_generator(request):
            raise RuntimeError("primary unavailable")

        def working_generator(request):
            return {
                "resource_type": request["required_output"],
                "level": request["level"],
                "objective": request["objective"],
                "content": "A short A2 listening about a past weekend experience.",
            }

        return {
            "audio-primary": failing_generator,
            "audio-fallback": working_generator,
        }

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

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertIsNotNone(result.resource_decision)
        self.assertEqual(result.resource_decision.action, "CREATE")
        self.assertEqual(result.resource_decision.resource_type, "audio")
        self.assertTrue(result.resource_decision.required)
        self.assertEqual(result.learning_plan.resource_need, "CREATE")

    def test_resource_decision_executes_through_provider_fallback_and_acceptance(self):
        result = run_lesson_planning(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 90,
                "objective": "Understand and respond to a short listening text.",
            },
            tools=self._resource_tools(),
            generators=self._resource_generators(),
        )

        self.assertEqual(result.status, "READY")
        self.assertIsNotNone(result.resource_decision)
        self.assertEqual(result.resource_decision.action, "CREATE")
        self.assertEqual(result.resource_decision.resource_type, "audio")
        self.assertIsNotNone(result.resource_task)
        self.assertEqual(result.resource_task.required_output, "audio")
        self.assertEqual(result.resource_tool.tool_id, "audio-fallback")
        self.assertEqual(result.resource_generation["status"], "ACCEPTED")
        self.assertEqual(
            [attempt.tool_id for attempt in result.resource_generation["provider_attempts"]],
            ["audio-primary", "audio-fallback"],
        )
        self.assertEqual(result.resource_generation["result"]["resource_type"], "audio")
        self.assertTrue(result.resource_validation.checks["level_alignment"])
        self.assertTrue(result.resource_validation.checks["objective_alignment"])


if __name__ == "__main__":
    unittest.main()
