from core.orchestration.provider_contract import validate_provider_output


def test_provider_output_contract_accepts_minimum_lesson_artifact():
    assert validate_provider_output(
        {
            "level": "A2",
            "objective": "Discuss past experiences.",
            "duration_minutes": 90,
            "activities": [],
        }
    ) == []


def test_provider_output_contract_rejects_non_object():
    assert validate_provider_output(["lesson"]) == ["PROVIDER_OUTPUT_NOT_OBJECT"]


def test_provider_output_contract_reports_missing_fields():
    assert validate_provider_output({}) == [
        "PROVIDER_OUTPUT_MISSING:level",
        "PROVIDER_OUTPUT_MISSING:objective",
        "PROVIDER_OUTPUT_MISSING:duration_minutes",
        "PROVIDER_OUTPUT_MISSING:activities",
    ]


def test_provider_output_contract_reports_invalid_types():
    errors = validate_provider_output(
        {
            "level": 2,
            "objective": ["objective"],
            "duration_minutes": True,
            "activities": {},
        }
    )

    assert errors == [
        "PROVIDER_OUTPUT_INVALID_TYPE:level",
        "PROVIDER_OUTPUT_INVALID_TYPE:objective",
        "PROVIDER_OUTPUT_INVALID_TYPE:duration_minutes",
        "PROVIDER_OUTPUT_INVALID_TYPE:activities",
    ]
