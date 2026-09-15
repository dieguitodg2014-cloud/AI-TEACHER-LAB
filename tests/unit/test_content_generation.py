import pytest

from core.resources.approved_content import ApprovedResourceContent
from core.resources.content_generation import bind_approved_resource_content


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
