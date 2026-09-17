import unittest

from core.workflow.teacher_lesson_card import TeacherLessonActivity, TeacherLessonCard
from core.workflow.teacher_lesson_card_renderer import render_teacher_lesson_card


class TeacherLessonCardRendererTests(unittest.TestCase):
    def test_a2_card_renders_classroom_essentials_and_accepted_resource(self):
        card = TeacherLessonCard(
            version="v1",
            level="A2",
            audience="adult ESL learners",
            objective="Discuss past experiences and ask follow-up questions.",
            duration_minutes=90,
            activities=(
                TeacherLessonActivity(
                    activity_id="activity-1",
                    purpose="Guided discussion",
                    interaction="PAIR",
                    minutes=20,
                    student_production="Discuss a past experience.",
                    assessment_link="Teacher observes follow-up questions.",
                ),
            ),
            assessment={
                "type": "OBSERVATION",
                "target": "Past experiences and follow-up questions",
                "evidence": "Learner response during the task",
            },
            resource={
                "required_output": "worksheet",
                "purpose": "Support the pair discussion",
                "tool_id": "approved-resource-tool",
            },
        )

        html = render_teacher_lesson_card(card)

        self.assertIn("A2", html)
        self.assertIn("adult ESL learners", html)
        self.assertIn("90 min", html)
        self.assertIn("Guided discussion", html)
        self.assertIn("OBSERVATION", html)
        self.assertIn("worksheet", html)
        self.assertNotIn("approved-resource-tool", html)


if __name__ == "__main__":
    unittest.main()
