"""Executable end-to-end lesson planning vertical slice."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from core.assessment.decision_engine import decide_assessment
from core.context.engine import build_context
from core.context.request_interpreter import interpret_request
from core.generation.revision import generate_with_revision
from core.orchestration.generation_orchestrator import GenerationOrchestrator
from core.orchestration.provider_contract import validate_provider_output
from core.orchestration.provider_task_eligibility import validate_provider_task_eligibility
from core.orchestration.tool_selector import ToolCandidate
from core.pedagogy.sequence_planner import SequencePlanner, SequenceRequest
from core.pedagogy.level_planner import build_level_plan
from core.progression.level_control import decide_level
from core.resources.decision_engine import apply_resource_decision, decide_resource
from core.resources.output_validator import ResourceValidationResult, validate_resource_output
from core.validation.lesson_quality import LessonQualityValidator, LessonValidationResult, validate_lesson_structure
from tools.registry import ToolRegistry
from tools.registry.config_loader import load_tool_registry_config


@dataclass(frozen=True)
class VerticalSliceResult:
    status: str
    context: Any
    level_decision: Any
    learning_plan: Any
    assessment_decision: Any
    resource_decision: Any
    resource_task: Any
    resource_tool: Any
    resource_handoff: Any
    resource_validation: ResourceValidationResult | None
    generation: dict[str, Any] | None
    missing: list[str]
    errors: list[str]

    @property
    def resource_generation(self) -> dict[str, Any] | None:
        """Backward-compatible alias for the resource-generation result.

        ``generation`` is the established public field used by the workflow
        contract. Resource-producing callers historically accessed the same
        payload as ``resource_generation``; expose that alias without creating
        a second mutable source of truth.
        """
        return self.generation


def run_lesson_planning(
    request: dict[str, Any] | str,
    *,
    tools: list[ToolCandidate] | None = None,
    generators: dict[str, Callable] | None = None,
    tool_config_path: str | Path | None = None,
    produced_resource: dict[str, Any] | None = None,
    revision_count: int = 0,
    independent_validator: Callable[..., LessonValidationResult] | LessonQualityValidator | None = validate_lesson_structure,
) -> VerticalSliceResult:
    """Run context, pedagogy, assessment, lesson validation, resources and generation.

    ``independent_validator`` is provider-neutral and receives the authoritative
    Context plus approved learning plan. It runs after generation and after each
    revision, before resource production. Pass ``None`` to disable this gate only
    for workflows that intentionally manage validation elsewhere.
    """
    structured_request = interpret_request(request)
    context_result = build_context(structured_request)
    if context_result.context is None:
        return VerticalSliceResult(
            "MISSING_INPUT",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            context_result.missing,
            context_result.errors,
        )

    context = context_result.context
    level_decision = decide_level(context)
    level_plan = build_level_plan(level_decision, context)
    sequence_request = SequenceRequest(
        level=context.level,
        duration_minutes=context.duration_minutes,
        interaction=structured_request.get("interaction", "pair"),
        primary_skill=structured_request.get("skill", "speaking"),
        requires_communication=structured_request.get("requires_communication", True),
        requires_assessment=structured_request.get("requires_assessment", True),
    )
    learning_plan = SequencePlanner().plan(sequence_request)
    assessment_decision = decide_assessment(context, learning_plan)
    resource_decision = decide_resource(context, learning_plan, assessment_decision)
    resource_task = apply_resource_decision(resource_decision, context, learning_plan)

    selected_tools = tools or []
    generators = generators or {}
    resource_tool = None
    resource_handoff = None
    resource_validation = None

    if resource_task is not None:
        if tools:
            resource_tool = next((tool for tool in tools if "resource_generation" in tool.capabilities), None)
        if resource_tool is None:
            resource_handoff = {"status": "HUMAN_HANDOFF", "reason": "NO_RESOURCE_PROVIDER"}
        elif produced_resource is not None:
            resource_errors = validate_provider_output(produced_resource)
            if resource_errors:
                resource_validation = ResourceValidationResult(
                    validation_id="resource-return-provider",
                    status="REJECT",
                    score=0.0,
                    critical_failure=True,
                    checks={},
                    blocking_errors=tuple(resource_errors),
                )
            else:
                resource_validation = validate_resource_output(produced_resource, resource_task)

    generation_request = {
        "level": context.level,
        "objective": context.objective,
        "duration_minutes": context.duration_minutes,
        "topic": context.topic,
        "constraints": list(context.constraints),
        "assessment_decision": asdict(assessment_decision) if assessment_decision else None,
        "sequence": [asdict(item) for item in learning_plan.sequence],
    }
    orchestration = GenerationOrchestrator(selected_tools, generators)
    generation = orchestration.run(
        generation_request,
        free_first=True,
        independent_validator=independent_validator,
        validation_context=context,
        learning_plan=learning_plan,
    )
    return VerticalSliceResult(
        generation["status"],
        context,
        level_decision,
        learning_plan,
        assessment_decision,
        resource_decision,
        resource_task,
        resource_tool,
        resource_handoff,
        resource_validation,
        generation,
        [],
        generation.get("errors", []),
    )
