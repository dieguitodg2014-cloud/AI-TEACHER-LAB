import unittest

from dataclasses import FrozenInstanceError

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.teacher_lesson_card import teacher_lesson_card_from_result
from core.workflow.teacher_lesson_card_renderer import render_teacher_lesson_card
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
                "activities": [
                    {
                        **contract,
                        "name": "approved activity",
                        "instructions": "Model the target language, then have learners practice with a partner.",
                        "student_production": contract["evidence"] or "Students complete the approved task.",
                        "assessment_link": "Teacher observes the learner response.",
                    }
                    for contract in generation_request["activity_contracts"]
                ],
            }

        result = run_lesson_planning(
            request,
            tools=tools,
            generators={"test-generator": generator},
        )

        self.assertEqual(result.status, "READY")
        card = teacher_lesson_card_from_result(result)

        self.assertEqual(card.version, "v3")
        self.assertEqual(card.level, "A2")
        self.assertEqual(card.audience, "adult ESL learners")
        self.assertEqual(card.objective, request["objective"])
        self.assertEqual(card.duration_minutes, 90)
        self.assertEqual(card.topic, "life experiences")
        self.assertEqual(card.prior_knowledge, ())
        self.assertEqual(card.constraints, ())
        self.assertTrue(card.activities)
        self.assertEqual(card.activities[3].skill, "SPEAKING")
        self.assertEqual(card.activities[3].cognitive_demand, "APPLY")
        self.assertEqual(card.activities[3].scaffolding, 2)
        self.assertEqual(card.activities[3].language_target, request["objective"])
        self.assertEqual(
            card.activities[3].instructions,
            "Model the target language, then have learners practice with a partner.",
        )
        self.assertEqual(card.assessment["type"], result.assessment_decision.type)
        self.assertEqual(card.assessment["evidence"], result.assessment_decision.evidence)

        rendered = render_teacher_lesson_card(card)
        self.assertIn("Approved lesson context", rendered)
        self.assertIn("life experiences", rendered)
        self.assertIn("SPEAKING", rendered)
        self.assertIn("Scaffolding:", rendered)
        self.assertIn("Teacher instructions:", rendered)

        with self.assertRaises(FrozenInstanceError):
            card.activities += (card.activities[0],)
        with self.assertRaises(TypeError):
            card.assessment["type"] = "WRITTEN"


if __name__ == "__main__":
    unittest.main()
