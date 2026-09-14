import pytest

from core.orchestration.capability_validation import (
    NOT_VALIDATED,
    VALIDATED,
    apply_validation_result,
    capability_fingerprint,
    validate_capability,
    CapabilityValidationResult,
)
from core.orchestration.tool_selector import ToolCandidate


def test_passed_validation_returns_validated_with_evidence():
    tool = ToolCandidate("notebooklm", frozenset({"visual_resource_generation"}))
    result = validate_capability(
        tool,
        "visual_resource_generation",
        passed=True,
        evidence=["visual-presentation-smoke-test"],
    )
    assert result.status == VALIDATED
    assert result.passed is True
    assert result.evidence == ("visual-presentation-smoke-test",)
    assert result.tool_fingerprint == capability_fingerprint(tool)


def test_passed_validation_without_evidence_remains_not_validated():
    tool = ToolCandidate("notebooklm", frozenset({"visual_resource_generation"}))
    result = validate_capability(
        tool,
        "visual_resource_generation",
        passed=True,
    )
    assert result.status == NOT_VALIDATED
    assert result.passed is False
    assert result.evidence == ()


def test_failed_validation_remains_not_validated():
    tool = ToolCandidate("notebooklm", frozenset({"visual_resource_generation"}))
    result = validate_capability(
        tool,
        "visual_resource_generation",
        passed=False,
        evidence=["visual-presentation-smoke-test-failed"],
    )
    assert result.status == NOT_VALIDATED
    assert result.passed is False


def test_undeclared_capability_cannot_be_validated():
    tool = ToolCandidate("notebooklm", frozenset({"resource_generation"}))
    result = validate_capability(
        tool,
        "visual_resource_generation",
        passed=True,
        evidence=["claimed-but-undeclared"],
    )
    assert result.status == NOT_VALIDATED
    assert result.passed is False


def test_validated_result_without_evidence_is_rejected_at_construction():
    with pytest.raises(ValueError, match="VALIDATED_CAPABILITY_REQUIRES_EVIDENCE"):
        CapabilityValidationResult(
            tool_id="notebooklm",
            capability="visual_resource_generation",
            status=VALIDATED,
            tool_fingerprint="fingerprint",
        )


def test_validated_result_without_fingerprint_is_rejected_at_construction():
    with pytest.raises(ValueError, match="VALIDATED_CAPABILITY_REQUIRES_FINGERPRINT"):
        CapabilityValidationResult(
            tool_id="notebooklm",
            capability="visual_resource_generation",
            status=VALIDATED,
            evidence=("visual-presentation-smoke-test",),
        )


def test_unknown_validation_status_is_rejected_at_construction():
    with pytest.raises(ValueError, match="INVALID_CAPABILITY_VALIDATION_STATUS"):
        CapabilityValidationResult(
            tool_id="notebooklm",
            capability="visual_resource_generation",
            status="unknown",
        )


def test_stale_validated_result_is_rejected_when_applied():
    original_tool = ToolCandidate(
        "notebooklm",
        frozenset({"visual_resource_generation"}),
    )
    changed_tool = ToolCandidate(
        "notebooklm",
        frozenset({"visual_resource_generation", "audio_generation"}),
    )
    result = validate_capability(
        original_tool,
        "visual_resource_generation",
        passed=True,
        evidence=["visual-presentation-smoke-test"],
    )

    with pytest.raises(ValueError, match="STALE_CAPABILITY_VALIDATION"):
        apply_validation_result(changed_tool, result)
