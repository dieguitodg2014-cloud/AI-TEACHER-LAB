"""Context normalization for the MVP request-to-decision flow.

The engine deliberately does not make pedagogical decisions. It extracts and
normalizes information; missing information is reported instead of invented.
"""

from dataclasses import dataclass
import re
from uuid import uuid4

from core.foundation.models import Context, Level
from core.foundation.validation import validate_context


@dataclass(frozen=True)
class ContextResult:
    context: Context | None
    missing: list[str]
    errors: list[str]


def _find_level(text: str) -> Level | None:
    match = re.search(r"\b(A0|A1|A2|B1|B2)\b", text, re.IGNORECASE)
    return match.group(1).upper() if match else None  # type: ignore[return-value]


def _find_duration(text: str) -> int | None:
    patterns = [
        r"(\d+)\s*(?:minutes?|mins?)\b",
        r"(\d+(?:\.5)?)\s*(?:hours?|hrs?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return int(value * 60)
    return None


def _find_group_size(text: str) -> int | None:
    match = re.search(r"\b(\d+)\s+(?:students?|learners?|people)\b", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def build_context(request: dict) -> ContextResult:
    """Build a Context from normalized request fields.

    Required fields can be supplied directly. A natural-language ``request``
    field receives conservative extraction for level, duration, and group size.
    The function never guesses an objective or audience.
    """
    text = str(request.get("request", ""))
    level = request.get("level") or _find_level(text)
    duration = request.get("duration_minutes") or _find_duration(text)
    group_size = request.get("group_size") or _find_group_size(text)
    audience = str(request.get("audience", "")).strip()
    objective = str(request.get("objective", "")).strip()
    topic = str(request.get("topic", "")).strip() or None

    missing: list[str] = []
    if not level:
        missing.append("level")
    if not audience:
        missing.append("audience")
    if not duration:
        missing.append("duration_minutes")
    if not objective:
        missing.append("objective")
    if not request.get("constraints"):
        constraints = []
    else:
        constraints = [str(item) for item in request["constraints"]]

    if missing:
        return ContextResult(context=None, missing=missing, errors=[])

    context = Context(
        context_id=str(request.get("context_id") or f"ctx-{uuid4().hex[:10]}"),
        level=level,
        audience=audience,
        duration_minutes=int(duration),
        objective=objective,
        constraints=constraints,
        group_size=group_size,
        topic=topic,
        prior_knowledge=[str(x) for x in request.get("prior_knowledge", [])],
        technology=[str(x) for x in request.get("technology", [])],
        teacher_preferences=dict(request.get("teacher_preferences", {})),
    )
    return ContextResult(context=context, missing=[], errors=validate_context(context))
