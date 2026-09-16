from dataclasses import asdict

import pytest

from core.foundation.models import Context, FrozenMapping


def _context(**overrides):
    values = {
        "context_id": "ctx-immutability",
        "level": "A2",
        "audience": "adult learners",
        "duration_minutes": 60,
        "objective": "Practice speaking",
        "constraints": ["Use pair work"],
        "prior_knowledge": ["Present Simple"],
        "technology": ["projector"],
        "teacher_preferences": {
            "pace": "slow",
            "formats": ["pairs"],
            "nested": {"feedback": "selective"},
        },
    }
    values.update(overrides)
    return Context(**values)


def test_contract_collections_are_immutable():
    context = _context()

    assert context.constraints == ("Use pair work",)
    assert context.prior_knowledge == ("Present Simple",)
    assert context.technology == ("projector",)
    assert isinstance(context.teacher_preferences, FrozenMapping)

    with pytest.raises(TypeError):
        context.constraints[0] = "No phones"
    with pytest.raises(TypeError):
        context.prior_knowledge[0] = "Past Simple"
    with pytest.raises(TypeError):
        context.technology[0] = "audio"
    with pytest.raises(TypeError):
        context.teacher_preferences["pace"] = "fast"


def test_nested_teacher_preferences_are_immutable():
    context = _context()

    with pytest.raises(TypeError):
        context.teacher_preferences["nested"]["feedback"] = "immediate"
    with pytest.raises(TypeError):
        context.teacher_preferences["formats"][0] = "groups"


def test_constructor_defensively_copies_mutable_inputs():
    constraints = ["Use pair work"]
    prior_knowledge = ["Present Simple"]
    technology = ["projector"]
    preferences = {"nested": {"feedback": "selective"}}

    context = _context(
        constraints=constraints,
        prior_knowledge=prior_knowledge,
        technology=technology,
        teacher_preferences=preferences,
    )

    constraints.append("No phones")
    prior_knowledge.append("Past Simple")
    technology.append("audio")
    preferences["nested"]["feedback"] = "immediate"

    assert context.constraints == ("Use pair work",)
    assert context.prior_knowledge == ("Present Simple",)
    assert context.technology == ("projector",)
    assert context.teacher_preferences["nested"]["feedback"] == "selective"


def test_asdict_preserves_mapping_read_compatibility():
    context = _context()
    payload = asdict(context)

    assert payload["constraints"] == ("Use pair work",)
    assert payload["prior_knowledge"] == ("Present Simple",)
    assert payload["technology"] == ("projector",)
    assert payload["teacher_preferences"]["pace"] == "slow"
