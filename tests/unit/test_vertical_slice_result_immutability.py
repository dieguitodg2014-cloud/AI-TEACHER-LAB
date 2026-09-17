from dataclasses import asdict

import pytest

from core.workflow.vertical_slice import VerticalSliceResult


def _result(missing=None, errors=None):
    return VerticalSliceResult(
        status="FAILED",
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
        missing=missing if missing is not None else ["objective"],
        errors=errors if errors is not None else ["missing objective"],
    )


def test_result_collections_are_stored_as_tuples():
    result = _result()
    assert isinstance(result.missing, tuple)
    assert isinstance(result.errors, tuple)


def test_reassignment_is_rejected():
    result = _result()
    with pytest.raises(AttributeError):
        result.missing = ("duration",)
    with pytest.raises(AttributeError):
        result.errors = ("failure",)


def test_structural_collection_mutation_is_rejected():
    result = _result()
    with pytest.raises(AttributeError):
        result.missing.append("level")
    with pytest.raises(AttributeError):
        result.errors.append("failure")


def test_constructor_defensively_copies_mutable_inputs():
    missing = ["objective"]
    errors = ["missing objective"]
    result = _result(missing, errors)

    missing.append("duration")
    errors.append("other failure")

    assert result.missing == ("objective",)
    assert result.errors == ("missing objective",)


def test_asdict_preserves_immutable_collection_values():
    payload = asdict(_result())
    assert payload["missing"] == ("objective",)
    assert payload["errors"] == ("missing objective",)
