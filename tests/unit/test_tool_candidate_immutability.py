from dataclasses import asdict

import pytest

from core.orchestration.tool_selector import ToolCandidate


def _candidate(capabilities=None):
    return ToolCandidate(
        tool_id="test-tool",
        capabilities=capabilities if capabilities is not None else {"lesson_generation"},
        quality=1.0,
        reliability=1.0,
        accessibility=1.0,
        speed=1.0,
        cost=0.0,
    )


def test_capabilities_are_stored_as_frozenset():
    candidate = _candidate({"lesson_generation"})
    assert isinstance(candidate.capabilities, frozenset)


def test_reassignment_is_rejected():
    candidate = _candidate()
    with pytest.raises(AttributeError):
        candidate.capabilities = frozenset({"resource_generation"})


def test_structural_capability_mutation_is_rejected():
    candidate = _candidate()
    with pytest.raises(AttributeError):
        candidate.capabilities.add("resource_generation")


def test_constructor_defensively_copies_mutable_capabilities():
    capabilities = {"lesson_generation"}
    candidate = _candidate(capabilities)

    capabilities.add("resource_generation")

    assert candidate.capabilities == frozenset({"lesson_generation"})


def test_asdict_preserves_frozen_capabilities():
    payload = asdict(_candidate())
    assert payload["capabilities"] == frozenset({"lesson_generation"})
