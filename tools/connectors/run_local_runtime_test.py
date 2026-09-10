"""Run the configured AI-TEACHER-LAB lesson flow against local LM Studio."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from core.workflow.configured_runtime import run_configured_lesson_planning

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN_CASE = REPO_ROOT / "tests" / "regression" / "golden_case_a2_present_perfect.json"
DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_MODEL = "google/gemma-3n-e4b"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=os.getenv("AI_TEACHER_LAB_PROVIDER_URL", DEFAULT_BASE_URL))
    parser.add_argument("--case", default=str(DEFAULT_GOLDEN_CASE))
    args = parser.parse_args()

    os.environ["AI_TEACHER_LAB_PROVIDER_MODEL"] = args.model
    os.environ["AI_TEACHER_LAB_PROVIDER_URL"] = args.base_url

    case_path = Path(args.case)
    if not case_path.is_absolute():
        case_path = REPO_ROOT / case_path
    if not case_path.exists():
        print(f"GOLDEN_CASE_NOT_FOUND: {case_path}", file=sys.stderr)
        return 2

    case = json.loads(case_path.read_text(encoding="utf-8"))
    request = case.get("request")
    if not isinstance(request, dict):
        print("INVALID_GOLDEN_CASE:request", file=sys.stderr)
        return 2

    result = run_configured_lesson_planning(request)

    output = {
        "status": result.status,
        "model": args.model,
        "base_url": args.base_url,
        "missing": result.missing,
        "errors": result.errors,
        "context": result.context.__dict__ if result.context else None,
        "level_decision": result.level_decision.__dict__ if result.level_decision else None,
        "learning_plan": result.learning_plan.__dict__ if result.learning_plan else None,
        "generation": result.generation,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))

    return 0 if result.status == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
