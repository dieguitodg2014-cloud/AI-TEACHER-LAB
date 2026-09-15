import unittest

from core.workflow.teacher_interface import plan_for_teacher
from core.workflow.teacher_lesson_card import build_teacher_lesson_card


class TeacherLessonCardTests(unittest.TestCase):
    def test_card_projects_classroom_essentials(self):
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": "Give recommendations using should and shouldn't.",
                "topic": "recommendations",
            }
        )

        card = build_teacher_lesson_card(result)

        self.assertEqual(card["header"]["level"], "A2")
        self.assertEqual(card["header"]["duration_minutes"], 60)
        self.assertEqual(card["objective"], result.objective)
        self.assertGreater(len(card["activities"]), 0)
        self.assertIsNotNone(card["assessment"])
        self.assertIn("teacher_notes", card)

    def test_unaccepted_resource_is_not_exposed_as_accepted(self):
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": "Identify key information in a short conversation.",
                "topic": "listening",
            }
        )

        card = build_teacher_lesson_card(result)

        self.assertNotEqual(result.status, "ACCEPTED")
        self.assertIsNone(card["accepted_resource"])

    def test_accepted_resource_is_projected_without_internal_fields(self):
        resource = {
            "resource_type": "audio",
            "level": "A2",
            "objective": "Identify key information in a short conversation.",
            "content": "A short conversation about a weekend appointment.",
        }
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": resource["objective"],
                "topic": "listening",
            },
            produced_resource=resource,
        )

        card = build_teacher_lesson_card(result)

        self.assertEqual(result.status, "ACCEPTED")
        self.assertEqual(card["accepted_resource"], resource)
        self.assertNotIn("TaskPacket", str(card))
        self.assertNotIn("capability_validation", str(card))
        self.assertNotIn("provider_revision", str(card))


if __name__ == "__main__":
    unittest.main()
