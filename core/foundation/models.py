"""Minimal typed models for the AI Teacher Lab MVP foundation.

The models mirror the executable contracts in data/schemas/mvp-contracts.schema.json.
They intentionally contain no provider-specific or UI-specific logic.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

Level = Literal["A0", "A1", "A2", "B1", "B2"]


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
    teacher_preferences: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize context sequences to immutable tuples at the boundary."""
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "prior_knowledge", tuple(self.prior_knowledge))
        object.__setattr__(self, "technology", tuple(self.technology))


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
        """Normalize the pedagogical sequence to an immutable tuple."""
        object.__setattr__(self, "sequence", tuple(self.sequence))


@dataclass(frozen=True)
class AssessmentDecision:
    assessment_id: str
    type: Literal["FORMATIVE", "PERFORMANCE", "WRITTEN", "ORAL", "MIXED"]
    target: str
    evidence: str
    success_criteria: tuple[str, ...]

    def __post_init__(self) -> None:
        """Normalize assessment criteria to an immutable tuple."""
        object.__setattr__(self, "success_criteria", tuple(self.success_criteria))


@dataclass(frozen=True)
class ResourceDecision:
    decision_id: str
    action: Literal["CREATE", "REUSE", "ADAPT", "OMIT", "NO_RESOURCE_REQUIRED"]
    purpose: str
    resource_type: str = ""
    reason: str = ""
    required: bool = False
    source_based: bool = False
    visual: bool = False
    preferred_tool: str = ""
    fallback_tool: str = ""


@dataclass(frozen=True)
class ToolDecision:
    decision_id: str
    task_type: str
    selected_tool: str
    fallback_policy: tuple[str, ...]
    human_handoff_allowed: bool
    reason: str = ""

    def __post_init__(self) -> None:
        """Normalize fallback policy so the decision cannot be mutated after creation."""
        object.__setattr__(self, "fallback_policy", tuple(self.fallback_policy))


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
    input_materials: tuple[str, ...] = ()
    preferred_tool: str = ""
    fallback_tool: str = ""
    source_based: bool = False
    visual: bool = False
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "HUMAN_HANDOFF"] = "PENDING"

    def __post_init__(self) -> None:
        """Deep-freeze mutable sequence inputs at the authoritative boundary."""
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
