import json
from pathlib import Path

from core.workflow.vertical_slice import run_lesson_planning


REGRESSION_DIR = Path(__file__).resolve().parents[1] / "regression"


def test_cefr_golden_cases_preserve_pedagogical_invariants():
    cases = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(REGRESSION_DIR.glob("golden_case_*.json"))
        if path.name != "golden_case_a2_present_perfect.json"
    ]

    assert {case["request"]["level"] for case in cases} >= {"A0", "A1", "B1"}

    for case in cases:
        result = run_lesson_planning(case["request"])
        invariants = case["expected_invariants"]

        assert result.status == "PLANNED", case["case_id"]
        assert result.context is not None
        assert result.learning_plan is not None
        assert result.context.level == invariants["level"]
        assert result.context.duration_minutes == invariants["duration_minutes"]
        assert result.context.objective == invariants["objective"]
        assert len(result.learning_plan.sequence) == len(invariants["required_learning_plan_stages"])
        assert result.learning_plan.total_minutes == invariants["duration_minutes"]
        assert result.learning_plan.evidence_of_learning
        assert result.learning_plan.resource_need in {
            "CREATE", "REUSE", "ADAPT", "OMIT", "NO_RESOURCE_REQUIRED"
        }
