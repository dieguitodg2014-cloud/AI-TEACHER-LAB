from core.workflow.vertical_slice import run_lesson_planning


REQUEST = {
    "level": "A2",
    "audience": "adult ESL learners",
    "duration_minutes": 90,
    "objective": "Understand a short conversation and identify key information.",
    "topic": "Listening for key information",
    "constraints": ["Students need listening practice"],
}


VALID_RESOURCE = {
    "resource_type": "audio",
    "level": "A2",
    "objective": REQUEST["objective"],
    "content": "A short conversation between two adults about making a weekend appointment.",
}


def test_vertical_slice_accepts_valid_produced_resource():
    result = run_lesson_planning(REQUEST, produced_resource=VALID_RESOURCE)

    assert result.status == "PLANNED"
    assert result.resource_task is not None
    assert result.resource_validation is not None
    assert result.resource_validation.status == "READY"
    assert result.resource_validation.critical_failure is False
    assert result.resource_validation.score == 100.0


def test_vertical_slice_requests_revision_for_incomplete_quality_evidence():
    resource = {
        **VALID_RESOURCE,
        "quality_criteria_addressed": [
            "Directly support the stated learning objective.",
        ],
    }

    result = run_lesson_planning(REQUEST, produced_resource=resource)

    assert result.status == "REVISION_REQUIRED"
    assert result.resource_validation is not None
    assert result.resource_validation.status == "REVISION_REQUIRED"
    assert result.resource_validation.critical_failure is False
    assert result.resource_handoff is not None
    assert result.resource_handoff["status"] == "REVISION_REQUIRED"
    assert result.resource_handoff["workflow"] == "NotebookLM"
    assert result.resource_handoff["validation_id"] == result.resource_validation.validation_id
    assert result.resource_handoff["failed_checks"] == ["quality_criteria_acknowledged"]
    assert result.resource_handoff["return_contract"]["required_fields"] == [
        "resource_type",
        "level",
        "objective",
        "content",
    ]


def test_vertical_slice_requests_revision_for_objective_declaration_mismatch():
    resource = {**VALID_RESOURCE, "objective": "Practice general listening."}

    result = run_lesson_planning(REQUEST, produced_resource=resource)

    assert result.status == "REVISION_REQUIRED"
    assert result.resource_validation is not None
    assert result.resource_validation.status == "REVISION_REQUIRED"
    assert result.resource_validation.critical_failure is False
    assert result.resource_validation.blocking_errors == []
    assert "objective" in result.resource_validation.feedback[0]


def test_vertical_slice_rejects_produced_resource_with_wrong_type():
    resource = {**VALID_RESOURCE, "resource_type": "presentation"}

    result = run_lesson_planning(REQUEST, produced_resource=resource)

    assert result.status == "REJECT"
    assert result.resource_validation is not None
    assert result.resource_validation.status == "REJECT"
    assert result.resource_validation.critical_failure is True
    assert "resource_type" in result.resource_validation.blocking_errors[0]


def test_vertical_slice_rejects_produced_resource_with_wrong_level():
    resource = {**VALID_RESOURCE, "level": "B1"}

    result = run_lesson_planning(REQUEST, produced_resource=resource)

    assert result.status == "REJECT"
    assert result.resource_validation is not None
    assert result.resource_validation.status == "REJECT"
    assert result.resource_validation.critical_failure is True
    assert "Level mismatch" in result.resource_validation.blocking_errors[0]


def test_vertical_slice_rejects_produced_resource_without_usable_content():
    resource = {**VALID_RESOURCE, "content": ""}

    result = run_lesson_planning(REQUEST, produced_resource=resource)

    assert result.status == "REJECT"
    assert result.resource_validation is not None
    assert result.resource_validation.status == "REJECT"
    assert result.resource_validation.critical_failure is True
    assert any("usable content" in error for error in result.resource_validation.blocking_errors)


def test_revision_round_trip_can_be_validated_again():
    first_resource = {
        **VALID_RESOURCE,
        "quality_criteria_addressed": [
            "Directly support the stated learning objective.",
        ],
    }

    first_result = run_lesson_planning(REQUEST, produced_resource=first_resource)

    assert first_result.status == "REVISION_REQUIRED"
    assert first_result.resource_handoff is not None

    revised_resource = {
        **VALID_RESOURCE,
        "quality_criteria_addressed": [
            "Directly support the stated learning objective.",
            "Match the approved learner level and audience.",
            "Be usable within the planned lesson time.",
            "Do not introduce unnecessary content or complexity.",
        ],
    }

    second_result = run_lesson_planning(
        REQUEST,
        produced_resource=revised_resource,
        revision_count=1,
    )

    assert second_result.status == "PLANNED"
    assert second_result.resource_validation is not None
    assert second_result.resource_validation.status == "READY"
    assert second_result.resource_validation.score == 100.0
    assert second_result.resource_handoff is not None
    assert "return_contract" in second_result.resource_handoff


def test_repeated_revision_failure_triggers_redesign():
    resource = {
        **VALID_RESOURCE,
        "quality_criteria_addressed": [
            "Directly support the stated learning objective.",
        ],
    }

    result = run_lesson_planning(
        REQUEST,
        produced_resource=resource,
        revision_count=1,
    )

    assert result.status == "REJECT_AND_REDESIGN"
    assert result.resource_validation is not None
    assert result.resource_validation.status == "REJECT_AND_REDESIGN"
    assert result.resource_validation.critical_failure is False
    assert result.resource_handoff is None
    assert any("Redesign" in error for error in result.errors)
