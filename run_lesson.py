"""Command-line entry point for the configured AI TEACHER LAB runtime."""

from __future__ import annotations

import argparse
import json
from typing import Any

from core.context.request_interpreter import interpret_request
from core.workflow.configured_runtime import run_configured_lesson_planning
from core.workflow.teacher_interface import (
    render_teacher_result,
    teacher_result_to_dict,
    to_teacher_result,
)
from core.workflow.vertical_slice import result_to_dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run AI TEACHER LAB lesson planning with the configured runtime."
    )
    request_group = parser.add_mutually_exclusive_group(required=True)
    request_group.add_argument("--request", help="Natural-language lesson request.")
    request_group.add_argument("--objective", help="Observable learning objective for a structured request.")
    parser.add_argument("--level", help="Learner level, e.g. A0, A1, A2, B1, or B2")
    parser.add_argument("--audience", help="Learner audience")
    parser.add_argument("--duration", type=int, default=90, help="Lesson duration in minutes")
    parser.add_argument("--topic", default="", help="Lesson topic")
    parser.add_argument("--group-size", type=int, default=None, help="Number of learners")
    parser.add_argument(
        "--format",
        choices=("teacher-text", "teacher", "internal"),
        default="teacher-text",
        help="Output contract. 'teacher-text' is the classroom-readable default; 'teacher' returns the stable teacher JSON contract; 'internal' preserves the orchestration view.",
    )
    return parser


def build_request(args: argparse.Namespace) -> dict[str, Any] | str:
    if args.request:
        return interpret_request(args.request)

    if not args.level or not args.audience:
        raise ValueError("--level and --audience are required when using --objective")

    request: dict[str, Any] = {
        "level": args.level,
        "audience": args.audience,
        "duration_minutes": args.duration,
        "objective": args.objective,
    }
    if args.topic:
        request["topic"] = args.topic
    if args.group_size is not None:
        request["group_size"] = args.group_size
    return request


def main() -> int:
    args = build_parser().parse_args()
    result = run_configured_lesson_planning(build_request(args))
    teacher_result = to_teacher_result(result)

    if args.format == "teacher-text":
        print(render_teacher_result(teacher_result))
    elif args.format == "teacher":
        print(json.dumps(teacher_result_to_dict(teacher_result), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))

    # Resource workflows succeed only after final acceptance. Lesson-only
    # workflows retain READY as their generation completion state because no
    # ResourceAcceptanceGate is involved.
    if result.resource_task is not None:
        return 0 if result.status == "ACCEPTED" else 1
    return 0 if result.status == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
