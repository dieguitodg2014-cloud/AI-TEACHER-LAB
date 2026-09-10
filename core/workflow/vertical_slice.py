"""First end-to-end executable workflow for lesson planning and generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from core.context.engine import build_context
from core.foundation.models import Context, LearningPlanDecision, LevelDecision, ResourceDecision
from core.generation.lesson_generator import build_generation_request
from core.orchestration.generation_orchestrator import GenerationOrchestrator
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
    """Run request through context, pedagogy, resources, selection, generation and validation."""
    context_result = build_context(request)

    if context_result.errors or context_result.missing or context_result.context is None:
        return VerticalSliceResult(
            status="MISSING_CONTEXT" if context_result.missing else "FAILED",
            context=context_result.context,
            level_decision=None,
            learning_plan=None,
            resource_decision=None,
            generation=None,
            missing=context_result.missing,
            errors=context_result.errors,
        )

    try:
        level_decision = decide_level(context_result.context)
        learning_plan = decide_learning_plan(context_result.context, level_decision)
        resource_decision = decide_resource(context_result.context, learning_plan)
        learning_plan = apply_resource_decision(learning_plan, resource_decision)
    except (ValueError, OSError, KeyError) as exc:
        return VerticalSliceResult(
            status="FAILED",
            context=context_result.context,
            level_decision=None,
            learning_plan=None,
            resource_decision=None,
            generation=None,
            missing=[],
            errors=[str(exc)],
        )

    # Preserve planning-only behavior when no execution dependencies are supplied.
    if tools is None and generators is None:
        return VerticalSliceResult(
            status="PLANNED",
            context=context_result.context,
            level_decision=level_decision,
            learning_plan=learning_plan,
            resource_decision=resource_decision,
            generation=None,
            missing=[],
            errors=[],
        )

    free_first = True
    try:
        if tools is None:
            configured_tools, policy = load_tool_registry_config(
                tool_config_path or DEFAULT_TOOL_CONFIG
            )
            registry = ToolRegistry(configured_tools)
            selected_tools = registry.list_available()
            free_first = bool(policy.get("free_first", True))
        else:
            selected_tools = tools
    except (OSError, ValueError, TypeError) as exc:
        return VerticalSliceResult(
            status="FAILED",
            context=context_result.context,
            level_decision=level_decision,
            learning_plan=learning_plan,
            resource_decision=resource_decision,
            generation=None,
            missing=[],
            errors=[f"TOOL_REGISTRY_ERROR:{exc}"],
        )

    if generators is None:
        return VerticalSliceResult(
            status="HUMAN_HANDOFF",
            context=context_result.context,
            level_decision=level_decision,
            learning_plan=learning_plan,
            resource_decision=resource_decision,
            generation={
                "status": "HUMAN_HANDOFF",
                "tool_id": None,
                "result": None,
                "errors": ["GENERATOR_UNAVAILABLE"],
            },
            missing=[],
            errors=["GENERATOR_UNAVAILABLE"],
        )

    generation_request = build_generation_request(
        learning_plan,
        asdict(context_result.context),
    )
    orchestration = GenerationOrchestrator(selected_tools, generators)
    generation = orchestration.run(
        generation_request,
        free_first=free_first,
    )
    return VerticalSliceResult(
        status=generation["status"],
        context=context_result.context,
        level_decision=level_decision,
        learning_plan=learning_plan,
        resource_decision=resource_decision,
        generation=generation,
        missing=[],
        errors=generation.get("errors", []),
    )


def result_to_dict(result: VerticalSliceResult) -> dict[str, Any]:
    """Serialize the workflow result for an API, CLI, or future interface."""
    return asdict(result)
