"""Deterministic course/session memory for cross-lesson continuity.

Course Memory stores only completed lesson/session facts. It does not infer
learner performance and does not adapt pedagogy; those responsibilities remain
in the deferred Learning Evidence and Adaptation tracks.
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
class CourseMemory:
    """Immutable snapshot of the completed history of one course."""

    course_id: str
    session_count: int = 0
    completed_lesson_ids: tuple[str, ...] = ()
    completed_topics: tuple[str, ...] = ()
    last_lesson_id: str | None = None
    last_topic: str | None = None
    last_level: str | None = None
    last_objective: str | None = None
    last_duration_minutes: int | None = None

    def __post_init__(self) -> None:
        course_id = str(self.course_id).strip()
        if not course_id:
            raise ValueError("course_id is required")
        if self.session_count < 0:
            raise ValueError("session_count cannot be negative")
        lesson_ids = tuple(str(item).strip() for item in self.completed_lesson_ids)
        if any(not item for item in lesson_ids):
            raise ValueError("completed_lesson_ids cannot contain empty values")
        if len(set(lesson_ids)) != len(lesson_ids):
            raise ValueError("completed_lesson_ids must be unique")
        topics = tuple(str(item).strip() for item in self.completed_topics if str(item).strip())
        if self.session_count != len(lesson_ids):
            raise ValueError("session_count must equal completed_lesson_ids length")
        if len(topics) > self.session_count:
            raise ValueError("completed_topics cannot exceed session_count")
        if self.last_duration_minutes is not None and self.last_duration_minutes <= 0:
            raise ValueError("last_duration_minutes must be positive")
        object.__setattr__(self, "course_id", course_id)
        object.__setattr__(self, "completed_lesson_ids", lesson_ids)
        object.__setattr__(self, "completed_topics", topics)

    @property
    def next_session_number(self) -> int:
        return self.session_count + 1

    def record_completed_lesson(
        self,
        lesson_id: str,
        *,
        topic: str | None = None,
        level: str | None = None,
        objective: str | None = None,
        duration_minutes: int | None = None,
    ) -> "CourseMemory":
        """Return a new snapshot after recording a completed lesson.

        Recording the same lesson twice is idempotent so retries cannot inflate
        the course session count.
        """
        lesson_id = str(lesson_id).strip()
        if not lesson_id:
            raise ValueError("lesson_id is required")
        if duration_minutes is not None and duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if lesson_id in self.completed_lesson_ids:
            return self

        normalized_topic = str(topic).strip() if topic is not None else ""
        return CourseMemory(
            course_id=self.course_id,
            session_count=self.session_count + 1,
            completed_lesson_ids=self.completed_lesson_ids + (lesson_id,),
            completed_topics=(
                self.completed_topics + (normalized_topic,)
                if normalized_topic
                else self.completed_topics
            ),
            last_lesson_id=lesson_id,
            last_topic=normalized_topic or None,
            last_level=str(level).strip() if level is not None else None,
            last_objective=str(objective).strip() if objective is not None else None,
            last_duration_minutes=duration_minutes,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the immutable snapshot into JSON-compatible values."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CourseMemory":
        """Restore a snapshot from persisted JSON data."""
        return cls(
            course_id=data["course_id"],
            session_count=int(data.get("session_count", 0)),
            completed_lesson_ids=tuple(data.get("completed_lesson_ids", ())),
            completed_topics=tuple(data.get("completed_topics", ())),
            last_lesson_id=data.get("last_lesson_id"),
            last_topic=data.get("last_topic"),
            last_level=data.get("last_level"),
            last_objective=data.get("last_objective"),
            last_duration_minutes=(
                int(data["last_duration_minutes"])
                if data.get("last_duration_minutes") is not None
                else None
            ),
        )


class CourseMemoryStore(Protocol):
    def get(self, course_id: str) -> CourseMemory: ...
    def save(self, memory: CourseMemory) -> CourseMemory: ...


class InMemoryCourseMemoryStore:
    """Process-local store useful for tests and ephemeral runtime sessions."""

    def __init__(self) -> None:
        self._items: dict[str, CourseMemory] = {}
        self._lock = RLock()

    def get(self, course_id: str) -> CourseMemory:
        course_id = str(course_id).strip()
        if not course_id:
            raise ValueError("course_id is required")
        with self._lock:
            return self._items.get(course_id, CourseMemory(course_id=course_id))

    def save(self, memory: CourseMemory) -> CourseMemory:
        with self._lock:
            self._items[memory.course_id] = memory
            return memory


class JsonCourseMemoryStore:
    """Durable JSON-backed store for course memory snapshots."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("course memory store must contain a JSON object")
        return data

    def get(self, course_id: str) -> CourseMemory:
        course_id = str(course_id).strip()
        if not course_id:
            raise ValueError("course_id is required")
        data = self._read()
        raw = data.get(course_id)
        return CourseMemory(course_id=course_id) if raw is None else CourseMemory.from_dict(raw)

    def save(self, memory: CourseMemory) -> CourseMemory:
        data = self._read()
        data[memory.course_id] = memory.to_dict()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=f"{self.path.name}.", dir=self.path.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\\n")
            os.replace(temp_path, self.path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        return memory
