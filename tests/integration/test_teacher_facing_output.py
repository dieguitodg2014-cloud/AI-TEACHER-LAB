import unittest
from unittest.mock import Mock

from core.workflow.teacher_facing_output import (
    TeacherFacingOutputError,
    build_teacher_lesson_card,
    run_teacher_facing_lesson,
)
from core.workflow.vertical_slice import VerticalSliceResult


class TeacherFacingOutputTests(unittest.TestCase):
    def test_ready_result_becomes_rendered_teacher_output(self):
        result = Mock(spec=VerticalSliceResult)
        result.status = "READY"
        result.context = Mock(
            level="A2",
            audience="adult ESL learners",
            objective="Talk about past experiences and ask follow-up questions.",
            duration_minutes=60,
        )
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

        self.assertIn("A2", html)
        self.assertIn("adult ESL learners", html)
        self.assertIn("Talk about past experiences", html)
        self.assertIn("OBSERVATION", html)

    def test_non_ready_result_cannot_cross_teacher_facing_boundary(self):
        result = Mock(spec=VerticalSliceResult)
        result.status = "FAILED"

        with self.assertRaises(TeacherFacingOutputError):
            build_teacher_lesson_card(result)


if __name__ == "__main__":
    unittest.main()
