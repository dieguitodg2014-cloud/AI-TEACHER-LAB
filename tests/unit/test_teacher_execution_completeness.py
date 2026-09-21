from core.quality.teacher_execution_completeness import (
    validate_teacher_execution_completeness,
)


def _complete_execution() -> dict:
    return {
        "teacher_explanation": "Explain the target language with clear examples.",
        "target_language": ["should + base verb"],
        "language_bank": ["You should...", "Why don't you...?"],
        "teacher_talk": ["Look at the example.", "Now practice with a partner."],
        "ccqs": ["Is this advice?", "Do we use the base verb?"],
        "examples": ["You should rest.", "Let's go home."],
        "scaffolding": ["Provide a sentence frame."],
        "materials": ["Board", "Worksheet"],
        "worksheet": {"task": "Complete the sentences."},
        "role_cards": ["Student A: Give advice.", "Student B: Respond."],
        "assessment_checklist": ["Uses target language.", "Gives appropriate advice."],
        "common_errors": {
            "error": "should to go",
            "correction": "should go",
        },
        "answer_key": {
            "1": "should",
            "2": "Let's",
        },
        "exit_ticket": {
            "task": "Give one piece of advice.",
        },
    }


def test_missing_teacher_execution_is_rejected():
    errors = validate_teacher_execution_completeness(None)

    assert errors == ["TEACHER_EXECUTION_MISSING"]


def test_non_mapping_teacher_execution_is_rejected():
    errors = validate_teacher_execution_completeness(["invalid"])

    assert errors == ["INVALID_TEACHER_EXECUTION"]


def test_missing_required_field_is_rejected():
    execution = _complete_execution()
    del execution["ccqs"]

    errors = validate_teacher_execution_completeness(execution)

    assert "TEACHER_EXECUTION_INCOMPLETE:ccqs" in errors


def test_empty_required_sequence_is_rejected():
    execution = _complete_execution()
    execution["examples"] = []

    errors = validate_teacher_execution_completeness(execution)

    assert "TEACHER_EXECUTION_INCOMPLETE:examples" in errors


def test_placeholder_sequence_is_rejected():
    execution = _complete_execution()
    execution["language_bank"] = ["Examples"]

    errors = validate_teacher_execution_completeness(execution)

    assert errors == []


def test_placeholder_text_is_rejected():
    execution = _complete_execution()
    execution["teacher_explanation"] = "..."

    errors = validate_teacher_execution_completeness(execution)

    assert "TEACHER_EXECUTION_INCOMPLETE:teacher_explanation" in errors


def test_empty_mapping_is_rejected():
    execution = _complete_execution()
    execution["answer_key"] = {}

    errors = validate_teacher_execution_completeness(execution)

    assert "TEACHER_EXECUTION_INCOMPLETE:answer_key" in errors


def test_complete_teacher_execution_is_accepted():
    execution = _complete_execution()

    errors = validate_teacher_execution_completeness(execution)

    assert errors == []