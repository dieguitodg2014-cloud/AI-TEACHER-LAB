from core.orchestration.capability_validation import (
    NOT_VALIDATED,
    VALIDATED,
    apply_validation_result,
    validate_capability,
)
from core.orchestration.tool_selector import ToolCandidate


def test_validation_result_updates_candidate_without_mutating_original():
    tool = ToolCandidate(
        "notebooklm",
        frozenset({"presentation_generation", "visual_resource_generation"}),
        capability_validation=(("visual_resource_generation", NOT_VALIDATED),),
    )
    result = validate_capability(
        tool,
        "visual_resource_generation",
        passed=True,
        evidence=["visual-presentation-smoke-test-v1"],
    )

    validated = apply_validation_result(tool, result)

    assert result.status == VALIDATED
    assert tool.validation_status("visual_resource_generation") == NOT_VALIDATED
    assert validated.validation_status("visual_resource_generation") == VALIDATED
    assert validated.tool_id == tool.tool_id
    assert validated.capabilities == tool.capabilities


def test_validation_result_rejects_different_provider():
    tool = ToolCandidate("notebooklm", frozenset({"visual_resource_generation"}))
    result = validate_capability(
        tool,
        "visual_resource_generation",
        passed=True,
        evidence=["smoke-test"],
    )
    other = ToolCandidate("canva", frozenset({"visual_resource_generation"}))

    try:
        apply_validation_result(other, result)
    except ValueError as exc:
        assert str(exc) == "CAPABILITY_VALIDATION_TOOL_MISMATCH"
    else:
        raise AssertionError("Expected provider mismatch to be rejected")
