"""Teacher-facing product boundary for accepted lesson results."""

from __future__ import annotations

from typing import Any, Callable

from core.workflow.configured_runtime import run_configured_lesson_planning
from core.workflow.teacher_lesson_card import TeacherLessonCard, teacher_lesson_card_from_result
from core.workflow.teacher_lesson_card_renderer import render_teacher_lesson_card
from core.workflow.vertical_slice import VerticalSliceResult


class TeacherFacingOutputError(ValueError):
    """Raised when a workflow result cannot become teacher-facing output."""


def build_teacher_lesson_card(result: VerticalSliceResult) -> TeacherLessonCard:
    """Convert only an accepted workflow result into the teacher-facing contract."""
    if result.status != "READY":
        raise TeacherFacingOutputError(
            f"Teacher-facing output requires READY result; got {result.status}"
        )
    return teacher_lesson_card_from_result(result)


def run_teacher_facing_lesson(
    request: dict[str, Any],
    *,
    planner: Callable[[dict[str, Any]], VerticalSliceResult] = run_configured_lesson_planning,
) -> str:
    """Run the configured lesson workflow and render its accepted teacher card.

    The adapter does not make pedagogical, provider, QC, or acceptance
    decisions. It only consumes the result produced by the existing runtime.
    """
    result = planner(request)
    card = build_teacher_lesson_card(result)
    return render_teacher_lesson_card(card)
