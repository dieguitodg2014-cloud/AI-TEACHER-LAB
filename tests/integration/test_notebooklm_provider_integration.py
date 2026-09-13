import unittest

from core.foundation.models import TaskPacket
from core.orchestration.notebooklm_provider import NotebookLMResourceProvider
from core.orchestration.resource_orchestrator import execute_resource_production_with_fallback
from core.orchestration.tool_selector import ToolCandidate


class NotebookLMProviderIntegrationTests(unittest.TestCase):
    def make_task(self) -> TaskPacket:
        return TaskPacket(
            task_id="task-notebooklm-integration",
            task_type="RESOURCE_PRODUCTION",
            objective="Students identify the main idea in a short listening text.",
            level="A2",
            required_output="audio",
            constraints=["CEFR A2"],
            quality_criteria=["objective_alignment", "level_alignment"],
            lesson_id="lesson-1",
            audience="adult ESL learners",
            source_based=True,
        )

    def make_tool(self, tool_id: str) -> ToolCandidate:
        return ToolCandidate(
            tool_id=tool_id,
            capabilities={
                "resource_generation",
                "source_based_resource_generation",
                "audio_generation",
            },
            quality=0.95,
            reliability=0.9,
            accessibility=0.8,
            speed=0.7,
            cost=0.0,
        )

    def valid_audio(self) -> dict[str, str]:
        return {
            "resource_type": "audio",
            "level": "A2",
            "objective": "Students identify the main idea in a short listening text.",
            "content": "Approved audio content",
        }

    def test_notebooklm_runs_through_fallback_and_qc(self) -> None:
        calls = []

        def executor(payload):
            calls.append(payload)
            return self.valid_audio()

        task = self.make_task()
        tools = [self.make_tool("notebooklm")]
        providers = {"notebooklm": NotebookLMResourceProvider(executor)}

        result = execute_resource_production_with_fallback(
            task,
            tools,
            providers,
            max_revisions=1,
        )

        self.assertEqual(result["status"], "ACCEPTED")
        self.assertEqual(result["tool_id"], "notebooklm")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["provider"], "notebooklm")
        self.assertEqual(calls[0]["task"].task_id, task.task_id)
        self.assertEqual(task.objective, "Students identify the main idea in a short listening text.")
        self.assertEqual(task.level, "A2")
        self.assertEqual(task.required_output, "audio")

    def test_notebooklm_failure_falls_back_without_changing_task(self) -> None:
        calls = []

        def notebooklm_executor(payload):
            calls.append("notebooklm")
            raise RuntimeError("NOTEBOOKLM_TEMPORARY_FAILURE")

        def fallback_executor(payload):
            calls.append("fallback")
            return self.valid_audio()

        task = self.make_task()
        tools = [self.make_tool("notebooklm"), self.make_tool("fallback")]
        providers = {
            "notebooklm": NotebookLMResourceProvider(notebooklm_executor),
            "fallback": NotebookLMResourceProvider(fallback_executor),
        }

        result = execute_resource_production_with_fallback(
            task,
            tools,
            providers,
            max_revisions=1,
        )

        self.assertEqual(result["status"], "ACCEPTED")
        self.assertEqual(result["tool_id"], "fallback")
        self.assertEqual(calls, ["notebooklm", "fallback"])
        self.assertEqual(task.level, "A2")
        self.assertEqual(task.required_output, "audio")
        self.assertEqual(task.objective, "Students identify the main idea in a short listening text.")


if __name__ == "__main__":
    unittest.main()
