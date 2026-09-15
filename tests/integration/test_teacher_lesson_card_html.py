import unittest

from core.workflow.teacher_interface import plan_for_teacher
from core.workflow.teacher_lesson_card import build_teacher_lesson_card
from core.workflow.teacher_lesson_card_html import render_teacher_lesson_card_html


class TeacherLessonCardHtmlTests(unittest.TestCase):
    def test_html_contains_classroom_essentials(self):
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": "Give recommendations using should and shouldn't.",
                "topic": "recommendations",
            }
        )
        html = render_teacher_lesson_card_html(build_teacher_lesson_card(result))

        self.assertIn("Learning objective", html)
        self.assertIn("Lesson activities", html)
        self.assertIn("Assessment", html)
        self.assertIn("A2", html)

    def test_accepted_resource_is_rendered_only_after_acceptance(self):
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
        html = render_teacher_lesson_card_html(build_teacher_lesson_card(result))

        self.assertEqual(result.status, "ACCEPTED")
        self.assertIn("Accepted resource", html)
        self.assertIn(resource["content"], html)

    def test_html_escapes_teacher_content(self):
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": "Use <strong>should</strong> safely.",
                "topic": "<script>alert('x')</script>",
            }
        )
        html = render_teacher_lesson_card_html(build_teacher_lesson_card(result))

        self.assertNotIn("<script>alert('x')</script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;strong&gt;", html)


if __name__ == "__main__":
    unittest.main()
