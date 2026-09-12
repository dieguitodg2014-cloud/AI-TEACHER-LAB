import unittest

from core.foundation.models import TaskPacket
from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import run_lesson_planning


class ResourceVerticalSliceE2ETests(unittest.TestCase):
    def _request(self):
        return {
            "context_id": "golden-a2-listening-001",
            "level": "A2",
            "audience": "adult learners",
            "duration_minutes": 90,
            "objective": "Listen to a short conversation about past experiences and identify key details.",
            "topic": "Listening practice",
            "constraints": ["communicative approach"],
        }

    def _resource_tool(self):
        return ToolCandidate(
            tool_id="notebooklm-mock",
            capabilities=frozenset({"resource_generation"}),
            quality=0.9,
            reliability=0.9,
            accessibility=1.0,
            speed=0.8,
            cost=0.0,
        )

    def test_listening_request_executes_audio_and_reaches_resource_ready(self):
        captured = {}

        def mock_resource_provider(task_dict):
            captured["task"] = task_dict
            return {
                "resource_type": task_dict["required_output"],
                "level": task_dict["level"],
                "objective": task_dict["objective"],
                "content": "Audio production placeholder for the approved listening task.",
                "format": "audio",
                "duration": 5,
                "language": "English",
                "production_status": "PRODUCED",
            }

        result = run_lesson_planning(
            self._request(),
            tools=[self._resource_tool()],
            generators={"notebooklm-mock": mock_resource_provider},
        )

        self.assertEqual(result.status, "PLANNED")
        self.assertIsNotNone(result.resource_decision)
        self.assertEqual(result.resource_decision.action, "CREATE")
        self.assertIsNotNone(result.resource_task)
        self.assertEqual(result.resource_task.task_type, "RESOURCE_PRODUCTION")
        self.assertEqual(result.resource_task.required_output, "audio")
        self.assertIsNotNone(result.resource_tool)
        self.assertEqual(result.resource_tool.tool_id, "notebooklm-mock")
        self.assertIsNotNone(result.resource_generation)
        self.assertEqual(result.resource_generation["status"], "PRODUCED")
        self.assertIsNotNone(result.resource_validation)
        self.assertEqual(result.resource_validation.status, "READY")
        self.assertEqual(result.resource_validation.score, 100.0)
        self.assertEqual(captured["task"]["task_type"], "RESOURCE_PRODUCTION")
        self.assertEqual(captured["task"]["required_output"], "audio")

    def test_listening_request_without_resource_provider_stops_at_human_handoff(self):
        result = run_lesson_planning(
            self._request(),
            tools=[],
            generators={},
        )

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertIsNotNone(result.resource_decision)
        self.assertEqual(result.resource_decision.action, "CREATE")
        self.assertIsNotNone(result.resource_task)
        self.assertEqual(result.resource_task.task_type, "RESOURCE_PRODUCTION")
        self.assertIsNone(result.resource_tool)
        self.assertIsNotNone(result.resource_handoff)
        self.assertEqual(result.errors, ["NO_SUITABLE_RESOURCE_TOOL"])


if __name__ == "__main__":
    unittest.main()
