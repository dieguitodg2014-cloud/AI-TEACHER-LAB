from core.foundation.models import Context
from core.generation.revision import generate_with_revision
from core.validation.lesson_quality import LessonQualityValidator, LessonValidationResult, validate_lesson_structure


def _context():
    return Context(
        context_id="ctx-001",
        level="A2",
        audience="adult ESL learners",
        duration_minutes=30,
        objective="Discuss past experiences.",
        group_size=10,
    )


def _lesson(request):
    return {
        "level": request["level"],
        "objective": request["objective"],
        "duration_minutes": request["duration_minutes"],
        "activities": [{"name": "discussion"}],
    }


def _result(status, revision=(), critical=()):
    return LessonValidationResult(
        validation_id="test-validation",
        status=status,
        score=100.0 if status == "READY" else 50.0,
        checks={"independent": status == "READY"},
        revision_required=tuple(revision),
        critical_failures=tuple(critical),
    )


def test_revision_required_is_revalidated_before_acceptance():
    calls = []

    def generator(request, errors):
        calls.append(list(errors))
        return _lesson(request)

    def validator(context, lesson, **kwargs):
        if len(calls) == 1:
            return _result("REVISION_REQUIRED", revision=("Fix the interaction format.",))
        return _result("READY")

    result = generate_with_revision(
        generator,
        {"level": "A2", "objective": "Discuss past experiences.", "duration_minutes": 30},
        independent_validator=validator,
        validation_context=_context(),
        max_revisions=1,
    )

    assert result["status"] == "READY"
    assert result["attempts"] == 2
    assert calls[1] == ["Fix the interaction format."]
    assert result["independent_validation"].status == "READY"


def test_critical_independent_failure_routes_to_human_handoff():
    def generator(request, errors):
        return _lesson(request)

    def validator(context, lesson, **kwargs):
        return _result("CRITICAL_FAILURE", critical=("Level mismatch cannot be repaired normally.",))

    result = generate_with_revision(
        generator,
        {"level": "A2", "objective": "Discuss past experiences.", "duration_minutes": 30},
        independent_validator=validator,
        validation_context=_context(),
    )

    assert result["status"] == "HUMAN_HANDOFF"
    assert result["errors"] == ["Level mismatch cannot be repaired normally."]
    assert result["independent_validation"].status == "CRITICAL_FAILURE"


def test_object_validator_contract_is_supported():
    class StubValidator(LessonQualityValidator):
        def validate(self, context, lesson, *, learning_plan=None, request=None):
            return _result("READY")

    result = generate_with_revision(
        lambda request, errors: _lesson(request),
        {"level": "A2", "objective": "Discuss past experiences.", "duration_minutes": 30},
        independent_validator=StubValidator(),
        validation_context=_context(),
    )

    assert result["status"] == "READY"
    assert result["independent_validation"].status == "READY"


def test_structural_validator_accepts_authoritative_metadata_without_redundant_fields():
    lesson = {
        "level": "A2",
        "objective": "Discuss past experiences.",
        "activities": [
            {
                "name": "discussion",
                "assessment_link": "Teacher observes target language use.",
            }
        ],
    }

    result = validate_lesson_structure(_context(), lesson)

    assert result.status == "READY"
    assert result.checks["audience_alignment"] is True
    assert result.checks["objectives_present"] is True
    assert result.checks["assessment_present"] is True


def test_structural_validator_flags_explicit_audience_contradiction():
    lesson = {
        "level": "A2",
        "audience": "children",
        "objective": "Discuss past experiences.",
        "activities": [
            {"name": "discussion", "assessment_link": "Teacher observation."}
        ],
    }

    result = validate_lesson_structure(_context(), lesson)

    assert result.status == "REVISION_REQUIRED"
    assert result.checks["audience_alignment"] is False


def test_structural_validator_keeps_level_mismatch_critical():
    lesson = {
        "level": "B1",
        "objective": "Discuss past experiences.",
        "activities": [
            {"name": "discussion", "assessment_link": "Teacher observation."}
        ],
    }

    result = validate_lesson_structure(_context(), lesson)

    assert result.status == "CRITICAL_FAILURE"
    assert result.checks["level_alignment"] is False
