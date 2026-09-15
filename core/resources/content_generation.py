"""Small contract for approved instructional resource content.

Content generation remains separate from media production: a content provider
may draft a resource script, but the result must be explicitly approved before
it can enter a TaskPacket as provider input.
"""

from __future__ import annotations

from typing import Any

from core.resources.approved_content import ApprovedResourceContent


def approve_resource_content(
    generated: dict[str, Any],
    *,
    expected_type: str,
) -> ApprovedResourceContent:
    """Turn an explicit generated content artifact into an approved contract.

    This function deliberately performs no pedagogical judgment. Approval is
    only valid after the caller has already run the applicable content/QC gate.
    """
    if not isinstance(generated, dict):
        raise TypeError("RESOURCE_CONTENT_OUTPUT_NOT_OBJECT")

    content = generated.get("resource_content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("RESOURCE_CONTENT_REQUIRED")

    content_type = generated.get("resource_content_type", expected_type or "script")
    return ApprovedResourceContent(content=content, content_type=content_type)
