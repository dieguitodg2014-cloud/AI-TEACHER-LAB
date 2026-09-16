"""Context normalization for the MVP request-to-decision flow.

The engine deliberately does not make pedagogical decisions. It extracts and
normalizes information; missing information is reported instead of invented.
"""

from dataclasses import dataclass
from uuid import uuid4

from core.context.request_interpreter import interpret_request
from core.foundation.models import Context, Level
from core.foundation.validation import validate_context


@dataclass(frozen=True)
class ContextResult:
    context: Context | None
    missing: list[str]
    errors: list[str]


def build_context(request: dict) -> ContextResult:
    """Build a Context from a normalized request.

    Natural-language extraction is delegated to the request interpreter so
    every Context entry point uses the same conservative normalization rules.
    The engine never guesses pedagogical decisions.
    """
    request = interpret_request(request)
    level = request.get("level")
    duration = request.get("duration_minutes")
    group_size = request.get("group_size")
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
