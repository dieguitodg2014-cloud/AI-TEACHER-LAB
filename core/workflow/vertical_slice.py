"""First end-to-end executable workflow for lesson planning and generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from core.assessment.decision_engine import decide_assessment
from core.context.engine import build_context
from core.context.request_interpreter import interpret_request
from core.foundation.models import AssessmentDecision, Context, LearningPlanDecision, LevelDecision, ResourceDecision, TaskPacket
from core.generation.lesson_generator import build_generation_request
from core.orchestration.generation_orchestrator import GenerationOrchestrator
from core.orchestration.resource_handoff import build_resource_handoff
from core.orchestration.resource_orchestrator import select_resource_tool
from core.orchestration.task_packets import build_resource_task_packet
from core.orchestration.tool_selector import ToolCandidate
from core.pedagogy.decision_engine import decide_learning_plan
from core.progression.level_control import decide_level
from core.resources.decision_engine import apply_resource_decision, decide_resource
from tools.registry import ToolRegistry
from tools.registry.config_loader import load_tool_registry_config

DEFAULT_TOOL_CONFIG = Path(__file__).resolve().parents[2] / "config" / "tools.json"


@dataclass(frozen=True)
class VerticalSliceResult:
    status: str
    context: Context | None
    level_decision: LevelDecision | None
    learning_plan: LearningPlanDecision | None
    assessment_decision: AssessmentDecision | None
    resource_decision: ResourceDecision | None
    resource_task: TaskPacket | None
    resource_tool: ToolCandidate | None
    resource_handoff: dict[str, Any] | None
    generation: dict[str, Any] | None
    missing: list[str]
    errors: list[str]


def run_lesson_planning(
    request: dict[str, Any] | str,
    *,
    tools: list[ToolCandidate] | None = None,
    generators: dict[str, Callable] | None = None,
    tool_config_path: str | Path | None = None,
) -> VerticalSliceResult:
    """Run context, pedagogy, assessment, resources, packaging and generation."""
    structured_request = interpret_request(request)
    context_result = build_context(structured_request)

    if context_result.errors or context_result.missing or context_result.context is None:
        return VerticalSliceResult("MISSING_CONTEXT" if context_result.missing else "FAILED", context_result.context, None, None, None, None, None, None, None, None, context_result.missing, context_result.errors)

    try:
        level_decision = decide_level(context_result.context)
        learning_plan = decide_learning_plan(context_result.context, level_decision)
        assessment_decision = decide_assessment(
            objective=context_result.context.objective,
            level_decision=level_decision,
            learning_plan=learning_plan,
        )
        resource_decision = decide_resource(context_result.context, learning_plan)
        learning_plan = apply_resource_decision(learning_plan, resource_decision)
        resource_task = build_resource_task_packet(context_result.context, learning_plan, resource_decision)
    except (ValueError, OSError, KeyError) as exc:
        return VerticalSliceResult("FAILED", context_result.context, None, None, None, None, None, None, None, None, [], [str(exc)])

    if tools is None and generators is None:
        return VerticalSliceResult("PLANNED", context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, None, None, None, [], [])

    free_first = True
    try:
        if tools is None:
            configured_tools, policy = load_tool_registry_config(tool_config_path or DEFAULT_TOOL_CONFIG)
            registry = ToolRegistry(configured_tools)
            selected_tools = registry.list_available()
            free_first = bool(policy.get("free_first", True))
        else:
            selected_tools = tools
    except (OSError, ValueError, TypeError) as exc:
        return VerticalSliceResult("FAILED", context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, None, None, None, [], [f"TOOL_REGISTRY_ERROR:{exc}"])

    resource_tool = select_resource_tool(resource_task, selected_tools, free_first=free_first)
    resource_handoff = (
        build_resource_handoff(context_result.context, resource_task)
        if resource_task is not None and resource_tool is None
        else None
    )

    # When no lesson generator is supplied, distinguish resource-planning
    # mode from lesson-generation mode. A resource-capable tool indicates
    # that the caller is inspecting/planning the resource path, so generation
    # is not required yet. Otherwise the request is entering lesson generation
    # and the absence of a generator requires human handoff.
    if generators is None:
        has_resource_capability = any(
            "resource_generation" in tool.capabilities for tool in selected_tools
        )
        if resource_task is not None or has_resource_capability:
            return VerticalSliceResult("PLANNED", context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, resource_tool, resource_handoff, None, [], [])
        return VerticalSliceResult("HUMAN_HANDOFF", context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, resource_tool, resource_handoff, {"status": "HUMAN_HANDOFF", "tool_id": None, "result": None, "errors": ["GENERATOR_UNAVAILABLE"]}, [], ["GENERATOR_UNAVAILABLE"])

    generation_request = build_generation_request(learning_plan, asdict(context_result.context))
    orchestration = GenerationOrchestrator(selected_tools, generators)
    generation = orchestration.run(generation_request, free_first=free_first)
    return VerticalSliceResult(generation["status"], context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, resource_tool, resource_handoff, generation, [], generation.get("errors", []))


def result_to_dict(result: VerticalSliceResult) -> dict[str, Any]:
    """Serialize the workflow result for an API, CLI, or future interface."""
    return asdict(result)
