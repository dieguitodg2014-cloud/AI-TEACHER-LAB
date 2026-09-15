import pytest

from core.foundation.models import Level, TaskPacket
from core.resources.approved_content import ApprovedResourceContent
from core.resources.content_generation import (
    approve_resource_content,
    bind_approved_resource_content,
    validate_resource_content,
)


def _task():
    return TaskPacket(
        task_id="task-1",
        task_type="RESOURCE_PRODUCTION",
        objective="Identify key details in a short conversation.",
        level=Level.A2,
        required_output="audio",
        constraints=(),
        quality_criteria=("Support the objective.",),
    )


def test_bind_approved_resource_content_requires_explicit_resource_content():
    approved = bind_approved_resource_content(
        {"resource_content": "A: What time do you start? B: At eight."},
        expected_type="script",
    )

    assert approved == ApprovedResourceContent(
        "A: What time do you start? B: At eight.",
        "script",
    )


def test_bind_approved_resource_content_rejects_missing_content():
    with pytest.raises(ValueError, match="RESOURCE_CONTENT_REQUIRED"):
        bind_approved_resource_content({}, expected_type="script")


def test_bind_approved_resource_content_does_not_accept_non_object():
    with pytest.raises(TypeError, match="RESOURCE_CONTENT_OUTPUT_NOT_OBJECT"):
        bind_approved_resource_content([], expected_type="script")


def test_validate_resource_content_accepts_matching_identity():
    result = validate_resource_content(
        _task(),
        {
            "resource_content": "A: Have you ever traveled? B: Yes, I have.",
            "resource_content_type": "script",
            "level": "A2",
            "objective": "Identify key details in a short conversation.",
        },
        expected_type="script",
    )

    assert result.status == "READY"
    assert result.errors == ()


def test_approve_resource_content_rejects_mismatched_type_or_level():
    generated = {
        "resource_content": "A short dialogue.",
        "resource_content_type": "worksheet",
        "level": "A1",
    }

    result = validate_resource_content(_task(), generated, expected_type="script")
    assert result.status == "REJECT"
    assert "RESOURCE_CONTENT_TYPE_MISMATCH" in result.errors
    assert "RESOURCE_CONTENT_LEVEL_MISMATCH" in result.errors

    with pytest.raises(ValueError, match="RESOURCE_CONTENT_NOT_APPROVED"):
        approve_resource_content(generated, expected_type="script", task=_task())
