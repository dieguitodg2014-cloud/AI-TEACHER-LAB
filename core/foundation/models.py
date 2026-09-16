"""Minimal typed models for the AI Teacher Lab MVP foundation.

The models mirror the executable contracts in data/schemas/mvp-contracts.schema.json.
They intentionally contain no provider-specific or UI-specific logic.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Literal

Level = Literal["A0", "A1", "A2", "B1", "B2"]


class FrozenMapping(Mapping[str, Any]):
    """Recursively immutable mapping used by foundation contracts.

    It keeps mapping-style reads while preventing mutation through the public
    contract. ``__deepcopy__`` preserves compatibility with ``dataclasses.asdict``.
    """

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        object.__setattr__(self, "_data", {key: _freeze(value) for key, value in (data or {}).items()})

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __deepcopy__(self, memo: dict[int, Any]) -> "FrozenMapping":
        memo[id(self)] = self
        return self

    def __repr__(self) -> str:
        return f"FrozenMapping({self._data!r})"


def _freeze(value: Any) -> Any:
    """Recursively convert common mutable containers into immutable values."""
    if isinstance(value, FrozenMapping):
        return value
    if isinstance(value, Mapping):
        return FrozenMapping(value)
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class Context:
    context_id: str
    level: Level
    audience: str
    duration_minutes: int
    objective: str
    constraints: tuple[str, ...] = ()
    group_size: int | None = None
    topic: str | None = None
    prior_knowledge: tuple[str, ...] = ()
    technology: tuple[str, ...] = ()
    teacher_preferences: FrozenMapping = field(default_factory=FrozenMapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "prior_knowledge", tuple(self.prior_knowledge))
        object.__setattr__(self, "technology", tuple(self.technology))
        object.__setattr__(self, "teacher_preferences", FrozenMapping(self.teacher_preferences))


@dataclass(frozen=True)
class LevelDecision:
    decision_id: str
    level: Level
    linguistic_complexity: str
    cognitive_demand: str
    interaction_expectation: str
    scaffolding: str
    assessment_expectation: str
    autonomy_expectation: str = ""
    grammar_precision: str = ""
    fluency_expectation: str = ""
    register: str = ""


@dataclass(frozen=True)
class ActivityPlan:
    activity_id: str
    purpose: str
    interaction: str
    minutes: int
    student_production: str = ""
    assessment_link: str = ""


@dataclass(frozen=True)
class LearningPlanDecision:
    plan_id: str
    objective: str
    sequence: tuple[ActivityPlan, ...]
    total_minutes: int
    evidence_of_learning: str
    resource_need: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "sequence", tuple(self.sequence))


@dataclass(frozen=True)
class AssessmentDecision:
    assessment_id: str
    type: Literal["FORMATIVE", "PERFORMANCE", "WRITTEN", "ORAL", "MIXED"]
    target: str
    evidence: str
    success_criteria: list[str]


@dataclass(frozen=True)
class ResourceDecision:
    decision_id: str
    action: Literal["CREATE", "REUSE", "ADAPT", "OMIT", "NO_RESOURCE_REQUIRED"]
    purpose: str
    resource_type: str = ""
    reason: str = ""
    required: bool = False


@dataclass(frozen=True)
class ToolDecision:
    decision_id: str
    task_type: str
    selected_tool: str
    fallback_policy: list[str]
    human_handoff_allowed: bool
    reason: str = ""


@dataclass(frozen=True)
class TaskPacket:
    task_id: str
    task_type: str
    objective: str
    level: Level
    required_output: str
    constraints: tuple[str, ...]
    quality_criteria: tuple[str, ...]
    course_id: str = ""
    lesson_id: str = ""
    audience: str = ""
    input_materials: tuple[str, ...] = field(default_factory=tuple)
    preferred_tool: str = ""
    fallback_tool: str = ""
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "HUMAN_HANDOFF"] = "PENDING"

    def __post_init__(self) -> None:
        """Normalize contract-owned collections into immutable tuples."""
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "quality_criteria", tuple(self.quality_criteria))
        object.__setattr__(self, "input_materials", tuple(self.input_materials))


@dataclass(frozen=True)
class QCChecks:
    level_alignment: bool
    objective_alignment: bool
    communicative_value: bool
    time_realism: bool
    linguistic_accuracy: bool
    assessment_alignment: bool


@dataclass(frozen=True)
class QCResult:
    qc_id: str
    status: Literal["READY", "ACCEPTABLE", "REVISION_REQUIRED", "REJECT_AND_REDESIGN"]
    score: float
    critical_failure: bool
    checks: QCChecks
    revision_required: bool = False
    feedback: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)
