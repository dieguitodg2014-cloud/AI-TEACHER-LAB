import pytest

from core.pedagogy.lesson_trajectory import LessonTrajectory, TrajectoryPhase


def _phase(
    phase="EXPERIENCE",
    production_level="P0",
    interaction_level="I0",
    demand_level="LOW",
    scaffolding=4,
):
    return TrajectoryPhase(
        phase=phase,
        production_level=production_level,
        interaction_level=interaction_level,
        demand_level=demand_level,
        scaffolding=scaffolding,
        purpose="Build access to the target language.",
    )


def _trajectory(**overrides):
    values = {
        "starting_point": "P0",
        "target_point": "P2",
        "phases": [
            _phase(),
            _phase(
                phase="COMMUNICATIVE_TASK",
                production_level="P2",
                interaction_level="I3",
                demand_level="HIGH",
                scaffolding=1,
            ),
        ],
        "final_evidence": "Observable student performance.",
    }
    values.update(overrides)
    return LessonTrajectory(**values)


def test_trajectory_requires_phases():
    with pytest.raises(ValueError, match="at least one"):
        LessonTrajectory(
            starting_point="P0",
            target_point="P0",
            phases=[],
            final_evidence="Evidence.",
        )


def test_first_phase_must_match_starting_point():
    with pytest.raises(ValueError, match="starting_point"):
        _trajectory(
            phases=[
                _phase(production_level="P1"),
                _phase(
                    phase="TRANSFER",
                    production_level="P2",
                    interaction_level="I4",
                    demand_level="HIGH",
                    scaffolding=0,
                ),
            ]
        )


def test_last_phase_must_match_target_point():
    with pytest.raises(ValueError, match="target_point"):
        _trajectory(
            phases=[
                _phase(),
                _phase(
                    phase="TRANSFER",
                    production_level="P1",
                    interaction_level="I2",
                    demand_level="MEDIUM",
                    scaffolding=2,
                ),
            ]
        )


def test_trajectory_is_immutable_and_phases_are_tuple():
    trajectory = _trajectory()

    assert isinstance(trajectory.phases, tuple)

    with pytest.raises(AttributeError):
        trajectory.target_point = "P3"

    with pytest.raises(AttributeError):
        trajectory.phases.append(_phase())


def test_phase_requires_purpose_and_valid_scaffolding():
    with pytest.raises(ValueError, match="purpose"):
        TrajectoryPhase(
            phase="NOTICE",
            production_level="P1",
            interaction_level="I1",
            demand_level="LOW",
            scaffolding=2,
            purpose="",
        )

    with pytest.raises(ValueError, match="between 0 and 4"):
        TrajectoryPhase(
            phase="NOTICE",
            production_level="P1",
            interaction_level="I1",
            demand_level="LOW",
            scaffolding=5,
            purpose="Notice the target language.",
        )
