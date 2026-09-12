"""Configured runtime entry point for executable lesson generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.workflow.vertical_slice import VerticalSliceResult, run_lesson_planning
from tools.connectors.runtime_loader import load_runtime_generators

DEFAULT_TOOL_CONFIG = Path(__file__).resolve().parents[2] / "config" / "tools.json"


def run_configured_lesson_planning(
    request: dict[str, Any],
    *,
    tool_config_path: str | Path | None = None,
    produced_resource: dict[str, Any] | None = None,
) -> VerticalSliceResult:
    """Run the vertical slice using generators resolved from tool configuration.

    ``produced_resource`` optionally carries a resource returned by an external
    producer so the main workflow can validate it before continuing.
    """
    config_path = tool_config_path or DEFAULT_TOOL_CONFIG
    try:
        generators = load_runtime_generators(config_path)
    except (OSError, ValueError, TypeError) as exc:
        return VerticalSliceResult(
            status="FAILED",
            context=None,
            level_decision=None,
            learning_plan=None,
            assessment_decision=None,
            resource_decision=None,
            resource_task=None,
            resource_tool=None,
            resource_handoff=None,
            resource_validation=None,
            generation=None,
            missing=[],
            errors=[f"RUNTIME_CONNECTOR_ERROR:{exc}"],
        )

    return run_lesson_planning(
        request,
        generators=generators,
        tool_config_path=config_path,
        produced_resource=produced_resource,
    )
