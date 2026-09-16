from core.foundation.models import TaskPacket
from core.validation.lesson_quality import validate_lesson_structure


def _task(duration=30):
    return TaskPacket(
        task_id="lesson-001",
        task_type="LESSON_GENERATION",
        level="A2",
        audience="adult ESL learners",
        duration_minutes=duration,
        group_size=10,
        objective="Students can book a table using a short restaurant conversation.",
        required_output="lesson",
        constraints=("Pair work",),
        quality_criteria=("Objective alignment",),
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
    result = validate_lesson_structure(_task(), _lesson())
    assert result.status == "READY"
    assert result.checks["timing_alignment"] is True


def test_timing_mismatch_requires_revision():
    result = validate_lesson_structure(_task(30), _lesson(35))
    assert result.status == "REVISION_REQUIRED"
    assert any("Timing mismatch" in item for item in result.revision_required)


def test_level_mismatch_is_critical():
    lesson = _lesson()
    lesson["level"] = "B1"
    result = validate_lesson_structure(_task(), lesson)
    assert result.status == "CRITICAL_FAILURE"
    assert result.critical_failures


def test_missing_assessment_requires_revision():
    lesson = _lesson()
    lesson.pop("assessment")
    result = validate_lesson_structure(_task(), lesson)
    assert result.status == "REVISION_REQUIRED"
    assert any("Assessment" in item for item in result.revision_required)


def test_validator_does_not_mutate_task_packet():
    task = _task()
    original = (task.level, task.audience, task.objective, task.constraints)
    lesson = _lesson()
    lesson["level"] = "B1"
    validate_lesson_structure(task, lesson)
    assert (task.level, task.audience, task.objective, task.constraints) == original
