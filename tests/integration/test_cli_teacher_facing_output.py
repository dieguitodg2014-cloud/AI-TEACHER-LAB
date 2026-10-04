from __future__ import annotations

from unittest.mock import patch

import run_lesson
from core.workflow.vertical_slice import VerticalSliceResult


def _result(
    *,
    status: str,
    missing: tuple[str, ...] = (),
    errors: tuple[str, ...] = (),
):
    return VerticalSliceResult(
        status=status,
        context=None,
        level_decision=None,
        learning_plan=None,
        assessment_decision=None,
        resource_decision=None,
        resource_task=None,
        resource_tool=None,
        resource_handoff=None,
        resource_validation=None,
        generation=None,
        missing=missing,
        errors=errors,
    )


def test_cli_renders_ready_teacher_facing_output(capsys):
    result = _result(status="READY")

    with patch.object(
        run_lesson,
        "run_configured_lesson_planning",
        return_value=result,
    ) as planner:
        with patch.object(
            run_lesson,
            "render_teacher_facing_result",
            return_value="<html>teacher card</html>",
        ) as renderer:
            with patch.object(run_lesson, "build_request") as builder:
                builder.return_value = {"objective": "Talk about routines"}
                with patch.object(run_lesson, "build_parser") as parser_builder:
                    parser_builder.return_value.parse_args.return_value = object()

                    assert run_lesson.main() == 0

    planner.assert_called_once_with(
        {
            "objective": "Talk about routines",
            "teacher_facing": True,
        }
    )
    renderer.assert_called_once_with(result)
    assert capsys.readouterr().out.strip() == "<html>teacher card</html>"


def test_cli_reports_missing_context(capsys):
    result = _result(
        status="MISSING_CONTEXT",
        missing=("objective",),
    )

    with patch.object(
        run_lesson,
        "run_configured_lesson_planning",
        return_value=result,
    ):
        with patch.object(run_lesson, "build_request") as builder:
            builder.return_value = {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 90,
            }
            with patch.object(run_lesson, "build_parser") as parser_builder:
                parser_builder.return_value.parse_args.return_value = object()

                assert run_lesson.main() == 1

    assert (
        capsys.readouterr().out.strip()
        == "Missing required lesson information: objective."
    )


def test_cli_reports_non_ready_workflow_status(capsys):
    result = _result(
        status="HUMAN_HANDOFF",
        errors=("GENERATOR_UNAVAILABLE",),
    )

    with patch.object(
        run_lesson,
        "run_configured_lesson_planning",
        return_value=result,
    ):
        with patch.object(run_lesson, "build_request") as builder:
            builder.return_value = {"objective": "Talk about routines"}
            with patch.object(run_lesson, "build_parser") as parser_builder:
                parser_builder.return_value.parse_args.return_value = object()

                assert run_lesson.main() == 1

    assert capsys.readouterr().out.strip() == (
        "Lesson workflow status: HUMAN_HANDOFF.\n"
        "- GENERATOR_UNAVAILABLE"
    )