from core.orchestration.capability_validation import (
    NOT_VALIDATED,
    VALIDATED,
    CapabilityValidationResult,
    validate_capability,
)
from core.orchestration.capability_validation_registry import CapabilityValidationRegistry
from core.orchestration.tool_selector import ToolCandidate


def test_record_replaces_previous_result_for_same_provider_capability():
    registry = CapabilityValidationRegistry()
    first = CapabilityValidationResult("notebooklm", "visual_resource_generation", NOT_VALIDATED)
    tool = ToolCandidate("notebooklm", frozenset({"visual_resource_generation"}))
    second = validate_capability(
        tool,
        "visual_resource_generation",
        passed=True,
        evidence=("visual-smoke-test",),
    )

    updated = registry.record(first).record(second)

    assert updated.get("notebooklm", "visual_resource_generation") == second
    assert len(updated.results) == 1


def test_effective_tool_promotes_current_validated_declared_capability():
    tool = ToolCandidate(
        "notebooklm",
        frozenset({"resource_generation", "visual_resource_generation"}),
        capability_validation=(("visual_resource_generation", NOT_VALIDATED),),
    )
    result = validate_capability(
        tool,
        "visual_resource_generation",
        passed=True,
        evidence=("visual-smoke-test",),
    )

    effective = CapabilityValidationRegistry((result,)).effective_tool(tool)

    assert effective is not tool
    assert effective.validation_status("visual_resource_generation") == VALIDATED
    assert tool.validation_status("visual_resource_generation") == NOT_VALIDATED


def test_effective_tool_preserves_provider_revision_for_fingerprint_integrity():
    tool = ToolCandidate(
        "notebooklm",
        frozenset({"visual_resource_generation"}),
        provider_revision="capability-contract-v1",
    )
    result = validate_capability(
        tool,
        "visual_resource_generation",
        passed=True,
        evidence=("visual-smoke-test",),
    )

    effective = CapabilityValidationRegistry((result,)).effective_tool(tool)

    assert effective.provider_revision == "capability-contract-v1"
    assert effective.validation_status("visual_resource_generation") == VALIDATED


def test_stale_validation_does_not_promote_changed_provider_configuration():
    original_tool = ToolCandidate(
        "notebooklm",
        frozenset({"resource_generation", "visual_resource_generation"}),
    )
    result = validate_capability(
        original_tool,
        "visual_resource_generation",
        passed=True,
        evidence=("visual-smoke-test",),
    )
    changed_tool = ToolCandidate(
        "notebooklm",
        frozenset({"resource_generation", "visual_resource_generation", "audio_generation"}),
        capability_validation=(("visual_resource_generation", NOT_VALIDATED),),
    )

    effective = CapabilityValidationRegistry((result,)).effective_tool(changed_tool)

    assert effective.validation_status("visual_resource_generation") == NOT_VALIDATED


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
        "notebooklm", "visual_resource_generation", VALIDATED, ("notebooklm-test",), "different-fingerprint"
    )

    effective = CapabilityValidationRegistry((result,)).effective_tool(tool)

    assert effective.validation_status("visual_resource_generation") == NOT_VALIDATED
    assert effective.tool_id == "canva"
    assert effective.capability_validation == (("visual_resource_generation", NOT_VALIDATED),)
