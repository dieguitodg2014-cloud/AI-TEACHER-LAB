import pytest

from core.context.engine import build_context
from core.foundation.validation import validate_context


def _request(primary_skill):
    return {
        "level": "A2",
        "audience": "adult ESL learners",
        "duration_minutes": 90,
        "objective": "Students will communicate using the target language.",
        "primary_skill": primary_skill,
    }


@pytest.mark.parametrize(
    "skill",
    ["LISTENING", "SPEAKING", "READING", "WRITING", "MIXED"],
)
def test_context_preserves_explicit_primary_skill(skill):
    result = build_context(_request(skill))

    assert result.context is not None
    assert result.context.primary_skill == skill
    assert result.errors == []


def test_context_rejects_unsupported_primary_skill():
    result = build_context(_request("GRAMMAR"))

    assert result.context is not None
    assert "Unsupported primary skill" in result.errors
    assert validate_context(result.context) == ["Unsupported primary skill"]
