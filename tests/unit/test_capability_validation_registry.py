from core.orchestration.capability_validation import (
    NOT_VALIDATED,
    VALIDATED,
    CapabilityValidationResult,
)
from core.orchestration.capability_validation_registry import CapabilityValidationRegistry
from core.orchestration.tool_selector import ToolCandidate


def test_record_replaces_previous_result_for_same_provider_capability():
    registry = CapabilityValidationRegistry()
    first = CapabilityValidationResult("notebooklm", "visual_resource_generation", NOT_VALIDATED)
    second = CapabilityValidationResult(
        "notebooklm",
        "visual_resource_generation",
        VALIDATED,
        ("visual-smoke-test",),
    )

    updated = registry.record(first).record(second)

    assert updated.get("notebooklm", "visual_resource_generation") == second
    assert len(updated.results) == 1


def test_effective_tool_promotes_only_validated_declared_capabilities():
    tool = ToolCandidate(
        "notebooklm",
        frozenset({"resource_generation", "visual_resource_generation"}),
        capability_validation=(("visual_resource_generation", NOT_VALIDATED),),
    )
    result = CapabilityValidationResult(
        "notebooklm", "visual_resource_generation", VALIDATED
    )

    effective = CapabilityValidationRegistry((result,)).effective_tool(tool)

    assert effective is not tool
    assert effective.validation_status("visual_resource_generation") == VALIDATED
    assert tool.validation_status("visual_resource_generation") == NOT_VALIDATED


def test_failed_validation_does_not_promote_capability():
    tool = ToolCandidate("notebooklm", frozenset({"visual_resource_generation"}))
    result = CapabilityValidationResult(
        "notebooklm", "visual_resource_generation", NOT_VALIDATED
    )

    effective = CapabilityValidationRegistry((result,)).effective_tool(tool)

    assert effective.validation_status("visual_resource_generation") == NOT_VALIDATED


def test_result_for_different_provider_cannot_promote_tool():
    tool = ToolCandidate(
        "canva",
        frozenset({"visual_resource_generation"}),
        capability_validation=(("visual_resource_generation", NOT_VALIDATED),),
    )
    result = CapabilityValidationResult(
        "notebooklm", "visual_resource_generation", VALIDATED
    )

    effective = CapabilityValidationRegistry((result,)).effective_tool(tool)

    assert effective.validation_status("visual_resource_generation") == NOT_VALIDATED
