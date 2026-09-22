from core.quality.alignment_validator import validate_teacher_facing_alignment


def complete_lesson():
    return {
        "objective": "Students will give advice about everyday problems.",
        "teacher_execution": {
            "target_language": ["should + base verb"],
            "exit_ticket": {"prompt": "Give one piece of advice."},
        },
        "activities": [
            {
                "language_target": "should + base verb",
                "assessment_link": "Teacher checks the advice produced.",
            }
        ],
        "assessment": {
            "evidence": "Students produce spoken advice.",
            "success_criteria": ["Uses should correctly."],
        },
    }


def test_complete_teacher_facing_lesson_is_aligned():
    assert validate_teacher_facing_alignment(complete_lesson()) == []


def test_missing_target_language_is_rejected():
    lesson = complete_lesson()
    lesson["teacher_execution"]["target_language"] = []

    assert "ALIGNMENT_TARGET_LANGUAGE_MISSING" in (
        validate_teacher_facing_alignment(lesson)
    )


def test_activity_without_language_target_is_rejected():
    lesson = complete_lesson()
    lesson["activities"][0]["language_target"] = ""

    assert "ALIGNMENT_ACTIVITY_LANGUAGE_TARGET_MISSING:1" in (
        validate_teacher_facing_alignment(lesson)
    )


def test_activity_without_assessment_link_is_rejected():
    lesson = complete_lesson()
    lesson["activities"][0]["assessment_link"] = ""

    assert "ALIGNMENT_ACTIVITY_ASSESSMENT_LINK_MISSING:1" in (
        validate_teacher_facing_alignment(lesson)
    )


def test_missing_assessment_evidence_is_rejected():
    lesson = complete_lesson()
    lesson["assessment"]["evidence"] = ""

    assert "ALIGNMENT_ASSESSMENT_EVIDENCE_MISSING" in (
        validate_teacher_facing_alignment(lesson)
    )


def test_missing_exit_ticket_is_rejected():
    lesson = complete_lesson()
    lesson["teacher_execution"]["exit_ticket"] = {}

    assert "ALIGNMENT_EXIT_TICKET_MISSING" in (
        validate_teacher_facing_alignment(lesson)
    )