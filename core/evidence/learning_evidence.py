"""Deterministic storage of observable learning evidence.

This layer records what was observed against an approved lesson/activity. It
intentionally does not infer mastery, diagnose learners, or change pedagogy;
those responsibilities belong to later evidence-analysis/adaptation work.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Protocol


@dataclass(frozen=True)
class EvidenceRecord:
    """Immutable observation produced by a lesson or assessment."""

    evidence_id: str
    course_id: str
    lesson_id: str
    activity_id: str
    level: str
    objective: str
    evidence_type: str
    observation: str
    success: bool | None = None
    score: float | None = None
    criteria_met: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = {
            "evidence_id": self.evidence_id,
            "course_id": self.course_id,
            "lesson_id": self.lesson_id,
            "activity_id": self.activity_id,
            "level": self.level,
            "objective": self.objective,
            "evidence_type": self.evidence_type,
            "observation": self.observation,
        }
        for name, value in required.items():
            if not str(value).strip():
                raise ValueError(f"{name} is required")
        if self.score is not None and not 0 <= self.score <= 100:
            raise ValueError("score must be between 0 and 100")
        object.__setattr__(self, "criteria_met", tuple(str(item).strip() for item in self.criteria_met if str(item).strip()))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceRecord":
        return cls(
            evidence_id=data["evidence_id"],
            course_id=data["course_id"],
            lesson_id=data["lesson_id"],
            activity_id=data["activity_id"],
            level=data["level"],
            objective=data["objective"],
            evidence_type=data["evidence_type"],
            observation=data["observation"],
            success=data.get("success"),
            score=float(data["score"]) if data.get("score") is not None else None,
            criteria_met=tuple(data.get("criteria_met", ())),
        )


class LearningEvidenceStore(Protocol):
    def list_for_lesson(self, course_id: str, lesson_id: str) -> tuple[EvidenceRecord, ...]: ...
    def save(self, evidence: EvidenceRecord) -> EvidenceRecord: ...


class InMemoryLearningEvidenceStore:
    """Process-local evidence store for runtime and tests."""

    def __init__(self) -> None:
        self._items: dict[str, EvidenceRecord] = {}
        self._lock = RLock()

    def save(self, evidence: EvidenceRecord) -> EvidenceRecord:
        with self._lock:
            existing = self._items.get(evidence.evidence_id)
            if existing is not None:
                if existing != evidence:
                    raise ValueError("evidence_id already exists with different content")
                return existing
            self._items[evidence.evidence_id] = evidence
            return evidence

    def list_for_lesson(self, course_id: str, lesson_id: str) -> tuple[EvidenceRecord, ...]:
        with self._lock:
            return tuple(
                item for item in self._items.values()
                if item.course_id == course_id and item.lesson_id == lesson_id
            )


class JsonLearningEvidenceStore:
    """Durable JSON-backed evidence store."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("learning evidence store must contain a JSON object")
        return data

    def save(self, evidence: EvidenceRecord) -> EvidenceRecord:
        data = self._read()
        existing = data.get(evidence.evidence_id)
        if existing is not None and EvidenceRecord.from_dict(existing) != evidence:
            raise ValueError("evidence_id already exists with different content")
        data[evidence.evidence_id] = evidence.to_dict()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=f"{self.path.name}.", dir=self.path.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(temp_path, self.path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        return evidence

    def list_for_lesson(self, course_id: str, lesson_id: str) -> tuple[EvidenceRecord, ...]:
        data = self._read()
        return tuple(
            EvidenceRecord.from_dict(item)
            for item in data.values()
            if item.get("course_id") == course_id and item.get("lesson_id") == lesson_id
        )
