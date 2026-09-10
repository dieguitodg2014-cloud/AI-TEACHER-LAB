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
    constraints: list[str] = field(default_factory=list)
    group_size: int | None = None
    topic: str | None = None
    prior_knowledge: list[str] = field(default_factory=list)
    technology: list[str] = field(default_factory=list)
    teacher_preferences: dict[str, Any] = field(default_factory=dict)


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
    sequence: list[ActivityPlan]
    total_minutes: int
    evidence_of_learning: str
    resource_need: str = ""


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
    constraints: list[str]
    quality_criteria: list[str]
    course_id: str = ""
    lesson_id: str = ""
    audience: str = ""
    input_materials: list[str] = field(default_factory=list)
    preferred_tool: str = ""
    fallback_tool: str = ""
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "HUMAN_HANDOFF"] = "PENDING"


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
