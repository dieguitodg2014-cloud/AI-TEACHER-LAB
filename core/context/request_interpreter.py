"""Conservative normalization of natural-language lesson requests.

The interpreter extracts only information that can be identified with high
confidence. It never invents pedagogical decisions or fills missing fields
with assumptions.
"""

from __future__ import annotations

import re
from typing import Any


_LEVEL_PATTERN = re.compile(r"\b(A0|A1|A2|B1|B2)\b", re.IGNORECASE)
_DURATION_MINUTES = re.compile(r"\b(\d+)\s*(?:minutes?|mins?)\b", re.IGNORECASE)
_DURATION_HOURS = re.compile(r"\b(\d+(?:\.5)?)\s*(?:hours?|hrs?)\b", re.IGNORECASE)
_GROUP_SIZE = re.compile(r"\b(\d+)\s+(?:students?|learners?|people)\b", re.IGNORECASE)
_OBJECTIVE = re.compile(r"\b(?:objective|goal|aim)\s*:\s*(.+?)(?=\s+(?:topic|level|audience|duration|constraints?)\s*:|$)", re.IGNORECASE)
_TOPIC = re.compile(r"\btopic\s*:\s*(.+?)(?=\s+(?:objective|goal|aim|level|audience|duration|constraints?)\s*:|$)", re.IGNORECASE)
_AUDIENCE = re.compile(r"\baudience\s*:\s*(.+?)(?=\s+(?:objective|goal|aim|topic|level|duration|constraints?)\s*:|$)", re.IGNORECASE)
_CONSTRAINTS = re.compile(r"\bconstraints?\s*:\s*(.+)$", re.IGNORECASE)


def _clean(value: str) -> str:
    return " ".join(value.strip().split())


def _find_duration(text: str) -> int | None:
    match = _DURATION_MINUTES.search(text)
    if match:
        return int(match.group(1))
    match = _DURATION_HOURS.search(text)
    if match:
        return int(float(match.group(1)) * 60)
    return None


def interpret_request(request: str | dict[str, Any]) -> dict[str, Any]:
    """Return a conservative structured request.

    Structured request fields are preserved. Natural-language extraction is
    limited to explicit or unambiguous patterns. Missing information remains
    absent so the Context Engine can report it instead of guessing.
    """
    if isinstance(request, dict):
        normalized = dict(request)
        text = str(normalized.get("request", "")).strip()
        if not text:
            return normalized
    else:
        normalized = {}
        text = str(request).strip()

    if not text:
        return normalized

    level = _LEVEL_PATTERN.search(text)
    if "level" not in normalized and level:
        normalized["level"] = level.group(1).upper()

    if "duration_minutes" not in normalized:
        duration = _find_duration(text)
        if duration is not None:
            normalized["duration_minutes"] = duration

    if "group_size" not in normalized:
        group = _GROUP_SIZE.search(text)
        if group:
            normalized["group_size"] = int(group.group(1))

    for field, pattern in (
        ("objective", _OBJECTIVE),
        ("topic", _TOPIC),
        ("audience", _AUDIENCE),
    ):
        if not normalized.get(field):
            match = pattern.search(text)
            if match:
                normalized[field] = _clean(match.group(1))

    if not normalized.get("constraints"):
        match = _CONSTRAINTS.search(text)
        if match:
            normalized["constraints"] = [
                _clean(item) for item in re.split(r"\s*;\s*", match.group(1)) if _clean(item)
            ]

    return normalized
