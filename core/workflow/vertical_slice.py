"""First end-to-end executable workflow for lesson planning."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.context.engine import build_context
from core.foundation.models import Context, LearningPlanDecision, LevelDecision
from core.pedagogy.decision_engine import decide_learning_plan
from core.progression.level_control import decide_level


@dataclass(frozen=True)
class VerticalSliceResult:
    status: str
    context: Context | None
    level_decision: LevelDecision | None
    learning_plan: LearningPlanDecision | None
    missing: list[str]
    errors: list[str]


def run_lesson_planning(request: dict[str, Any]) -> VerticalSliceResult:
    """Run request -> context -> level -> pedagogy without generating materials."""
    context_result = build_context(request)

    if context_result.errors or context_result.missing or context_result.context is None:
        return VerticalSliceResult(
            status="MISSING_CONTEXT" if context_result.missing else "FAILED",
            context=context_result.context,
            level_decision=None,
            learning_plan=None,
            missing=context_result.missing,
            errors=context_result.errors,
        )

    try:
        level_decision = decide_level(context_result.context)
        learning_plan = decide_learning_plan(context_result.context, level_decision)
    except (ValueError, OSError, KeyError) as exc:
        return VerticalSliceResult(
            status="FAILED",
            context=context_result.context,
            level_decision=None,
            learning_plan=None,
            missing=[],
            errors=[str(exc)],
        )

    return VerticalSliceResult(
        status="PLANNED",
        context=context_result.context,
        level_decision=level_decision,
        learning_plan=learning_plan,
        missing=[],
        errors=[],
    )


def result_to_dict(result: VerticalSliceResult) -> dict[str, Any]:
    """Serialize the workflow result for an API, CLI, or future orchestrator."""
    return asdict(result)
