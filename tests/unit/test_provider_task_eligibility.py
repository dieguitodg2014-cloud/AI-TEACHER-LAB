import unittest

from core.orchestration.provider_task_eligibility import (
    validate_provider_task_eligibility,
)
from core.orchestration.tool_selector import ToolCandidate


class ProviderTaskEligibilityTests(unittest.TestCase):
    def setUp(self):
        self.lesson_provider = ToolCandidate(
            "lesson-provider",
            frozenset({"lesson_generation"}),
        )
        self.resource_provider = ToolCandidate(
            "resource-provider",
            frozenset({"resource_generation"}),
        )

    def test_provider_is_eligible_for_declared_task(self):
        errors = validate_provider_task_eligibility(
            self.lesson_provider,
            "LESSON_GENERATION",
            lambda request, errors: {},
        )
        self.assertEqual(errors, [])

    def test_provider_without_task_capability_is_rejected(self):
        errors = validate_provider_task_eligibility(
            self.resource_provider,
            "LESSON_GENERATION",
            lambda request, errors: {},
        )
        self.assertEqual(
            errors,
            ["PROVIDER_NOT_ELIGIBLE_FOR_TASK:resource-provider:LESSON_GENERATION"],
        )

    def test_unsupported_task_type_is_rejected(self):
        errors = validate_provider_task_eligibility(
            self.lesson_provider,
            "UNKNOWN_TASK",
            lambda request, errors: {},
        )
        self.assertEqual(errors, ["TASK_TYPE_UNSUPPORTED:UNKNOWN_TASK"])

    def test_required_capabilities_must_include_task_capability(self):
        errors = validate_provider_task_eligibility(
            self.lesson_provider,
            "LESSON_GENERATION",
            lambda request, errors: {},
            required_capabilities={"resource_generation"},
        )
        self.assertEqual(
            errors,
            [
                "PROVIDER_NOT_ELIGIBLE_FOR_TASK:lesson-provider:LESSON_GENERATION",
                "TASK_CAPABILITY_MISMATCH:LESSON_GENERATION:lesson_generation",
            ],
        )

    def test_missing_generator_is_not_eligible_for_execution(self):
        errors = validate_provider_task_eligibility(
            self.lesson_provider,
            "LESSON_GENERATION",
            None,
        )
        self.assertEqual(errors, ["GENERATOR_UNAVAILABLE:lesson-provider"])


if __name__ == "__main__":
    unittest.main()
