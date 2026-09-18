"""Bounded, deterministic adaptation over recorded learning evidence.

Adaptation produces a recommendation for the next instructional step. It does
not mutate the approved lesson contract, change the learner level, infer
mastery, or rewrite course memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from core.evidence.learning_evidence import EvidenceRecord


@dataclass(frozen=True)
class AdaptationDecision:
    """Immutable recommendation derived from observable evidence."""

    adaptation_id: str
    course_id: str
    lesson_id: str
    action: str
    rationale: str
    basis_evidence_ids: tuple[str, ...]
    recommended_scaffolding_delta: int = 0
    preserve_level: bool = True

    def __post_init__(self) -> None:
        for name in ("adaptation_id", "course_id", "lesson_id", "action", "rationale"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if self.recommended_scaffolding_delta not in (-1, 0, 1):
            raise ValueError("recommended_scaffolding_delta must be -1, 0, or 1")
        if not self.preserve_level:
            raise ValueError("adaptation cannot change learner level")
        object.__setattr__(self, "basis_evidence_ids", tuple(self.basis_evidence_ids))


def decide_adaptation(
    evidence: Sequence[EvidenceRecord],
    *,
    adaptation_id: str = "adaptation-1",
) -> AdaptationDecision:
    """Create a bounded next-step recommendation from lesson evidence.

    Rules are deliberately simple and deterministic:
    - no evidence -> maintain the current instructional approach;
    - any explicit failure -> reinforce with more support;
    - otherwise mean score < 60 -> reinforce;
    - mean score < 80 -> guided practice;
    - otherwise -> extend practice.

    A score is used only when supplied. No score or success flag is converted
    into a claim about mastery.
    """
    records = tuple(evidence)
    if not records:
        return AdaptationDecision(
            adaptation_id=adaptation_id,
            course_id="unknown",
            lesson_id="unknown",
            action="MAINTAIN",
            rationale="No learning evidence was recorded; retain the current approach.",
            basis_evidence_ids=(),
        )

    course_ids = {record.course_id for record in records}
    lesson_ids = {record.lesson_id for record in records}
    if len(course_ids) != 1 or len(lesson_ids) != 1:
        raise ValueError("evidence must belong to one course and one lesson")

    failures = sum(record.success is False for record in records)
    scores = tuple(record.score for record in records if record.score is not None)
    mean_score = sum(scores) / len(scores) if scores else None

    if failures:
        action = "REINFORCE"
        delta = 1
        rationale = "Observed explicit failure; add support and repeat targeted practice."
    elif mean_score is not None and mean_score < 60:
        action = "REINFORCE"
        delta = 1
        rationale = "Observed evidence is below the reinforcement threshold; add support and repeat targeted practice."
    elif mean_score is not None and mean_score < 80:
        action = "GUIDED_PRACTICE"
        delta = 0
        rationale = "Observed evidence suggests additional guided practice before extension."
    else:
        action = "EXTEND"
        delta = -1
        rationale = "Observed evidence supports extending practice with slightly less scaffolding."

    return AdaptationDecision(
        adaptation_id=adaptation_id,
        course_id=records[0].course_id,
        lesson_id=records[0].lesson_id,
        action=action,
        rationale=rationale,
        basis_evidence_ids=tuple(record.evidence_id for record in records),
        recommended_scaffolding_delta=delta,
    )
