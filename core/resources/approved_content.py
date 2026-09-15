"""Explicit contract for content approved before resource production."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApprovedResourceContent:
    """Content artifact authorized for downstream resource production.

    Providers such as TTS may transform this content into another medium, but
    they must not author or expand the instructional content themselves.
    """

    content: str
    content_type: str = "script"

    def __post_init__(self) -> None:
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("APPROVED_RESOURCE_CONTENT_REQUIRED")
        if not isinstance(self.content_type, str) or not self.content_type.strip():
            raise ValueError("APPROVED_RESOURCE_CONTENT_TYPE_REQUIRED")


def approved_input_materials(
    content: ApprovedResourceContent | None,
) -> tuple[str, ...]:
    """Return immutable TaskPacket input materials from approved content only."""
    if content is None:
        return ()
    return (content.content,)
