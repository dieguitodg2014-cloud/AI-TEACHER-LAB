import unittest

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
        request["assessment_decision"] = {"success_criteria": ["ask a question"]}

        def generator(provider_request, errors):
            with self.assertRaises(TypeError):
                provider_request["level"] = "B2"
            with self.assertRaises(TypeError):
                provider_request["constraints"].append("new constraint")
            with self.assertRaises(TypeError):
                provider_request["assessment_decision"]["success_criteria"] += ("new",)
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
            "language_target": "Discuss past experiences and ask follow-up questions.",
            "evidence": "Teacher observes the learner response.",
        }]
        calls = []

        def generator(generation_request, errors):
            calls.append(list(errors))
            contract = generation_request["activity_contracts"][0]
            activity = {
                **contract,
                "evidence": contract["evidence"],
                "student_production": "Students discuss a past experience.",
                "assessment_link": "Teacher observes the learner response.",
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

    def test_repeated_failure_is_rejected(self):
        def generator(request, errors):
            return {
                "level": "B1",
                "objective": request["objective"],
                "duration_minutes": 90,
                "activities": [{"name": "discussion"}],
            }

        result = generate_with_revision(generator, self._request(), max_revisions=2)

        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["attempts"], 3)
        self.assertIn("LEVEL_MISMATCH", result["errors"])
        self.assertEqual(result["qc"]["status"], "REJECT_AND_REDESIGN")
        self.assertTrue(result["qc"]["critical_failure"])
        self.assertIn("LEVEL_MISMATCH", result["qc"]["blocking_errors"])


if __name__ == "__main__":
    unittest.main()
