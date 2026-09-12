import unittest

from core.foundation.models import TaskPacket
from core.resources.output_validator import validate_resource_output


class TestResourceOutputValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.task = TaskPacket(
            task_id="task-a2-listening",
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

    def test_ready_when_output_matches_task(self):
        result = validate_resource_output(self.task, self._resource())

        self.assertEqual(result.status, "READY")
        self.assertEqual(result.score, 100.0)
        self.assertFalse(result.critical_failure)
        self.assertTrue(all(result.checks.values()))

    def test_revision_required_when_optional_quality_evidence_is_incomplete(self):
        result = validate_resource_output(
            self.task,
            self._resource(
                quality_criteria_addressed=[self.task.quality_criteria[0]],
            ),
        )

        self.assertEqual(result.status, "REVISION_REQUIRED")
        self.assertFalse(result.critical_failure)
        self.assertIn("quality_criteria_acknowledged", result.checks)

    def test_reject_when_resource_type_is_wrong(self):
        result = validate_resource_output(
            self.task,
            self._resource(resource_type="video"),
        )

        self.assertEqual(result.status, "REJECT")
        self.assertTrue(result.critical_failure)
        self.assertTrue(result.blocking_errors)

    def test_reject_when_level_is_wrong(self):
        result = validate_resource_output(
            self.task,
            self._resource(level="B1"),
        )

        self.assertEqual(result.status, "REJECT")
        self.assertTrue(result.critical_failure)

    def test_reject_when_content_is_missing(self):
        result = validate_resource_output(
            self.task,
            self._resource(content=""),
        )

        self.assertEqual(result.status, "REJECT")
        self.assertTrue(result.critical_failure)

    def test_missing_resource_is_rejected(self):
        result = validate_resource_output(self.task, {})

        self.assertEqual(result.status, "REJECT")
        self.assertTrue(result.critical_failure)


if __name__ == "__main__":
    unittest.main()
