"""Post-lesson integration for Course Memory, Learning Evidence, and Adaptation.

This boundary is intentionally separate from lesson generation: a lesson is not
recorded as completed merely because generation reached READY. Completion must
be explicitly reported with observable evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from core.adaptation.adaptation_engine import AdaptationDecision, decide_adaptation
from core.evidence.learning_evidence import EvidenceRecord, LearningEvidenceStore
from core.memory.course_memory import CourseMemory, CourseMemoryStore


@dataclass(frozen=True)
class LessonOutcome:
    """Immutable result of explicitly recording a completed lesson."""

    memory: CourseMemory
    evidence: tuple[EvidenceRecord, ...]
    adaptation: AdaptationDecision


def record_lesson_outcome(
    *,
    memory_store: CourseMemoryStore,
    evidence_store: LearningEvidenceStore,
    course_id: str,
    lesson_id: str,
    topic: str | None,
    level: str,
    objective: str,
    duration_minutes: int,
    evidence: Sequence[EvidenceRecord],
    adaptation_id: str = "adaptation-1",
) -> LessonOutcome:
    """Persist a completed lesson and derive its bounded next-step guidance.

    The supplied evidence must belong to the same course and lesson. Course
    Memory is updated only after evidence is validated and persisted. The
    adaptation result is advisory and cannot alter the approved level or lesson
    contract.
    """
    records = tuple(evidence)
    for record in records:
        if record.course_id != course_id or record.lesson_id != lesson_id:
            raise ValueError("evidence must match course_id and lesson_id")
        evidence_store.save(record)

    memory = memory_store.get(course_id)
    updated_memory = memory.record_completed_lesson(
        lesson_id,
        topic=topic,
        level=level,
        objective=objective,
        duration_minutes=duration_minutes,
    )
    memory_store.save(updated_memory)

    lesson_evidence = evidence_store.list_for_lesson(course_id, lesson_id)
    adaptation = decide_adaptation(lesson_evidence, adaptation_id=adaptation_id)
    return LessonOutcome(updated_memory, lesson_evidence, adaptation)
