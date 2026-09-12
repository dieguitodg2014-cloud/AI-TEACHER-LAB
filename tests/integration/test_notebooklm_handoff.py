import unittest

from core.foundation.models import Context, LearningPlanDecision
from core.orchestration.notebooklm_handoff import build_notebooklm_handoff
from core.orchestration.task_packets import build_resource_task_packet
from core.resources.decision_engine import decide_resource


class NotebookLMHandoffIntegrationTests(unittest.TestCase):
    def test_audio_task_becomes_complete_notebooklm_handoff(self):
        context = Context(
            context_id="notebooklm-001",
            level="A2",
            audience="adult learners",
            duration_minutes=90,
            objective="Practice listening to short conversations.",
            constraints=["Use simple, authentic audio.", "Keep the audio under 3 minutes."],
            prior_knowledge=["Past Simple"],
        )
        plan = LearningPlanDecision(
            plan_id="plan-notebooklm-001",
            objective=context.objective,
            sequence=["Modeling", "Listening Practice", "Communicative Practice"],
            total_minutes=90,
            evidence_of_learning="Students complete a short listening task and respond orally.",
        )

        decision = decide_resource(context, plan)
        task = build_resource_task_packet(context, plan, decision)
        handoff = build_notebooklm_handoff(context, task)

        self.assertEqual(decision.action, "CREATE")
        self.assertEqual(task.required_output, "audio")
        self.assertEqual(handoff["status"], "HUMAN_HANDOFF")
        self.assertEqual(handoff["workflow"], "NotebookLM")
        self.assertEqual(handoff["task_id"], task.task_id)
        self.assertEqual(handoff["resource_type"], "audio")
        self.assertEqual(handoff["format"], "audio")
        self.assertEqual(handoff["duration"], 90)
        self.assertEqual(handoff["level"], "A2")
        self.assertEqual(handoff["objective"], context.objective)
        self.assertIn("return_contract", handoff["validation_requirements"])
        self.assertTrue(handoff["validation_requirements"]["preserve_task_id"])
        self.assertIn("teacher-approved", " ".join(handoff["source_requirements"]))


if __name__ == "__main__":
    unittest.main()
