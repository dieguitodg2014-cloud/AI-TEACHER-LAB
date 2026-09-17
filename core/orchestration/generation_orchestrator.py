"""Connect tool selection to the controlled lesson generation cycle."""

from __future__ import annotations

from typing import Any, Callable

from core.foundation.models import Context, LearningPlanDecision
from core.generation.revision import generate_with_revision
from core.orchestration.provider_task_eligibility import validate_provider_task_eligibility
from core.orchestration.tool_selector import ToolCandidate, select_tool_decision
from core.validation.lesson_quality import LessonQualityValidator, LessonValidationResult


class GenerationOrchestrator:
    """Route a generation task through an immutable tool-selection decision."""

    def __init__(self, tools: list[ToolCandidate], generators: dict[str, Callable]):
        self._tools = tools
        self._generators = generators

    def run(
        self,
        generation_request: dict[str, Any],
        *,
        required_capabilities: set[str] | None = None,
        blocked_tools: set[str] | None = None,
        max_revisions: int = 2,
        free_first: bool = True,
        task_type: str = "LESSON_GENERATION",
        independent_validator: Callable[..., LessonValidationResult] | LessonQualityValidator | None = None,
        validation_context: Context | None = None,
        learning_plan: LearningPlanDecision | None = None,
    ) -> dict[str, Any]:
        capabilities = required_capabilities or {"lesson_generation"}
        decision = select_tool_decision(
            self._tools,
            capabilities,
            blocked_tools=blocked_tools,
            free_first=free_first,
            task_type=task_type,
        )

        if decision is None:
            return {
                "status": "HUMAN_HANDOFF",
                "tool_id": None,
                "result": None,
                "errors": ["NO_SUITABLE_TOOL"],
            }

        # Resolve exactly the tool named by the immutable decision. The
        # execution boundary must not call select_tool() again.
        tool = next(
            (candidate for candidate in self._tools if candidate.tool_id == decision.selected_tool),
            None,
        )
        if tool is None:
            return {
                "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
                "tool_id": decision.selected_tool,
                "result": None,
                "errors": ["SELECTED_TOOL_UNAVAILABLE"],
            }

        generator = self._generators.get(decision.selected_tool)
        if generator is None:
            return {
                "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
                "tool_id": decision.selected_tool,
                "result": None,
                "errors": ["GENERATOR_UNAVAILABLE"],
            }

        eligibility_errors = validate_provider_task_eligibility(
            tool,
            task_type,
            generator,
            required_capabilities=capabilities,
        )
        if eligibility_errors:
            return {
                "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
                "tool_id": decision.selected_tool,
                "result": None,
                "errors": eligibility_errors,
            }

        result = generate_with_revision(
            generator,
            generation_request,
            max_revisions=max_revisions,
            independent_validator=independent_validator,
            validation_context=validation_context,
            learning_plan=learning_plan,
        )
        return {
            "status": result["status"],
            "tool_id": decision.selected_tool,
            "result": result,
            "errors": result.get("errors", []),
        }
