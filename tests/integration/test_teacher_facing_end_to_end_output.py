import unittest
from unittest.mock import Mock

from core.workflow.teacher_facing_output import run_teacher_facing_lesson
from core.workflow.vertical_slice import VerticalSliceResult


class TeacherFacingEndToEndOutputTests(unittest.TestCase):
    def test_ready_result_becomes_teacher_facing_html(self):
        result = Mock(spec=VerticalSliceResult)
        result.status = "READY"
        result.context = Mock(level="A2", audience="adult ESL learners", objective="Talk about past experiences", duration_minutes=60)
        result.learning_plan = Mock(sequence=())
        result.assessment_decision = Mock(
            type="OBSERVATION",
            target="Past experiences",
            evidence="Learner response",
            success_criteria=(),
        )
        result.resource_task = None
        result.resource_decision = None
        result.resource_tool = None

        html = run_teacher_facing_lesson(
            {},
            planner=lambda request: result,
        )

        self.assertIsInstance(html, str)
        self.assertIn("A2", html)
        self.assertIn("adult ESL learners", html)
        self.assertIn("Talk about past experiences", html)
        self.assertIn("OBSERVATION", html)

    def test_non_ready_result_cannot_become_teacher_facing_output(self):
        result = Mock(spec=VerticalSliceResult)
        result.status = "REVISION_REQUIRED"

        with self.assertRaises(ValueError):
            from core.workflow.teacher_facing_output import build_teacher_lesson_card
            build_teacher_lesson_card(result)


if __name__ == "__main__":
    unittest.main()
