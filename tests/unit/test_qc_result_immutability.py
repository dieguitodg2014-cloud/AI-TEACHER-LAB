from dataclasses import asdict

import pytest

from core.foundation.models import QCChecks, QCResult


def _result(**overrides) -> QCResult:
    values = {
        "qc_id": "qc-immutability",
        "status": "READY",
        "score": 100.0,
        "critical_failure": False,
        "checks": QCChecks(
            level_alignment=True,
            objective_alignment=True,
            communicative_value=True,
            time_realism=True,
            linguistic_accuracy=True,
            assessment_alignment=True,
        ),
        "feedback": ["All checks passed."],
        "blocking_errors": [],
    }
    values.update(overrides)
    return QCResult(**values)


def test_qc_collections_are_stored_as_tuples():
    result = _result()

    assert isinstance(result.feedback, tuple)
    assert isinstance(result.blocking_errors, tuple)
    assert result.feedback == ("All checks passed.",)
    assert result.blocking_errors == ()


def test_feedback_and_blocking_errors_reassignment_is_rejected():
    result = _result()

    with pytest.raises(AttributeError):
        result.feedback = ("different",)
    with pytest.raises(AttributeError):
        result.blocking_errors = ("different",)


def test_qc_collections_structural_mutation_is_rejected():
    result = _result()

    with pytest.raises(AttributeError):
        result.feedback.append("another")
    with pytest.raises(TypeError):
        result.feedback[0] = "different"


def test_constructor_defensively_copies_mutable_qc_inputs():
    feedback = ["feedback"]
    blocking_errors = ["error"]
    result = _result(feedback=feedback, blocking_errors=blocking_errors)

    feedback.append("later feedback")
    blocking_errors.append("later error")

    assert result.feedback == ("feedback",)
    assert result.blocking_errors == ("error",)


def test_asdict_preserves_read_compatibility():
    result = _result(blocking_errors=["error"])
    payload = asdict(result)

    assert isinstance(payload["feedback"], tuple)
    assert isinstance(payload["blocking_errors"], tuple)
    assert payload["feedback"] == result.feedback
    assert payload["blocking_errors"] == result.blocking_errors
