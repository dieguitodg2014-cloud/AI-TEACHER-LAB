import unittest

from core.foundation.models import TaskPacket
from core.resources.output_validator import validate_resource_output
from core.resources.regression_guard import check_resource_revision_regression


class TestResourceRegressionGuard(unittest.TestCase):
    def setUp(self) -> None:
        self.task = TaskPacket(
            task_id="task-a2-listening",
            task_type="RESOURCE_PRODUCTION",
            objective="Students will identify the main idea and key details in a short listening text.",
            level="A2",
            required_output="audio",
            constraints=["Keep the resource under 3 minutes."],
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

    def test_regression_guard_works_with_immutable_validation_checks(self):
        validation = validate_resource_output(self.task, self._resource())
        result = check_resource_revision_regression(self.task, validation, self._resource())
        self.assertTrue(result.passed)
        self.assertEqual(result.errors, ())

    def test_regression_result_errors_are_immutable(self):
        validation = validate_resource_output(self.task, self._resource())
        result = check_resource_revision_regression(
            self.task,
            validation,
            self._resource(resource_type="video"),
        )
        self.assertFalse(result.passed)
        self.assertTrue(result.errors)
        with self.assertRaises(AttributeError):
            result.errors.append("mutation")

    def test_revision_can_fix_failed_objective_without_regression(self):
        initial = self._resource(objective="Students will practice listening.")

        def reviser(task, resource, validation):
            return self._resource(objective=task.objective, content="Revised listening content.")

        from core.resources.revision_engine import ResourceRevisionEngine
        result = ResourceRevisionEngine().run(self.task, initial, reviser)

        self.assertEqual(result.status, "ACCEPTED")
        self.assertTrue(result.accepted)
        self.assertEqual(result.attempts, 2)

    def test_revision_is_blocked_when_it_breaks_previously_valid_level(self):
        initial = self._resource(objective="Students will practice listening.")

        def reviser(task, resource, validation):
            return self._resource(objective=task.objective, level="B1", content="Revised listening content.")

        from core.resources.revision_engine import ResourceRevisionEngine
        result = ResourceRevisionEngine().run(self.task, initial, reviser)

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertIn("RESOURCE_REGRESSION:level", result.acceptance.reasons)

    def test_revision_is_blocked_when_it_breaks_previously_valid_resource_type(self):
        initial = self._resource(objective="Students will practice listening.")

        def reviser(task, resource, validation):
            return self._resource(objective=task.objective, resource_type="video", content="Revised resource content.")

        from core.resources.revision_engine import ResourceRevisionEngine
        result = ResourceRevisionEngine().run(self.task, initial, reviser)

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertIn("RESOURCE_REGRESSION:resource_type", result.acceptance.reasons)

    def test_reviser_cannot_mutate_authorized_task_packet(self):
        initial = self._resource(objective="Students will practice listening.")

        def reviser(task, resource, validation):
            with self.assertRaises(AttributeError):
                task.constraints.append("Use a video instead.")
            return self._resource(objective=task.objective, content="Revised content.")

        from core.resources.revision_engine import ResourceRevisionEngine
        result = ResourceRevisionEngine().run(self.task, initial, reviser)

        self.assertEqual(result.status, "ACCEPTED")
        self.assertEqual(self.task.constraints, ("Keep the resource under 3 minutes.",))

    def test_reviser_cannot_mutate_engine_owned_resource(self):
        initial = self._resource(objective="Students will practice listening.", metadata={"attempt": 1})
        initial_snapshot = {**initial, "metadata": dict(initial["metadata"])}

        def reviser(task, resource, validation):
            resource["resource_type"] = "video"
            resource["metadata"]["attempt"] = 999
            return self._resource(objective=task.objective, content="Revised listening content.")

        from core.resources.revision_engine import ResourceRevisionEngine
        result = ResourceRevisionEngine().run(self.task, initial, reviser)

        self.assertEqual(result.status, "ACCEPTED")
        self.assertEqual(initial, initial_snapshot)
        self.assertEqual(result.resource["resource_type"], "audio")
        self.assertEqual(result.resource["objective"], self.task.objective)

    def test_blocking_level_mismatch_never_enters_revision(self):
        initial = self._resource(level="B1")
        calls = []

        def reviser(task, resource, validation):
            calls.append(True)
            return self._resource(level=task.level)

        from core.resources.revision_engine import ResourceRevisionEngine
        result = ResourceRevisionEngine().run(self.task, initial, reviser)

        self.assertEqual(result.status, "REJECT")
        self.assertEqual(calls, [])
        self.assertTrue(result.acceptance.blocking)


if __name__ == "__main__":
    unittest.main()
