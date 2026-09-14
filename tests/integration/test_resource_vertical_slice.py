import unittest

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import run_lesson_planning


REQUEST = {
    "context_id": "resource-001",
    "level": "A2",
    "audience": "adult learners",
    "duration_minutes": 90,
    "objective": "Practice listening to short conversations.",
    "constraints": [],
}


class ResourceVerticalSliceIntegrationTests(unittest.TestCase):
    def test_required_audio_resource_selects_capable_tool(self):
        tools = [
            ToolCandidate(
                tool_id="resource-tool",
                capabilities=frozenset({"lesson_generation", "resource_generation", "audio_generation"}),
                quality=0.8,
                reliability=0.9,
                accessibility=1.0,
                speed=0.7,
                cost=0.0,
            )
        ]

        result = run_lesson_planning(REQUEST, tools=tools)

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNotNone(result.resource_task)
        self.assertEqual(result.resource_decision.action, "CREATE")
        self.assertEqual(result.resource_decision.resource_type, "audio")
        self.assertIsNotNone(result.resource_tool)
        self.assertEqual(result.resource_tool.tool_id, "resource-tool")

    def test_required_resource_without_capable_tool_has_no_selected_resource_tool(self):
        tools = [
            ToolCandidate(
                tool_id="lesson-only-tool",
                capabilities=frozenset({"lesson_generation"}),
            )
        ]

        result = run_lesson_planning(REQUEST, tools=tools)

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNotNone(result.resource_task)
        self.assertIsNone(result.resource_tool)

    def test_no_resource_needed_does_not_select_resource_tool(self):
        tools = [
            ToolCandidate(
                tool_id="resource-tool",
                capabilities=frozenset({"lesson_generation", "resource_generation"}),
            )
        ]

        result = run_lesson_planning(
            {
                **REQUEST,
                "objective": "Discuss past experiences and ask follow-up questions.",
            },
            tools=tools,
        )

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNone(result.resource_task)
        self.assertIsNone(result.resource_tool)

    def test_resource_provider_executes_task_and_resource_qc_accepts_output(self):
        tools = [
            ToolCandidate(
                tool_id="mock-resource-provider",
                capabilities=frozenset({"resource_generation", "audio_generation"}),
                quality=1.0,
                reliability=1.0,
                accessibility=1.0,
                speed=1.0,
                cost=0.0,
            )
        ]
        calls = []

        def mock_resource_provider(task_packet):
            calls.append(task_packet)
            return {
                "resource_type": "audio",
                "level": task_packet["level"],
                "objective": task_packet["objective"],
                "content": "A short conversation between two adults about making a weekend appointment.",
                "quality_criteria_addressed": task_packet["quality_criteria"],
            }

        result = run_lesson_planning(
            REQUEST,
            tools=tools,
            generators={"mock-resource-provider": mock_resource_provider},
        )

        self.assertEqual(result.status, "ACCEPTED")
        self.assertEqual(result.generation["status"], "ACCEPTED")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["task_type"], "RESOURCE_PRODUCTION")
        self.assertIsNotNone(result.resource_tool)
        self.assertEqual(result.resource_tool.tool_id, "mock-resource-provider")
        self.assertIsNotNone(result.generation)
        self.assertIsNotNone(result.resource_validation)
        self.assertEqual(result.resource_validation.status, "READY")
        self.assertEqual(result.resource_validation.score, 100.0)

    def test_resource_task_cannot_be_executed_by_lesson_only_provider(self):
        tools = [
            ToolCandidate(
                tool_id="lesson-only-tool",
                capabilities=frozenset({"lesson_generation"}),
            )
        ]

        def lesson_provider(_task_packet):
            return {"resource_type": "audio"}

        result = run_lesson_planning(
            REQUEST,
            tools=tools,
            generators={"lesson-only-tool": lesson_provider},
        )

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertIsNotNone(result.resource_task)
        self.assertIsNone(result.resource_validation)
        self.assertIn("NO_SUITABLE_RESOURCE_TOOL", result.errors)

    def test_resource_provider_output_failure_reaches_resource_acceptance_boundary(self):
        tools = [
            ToolCandidate(
                tool_id="mock-resource-provider",
                capabilities=frozenset({"resource_generation", "audio_generation"}),
            )
        ]

        def mock_resource_provider(task_packet):
            return {
                "resource_type": "presentation",
                "level": task_packet["level"],
                "objective": task_packet["objective"],
                "content": "Wrong resource type.",
            }

        result = run_lesson_planning(
            REQUEST,
            tools=tools,
            generators={"mock-resource-provider": mock_resource_provider},
        )

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertIsNotNone(result.resource_validation)
        self.assertEqual(result.resource_validation.status, "REJECT")
        self.assertTrue(result.resource_validation.critical_failure)
        self.assertIsNone(result.generation)
        self.assertIn("resource_type mismatch", result.errors[0])

    def test_qc_rejection_does_not_trigger_provider_fallback(self):
        tools = [
            ToolCandidate(
                tool_id="provider-a",
                capabilities=frozenset({"resource_generation", "audio_generation"}),
                quality=1.0,
                reliability=1.0,
            ),
            ToolCandidate(
                tool_id="provider-b",
                capabilities=frozenset({"resource_generation", "audio_generation"}),
                quality=0.9,
                reliability=0.9,
            ),
        ]
        calls = []

        def rejected_provider(task_packet):
            calls.append("provider-a")
            return {
                "resource_type": "presentation",
                "level": task_packet["level"],
                "objective": task_packet["objective"],
                "content": "Wrong resource type.",
            }

        def fallback_provider(task_packet):
            calls.append("provider-b")
            return {
                "resource_type": "audio",
                "level": task_packet["level"],
                "objective": task_packet["objective"],
                "content": "A valid fallback audio resource.",
                "quality_criteria_addressed": task_packet["quality_criteria"],
            }

        result = run_lesson_planning(
            REQUEST,
            tools=tools,
            generators={
                "provider-a": rejected_provider,
                "provider-b": fallback_provider,
            },
        )

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertEqual(calls, ["provider-a"])
        self.assertEqual(result.generation["tool_id"], "provider-a")
        self.assertEqual(result.generation["status"], "HUMAN_HANDOFF")
        self.assertEqual(result.resource_validation.status, "REJECT")
        self.assertNotIn("provider-b", calls)

    def test_produced_resource_without_task_cannot_cross_acceptance_boundary(self):
        tools = [
            ToolCandidate(
                tool_id="resource-tool",
                capabilities=frozenset({"lesson_generation", "resource_generation"}),
            )
        ]

        result = run_lesson_planning(
            {
                **REQUEST,
                "objective": "Discuss past experiences and ask follow-up questions.",
            },
            tools=tools,
            produced_resource={
                "resource_type": "audio",
                "level": "A2",
                "objective": "Discuss past experiences and ask follow-up questions.",
                "content": "Unapproved resource.",
            },
        )

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertEqual(result.errors, ["RESOURCE_TASK_MISSING_FOR_ACCEPTANCE"])
        self.assertIsNone(result.generation)

    def test_notebooklm_executor_runs_through_same_resource_qc_boundary(self):
        tools = [
            ToolCandidate(
                tool_id="notebooklm",
                capabilities=frozenset({"resource_generation", "audio_generation"}),
                quality=1.0,
                reliability=1.0,
                accessibility=0.8,
                speed=0.7,
                cost=0.0,
            )
        ]
        calls = []

        def notebooklm_executor(payload):
            calls.append(payload)
            task = payload["task"]
            return {
                "resource_type": "audio",
                "level": task["level"],
                "objective": task["objective"],
                "content": "A short A2 listening conversation produced by the connector.",
                "quality_criteria_addressed": task["quality_criteria"],
            }

        result = run_lesson_planning(
            REQUEST,
            tools=tools,
            notebooklm_executor=notebooklm_executor,
        )

        self.assertEqual(result.status, "ACCEPTED")
        self.assertEqual(result.generation["status"], "ACCEPTED")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["provider"], "notebooklm")
        self.assertEqual(calls[0]["task"]["task_type"], "RESOURCE_PRODUCTION")
        self.assertIsNotNone(result.resource_validation)
        self.assertEqual(result.resource_validation.status, "READY")
        self.assertEqual(result.resource_validation.score, 100.0)
        self.assertEqual(result.resource_tool.tool_id, "notebooklm")

    def test_canva_executor_runs_through_same_resource_qc_boundary(self):
        tools = [
            ToolCandidate(
                tool_id="canva",
                capabilities=frozenset({"resource_generation", "presentation_generation", "visual_resource_generation"}),
                quality=1.0,
                reliability=1.0,
                accessibility=0.85,
                speed=0.8,
                cost=0.0,
            )
        ]
        calls = []

        def canva_executor(payload):
            calls.append(payload)
            task = payload["task"]
            return {
                "resource_type": "presentation",
                "level": task["level"],
                "objective": task["objective"],
                "content": "A short visual presentation for classroom greetings.",
                "quality_criteria_addressed": task["quality_criteria"],
            }

        result = run_lesson_planning(
            {
                **REQUEST,
                "objective": "Practice greetings with visual prompts.",
            },
            tools=tools,
            canva_executor=canva_executor,
        )

        self.assertEqual(result.status, "ACCEPTED")
        self.assertEqual(result.generation["status"], "ACCEPTED")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["provider"], "canva")
        self.assertEqual(calls[0]["task"]["task_type"], "RESOURCE_PRODUCTION")
        self.assertEqual(calls[0]["task"]["resource_type"], "presentation")
        self.assertIsNotNone(result.resource_validation)
        self.assertEqual(result.resource_validation.status, "READY")
        self.assertEqual(result.resource_validation.score, 100.0)
        self.assertEqual(result.resource_tool.tool_id, "canva")


if __name__ == "__main__":
    unittest.main()
