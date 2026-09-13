"""Golden tests for Bionic's minimum-effective-sequence planner."""

import pytest

from core.pedagogy.sequence_planner import SequencePlanner, SequenceRequest


class TestSequencePlanner:
    def test_a1_daily_routines_60_minute_speaking_pair(self):
        request = SequenceRequest(
            level="A1",
            duration_minutes=60,
            primary_skill="SPEAKING",
            interaction="PAIR",
            requires_communication=True,
            requires_assessment=True,
        )

        plan = SequencePlanner().plan(request)

        assert plan.uncovered_roles == ()
        assert plan.total_minutes <= 60
        assert plan.pattern_ids == (
            "MODEL_AND_REPEAT",
            "VISUAL_NOTICING",
            "CONTROLLED_PRACTICE",
            "GUIDED_PRODUCTION",
            "INTERVIEW",
            "EXIT_TICKET",
        )

    def test_planner_does_not_add_unnecessary_patterns(self):
        request = SequenceRequest(
            level="A1",
            duration_minutes=60,
            primary_skill="SPEAKING",
            interaction="PAIR",
            requires_communication=True,
            requires_assessment=True,
        )

        plan = SequencePlanner().plan(request)

        assert "SURVEY" not in plan.pattern_ids
        assert "ROLE_PLAY" not in plan.pattern_ids
        assert "FIND_SOMEONE_WHO" not in plan.pattern_ids
        assert len(plan.pattern_ids) == len(set(plan.pattern_ids))

    def test_short_lesson_reports_uncovered_roles_instead_of_inventing_time(self):
        request = SequenceRequest(
            level="A1",
            duration_minutes=12,
            primary_skill="SPEAKING",
            interaction="PAIR",
            requires_communication=True,
            requires_assessment=True,
        )

        plan = SequencePlanner().plan(request)

        assert plan.total_minutes <= 12
        assert plan.uncovered_roles
        assert plan.warnings

    def test_invalid_duration_is_rejected(self):
        request = SequenceRequest(
            level="A1",
            duration_minutes=0,
            primary_skill="SPEAKING",
        )

        with pytest.raises(ValueError):
            SequencePlanner().plan(request)
