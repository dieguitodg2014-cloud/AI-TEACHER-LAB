"""Command-line entry point for the configured AI TEACHER LAB runtime."""

from __future__ import annotations

import argparse
from typing import Any

from core.context.request_interpreter import interpret_request
from core.workflow.configured_runtime import run_configured_lesson_planning
from core.workflow.teacher_facing_output import (
    render_teacher_facing_result,
)


SUPPORTED_SKILLS = (
    "LISTENING",
    "SPEAKING",
    "READING",
    "WRITING",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run AI TEACHER LAB lesson planning with the configured runtime."
    )
    request_group = parser.add_mutually_exclusive_group(required=True)
    request_group.add_argument(
        "--request",
        help="Natural-language lesson request.",
    )
    request_group.add_argument(
        "--objective",
        help="Observable learning objective for a structured request.",
    )
    parser.add_argument(
        "--level",
        help="Learner level, e.g. A0, A1, A2, B1, or B2",
    )
    parser.add_argument(
        "--audience",
        help="Learner audience",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=90,
        help="Lesson duration in minutes",
    )
    parser.add_argument(
        "--topic",
        default="",
        help="Lesson topic",
    )
    parser.add_argument(
        "--skill",
        type=str.upper,
        choices=SUPPORTED_SKILLS,
        help="Primary lesson skill.",
    )
    parser.add_argument(
        "--group-size",
        type=int,
        default=None,
        help="Number of learners",
    )
    return parser


def build_request(args: argparse.Namespace) -> dict[str, Any] | str:
    if args.request:
        return interpret_request(args.request)

    if not args.level or not args.audience:
        raise ValueError(
            "--level and --audience are required when using --objective"
        )

    request: dict[str, Any] = {
        "level": args.level,
        "audience": args.audience,
        "duration_minutes": args.duration,
        "objective": args.objective,
    }

    if args.topic:
        request["topic"] = args.topic

    if args.skill:
        request["primary_skill"] = args.skill

    if args.group_size is not None:
        request["group_size"] = args.group_size

    return request


def _teacher_facing_request(request: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(request, dict):
        normalized = dict(request)
    else:
        normalized = {"request": request}

    normalized["teacher_facing"] = True
    return normalized


def main() -> int:
    args = build_parser().parse_args()

    try:
        request = build_request(args)
        result = run_configured_lesson_planning(
            _teacher_facing_request(request)
        )
    except ValueError as exc:
        print(str(exc))
        return 1

    if result.status == "MISSING_CONTEXT":
        missing = ", ".join(result.missing)
        print(f"Missing required lesson information: {missing}.")
        return 1

    if result.status != "READY":
        print(f"Lesson workflow status: {result.status}.")
        if result.errors:
            for error in result.errors:
                print(f"- {error}")
        return 1

    try:
        print(render_teacher_facing_result(result))
    except ValueError as exc:
        print(str(exc))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())