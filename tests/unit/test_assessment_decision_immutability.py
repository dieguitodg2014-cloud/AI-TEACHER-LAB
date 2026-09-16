from dataclasses import asdict

import pytest

from core.foundation.models import AssessmentDecision


def _decision(**overrides) -> AssessmentDecision:
    values = {
        "assessment_id": "assessment-immutability",
        "type": "PERFORMANCE",
        "target": "Demonstrate the lesson objective.",
        "evidence": "Observable learner performance.",
        "success_criteria": [
            "Completes the communicative task.",
            "Uses the taught language.",
        ],
    }
    values.update(overrides)
    return AssessmentDecision(**values)


def test_success_criteria_is_stored_as_tuple():
    decision = _decision()

    assert isinstance(decision.success_criteria, tuple)
    assert decision.success_criteria == (
        "Completes the communicative task.",
        "Uses the taught language.",
    )


def test_success_criteria_reassignment_is_rejected():
    decision = _decision()

    with pytest.raises(AttributeError):
        decision.success_criteria = ("Different criterion.",)


def test_success_criteria_structural_mutation_is_rejected():
    decision = _decision()

    with pytest.raises(AttributeError):
        decision.success_criteria.append("Another criterion.")
    with pytest.raises(TypeError):
        decision.success_criteria[0] = "Different criterion."


def test_constructor_defensively_copies_mutable_success_criteria_input():
    criteria = ["Completes the communicative task."]
    decision = _decision(success_criteria=criteria)

    criteria.append("Another criterion.")

    assert len(decision.success_criteria) == 1
    assert decision.success_criteria[0] == "Completes the communicative task."


def test_asdict_preserves_read_compatibility():
    decision = _decision()
    payload = asdict(decision)

    assert isinstance(payload["success_criteria"], tuple)
    assert payload["success_criteria"] == decision.success_criteria
