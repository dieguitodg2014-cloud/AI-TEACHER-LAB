import unittest

from dataclasses import FrozenInstanceError

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.teacher_lesson_card import teacher_lesson_card_from_result
from core.workflow.vertical_slice import run_lesson_planning


class TeacherLessonCardContractTests(unittest.TestCase):
    def test_a2_accepted_lesson_materializes_teacher_card(self):
        request = {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Discuss past experiences and ask follow-up questions.",
            "group_size": 12,
            "topic": "life experiences",
        }
        tools = [
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

        def generator(generation_request, errors):
            return {
                "level": generation_request["level"],
                "objective": generation_request["objective"],
                "duration_minutes": generation_request["duration_minutes"],
                "topic": generation_request["topic"],
                "activities": [{
                    "name": "communicative task",
                    "student_production": "Students discuss a past experience and ask a follow-up question.",
                    "assessment_link": "Teacher observes the learner response during the task.",
                }],
            }

        result = run_lesson_planning(
            request,
            tools=tools,
            generators={"test-generator": generator},
        )

        self.assertEqual(result.status, "READY")
        card = teacher_lesson_card_from_result(result)

        self.assertEqual(card.version, "v1")
        self.assertEqual(card.level, "A2")
        self.assertEqual(card.audience, "adult ESL learners")
        self.assertEqual(card.objective, request["objective"])
        self.assertEqual(card.duration_minutes, 90)
        self.assertTrue(card.activities)
        self.assertEqual(card.assessment["type"], result.assessment_decision.type)
        self.assertEqual(card.assessment["evidence"], result.assessment_decision.evidence)

        with self.assertRaises(FrozenInstanceError):
            card.activities += (card.activities[0],)
        with self.assertRaises(TypeError):
            card.assessment["type"] = "WRITTEN"


if __name__ == "__main__":
    unittest.main()
