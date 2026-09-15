import unittest

from core.foundation.models import TaskPacket
from core.resources.output_validator import ResourceValidationResult, validate_resource_output


class TestResourceValidationResultImmutability(unittest.TestCase):
    def setUp(self) -> None:
        self.task = TaskPacket(
            task_id="task-a2-listening-qc",
            task_type="RESOURCE_PRODUCTION",
            objective="Students will identify the main idea in a short listening text.",
            level="A2",
            required_output="audio",
            constraints=[],
            quality_criteria=["Directly support the stated learning objective."],
            audience="adult ESL learners",
        )

    def test_nested_validation_evidence_is_immutable(self):
        result = validate_resource_output(
            self.task,
            {
                "resource_type": "audio",
                "level": "A2",
                "objective": self.task.objective,
                "content": "Short listening content.",
            },
        )

        with self.assertRaises(TypeError):
            result.checks["new_check"] = True
        with self.assertRaises(TypeError):
            del result.checks["resource_type"]
        with self.assertRaises(AttributeError):
            result.feedback.append("mutate")
        with self.assertRaises(AttributeError):
            result.blocking_errors.append("mutate")

    def test_source_collections_are_snapshotted(self):
        checks = {"resource_present": True}
        feedback = ["Needs revision."]
        blocking_errors = ["Blocking issue."]

        result = ResourceValidationResult(
            validation_id="resource-qc-test",
            status="REVISION_REQUIRED",
            score=50.0,
            critical_failure=False,
            checks=checks,
            feedback=feedback,
            blocking_errors=blocking_errors,
        )

        checks["later"] = False
        feedback.append("later")
        blocking_errors.append("later")

        self.assertNotIn("later", result.checks)
        self.assertEqual(result.feedback, ("Needs revision.",))
        self.assertEqual(result.blocking_errors, ("Blocking issue.",))

    def test_top_level_fields_remain_frozen(self):
        result = ResourceValidationResult(
            validation_id="resource-qc-test",
            status="READY",
            score=100.0,
            critical_failure=False,
            checks={"resource_present": True},
        )

        with self.assertRaises(AttributeError):
            result.status = "REJECT"


if __name__ == "__main__":
    unittest.main()
