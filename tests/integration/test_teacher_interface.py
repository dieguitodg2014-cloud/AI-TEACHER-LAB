import unittest

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.teacher_interface import plan_for_teacher, render_teacher_result, teacher_result_to_dict


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

    def test_natural_language_request_preserves_complete_generated_lesson(self):
        generated_lesson = {
            "level": "A2",
            "objective": "Students will give recommendations using should and shouldn't.",
            "duration_minutes": 60,
            "topic": "recommendations",
            "teacher_notes": "Monitor accuracy after the role-play.",
            "activities": [
                {
                    "name": "Recommendation role-play",
                    "student_production": "Students give advice using should and shouldn't.",
                    "assessment_link": "Teacher listens for appropriate recommendations.",
                }
            ],
        }

        def generator(request, errors):
            return generated_lesson

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
        self.assertEqual(result.lesson, generated_lesson)
        self.assertEqual(result.lesson["teacher_notes"], generated_lesson["teacher_notes"])
        self.assertEqual(len(result.activities), 1)
        self.assertIsNotNone(result.assessment)
        self.assertEqual(result.assessment["type"], "FORMATIVE")

        payload = teacher_result_to_dict(result)
        self.assertIn("lesson", payload)
        self.assertNotIn("TaskPacket", str(payload))
        self.assertNotIn("capability_validation", str(payload))
        self.assertNotIn("provider_revision", str(payload))

    def test_accepted_resource_is_exposed_as_classroom_output(self):
        request = {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Understand a short conversation and identify key information.",
            "topic": "Listening for key information",
            "constraints": ["Students need listening practice"],
        }
        resource = {
            "resource_type": "audio",
            "level": "A2",
            "objective": request["objective"],
            "content": "A short conversation between two adults about making a weekend appointment.",
        }

        result = plan_for_teacher(request, produced_resource=resource)

        self.assertEqual(result.status, "ACCEPTED")
        self.assertIsNotNone(result.resource)
        self.assertEqual(result.resource["type"], "audio")
        self.assertEqual(result.resource["output"], resource)

        rendered = render_teacher_result(result)
        self.assertIn("Resource", rendered)
        self.assertIn("Accepted resource", rendered)
        self.assertIn(resource["content"], rendered)

    def test_teacher_text_render_contains_classroom_essentials(self):
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 90,
                "objective": "Discuss past experiences and ask follow-up questions.",
                "topic": "life experiences",
            },
            tools=self.tools,
        )
        rendered = render_teacher_result(result)
        self.assertIn("life experiences", rendered)
        self.assertIn("Learning objective", rendered)
        self.assertIn("Lesson activities", rendered)
        self.assertIn("Assessment", rendered)

    def test_planning_without_provider_is_still_useful(self):
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": "Discuss past experiences.",
                "topic": "life experiences",
            },
            tools=[],
            generators={},
        )
        self.assertEqual(result.status, "PLANNED")
        self.assertEqual(result.level, "A2")
        self.assertEqual(result.title, "life experiences")
        self.assertGreater(len(result.activities), 0)
        self.assertIsNotNone(result.assessment)

    def test_missing_context_is_teacher_readable(self):
        result = plan_for_teacher("I need a lesson about food.", tools=self.tools, generators={})
        self.assertEqual(result.status, "MISSING_CONTEXT")
        self.assertEqual(result.activities, ())
        self.assertIsNone(result.objective)
        self.assertTrue(result.errors)
        rendered = render_teacher_result(result)
        self.assertIn("MISSING_CONTEXT", rendered)
        self.assertIn("Issues", rendered)

    def test_serialized_contract_is_stable(self):
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": "Discuss past experiences.",
                "topic": "life experiences",
            },
            tools=[],
            generators={},
        )
        payload = teacher_result_to_dict(result)
        self.assertEqual(
            list(payload),
            [
                "status", "title", "level", "audience", "duration_minutes", "objective",
                "lesson", "activities", "assessment", "resource", "handoff", "errors",
            ],
        )
