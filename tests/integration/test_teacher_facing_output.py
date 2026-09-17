import unittest

from core.workflow.teacher_facing_output import (
    TeacherFacingOutputError,
    build_teacher_lesson_card,
    run_teacher_facing_lesson,
)
from core.workflow.vertical_slice import VerticalSliceResult


class TeacherFacingOutputTests(unittest.TestCase):
    def test_ready_result_becomes_rendered_teacher_output(self):
        result = VerticalSliceResult(
            status="READY",
            context=None,
            level_decision=None,
            learning_plan=None,
            assessment_decision=None,
            resource_decision=None,
            resource_task=None,
            resource_tool=None,
            resource_handoff=None,
            resource_validation=None,
            generation=None,
            missing=[],
            errors=[],
        )

        # The card mapper requires the approved context/plan/assessment. Use a
        # small real pipeline result below rather than duplicating those
        # contracts in this boundary test.
        from core.workflow.vertical_slice import run_lesson_planning

        result = run_lesson_planning(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": "Talk about past experiences and ask follow-up questions.",
            },
            independent_validator=lambda lesson, context, plan: {
                "status": "READY",
                "feedback": [],
            },
        )

        html = run_teacher_facing_lesson(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": "Talk about past experiences and ask follow-up questions.",
            },
            planner=lambda request: result,
        )

        self.assertIn("A2", html)
        self.assertIn("adult ESL learners", html)
        self.assertIn("Talk about past experiences", html)

    def test_non_ready_result_cannot_cross_teacher_facing_boundary(self):
        result = VerticalSliceResult(
            status="FAILED",
            context=None,
            level_decision=None,
            learning_plan=None,
            assessment_decision=None,
            resource_decision=None,
            resource_task=None,
            resource_tool=None,
            resource_handoff=None,
            resource_validation=None,
            generation=None,
            missing=[],
            errors=["TEST_FAILURE"],
        )

        with self.assertRaises(TeacherFacingOutputError):
            build_teacher_lesson_card(result)


if __name__ == "__main__":
    unittest.main()
