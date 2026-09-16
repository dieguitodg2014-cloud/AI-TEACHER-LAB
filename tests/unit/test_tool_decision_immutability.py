from dataclasses import asdict

import pytest

from core.foundation.models import ToolDecision


def _decision(**overrides) -> ToolDecision:
    values = {
        "decision_id": "tool-decision-immutability",
        "task_type": "LESSON_GENERATION",
        "selected_tool": "test-generator",
        "fallback_policy": [
            "try-secondary-generator",
            "human-handoff",
        ],
        "human_handoff_allowed": True,
        "reason": "Selected by capability match.",
    }
    values.update(overrides)
    return ToolDecision(**values)


def test_fallback_policy_is_stored_as_tuple():
    decision = _decision()

    assert isinstance(decision.fallback_policy, tuple)
    assert decision.fallback_policy == (
        "try-secondary-generator",
        "human-handoff",
    )


def test_fallback_policy_reassignment_is_rejected():
    decision = _decision()

    with pytest.raises(AttributeError):
        decision.fallback_policy = ("different-tool",)


def test_fallback_policy_structural_mutation_is_rejected():
    decision = _decision()

    with pytest.raises(AttributeError):
        decision.fallback_policy.append("another-tool")
    with pytest.raises(TypeError):
        decision.fallback_policy[0] = "different-tool"


def test_constructor_defensively_copies_mutable_fallback_policy_input():
    policy = ["try-secondary-generator"]
    decision = _decision(fallback_policy=policy)

    policy.append("human-handoff")

    assert len(decision.fallback_policy) == 1
    assert decision.fallback_policy[0] == "try-secondary-generator"


def test_asdict_preserves_read_compatibility():
    decision = _decision()
    payload = asdict(decision)

    assert isinstance(payload["fallback_policy"], tuple)
    assert payload["fallback_policy"] == decision.fallback_policy
