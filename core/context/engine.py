"""Context normalization for the MVP request-to-decision flow.

The engine deliberately does not make pedagogical decisions. It extracts and
normalizes information; missing information is reported instead of invented.
"""

from dataclasses import dataclass
import re
from uuid import uuid4

from core.context.request_interpreter import interpret_request
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
    match = re.search(r"\b(\d+)\s+(?:(?:adult|ESL)\s+)*(?:students?|learners?|people)\b", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def build_context(request: dict) -> ContextResult:
    """Build a Context from normalized request fields.

    The request interpreter is the single natural-language extraction
    boundary. Direct callers may still provide structured fields, while raw
    ``request`` text is normalized here for compatibility with the public
    context-building API.
    """
    normalized = interpret_request(request)
    text = str(normalized.get("request", ""))
    level = normalized.get("level") or _find_level(text)
    duration = normalized.get("duration_minutes") or _find_duration(text)
    group_size = normalized.get("group_size") or _find_group_size(text)
    audience = str(normalized.get("audience", "")).strip()
    objective = str(normalized.get("objective", "")).strip()
    topic = str(normalized.get("topic", "")).strip() or None

    missing: list[str] = []
    if not level:
        missing.append("level")
    if not audience:
        missing.append("audience")
    if not duration:
        missing.append("duration_minutes")
    if not objective:
        missing.append("objective")
    if not normalized.get("constraints"):
        constraints = []
    else:
        constraints = [str(item) for item in normalized["constraints"]]

    if missing:
        return ContextResult(context=None, missing=missing, errors=[])

    context = Context(
        context_id=str(normalized.get("context_id") or f"ctx-{uuid4().hex[:10]}"),
        level=level,
        audience=audience,
        duration_minutes=int(duration),
        objective=objective,
        constraints=constraints,
        group_size=group_size,
        topic=topic,
        prior_knowledge=[str(x) for x in normalized.get("prior_knowledge", [])],
        technology=[str(x) for x in normalized.get("technology", [])],
        teacher_preferences=dict(normalized.get("teacher_preferences", {})),
    )
    return ContextResult(context=context, missing=[], errors=validate_context(context))
