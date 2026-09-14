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
from core.orchestration.canva_provider import CanvaResourceProvider
from core.orchestration.capability_validation_registry import CapabilityValidationRegistry
from core.orchestration.generation_orchestrator import GenerationOrchestrator
from core.orchestration.notebooklm_provider import NotebookLMResourceProvider
from core.orchestration.resource_handoff import build_resource_handoff, build_resource_revision_handoff
from core.orchestration.resource_orchestrator import execute_resource_production_with_fallback, select_resource_tool
from core.orchestration.resource_provider import FunctionResourceProvider
from core.orchestration.task_packets import build_resource_task_packet
from core.orchestration.tool_selector import ToolCandidate
from core.pedagogy.decision_engine import decide_learning_plan
from core.progression.level_control import decide_level
from core.resources.acceptance_gate import ResourceAcceptanceGate
from core.resources.decision_engine import apply_resource_decision, decide_resource
from core.resources.output_validator import ResourceValidationResult, validate_resource_output
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
    resource_validation: ResourceValidationResult | None
    generation: dict[str, Any] | None
    missing: list[str]
    errors: list[str]


def run_lesson_planning(
    request: dict[str, Any] | str,
    *,
    tools: list[ToolCandidate] | None = None,
    generators: dict[str, Callable] | None = None,
    notebooklm_executor: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    canva_executor: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    tool_config_path: str | Path | None = None,
    produced_resource: dict[str, Any] | None = None,
    revision_count: int = 0,
    validation_registry: CapabilityValidationRegistry | None = None,
) -> VerticalSliceResult:
    """Run context, pedagogy, assessment, resources, validation and generation."""
    structured_request = interpret_request(request)
    context_result = build_context(structured_request)

    if context_result.errors or context_result.missing or context_result.context is None:
        return VerticalSliceResult("MISSING_CONTEXT" if context_result.missing else "FAILED", context_result.context, None, None, None, None, None, None, None, None, None, context_result.missing, context_result.errors)

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
        return VerticalSliceResult("FAILED", context_result.context, None, None, None, None, None, None, None, None, None, [], [str(exc)])

    resource_validation = None
    if produced_resource is not None:
        if resource_task is None:
            resource_validation = ResourceValidationResult(
                validation_id="resource-qc-no-task",
                status="REJECT",
                score=0.0,
                critical_failure=True,
                checks=(("resource_task_exists", False),),
                blocking_errors=("A produced resource was supplied, but the pedagogical decision did not create a Resource TaskPacket.",),
            )
            return VerticalSliceResult(
                "HUMAN_HANDOFF",
                context_result.context,
                level_decision,
                learning_plan,
                assessment_decision,
                resource_decision,
                resource_task,
                None,
                None,
                resource_validation,
                None,
                [],
                ["RESOURCE_TASK_MISSING_FOR_ACCEPTANCE"],
            )

        resource_validation = validate_resource_output(
            resource_task,
            produced_resource,
            revision_count=revision_count,
        )

        acceptance = ResourceAcceptanceGate().evaluate(resource_task, resource_validation)
        if acceptance.decision != "ACCEPT":
            revision_handoff = None
            if acceptance.decision == "REVISION_REQUIRED":
                revision_handoff = build_resource_revision_handoff(context_result.context, resource_task, resource_validation)
            return VerticalSliceResult(
                acceptance.decision,
                context_result.context,
                level_decision,
                learning_plan,
                assessment_decision,
                resource_decision,
                resource_task,
                None,
                revision_handoff,
                resource_validation,
                None,
                [],
                list(acceptance.reasons),
            )

        return VerticalSliceResult(
            "ACCEPTED",
            context_result.context,
            level_decision,
            learning_plan,
            assessment_decision,
            resource_decision,
            resource_task,
            None,
            None,
            resource_validation,
            {"status": "ACCEPTED", "tool_id": None, "result": produced_resource, "errors": []},
            [],
            [],
        )

    if tools is None and generators is None and notebooklm_executor is None and canva_executor is None:
        resource_handoff = build_resource_handoff(context_result.context, resource_task) if resource_task is not None else None
        return VerticalSliceResult("PLANNED", context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, None, resource_handoff, resource_validation, None, [], [])

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
        return VerticalSliceResult("FAILED", context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, None, None, resource_validation, None, [], [f"TOOL_REGISTRY_ERROR:{exc}"])

    resource_tool = select_resource_tool(
        resource_task,
        selected_tools,
        free_first=free_first,
        validation_registry=validation_registry,
    )
    resource_handoff = build_resource_handoff(context_result.context, resource_task) if resource_task is not None and resource_tool is None else None

    if resource_task is not None and (generators is not None or notebooklm_executor is not None or canva_executor is not None):
        providers = {tool_id: FunctionResourceProvider(generator) for tool_id, generator in (generators or {}).items() if callable(generator)}
        if notebooklm_executor is not None:
            providers["notebooklm"] = NotebookLMResourceProvider(notebooklm_executor)
        if canva_executor is not None:
            providers["canva"] = CanvaResourceProvider(canva_executor)

        resource_execution = execute_resource_production_with_fallback(
            resource_task,
            selected_tools,
            providers,
            max_revisions=max(0, 1 - revision_count),
            free_first=free_first,
            validation_registry=validation_registry,
        )
        selected_tool_id = resource_execution.get("tool_id")
        if selected_tool_id is not None:
            raw_resource_tool = next((tool for tool in selected_tools if tool.tool_id == selected_tool_id), resource_tool)
            resource_tool = (
                validation_registry.effective_tool(raw_resource_tool)
                if validation_registry is not None
                else raw_resource_tool
            )

        if resource_execution["status"] != "ACCEPTED":
            revision_handoff = None
            if resource_execution.get("validation") is not None and resource_execution["status"] == "REVISION_REQUIRED":
                revision_handoff = build_resource_revision_handoff(context_result.context, resource_task, resource_execution["validation"])
            return VerticalSliceResult(resource_execution["status"], context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, resource_tool, revision_handoff or resource_handoff or build_resource_handoff(context_result.context, resource_task), resource_execution.get("validation"), resource_execution, [], list(resource_execution.get("errors", [])))

        final_validation = resource_execution.get("validation")
        final_acceptance = ResourceAcceptanceGate().evaluate(resource_task, final_validation)
        if final_acceptance.decision != "ACCEPT":
            return VerticalSliceResult(final_acceptance.decision, context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, resource_tool, resource_handoff or build_resource_handoff(context_result.context, resource_task), final_validation, resource_execution, [], list(final_acceptance.reasons))

        return VerticalSliceResult("ACCEPTED", context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, resource_tool, None, final_validation, resource_execution, [], [])

    if generators is None:
        has_resource_capability = any("resource_generation" in tool.capabilities for tool in selected_tools)
        if resource_task is not None or has_resource_capability:
            return VerticalSliceResult("PLANNED", context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, resource_tool, resource_handoff, resource_validation, None, [], [])
        return VerticalSliceResult("HUMAN_HANDOFF", context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, resource_tool, resource_handoff, resource_validation, {"status": "HUMAN_HANDOFF", "tool_id": None, "result": None, "errors": ["GENERATOR_UNAVAILABLE"]}, [], ["GENERATOR_UNAVAILABLE"])

    generation_request = build_generation_request(learning_plan, asdict(context_result.context), assessment_decision)
    orchestration = GenerationOrchestrator(selected_tools, generators)
    generation = orchestration.run(generation_request, free_first=free_first)
    return VerticalSliceResult(generation["status"], context_result.context, level_decision, learning_plan, assessment_decision, resource_decision, resource_task, resource_tool, resource_handoff, resource_validation, generation, [], generation.get("errors", []))


def result_to_dict(result: VerticalSliceResult) -> dict[str, Any]:
    """Serialize the workflow result for an API, CLI, or future interface."""
    return asdict(result)
