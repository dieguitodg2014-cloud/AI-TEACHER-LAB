import unittest
from dataclasses import replace

from core.context.engine import build_context
from core.context.request_interpreter import interpret_request
from core.foundation.models import TaskPacket
from core.orchestration.resource_return import receive_resource, resource_return_to_dict
from core.resources.acceptance_gate import ResourceAcceptanceGate
from core.resources.output_validator import validate_resource_output


class TestResourceReturn(unittest.TestCase):
    def setUp(self) -> None:
        structured = interpret_request(
            "Create an A2 listening lesson for adult ESL learners."
        )
        context_result = build_context(structured)
        self.context = context_result.context
        self.assertIsNotNone(self.context)
        self.task = TaskPacket(
            task_id="task-a2-listening-return",
            task_type="RESOURCE_PRODUCTION",
            objective="Students will identify the main idea and key details in a short listening text.",
            level="A2",
            required_output="audio",
            constraints=[],
            quality_criteria=[
                "Directly support the stated learning objective.",
                "Match the approved learner level and audience.",
                "Be usable within the planned lesson time.",
                "Do not introduce unnecessary content or complexity.",
            ],
            audience="adult ESL learners",
        )

    def _resource(self, **overrides):
        resource = {
            "resource_type": "audio",
            "level": "A2",
            "objective": self.task.objective,
            "content": "A short listening script and its produced audio.",
        }
        resource.update(overrides)
        return resource

    def test_return_boundary_routes_valid_resource_to_accepted(self):
        result = receive_resource(self.context, self.task, self._resource())

        self.assertEqual(result.status, "ACCEPTED")
        self.assertEqual(result.task_id, self.task.task_id)
        self.assertIsNone(result.revision_handoff)
        self.assertFalse(result.errors)
        self.assertEqual(result.validation.status, "READY")

    def test_return_boundary_does_not_expose_qc_ready_as_delivery_status(self):
        result = receive_resource(self.context, self.task, self._resource())

        self.assertNotEqual(result.status, "READY")
        self.assertEqual(result.status, "ACCEPTED")

    def test_return_boundary_creates_revision_handoff(self):
        result = receive_resource(
            self.context,
            self.task,
            self._resource(quality_criteria_addressed=[self.task.quality_criteria[0]]),
        )

        self.assertEqual(result.status, "REVISION_REQUIRED")
        self.assertIsNotNone(result.revision_handoff)
        self.assertEqual(result.revision_handoff["task_id"], self.task.task_id)
        self.assertEqual(result.revision_handoff["status"], "REVISION_REQUIRED")

    def test_return_boundary_rejects_missing_resource(self):
        result = receive_resource(self.context, self.task, None)

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertTrue(result.validation.critical_failure)
        self.assertTrue(result.errors)

    def test_return_result_errors_are_immutable(self):
        result = receive_resource(self.context, self.task, None)

        self.assertIsInstance(result.errors, tuple)
        with self.assertRaises(AttributeError):
            result.errors.append("unexpected mutation")

    def test_return_result_is_serializable(self):
        result = receive_resource(self.context, self.task, self._resource())
        payload = resource_return_to_dict(result)

        self.assertEqual(payload["status"], "ACCEPTED")
        self.assertEqual(payload["task_id"], self.task.task_id)
        self.assertEqual(payload["validation"]["status"], "READY")
        self.assertEqual(payload["errors"], [])

    def test_return_boundary_rejects_unbound_ready_validation(self):
        validation = validate_resource_output(self.task, self._resource())
        unbound = replace(validation, task_fingerprint="")
        acceptance = ResourceAcceptanceGate().evaluate(self.task, unbound)

        self.assertEqual(validation.status, "READY")
        self.assertEqual(acceptance.decision, "HUMAN_HANDOFF")
        self.assertIn("RESOURCE_VALIDATION_TASK_BINDING_MISSING", acceptance.reasons)


if __name__ == "__main__":
    unittest.main()
