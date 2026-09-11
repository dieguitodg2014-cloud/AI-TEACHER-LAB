from core.assessment.decision_engine import decide_assessment
from core.foundation.models import ActivityPlan, LearningPlanDecision, LevelDecision


def make_level(level: str) -> LevelDecision:
    return LevelDecision(
        decision_id="level-test",
        level=level,
        linguistic_complexity="test",
        cognitive_demand="test",
        interaction_expectation="test",
        scaffolding="test",
        assessment_expectation="test",
    )


def make_plan(objective: str) -> LearningPlanDecision:
    return LearningPlanDecision(
        plan_id="plan-test",
        objective=objective,
        sequence=[
            ActivityPlan(
                activity_id="activity-1",
                purpose="practice",
                interaction="pairs",
                minutes=45,
                student_production="short responses",
            )
        ],
        total_minutes=45,
        evidence_of_learning="Learners discuss past experiences and ask follow-up questions.",
    )


def test_communicative_objective_selects_performance_assessment():
    objective = "Discuss past experiences and ask follow-up questions."
    decision = decide_assessment(
        objective=objective,
        level_decision=make_level("A2"),
        learning_plan=make_plan(objective),
    )

    assert decision.type == "PERFORMANCE"
    assert "communicative" in decision.target.lower()
    assert decision.evidence
    assert decision.success_criteria


def test_beginning_level_speaking_allows_emerging_fluency():
    objective = "Speak about yourself."
    decision = decide_assessment(
        objective=objective,
        level_decision=make_level("A0"),
        learning_plan=make_plan(objective),
    )

    assert decision.type == "PERFORMANCE"
    assert any("pauses" in criterion.lower() for criterion in decision.success_criteria)


def test_non_communicative_objective_uses_formative_evidence():
    objective = "Identify the main idea in a short text."
    decision = decide_assessment(
        objective=objective,
        level_decision=make_level("A2"),
        learning_plan=make_plan(objective),
    )

    assert decision.type == "FORMATIVE"
    assert decision.evidence
    assert len(decision.success_criteria) >= 2


def test_objective_must_match_learning_plan():
    try:
        decide_assessment(
            objective="Discuss past experiences.",
            level_decision=make_level("A2"),
            learning_plan=make_plan("Practice past experiences."),
        )
    except ValueError as exc:
        assert "learning plan objective" in str(exc).lower()
    else:
        raise AssertionError("Expected an objective mismatch error")
