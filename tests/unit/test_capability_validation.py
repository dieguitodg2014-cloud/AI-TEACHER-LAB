from core.orchestration.capability_validation import (
    NOT_VALIDATED,
    VALIDATED,
    validate_capability,
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
