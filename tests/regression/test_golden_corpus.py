import json
from pathlib import Path


REGRESSION_DIR = Path(__file__).resolve().parent


def test_golden_corpus_has_at_least_one_case():
    cases = sorted(REGRESSION_DIR.glob("golden_case_*.json"))
    assert cases, "Regression corpus must contain at least one golden case."


def test_each_golden_case_has_executable_invariants():
    required_case_keys = {"case_id", "name", "request", "expected_invariants", "success_criteria"}
    required_request_keys = {"level", "duration_minutes", "objective"}
    required_invariant_keys = {
        "level",
        "duration_minutes",
        "objective",
        "required_learning_plan_stages",
        "resource_decision_must_be_explicit",
        "tool_selection_must_be_capability_based",
        "qc_must_be_run_before_final_approval",
    }

    for path in sorted(REGRESSION_DIR.glob("golden_case_*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))

        assert required_case_keys <= case.keys(), path.name
        assert required_request_keys <= case["request"].keys(), path.name
        assert required_invariant_keys <= case["expected_invariants"].keys(), path.name
        assert case["success_criteria"], path.name
        assert case["expected_invariants"]["level"] == case["request"]["level"], path.name
        assert case["expected_invariants"]["duration_minutes"] == case["request"]["duration_minutes"], path.name
        assert case["expected_invariants"]["objective"] == case["request"]["objective"], path.name
        assert case["expected_invariants"]["required_learning_plan_stages"], path.name
