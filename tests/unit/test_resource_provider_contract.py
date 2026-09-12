import unittest

from core.foundation.models import TaskPacket
from core.orchestration.resource_provider import FunctionResourceProvider, ResourceProvider


class ResourceProviderContractTests(unittest.TestCase):
    def _task(self, task_type="RESOURCE_PRODUCTION"):
        return TaskPacket(
            task_id="resource-provider-test",
            task_type=task_type,
            objective="Create a short listening resource.",
            level="A2",
            audience="adult learners",
            duration_minutes=90,
            required_output="audio",
            constraints=["English"],
        )

    def test_function_adapter_exposes_minimal_provider_contract(self):
        captured = {}

        def generator(task_dict):
            captured["task"] = task_dict
            return {"resource_type": "audio", "content": "sample"}

        provider = FunctionResourceProvider(generator)

        self.assertIsInstance(provider, ResourceProvider)
        self.assertTrue(provider.can_produce(self._task()))
        self.assertFalse(provider.can_produce(self._task("LESSON_GENERATION")))
        self.assertEqual(provider.produce(self._task())["resource_type"], "audio")
        self.assertEqual(captured["task"]["task_type"], "RESOURCE_PRODUCTION")

    def test_provider_rejects_non_object_output(self):
        provider = FunctionResourceProvider(lambda task: ["not", "a", "resource"])

        with self.assertRaisesRegex(TypeError, "RESOURCE_OUTPUT_NOT_OBJECT"):
            provider.produce(self._task())

    def test_provider_requires_callable(self):
        with self.assertRaisesRegex(TypeError, "RESOURCE_PROVIDER_GENERATOR_NOT_CALLABLE"):
            FunctionResourceProvider(None)


if __name__ == "__main__":
    unittest.main()
