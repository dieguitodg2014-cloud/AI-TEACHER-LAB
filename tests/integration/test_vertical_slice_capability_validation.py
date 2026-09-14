import unittest

from core.orchestration.capability_validation import CapabilityValidationResult, VALIDATED
from core.orchestration.capability_validation_registry import CapabilityValidationRegistry
from core.orchestration.tool_selector import ToolCandidate
from core.workflow.vertical_slice import run_lesson_planning


REQUEST = {
    "context_id": "visual-resource-001",
    "level": "A1",
    "audience": "adult learners",
    "duration_minutes": 60,
    "objective": "Practice basic classroom greetings with visual prompts.",
    "constraints": [],
}


class VerticalSliceCapabilityValidationIntegrationTests(unittest.TestCase):
    def _tools(self):
        return [
            ToolCandidate(
                tool_id="notebooklm",
                capabilities=frozenset(
                    {
                        "resource_generation",
                        "presentation_generation",
                        "visual_resource_generation",
                    }
                ),
                quality=1.0,
                reliability=1.0,
                accessibility=0.9,
                speed=0.8,
                cost=0.0,
                capability_validation=(("visual_resource_generation", "not_validated"),),
            ),
            ToolCandidate(
                tool_id="canva",
                capabilities=frozenset(
                    {
                        "resource_generation",
                        "presentation_generation",
                        "visual_resource_generation",
                    }
                ),
                quality=0.95,
                reliability=0.95,
                accessibility=0.9,
                speed=0.8,
                cost=0.0,
            ),
        ]

    def test_vertical_slice_skips_unvalidated_preferred_provider(self):
        calls = []

        def notebooklm_executor(payload):
            calls.append("notebooklm")
            task = payload["task"]
            return {
                "resource_type": "presentation",
                "level": task["level"],
                "objective": task["objective"],
                "content": "This provider must not execute while visual capability is unvalidated.",
            }

        def canva_executor(payload):
            calls.append("canva")
            task = payload["task"]
            return {
                "resource_type": "presentation",
                "level": task["level"],
                "objective": task["objective"],
                "content": "A short visual presentation for classroom greetings.",
                "quality_criteria_addressed": task["quality_criteria"],
            }

        result = run_lesson_planning(
            REQUEST,
            tools=self._tools(),
            notebooklm_executor=notebooklm_executor,
            canva_executor=canva_executor,
            validation_registry=CapabilityValidationRegistry(),
        )

        self.assertEqual(result.status, "READY")
        self.assertEqual(calls, ["canva"])
        self.assertEqual(result.resource_tool.tool_id, "canva")
        self.assertIsNotNone(result.resource_validation)
        self.assertEqual(result.resource_validation.status, "READY")
        self.assertEqual(result.resource_validation.score, 100.0)

    def test_vertical_slice_uses_validated_preferred_provider(self):
        calls = []
        registry = CapabilityValidationRegistry().record(
            CapabilityValidationResult(
                tool_id="notebooklm",
                capability="visual_resource_generation",
                status=VALIDATED,
                evidence=("validated_visual_presentation_test",),
            )
        )

        def notebooklm_executor(payload):
            calls.append("notebooklm")
            task = payload["task"]
            return {
                "resource_type": "presentation",
                "level": task["level"],
                "objective": task["objective"],
                "content": "A validated visual presentation for classroom greetings.",
                "quality_criteria_addressed": task["quality_criteria"],
            }

        def canva_executor(_payload):
            calls.append("canva")
            raise AssertionError("Canva must not execute when NotebookLM is validated")

        result = run_lesson_planning(
            REQUEST,
            tools=self._tools(),
            notebooklm_executor=notebooklm_executor,
            canva_executor=canva_executor,
            validation_registry=registry,
        )

        self.assertEqual(result.status, "READY")
        self.assertEqual(calls, ["notebooklm"])
        self.assertEqual(result.resource_tool.tool_id, "notebooklm")
        self.assertIsNotNone(result.resource_validation)
        self.assertEqual(result.resource_validation.status, "READY")
        self.assertEqual(result.resource_validation.score, 100.0)

    def test_vertical_slice_preserves_exclusion_trace_when_all_providers_are_ineligible(self):
        tools = self._tools()
        tools[1] = ToolCandidate(
            tool_id="canva",
            capabilities=frozenset({"resource_generation", "presentation_generation"}),
            quality=0.95,
            reliability=0.95,
            accessibility=0.9,
            speed=0.8,
            cost=0.0,
        )
        calls = []

        def notebooklm_executor(_payload):
            calls.append("notebooklm")
            raise AssertionError("unvalidated provider must never execute")

        def canva_executor(_payload):
            calls.append("canva")
            raise AssertionError("provider missing visual capability must never execute")

        result = run_lesson_planning(
            REQUEST,
            tools=tools,
            notebooklm_executor=notebooklm_executor,
            canva_executor=canva_executor,
            validation_registry=CapabilityValidationRegistry(),
        )

        self.assertEqual(result.status, "HUMAN_HANDOFF")
        self.assertEqual(calls, [])
        self.assertIsNone(result.resource_tool)
        self.assertIsNotNone(result.generation)
        self.assertEqual(result.generation["provider_attempts"], ())
        self.assertEqual(
            result.generation["provider_execution_trace"]["excluded_tools"],
            (
                ("notebooklm", "CAPABILITY_NOT_VALIDATED:visual_resource_generation"),
                ("canva", "MISSING_REQUIRED_CAPABILITIES:visual_resource_generation"),
            ),
        )
        self.assertEqual(result.errors, ["NO_ELIGIBLE_RESOURCE_TOOL_AFTER_FALLBACK"])


if __name__ == "__main__":
    unittest.main()
