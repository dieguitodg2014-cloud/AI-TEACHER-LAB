import unittest

from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import execute_resource_provider
from core.orchestration.resource_provider import FunctionResourceProvider, ResourceProvider
from core.orchestration.tool_selector import ToolCandidate


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

    def _tool(self, capabilities=("resource_generation",)):
        return ToolCandidate(
            tool_id="resource-provider",
            capabilities=frozenset(capabilities),
            quality=1.0,
            reliability=1.0,
            accessibility=1.0,
            speed=1.0,
            cost=0.0,
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

    def test_provider_neutral_execution_accepts_resource_provider(self):
        provider = FunctionResourceProvider(
            lambda task: {
                "resource_type": task["required_output"],
                "content": "sample audio",
            }
        )

        result = execute_resource_provider(self._task(), self._tool(), provider)

        self.assertEqual(result["status"], "PRODUCED")
        self.assertEqual(result["tool_id"], "resource-provider")
        self.assertEqual(result["result"]["resource_type"], "audio")

    def test_provider_neutral_execution_rejects_lesson_only_capability(self):
        provider = FunctionResourceProvider(lambda task: {"content": "sample"})

        result = execute_resource_provider(
            self._task(), self._tool(("lesson_generation",)), provider
        )

        self.assertEqual(result["status"], "HUMAN_HANDOFF")
        self.assertIn("PROVIDER_NOT_ELIGIBLE_FOR_TASK", result["errors"][0])

    def test_provider_neutral_execution_rejects_invalid_provider_contract(self):
        class InvalidProvider:
            pass

        result = execute_resource_provider(self._task(), self._tool(), InvalidProvider())

        self.assertEqual(result["status"], "HUMAN_HANDOFF")
        self.assertEqual(result["errors"], ["RESOURCE_PROVIDER_CONTRACT_INVALID"])


if __name__ == "__main__":
    unittest.main()
