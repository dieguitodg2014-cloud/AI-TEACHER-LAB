import unittest

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.teacher_interface import plan_for_teacher, teacher_result_to_dict


class TeacherInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.tools = [
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

    def test_natural_language_request_becomes_teacher_ready_result(self):
        def generator(request, errors):
            return {
                "level": request["level"],
                "objective": request["objective"],
                "duration_minutes": request["duration_minutes"],
                "topic": request["topic"],
                "activities": [
                    {
                        "name": "Recommendation role-play",
                        "student_production": "Students give advice using should and shouldn't.",
                        "assessment_link": "Teacher listens for appropriate recommendations.",
                    }
                ],
            }

        result = plan_for_teacher(
            "Create an A2 lesson for adult ESL learners for 60 minutes. "
            "Objective: Students will give recommendations using should and shouldn't. "
            "Topic: recommendations",
            tools=self.tools,
            generators={"test-generator": generator},
        )

        self.assertEqual(result.status, "READY")
        self.assertEqual(result.level, "A2")
        self.assertEqual(result.duration_minutes, 60)
        self.assertEqual(result.title, "recommendations")
        self.assertEqual(len(result.activities), 1)
        self.assertIsNotNone(result.assessment)
        self.assertEqual(result.assessment["type"], "PERFORMANCE")

    def test_planning_without_provider_is_still_useful(self):
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 90,
                "objective": "Discuss past experiences and ask follow-up questions.",
                "topic": "life experiences",
            }
        )

        self.assertEqual(result.status, "PLANNED")
        self.assertEqual(result.level, "A2")
        self.assertEqual(result.title, "life experiences")
        self.assertGreater(len(result.activities), 0)
        self.assertIsNotNone(result.assessment)

    def test_missing_context_is_teacher_readable(self):
        result = plan_for_teacher("I need a lesson about food.")

        self.assertEqual(result.status, "MISSING_CONTEXT")
        self.assertEqual(result.activities, ())
        self.assertIsNone(result.objective)
        self.assertGreater(len(result.errors), 0)

    def test_serialized_contract_is_stable(self):
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": "Give recommendations using should and shouldn't.",
                "topic": "recommendations",
            }
        )

        payload = teacher_result_to_dict(result)
        self.assertEqual(
            tuple(payload.keys()),
            (
                "status",
                "title",
                "level",
                "audience",
                "duration_minutes",
                "objective",
                "activities",
                "assessment",
                "resource",
                "handoff",
                "errors",
            ),
        )


if __name__ == "__main__":
    unittest.main()
