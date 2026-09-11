"""Command-line entry point for the configured AI TEACHER LAB runtime."""

from __future__ import annotations

import argparse
import json
from typing import Any

from core.workflow.configured_runtime import run_configured_lesson_planning
from core.workflow.vertical_slice import result_to_dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run AI TEACHER LAB lesson planning with the configured runtime."
    )
    parser.add_argument("--level", required=True, help="Learner level, e.g. A0, A1, A2, B1, or B2")
    parser.add_argument("--audience", required=True, help="Learner audience")
    parser.add_argument("--duration", type=int, default=90, help="Lesson duration in minutes")
    parser.add_argument("--objective", required=True, help="Observable learning objective")
    parser.add_argument("--topic", default="", help="Lesson topic")
    parser.add_argument("--group-size", type=int, default=None, help="Number of learners")
    return parser


def build_request(args: argparse.Namespace) -> dict[str, Any]:
    request: dict[str, Any] = {
        "level": args.level,
        "audience": args.audience,
        "duration": args.duration,
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
    print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))
    return 0 if result.status == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
