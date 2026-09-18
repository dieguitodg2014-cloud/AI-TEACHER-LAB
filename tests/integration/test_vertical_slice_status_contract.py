import unittest

from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import run_lesson_planning


class VerticalSliceStatusContractTests(unittest.TestCase):
    def _request(self):
        return {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Discuss past experiences.",
        }

    def test_missing_required_context_is_distinguished_from_failure(self):
        request = self._request()
        del request["objective"]

        result = run_lesson_planning(request)

        self.assertEqual(result.status, "MISSING_CONTEXT")
        self.assertIsNone(result.context)
        self.assertTrue(result.missing)
        self.assertEqual(result.errors, ())

    def test_planning_is_distinguished_from_execution(self):
        result = run_lesson_planning(self._request())
        self.assertEqual(result.status, "PLANNED")
        self.assertIsNone(result.generation)
        self.assertEqual(result.errors, ())

    def test_missing_generator_is_human_handoff(self):
        tool = ToolCandidate(
            tool_id="available-tool",
            capabilities=frozenset({"lesson_generation"}),
            quality=1.0,
            reliability=1.0,
            accessibility=1.0,
            speed=1.0,