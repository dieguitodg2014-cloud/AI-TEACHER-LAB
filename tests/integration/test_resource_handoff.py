import unittest

from core.orchestration.resource_handoff import build_resource_handoff
from core.orchestration.task_packets import build_resource_task_packet
from core.resources.decision_engine import decide_resource
from core.foundation.models import Context, LearningPlanDecision


class ResourceHandoffIntegrationTests(unittest.TestCase):
    def test_required_resource_without_tool_can_be_handed_off(self):
        context = Context(
            context_id="handoff-001",
            level="A2",
            audience="adult learners",
            duration_minutes=90,
            objective="Practice listening to short conversations.",
            constraints=["Use simple, authentic audio."],
            prior_knowledge=["Past Simple"],
        )
        plan = LearningPlanDecision(
            plan_id="plan-handoff-001",
            objective=context.objective,
            sequence=["Presentation", "Modeling", "Guided Practice", "Communicative Practice", "Production", "Assessment"],
            total_minutes=90,
            evidence_of_learning="Students complete a short listening task and respond orally.",
        )

        decision = decide_resource(context, plan)
        task = build_resource_task_packet(context, plan, decision)
        handoff = build_resource_handoff(context, task)

        self.assertEqual(decision.action, "CREATE")
        self.assertEqual(decision.resource_type, "audio")
        self.assertIsNotNone(task)
        self.assertEqual(handoff["status"], "HUMAN_HANDOFF")
        self.assertEqual(handoff["workflow"], "NotebookLM")
        self.assertEqual(handoff["task_id"], task.task_id)
        self.assertEqual(handoff["required_output"], "audio")
        self.assertIn("teacher-approved", " ".join(handoff["source_requirements"]))


if __name__ == "__main__":
    unittest.main()
