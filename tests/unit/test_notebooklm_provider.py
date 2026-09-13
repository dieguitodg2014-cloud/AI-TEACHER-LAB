import unittest

from core.foundation.models import TaskPacket
from core.orchestration.notebooklm_provider import NotebookLMResourceProvider


class NotebookLMResourceProviderTests(unittest.TestCase):
    def make_task(self) -> TaskPacket:
        return TaskPacket(
            task_id="task-notebooklm-1",
            task_type="RESOURCE_PRODUCTION",
            objective="Students identify the main idea in a short listening text.",
            level="A2",
            required_output="audio",
            constraints=["CEFR A2", "3 minutes maximum"],
            quality_criteria=["objective_alignment", "level_alignment"],
            lesson_id="lesson-1",
            audience="adult ESL learners",
            source_based=True,
        )

    def test_unconfigured_provider_is_not_eligible(self) -> None:
        provider = NotebookLMResourceProvider()
        self.assertFalse(provider.can_produce(self.make_task()))
        with self.assertRaisesRegex(RuntimeError, "NOTEBOOKLM_CONNECTOR_NOT_CONFIGURED"):
            provider.produce(self.make_task())

    def test_executor_receives_provider_and_isolated_task(self) -> None:
        original = self.make_task()
        received = {}

        def executor(payload):
            received.update(payload)
            received["task"].constraints.append("CONNECTOR_MUTATION")
            return {
                "resource_type": "audio",
                "level": "A2",
                "objective": "Students identify the main idea in a short listening text.",
                "content": "Approved audio content",
            }

        provider = NotebookLMResourceProvider(executor)
        self.assertTrue(provider.can_produce(original))
        result = provider.produce(original)

        self.assertEqual(received["provider"], "notebooklm")
        self.assertEqual(received["task"].task_id, original.task_id)
        self.assertEqual(result["resource_type"], "audio")
        self.assertEqual(original.constraints, ["CEFR A2", "3 minutes maximum"])

    def test_executor_must_return_object(self) -> None:
        provider = NotebookLMResourceProvider(lambda payload: "invalid")
        with self.assertRaisesRegex(TypeError, "NOTEBOOKLM_RESOURCE_OUTPUT_NOT_OBJECT"):
            provider.produce(self.make_task())

    def test_constructor_rejects_non_callable_executor(self) -> None:
        with self.assertRaisesRegex(TypeError, "NOTEBOOKLM_EXECUTOR_NOT_CALLABLE"):
            NotebookLMResourceProvider(executor="not-callable")


if __name__ == "__main__":
    unittest.main()
