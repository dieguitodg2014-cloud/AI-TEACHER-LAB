import unittest

from core.generation.lesson_generator import build_generation_request
from core.generation.revision import generate_with_revision


class GenerationRevisionTests(unittest.TestCase):
    def _request(self):
        return {
            "level": "A2",
            "objective": "Discuss past experiences and ask follow-up questions.",
            "duration_minutes": 90,
        }

    def test_valid_generation_is_accepted_without_revision(self):
        calls = []

        def generator(request, errors):
            calls.append(errors)
            return {
                "level": "A2",
                "objective": request["objective"],
                "duration_minutes": 90,
                "activities": [{"name": "discussion"}],
            }

        result = generate_with_revision(generator, self._request())

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["qc"]["status"], "READY")
        self.assertEqual(result["qc"]["score"], 100.0)
        self.assertFalse(result["qc"]["critical_failure"])
        self.assertEqual(result["qc"]["blocking_errors"], [])

    def test_invalid_generation_can_be_revised(self):
        outputs = [
            {
                "level": "B1",
                "objective": "wrong",
                "duration_minutes": 120,
                "activities": [{"name": "discussion"}],
            },
            {
                "level": "A2",
                "objective": "Discuss past experiences and ask follow-up questions.",
                "duration_minutes": 90,
                "activities": [{"name": "discussion"}],
            },
        ]

        def generator(request, errors):
            return outputs.pop(0)

        result = generate_with_revision(generator, self._request())

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["qc"]["status"], "READY")
        self.assertEqual(result["qc"]["score"], 100.0)
        self.assertEqual(result["qc"]["blocking_errors"], [])

    def test_provider_cannot_mutate_generation_request(self):
        request = self._request()
        request["constraints"] = ["stay communicative"]
        request["assessment_decision"] = {
            "success_criteria": ["ask a question"]
        }

        def generator(provider_request, errors):
            with self.assertRaises(TypeError):
                provider_request["level"] = "B2"

            with self.assertRaises(AttributeError):
                provider_request["constraints"].append("new constraint")

            with self.assertRaises(TypeError):
                provider_request["assessment_decision"]["success_criteria"] += (
                    "new",
                )

            return {
                "level": provider_request["level"],
                "objective": provider_request["objective"],
                "duration_minutes": provider_request["duration_minutes"],
                "activities": [{
                    "name": "discussion",
                    "student_production": "Students discuss a past experience.",
                    "assessment_link": "Teacher observes the learner response.",
                }],
            }

        result = generate_with_revision(generator, request)

        self.assertEqual(result["status"], "READY")
        self.assertEqual(request["level"], "A2")
        self.assertEqual(request["constraints"], ["stay communicative"])
        self.assertEqual(
            request["assessment_decision"]["success_criteria"],
            ["ask a question"],
        )

    def test_activity_contract_failure_triggers_revision(self):
        request = self._request()
        request["activity_contracts"] = [{
            "activity_id": "activity-1",
            "level": "A2",
            "objective": request["objective"],
            "skill": "SPEAKING",
            "interaction": "pairs",
            "cognitive_demand": "APPLY",
            "scaffolding": 2,
            "duration_minutes": 15,
            "language_target": (
                "Discuss past experiences and ask follow-up questions."
            ),
            "evidence": "Teacher observes the learner response.",
        }]

        calls = []

        def generator(generation_request, errors):
            calls.append(list(errors))
            contract = generation_request["activity_contracts"][0]

            activity = {
                **contract,
                "evidence": contract["evidence"],
                "student_production": (
                    "Students discuss a past experience."
                ),
                "assessment_link": (
                    "Teacher observes the learner response."
                ),
            }

            if len(calls) == 1:
                activity["interaction"] = "individual"

            return {
                "level": generation_request["level"],
                "objective": generation_request["objective"],
                "duration_minutes": generation_request["duration_minutes"],
                "activities": [activity],
            }

        result = generate_with_revision(generator, request)

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["attempts"], 2)
        self.assertIn("INTERACTION_MISMATCH", calls[1])
        self.assertEqual(result["qc"]["status"], "READY")

    def test_build_generation_request_binds_approved_topic_to_activity_contract(self):
        class Activity:
            activity_id = "activity-1"
            skill = "MIXED"
            interaction = "pairs"
            cognitive_demand = "APPLY"
            scaffolding = 2
            minutes = 15
            language_target = ""
            assessment_link = ""
            student_production = (
                "Students discuss a past experience."
            )
            purpose = "Practice the approved topic."

        class Plan:
            objective = (
                "Discuss past experiences and ask follow-up questions."
            )
            sequence = [Activity()]
            evidence_of_learning = "Observable performance."
            resource_need = "NO_RESOURCE_REQUIRED"

        request = build_generation_request(
            Plan(),
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 90,
                "topic": "Present Perfect",
                "prior_knowledge": ["Past Simple"],
                "constraints": [],
            },
        )

        self.assertEqual(request["topic"], "Present Perfect")
        self.assertEqual(
            request["activity_contracts"][0]["must_include"],
            ["Present Perfect"],
        )
        self.assertEqual(
            request["activity_contracts"][0]["must_not_include"],
            [],
        )

    def test_repeated_failure_is_rejected(self):
        def generator(request, errors):
            return {
                "level": "B1",
                "objective": request["objective"],
                "duration_minutes": 90,
                "activities": [{"name": "discussion"}],
            }

        result = generate_with_revision(
            generator,
            self._request(),
            max_revisions=2,
        )

        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["attempts"], 3)
        self.assertIn("LEVEL_MISMATCH", result["errors"])
        self.assertEqual(
            result["qc"]["status"],
            "REJECT_AND_REDESIGN",
        )
        self.assertTrue(result["qc"]["critical_failure"])
        self.assertIn(
            "LEVEL_MISMATCH",
            result["qc"]["blocking_errors"],
        )

    def test_teacher_facing_missing_execution_is_rejected(self):
        request = self._request()
        request["teacher_facing"] = True

        def generator(generation_request, errors):
            return {
                "level": generation_request["level"],
                "objective": generation_request["objective"],
                "duration_minutes": generation_request["duration_minutes"],
                "activities": [{"name": "discussion"}],
            }

        result = generate_with_revision(
            generator,
            request,
            max_revisions=2,
        )

        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["attempts"], 3)
        self.assertIn(
            "TEACHER_EXECUTION_MISSING",
            result["errors"],
        )

    def test_teacher_facing_complete_execution_is_ready(self):
        request = self._request()
        request["teacher_facing"] = True

        def generator(generation_request, errors):
            return {
                "level": generation_request["level"],
                "objective": generation_request["objective"],
                "duration_minutes": generation_request["duration_minutes"],
                "activities": [{
                    "name": "discussion",
                    "language_target": "Have you ever ...? / I have ...",
                    "student_production": (
                        "Students discuss a past experience."
                    ),
                    "assessment_link": (
                        "Teacher observes the learner response."
                    ),
                }],
                "teacher_execution": {
                    "teacher_explanation": "Explain the target language.",
                    "target_language": ["Present Perfect"],
                    "language_bank": ["Have you ever ...?"],
                    "teacher_talk": ["Ask your partner."],
                    "ccqs": ["Is the action connected to now?"],
                    "examples": ["I have visited Cartagena."],
                    "common_errors": {
                        "I have went": "I have gone"
                    },
                    "scaffolding": ["Provide a sentence frame."],
                    "materials": ["Worksheet"],
                    "worksheet": {
                        "title": "Experience survey",
                        "items": ["Have you ever ...?"],
                    },
                    "role_cards": ["Student A asks; Student B answers."],
                    "answer_key": {
                        "answers": ["Have you ever visited Cartagena?"]
                    },
                    "assessment_checklist": [
                        "Uses the target structure accurately."
                    ],
                    "exit_ticket": {
                        "prompt": "Write one Present Perfect sentence."
                    },
                },
                "assessment": {
                    "evidence": (
                        "Students produce a spoken life-experience response."
                    ),
                    "success_criteria": [
                        "Learner asks a correct question.",
                        "Learner gives an understandable answer.",
                    ],
                },
            }

        result = generate_with_revision(generator, request)

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["attempts"], 1)

    def test_teacher_facing_incomplete_execution_is_rejected(self):
        request = self._request()
        request["teacher_facing"] = True

        def generator(generation_request, errors):
            return {
                "level": generation_request["level"],
                "objective": generation_request["objective"],
                "duration_minutes": generation_request["duration_minutes"],
                "activities": [{"name": "discussion"}],
                "teacher_execution": {
                    "teacher_explanation": "Explain the target language.",
                },
            }

        result = generate_with_revision(
            generator,
            request,
            max_revisions=2,
        )

        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["attempts"], 3)
        self.assertTrue(
            any(
                error.startswith("TEACHER_EXECUTION_INCOMPLETE:")
                for error in result["errors"]
            )
        )

    def test_teacher_facing_absent_preserves_legacy_behavior(self):
        def generator(request, errors):
            return {
                "level": "A2",
                "objective": request["objective"],
                "duration_minutes": 90,
                "activities": [{"name": "discussion"}],
            }

        result = generate_with_revision(
            generator,
            self._request(),
        )

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["attempts"], 1)

    def test_invalid_teacher_facing_type_fails_request_validation(self):
        request = self._request()
        request["teacher_facing"] = "true"

        def generator(request, errors):
            raise AssertionError("Generator should not be called.")

        result = generate_with_revision(
            generator,
            request,
        )

        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(
            result["errors"],
            ["INVALID_GENERATION_REQUEST"],
        )

    def test_build_generation_request_preserves_teacher_facing_mode(self):
        class Activity:
            activity_id = "activity-1"
            skill = "SPEAKING"
            interaction = "pairs"
            cognitive_demand = "APPLY"
            scaffolding = 2
            minutes = 15
            language_target = "should + base verb"
            assessment_link = "Teacher observes advice-giving."
            student_production = "Students give advice."
            purpose = "Practice giving advice."

        class Plan:
            objective = (
                "Students will give advice and make suggestions "
                "about everyday problems."
            )
            sequence = [Activity()]
            evidence_of_learning = (
                "Students give appropriate advice."
            )
            resource_need = "NO_RESOURCE_REQUIRED"

        request = build_generation_request(
            Plan(),
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 90,
                "topic": "Should / Why don't you...? / Let's...",
                "prior_knowledge": [],
                "constraints": [],
            },
            teacher_facing=True,
        )

        self.assertTrue(request["teacher_facing"])
        self.assertIn(
            "teacher_execution_contract",
            request,
        )
        self.assertIn(
            "teacher_explanation",
            request["teacher_execution_contract"],
        )


if __name__ == "__main__":
    unittest.main()
