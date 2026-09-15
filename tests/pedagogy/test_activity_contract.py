from core.pedagogy.activity_contract import (
    ActivityGenerationContract,
    ActivityContractValidator,
)


def contract(**overrides):
    data = dict(
        activity_id="ACT-001",
        pattern_id="INTERVIEW",
        level="A1",
        objective_ids=("OBJ-001",),
        skill="SPEAKING",
        language_target=("What time do you...?",),
        vocabulary=("wake up", "go to work"),
        interaction="PAIR",
        cognitive_demand="COMMUNICATIVE_PRODUCTION",
        scaffolding=3,
        duration_minutes=12,
        evidence_expected=("both students ask and answer",),
    )
    data.update(overrides)
    return ActivityGenerationContract(**data)


def test_valid_a1_pair_speaking_contract():
    result = ActivityContractValidator().validate(contract())
    assert result.valid
    assert result.errors == ()


def test_missing_objective_is_invalid():
    result = ActivityContractValidator().validate(contract(objective_ids=()))
    assert not result.valid
    assert "objective_id" in result.errors[0]


def test_speaking_requires_language_target():
    result = ActivityContractValidator().validate(contract(language_target=()))
    assert not result.valid
    assert "language target" in result.errors[0]


def test_a0_low_scaffolding_warns():
    result = ActivityContractValidator().validate(contract(level="A0", scaffolding=1))
    assert result.valid
    assert any("A0" in warning for warning in result.warnings)


def test_include_exclude_overlap_is_invalid():
    result = ActivityContractValidator().validate(
        contract(must_include=("sentence frames",), must_not_include=("sentence frames",))
    )
    assert not result.valid
    assert any("overlap" in error for error in result.errors)


def test_pair_without_evidence_warns():
    result = ActivityContractValidator().validate(contract(evidence_expected=()))
    assert result.valid
    assert any("evidence" in warning for warning in result.warnings)
