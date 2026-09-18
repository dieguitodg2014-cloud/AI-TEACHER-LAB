from dataclasses import FrozenInstanceError

import pytest

from core.foundation.models import FrozenMapping
from core.workflow.vertical_slice import VerticalSliceResult, result_to_dict


def _result() -> VerticalSliceResult:
    return VerticalSliceResult(
        status="FAILED",
        context=None,
        level_decision=None,
        learning_plan=None,
        assessment_decision=None,
        resource_decision=None,
        resource_task=None,
        resource_tool=None,
        resource_handoff={"nested": {"items": ["x"]}},
        resource_validation=None,
        generation={"errors": ["boom"], "nested": {"items": ["y"]}},
        missing=["context"],
        errors=["boom"],
    )


def test_vertical_slice_result_is_deeply_immutable():
    result = _result()

    assert isinstance(result.resource_handoff, FrozenMapping)
    assert isinstance(result.generation, FrozenMapping)
    assert result.missing == ("context",)
    assert result.errors == ("boom",)

    with pytest.raises(TypeError):
        result.resource_handoff["nested"]["items"] += ("unexpected",)
    with pytest.raises(TypeError):
        result.generation["nested"]["items"] += ("unexpected",)
    with pytest.raises(FrozenInstanceError):
        result.errors = ("changed",)


def test_result_to_dict_materializes_immutable_containers():
    payload = result_to_dict(_result())

    assert isinstance(payload["resource_handoff"], dict)
    assert isinstance(payload["resource_handoff"]["nested"]["items"], list)
    assert isinstance(payload["generation"], dict)
    assert isinstance(payload["generation"]["nested"]["items"], list)
    assert payload["missing"] == ["context"]
    assert payload["errors"] == ["boom"]
