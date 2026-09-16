from core.foundation.models import Context
from core.validation.lesson_quality import validate_lesson_structure


def _context(duration=30):
    return Context(
        context_id="ctx-001",
        level="A2",
        audience="adult ESL learners",
        duration_minutes=duration,
        group_size=10,
        objective="Students can book a table using a short restaurant conversation.",
        constraints=["Pair work"],
    )


def _lesson(total=30):
    return {
        "level": "A2",
        "audience": "adult ESL learners",
        "objectives": ["Students can book a table using a short restaurant conversation."],
        "stages": [
            {"name": "Warm-up", "minutes": 5},
            {"name": "Input", "minutes": 8},
            {"name": "Practice", "minutes": 10},
            {"name": "Communicative task", "minutes": total - 23},
        ],
        "assessment": "Pairs complete a short booking role-play using the target language.",
        "interaction": "pairs",
    }


def test_clean_lesson_is_ready():
    result = validate_lesson_structure(_context(), _lesson())
    assert result.status == "READY"
    assert result.checks["timing_alignment"] is True


def test_timing_mismatch_requires_revision():
    result = validate_lesson_structure(_context(30), _lesson(35))
    assert result.status == "REVISION_REQUIRED"
    assert any("Timing mismatch" in item for item in result.revision_required)


def test_level_mismatch_is_critical():
    lesson = _lesson()
    lesson["level"] = "B1"
    result = validate_lesson_structure(_context(), lesson)
    assert result.status == "CRITICAL_FAILURE"
    assert result.critical_failures


def test_missing_assessment_requires_revision():
    lesson = _lesson()
    lesson.pop("assessment")
    result = validate_lesson_structure(_context(), lesson)
    assert result.status == "REVISION_REQUIRED"
    assert any("Assessment" in item for item in result.revision_required)


def test_validator_does_not_mutate_authoritative_context():
    context = _context()
    original = (context.level, context.audience, context.objective, tuple(context.constraints))
    lesson = _lesson()
    lesson["level"] = "B1"
    validate_lesson_structure(context, lesson)
    assert (context.level, context.audience, context.objective, tuple(context.constraints)) == original
