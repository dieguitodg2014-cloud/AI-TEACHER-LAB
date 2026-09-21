import unittest

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import result_to_dict, run_lesson_planning


class GenerationVerticalSliceTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Discuss past experiences and ask follow-up questions.",
            "group_size": 12,
            "topic": "life experiences",
        }
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

    def test_full_slice_reaches_ready(self):
        def generator(request, errors):
            return {
                "level": request["level"],
                "objective": request["objective"],
                "duration_minutes": request["duration_minutes"],
                "topic": request["topic"],
                "activities": [
                    {
                        **contract,
                        "name": "approved activity",
                        "student_production": contract["evidence"]
                        or "Students complete the approved task.",
                        "assessment_link": (
                            "Teacher observes the learner response."
                        ),
                    }
                    for contract in request["activity_contracts"]
                ],
            }

        result = run_lesson_planning(
            self.request,
            tools=self.tools,
            generators={"test-generator": generator},
        )

        self.assertEqual(result.status, "READY")
        self.assertEqual(result.generation["tool_id"], "test-generator")
        self.assertEqual(result.generation["result"]["status"], "READY")

    def test_generator_receives_assessment_decision(self):
        captured = {}

        def generator(request, errors):
            captured.update(request)
            return {
                "level": request["level"],
                "objective": request["objective"],
                "duration_minutes": request["duration_minutes"],
                "topic": request["topic"],
                "activities": [
                    {
                        **contract,
                        "name": "approved activity",
                        "student_production": contract["evidence"]
                        or "Students complete the approved task.",
                        "assessment_link": (
                            "Teacher observes the learner response."
                        ),
                    }
                    for contract in request["activity_contracts"]
                ],
            }

        result = run_lesson_planning(
            self.request,
            tools=self.tools,
            generators={"test-generator": generator},
        )

        self.assertEqual(result.status, "READY")
        self.assertIsNotNone(result.assessment_decision)
        self.assertIn("assessment_decision", captured)
        self.assertEqual(
            captured["assessment_decision"]["assessment_id"],
            result.assessment_decision.assessment_id,
        )
        self.assertEqual(
            captured["assessment_decision"]["type"],
            result.assessment_decision.type,
        )
        self.assertEqual(
            captured["assessment_decision"]["evidence"],
            result.assessment_decision.evidence,
        )
        self.assertEqual(
            captured["assessment_decision"]["success_criteria"],
            tuple(result.assessment_decision.success_criteria),
        )

    def test_result_to_dict_exposes_stable_serializable_contract(self):
        def generator(request, errors):
            return {
                "level": request["level"],
                "objective": request["objective"],
                "duration_minutes": 90,
                "topic": request["topic"],
                "activities": [
                    {
                        **contract,
                        "name": "approved activity",
                        "student_production": contract["evidence"]
                        or "Students complete the approved task.",
                        "assessment_link": (
                            "Teacher observes the learner response."
                        ),
                    }
                    for contract in request["activity_contracts"]
                ],
            }

        result = run_lesson_planning(
            self.request,
            tools=self.tools,
            generators={"test-generator": generator},
        )
        payload = result_to_dict(result)

        self.assertEqual(payload["status"], "READY")
        self.assertEqual(payload["context"]["level"], "A2")
        self.assertEqual(
            payload["assessment_decision"]["type"],
            "PERFORMANCE",
        )
        self.assertEqual(
            payload["assessment_decision"]["target"],
            result.assessment_decision.target,
        )
        self.assertIsInstance(
            payload["assessment_decision"]["success_criteria"],
            list,
        )
        self.assertEqual(
            payload["generation"]["tool_id"],
            "test-generator",
        )
        self.assertIn("resource_decision", payload)
        self.assertIn("learning_plan", payload)

    def test_full_slice_can_handoff(self):
        result = run_lesson_planning(
            self.request,
            tools=[],
            generators={},
        )

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertIn("NO_SUITABLE_TOOL", result.errors)

    def test_without_execution_dependencies_it_remains_planned(self):
        result = run_lesson_planning(self.request)

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNone(result.generation)

    def test_teacher_facing_mode_reaches_generation_request(self):
        request = {
            **self.request,
            "teacher_facing": True,
        }
        captured = {}

        def generator(generation_request, errors):
            captured.update(generation_request)

            return {
                "level": generation_request["level"],
                "objective": generation_request["objective"],
                "duration_minutes": generation_request["duration_minutes"],
                "topic": generation_request["topic"],
                "activities": [
                    {
                        **contract,
                        "name": "approved activity",
                        "student_production": (
                            contract["evidence"]
                            or "Students complete the approved task."
                        ),
                        "assessment_link": (
                            "Teacher observes the learner response."
                        ),
                    }
                    for contract in generation_request["activity_contracts"]
                ],
                "teacher_execution": {
                    "teacher_explanation": (
                        "Explain how learners talk about life experiences."
                    ),
                    "target_language": [
                        "Have you ever ...?",
                        "I have ...",
                    ],
                    "language_bank": [
                        "Have you ever ...?",
                        "Yes, I have.",
                        "No, I haven't.",
                    ],
                    "teacher_talk": [
                        "Ask your partner.",
                        "Listen and ask one follow-up question.",
                    ],
                    "ccqs": [
                        "Are we asking about a life experience?"
                    ],
                    "examples": [
                        "Have you ever visited Cartagena?"
                    ],
                    "common_errors": {
                        "I have went": "I have gone"
                    },
                    "scaffolding": [
                        "Provide the sentence frame: Have you ever ...?"
                    ],
                    "materials": [
                        "Student worksheet"
                    ],
                    "worksheet": {
                        "title": "Life Experiences",
                        "items": [
                            "Have you ever traveled abroad?"
                        ],
                    },
                    "role_cards": [
                        "Student A asks a question. Student B answers."
                    ],
                    "answer_key": {
                        "answers": [
                            "Have you ever traveled abroad?"
                        ]
                    },
                    "assessment_checklist": [
                        "Learner asks a correct question.",
                        "Learner gives an understandable answer.",
                    ],
                    "exit_ticket": {
                        "prompt": "Write one sentence about a life experience."
                    },
                },
            }

        result = run_lesson_planning(
            request,
            tools=self.tools,
            generators={"test-generator": generator},
        )

        self.assertEqual(result.status, "READY")
        self.assertTrue(captured["teacher_facing"])
        self.assertIn(
            "teacher_execution_contract",
            captured,
        )

    def test_teacher_facing_missing_execution_is_rejected_end_to_end(self):
        request = {
            **self.request,
            "teacher_facing": True,
        }

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
                        "student_production": (
                            contract["evidence"]
                            or "Students complete the approved task."
                        ),
                        "assessment_link": (
                            "Teacher observes the learner response."
                        ),
                    }
                    for contract in generation_request["activity_contracts"]
                ],
            }

        result = run_lesson_planning(
            request,
            tools=self.tools,
            generators={"test-generator": generator},
        )

        self.assertEqual(result.status, "REJECT")
        self.assertIn(
            "TEACHER_EXECUTION_MISSING",
            result.errors,
        )


if __name__ == "__main__":
    unittest.main()
