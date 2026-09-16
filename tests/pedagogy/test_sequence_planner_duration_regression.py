"""Regression coverage for duration fitting in the sequence planner."""

from core.pedagogy.sequence_planner import PlannedPattern, SequencePlanner


def test_fit_to_duration_reduces_later_activities_without_dropping_roles():
    items = [
        PlannedPattern(pattern_id="A", sequence_role="EXPOSURE", timing_minutes=10),
        PlannedPattern(pattern_id="B", sequence_role="CONTROLLED_PRACTICE", timing_minutes=10),
        PlannedPattern(pattern_id="C", sequence_role="GUIDED_PRODUCTION", timing_minutes=10),
    ]

    fitted = SequencePlanner._fit_to_duration(items, 25)

    assert sum(item.timing_minutes for item in fitted) <= 25
    assert [item.pattern_id for item in fitted] == ["A", "B", "C"]
    assert all(item.timing_minutes >= 2 for item in fitted)
