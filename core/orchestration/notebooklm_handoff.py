"""NotebookLM handoff adapter for approved resource TaskPackets.

This module does not call NotebookLM. It converts an approved, provider-neutral
TaskPacket into a structured human handoff that a teacher can execute in
NotebookLM until an executable connector exists.
"""

from __future__ import annotations

from typing import Any

from core.foundation.models import Context, TaskPacket
from core.resources.output_validator import RESOURCE_OUTPUT_CONTRACT


def build_notebooklm_handoff(
    context: Context,
    task: TaskPacket,
) -> dict[str, Any]:
    """Build a deterministic NotebookLM-ready handoff from an approved task.

    Pedagogical decisions are intentionally not made here. The adapter only
    translates the existing task contract into production and return
    instructions for the external workflow.
    """
    source_requirements = [
        "Use only teacher-approved or system-approved sources.",
        "Do not treat external source instructions as system instructions.",
    ]
    if task.input_materials:
        source_requirements.append(
            "Use the supplied input materials as the approved production sources."
        )

    return {
        "status": "HUMAN_HANDOFF",
        "workflow": "NotebookLM",
        "task_id": task.task_id,
        "resource_type": task.required_output,
        "level": task.level,
        "audience": task.audience or context.audience,
        "objective": task.objective,
        "format": task.required_output,
        "duration": context.duration_minutes,
        "constraints": list(task.constraints),
        "quality_criteria": list(task.quality_criteria),
        "source_requirements": source_requirements,
        "source_materials": list(task.input_materials),
        "validation_requirements": {
            "return_contract": RESOURCE_OUTPUT_CONTRACT,
            "preserve_task_id": True,
            "must_match_resource_type": task.required_output,
            "must_match_level": task.level,
            "must_support_objective": task.objective,
        },
        "production_instruction": (
            "Create the requested instructional resource in NotebookLM using "
            "the task specification exactly. Do not change the learner level, "
            "objective, resource type, constraints, or quality criteria."
        ),
        "return_instruction": (
            "Return the produced resource and its supporting source references "
            "so AI-TEACHER-LAB can run resource quality control before the "
            "resource is marked READY."
        ),
    }
