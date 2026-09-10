"""First end-to-end executable workflow for lesson planning and generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from core.context.engine import build_context
from core.foundation.models import Context, LearningPlanDecision, LevelDecision, ResourceDecision, TaskPacket
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
    resource_decision: ResourceDecision | None
    resource_task: TaskPacket | None
    resource_tool: ToolCandidate | None
    resource_handoff: dict[str, Any] | None
    generation: dict[str, Any] | None
    missing: list[str]
    errors: list[str]


def run_lesson_planning(
    request: dict[str, Any],
    *,
    tools: list[ToolCandidate] | None = None,
    generators: dict[str, Callable] | None = None,
    tool_config_path: str | Path | None = None,
) -> VerticalSliceResult:
    """Run context, pedagogy, resources, task packaging, tool selection and generation."""
    context_result = build_context(request)

    if context_result.errors or context_result.missing or context_result.context is None:
        return VerticalSliceResult("MISSING_CONTEXT" if context_result.missing else "FAILED", context_result.context, None, None, None, None, None, None, None, context_result.missing, context_result.errors)

    try:
        level_decision = decide_level(context_result.context)
        learning_plan = decide_learning_plan(context_result.context, level_decision)
        resource_decision = decide_resource(context_result.context, learning_plan)
        learning_plan = apply_resource_decision(learning_plan, resource_decision)
        resource_task = build_resource_task_packet(context_result.context, learning_plan, resource_decision)
    except (ValueError, OSError, KeyError) as exc:
        return VerticalSliceResult("FAILED", context_result.context, None, None, None, None, None, None, None, [], [str(exc)])

    if tools is None and generators is None:
        return VerticalSliceResult("PLANNED", context_result.context, level_decision, learning_plan, resource_decision, resource_task, None, None, None, [], [])

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
        return VerticalSliceResult("FAILED", context_result.context, level_decision, learning_plan, resource_decision, resource_task, None, None, None, [], [f"TOOL_REGISTRY_ERROR:{exc}"])

    resource_tool = select_resource_tool(resource_task, selected_tools, free_first=free_first)
    resource_handoff = (
        build_resource_handoff(context_result.context, resource_task)
        if resource_task is not None and resource_tool is None
        else None
    )

    # A resource-only planning request does not require a lesson generator.
    # Keep the workflow in PLANNED state so resource orchestration can be
    # inspected independently from lesson generation. A missing generator is
    # a handoff only when there is no resource task and the caller has supplied
    # tools, meaning the request is entering the lesson-generation path.
    if generators is None:
        if resource_task is not None:
            return VerticalSliceResult("PLANNED", context_result.context, level_decision, learning_plan, resource_decision, resource_task, resource_tool, resource_handoff, None, [], [])
        return VerticalSliceResult("HUMAN_HANDOFF", context_result.context, level_decision, learning_plan, resource_decision, resource_task, resource_tool, resource_handoff, {"status": "HUMAN_HANDOFF", "tool_id": None, "result": None, "errors": ["GENERATOR_UNAVAILABLE"]}, [], ["GENERATOR_UNAVAILABLE"])

    generation_request = build_generation_request(learning_plan, asdict(context_result.context))
    orchestration = GenerationOrchestrator(selected_tools, generators)
    generation = orchestration.run(generation_request, free_first=free_first)
    return VerticalSliceResult(generation["status"], context_result.context, level_decision, learning_plan, resource_decision, resource_task, resource_tool, resource_handoff, generation, [], generation.get("errors", []))


def result_to_dict(result: VerticalSliceResult) -> dict[str, Any]:
    """Serialize the workflow result for an API, CLI, or future interface."""
    return asdict(result)
